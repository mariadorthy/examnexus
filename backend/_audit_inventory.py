# @'
import os, re

print("=" * 60)
print("TESTS")
print("=" * 60)
for root, dirs, files in os.walk("tests"):
    for f in sorted(files):
        if not f.startswith("test_") or not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            body = fh.read()
        funcs = re.findall(r"^def (test_\w+)", body, flags=re.MULTILINE)
        print(f"{path}  ({len(funcs)} tests)")
        for fn in funcs:
            print(f"    - {fn}")

print()
print("=" * 60)
print("SERVICES")
print("=" * 60)
for root, dirs, files in os.walk("app/services"):
    for f in sorted(files):
        if not f.endswith(".py") or f.startswith("__"):
            continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            body = fh.read()
        funcs = re.findall(r"^def (\w+)", body, flags=re.MULTILINE)
        public = [fn for fn in funcs if not fn.startswith("_")]
        print(f"{path}  ({len(public)} public functions)")
        for fn in public:
            print(f"    - {fn}")

print()
print("=" * 60)
print("ROUTES")
print("=" * 60)
for root, dirs, files in os.walk("app/routes"):
    for f in sorted(files):
        if not f.endswith(".py") or f.startswith("__"):
            continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            body = fh.read()
        routes = re.findall(r"@\w+\.route\(\s*[\"']([^\"']+)", body)
        print(f"{path}  ({len(routes)} routes)")
        for r in routes:
            print(f"    - {r}")
# '@ | Out-File -Encoding utf8 _audit_inventory.py