from pathlib import Path
p=Path('/home/demon/shorts_studio/app/autonomy/store.py')
s=p.read_text()
bad='''            tasks = db.execute("""SELECT t.* FROM tasks t JOIN task_events e ON e.task_id=t.task_id
                WHERE json_extract(e.detail_json,'$.plan_id')=? GROUP BY t.task_id ORDER BY t.created_at,t.task_id""",
                WHERE json_extract(e.detail_json,'$.plan_id')=? GROUP BY t.task_id ORDER BY t.created_at,t.task_id""",
                (plan_id,)).fetchall()
'''
good='''            tasks = db.execute("""SELECT t.* FROM tasks t JOIN task_events e ON e.task_id=t.task_id
                WHERE json_extract(e.detail_json,'$.plan_id')=? GROUP BY t.task_id ORDER BY t.created_at,t.task_id""",
                (plan_id,)).fetchall()
'''
assert bad in s
p.write_text(s.replace(bad,good))
