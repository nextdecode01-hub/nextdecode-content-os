import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home()/'.config/nextdecode/autonomy-db.env', override=False)
except Exception as e:
    print('ENV_LOADER',type(e).__name__)
dsn=os.environ.get('DATABASE_URL','').strip()
print('DATABASE_URL_CONFIGURED',bool(dsn))
if not dsn:
    raise SystemExit(0)
import psycopg
from psycopg.rows import dict_row
try:
    with psycopg.connect(dsn,connect_timeout=4,row_factory=dict_row,application_name='nextdecode-dashboard-readonly-audit') as c:
        print('CONNECTED',c.execute('select current_database() as db,current_user as usr,version() as version').fetchone())
        rows=c.execute("select table_schema,table_name from information_schema.tables where table_type='BASE TABLE' and table_schema not in ('pg_catalog','information_schema') order by table_schema,table_name").fetchall()
        print('TABLE_COUNT',len(rows))
        for row in rows:
            schema,table=row['table_schema'],row['table_name']
            count=c.execute('select count(*) as n from '+psycopg.sql.Identifier(schema,table).as_string(c)).fetchone()['n']
            cols=c.execute("select column_name,data_type,is_nullable from information_schema.columns where table_schema=%s and table_name=%s order by ordinal_position",(schema,table)).fetchall()
            print('TABLE',schema,table,'ROWS',count,'COLUMNS',[(x['column_name'],x['data_type'],x['is_nullable']) for x in cols])
        print('SCHEMA_MIGRATION_TABLES',[r['table_name'] for r in rows if any(x in r['table_name'].lower() for x in ['migration','alembic','schema_version'])])
except Exception as e:
    print('DATABASE_INSPECTION_FAILED',type(e).__name__,str(e).splitlines()[0][:240])
