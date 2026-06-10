"""
Per-node load test for the LLM microservice.

Targets only the stateless LLM-heavy nodes (1, 3, 4) so that date/state
contamination in Nodes 5-6 does not cause false failures during load testing.

Usage:
    pip install locust
    locust -f test/locustfile.py --host http://149.28.144.51
    # Open http://localhost:8089 to configure users and start the test.

Headless (CI-friendly):
    locust -f test/locustfile.py --host http://149.28.144.51 \
        --headless -u 9 -r 1 --run-time 15m \
        --html test/load_report.html --csv test/load_results
"""
import json
import os

from locust import HttpUser, between, task

_GOLDEN_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "health-insurance-claim",
    "synthetic data",
    "claim_B001_full_pipeline.json",
)

with open(_GOLDEN_PATH) as _f:
    _GOLDEN = json.load(_f)

# Node 1 input — claim metadata using server-side scanned_files paths (no upload needed)
NODE1_CLAIM_DATA = json.dumps(_GOLDEN["stage_1_intake"]["_input"])

# Node 3 input = Node 2 output
NODE3_INPUT = _GOLDEN["stage_2_policy_verification"]["_output"]

# Node 4 input = Node 3 output
NODE4_INPUT = _GOLDEN["stage_3_eligibility_check"]["_output"]


class LLMLoadUser(HttpUser):
    """
    Each virtual user repeatedly calls the three stateless LLM nodes.
    task weights: Node 4 (medical review, agentic loop) is weighted highest
    because it is the most expensive and represents real throughput ceiling.
    """
    wait_time = between(0, 1)

    @task(1)
    def node1_intake(self):
        self.client.post(
            "/intake/process",
            data={"claim_data": NODE1_CLAIM_DATA},
            timeout=120,
            name="node1_intake",
        )

    @task(2)
    def node3_eligibility(self):
        self.client.post(
            "/eligibility/process",
            json=NODE3_INPUT,
            timeout=90,
            name="node3_eligibility",
        )

    @task(3)
    def node4_medical(self):
        self.client.post(
            "/medical/process",
            json=NODE4_INPUT,
            timeout=120,
            name="node4_medical",
        )
