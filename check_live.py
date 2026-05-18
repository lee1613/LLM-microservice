import urllib.request, json, sys
url = "http://139.180.136.212/openapi.json"
with urllib.request.urlopen(url) as r:
    d = json.loads(r.read().decode())
info = d.get('info', {})
print(f"Title  : {info.get('title')}")
print(f"Version: {info.get('version')}")
print("Endpoints:")
for path, methods in d['paths'].items():
    for method in methods:
        print(f"  {method.upper():6} {path}")
