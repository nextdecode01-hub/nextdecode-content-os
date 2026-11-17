import os, re
for name in sorted(os.listdir("/home/demon/shorts_studio/dashboard/src/pages")):
    if not name.endswith(".tsx") or name.endswith(".test.tsx"):
        continue
    text = open(f"/home/demon/shorts_studio/dashboard/src/pages/{name}").read()
    has_loading = bool(re.search(r"if\(loading\)return <Loading", text))
    has_error = bool(re.search(r"if\(error\)return <ErrorBox", text))
    has_health = bool(re.search(r"\['health'\]", text))
    has_tasks = bool(re.search(r"\['tasks'\]", text))
    has_runs = bool(re.search(r"\['production-runs'\]", text))
    print(f"{name:28} loading={has_loading} error={has_error} health={has_health} tasks={has_tasks} runs={has_runs}")