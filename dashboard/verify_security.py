from pathlib import Path
from dotenv import dotenv_values
root=Path(__file__).parent
secrets=dotenv_values(Path.home()/'.config/nextdecode/api.env')
key=secrets.get('SHORTS_STUDIO_API_KEY','')
assets=list((root/'dist').rglob('*'))
assets=[p for p in assets if p.is_file()]
if not key: print('SERVER_KEY_CONFIGURED=False')
else: print('SERVER_KEY_CONFIGURED=True')
leak=bool(key) and any(key.encode() in p.read_bytes() for p in assets)
print('BROWSER_BUNDLE_SECRET_SCAN', 'FAIL' if leak else 'PASS')
print('DIST_ASSETS',len(assets))
