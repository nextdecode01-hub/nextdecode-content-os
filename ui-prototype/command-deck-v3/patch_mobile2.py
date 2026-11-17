from pathlib import Path
p=Path(__file__).with_name('index.html');s=p.read_text()
css='''\n/* Responsive format grid: single column by default, expand with available width */\n.format-grid{grid-template-columns:minmax(0,1fr)}.workspace-intro>div:first-child{min-width:0;flex:1}.workspace-intro p,.head p{overflow-wrap:anywhere}\n@media(min-width:621px){.format-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}\n@media(min-width:1121px){.format-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}\n'''
s=s.replace('</style>',css+'</style>',1);p.write_text(s);print('FORMAT GRID BREAKPOINTS UPDATED')
