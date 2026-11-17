import os, re
for name in sorted(os.listdir("/home/demon/shorts_studio/dashboard/src/pages")):
    if not name.endswith(".tsx") or name.endswith(".test.tsx"):
        continue
    text = open(f"/home/demon/shorts_studio/dashboard/src/pages/{name}").read()
    queries = re.findall(r"useQuery\(\s*\{[^}]*queryKey:\s*\['([^']+)'\]", text, re.S)
    has_errorbox = bool(re.search(r"<ErrorBox", text))
    has_loading = bool(re.search(r"<Loading", text))
    has_empty = bool(re.search(r"<Empty", text))
    has_try = bool(re.search(r"try\b", text))
    print(f"{name:28} queries={queries} ErrorBox={has_errorbox} Loading={has_loading} Empty={has_empty}")