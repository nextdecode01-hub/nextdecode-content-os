from pathlib import Path
import sqlite3, json, hashlib
root=Path('/home/demon/shorts_studio')
dbpath=root/'data/autonomy/tasks.sqlite3'
print('DB_EXISTS', dbpath.exists(), 'SIZE', dbpath.stat().st_size if dbpath.exists() else None)
if dbpath.exists():
    con=sqlite3.connect(f'file:{dbpath}?mode=ro', uri=True)
    print('SQLITE_VERSION', sqlite3.sqlite_version)
    tables=con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    for name, ddl in tables:
        count=con.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0]
        print('TABLE',name,'ROWS',count,'DDL',ddl)
    for name, in con.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"):
        print('INDEX',name)
    con.close()
print('POSTGRES_LISTENER')
import subprocess
for cmd in [['bash','-lc','ss -ltnp | grep :5432 || true'],['bash','-lc','pgrep -a postgres || true']]:
    x=subprocess.run(cmd,capture_output=True,text=True); print(x.stdout.strip() or '(none)')
print('AUTONOMY_MODULE_FILES')
for p in sorted((root/'app/autonomy').glob('*.py')):
    print(p.name, hashlib.sha256(p.read_bytes()).hexdigest()[:12])
