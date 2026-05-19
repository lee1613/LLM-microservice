import json
import re
from typing import Any, Dict, List, Optional
from openai import OpenAI

def call_llm_with_json_retry(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Calls the LLM and guarantees a JSON response using response_format and a reflection loop.
    Handles JSONDecodeError by feeding the error back to the LLM.
    """
    current_messages = list(messages)
    
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": current_messages,
            }
            if tools:
                kwargs["tools"] = tools
            else:
                kwargs["response_format"] = {"type": "json_object"}
                
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
                
            response = client.chat.completions.create(**kwargs)
            response_message = response.choices[0].message
            content = response_message.content or ""
            
            # If the model called tools, we assume the caller handles them differently.
            # This utility strictly expects the final content to be JSON.
            # But just in case, if there are tool calls, we return them alongside the content.
            if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                # Return raw response message if tool calls are present
                return response_message
                
            # Clean up the output in case the model ignored response_format (e.g. DeepSeek V3 <think> tags)
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            content = re.sub(r'^```(?:json)?', '', content.strip(), flags=re.MULTILINE).strip()
            content = re.sub(r'```$', '', content.strip(), flags=re.MULTILINE).strip()
            
            if not content:
                raise ValueError("LLM returned empty content.")
                
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to parse LLM JSON output after {max_retries} attempts. Last error: {e}. Output: {content}")
                
            # Reflection loop: feed error back
            current_messages.append({
                "role": "assistant",
                "content": response_message.content if hasattr(response_message, "content") else content
            })
            current_messages.append({
                "role": "user",
                "content": f"Your previous response was not valid JSON. Error: {e}. Please correct it and output ONLY valid JSON without markdown fences."
            })
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"LLM call failed after {max_retries} attempts. Last error: {e}")
            
            current_messages.append({
                "role": "user",
                "content": f"An error occurred: {e}. Please try again."
            })
