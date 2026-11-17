from pathlib import Path
p=Path(__file__).with_name('index.html');s=p.read_text()
s=s.replace('data-go="studio"','data-go="shorts"')
p.write_text(s)
print('SHORTS LINKS ROUTED',s.count('data-go="shorts"'),'old studio links',s.count('data-go="studio"'))
