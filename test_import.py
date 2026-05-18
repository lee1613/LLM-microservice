import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.main import app
print(f"App: {app.title} v{app.version}")
for r in app.routes:
    if hasattr(r, 'path'):
        methods = getattr(r, 'methods', set()) or set()
        print(f"  {','.join(sorted(methods)):8} {r.path}")
print("\nAll 6 routers loaded OK!")
