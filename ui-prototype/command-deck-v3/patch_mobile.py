from pathlib import Path
p=Path(__file__).with_name('index.html');s=p.read_text()
css='''\n/* Narrow-screen overflow guard */\n@media(max-width:480px){.content{width:100%;max-width:100%;min-width:0;padding:13px 10px 24px}.head>div,.workspace-intro>div:first-child{min-width:0;max-width:100%}.workspace-intro{width:100%;min-width:0;flex-wrap:wrap}.workspace-intro p,.head p{overflow-wrap:anywhere}.workspace-orb{margin-left:auto}.format-grid,.scope-panel .cards{grid-template-columns:minmax(0,1fr)}.format-card{width:100%;min-width:0}.graph-branches{grid-template-columns:minmax(0,1fr)}.welcome{padding:18px 13px}.welcome h1{font-size:25px}.promptbar{max-width:100%;min-width:0}.promptbar input{font-size:10px}.quickActions button{max-width:100%}.homeSectionHead{align-items:flex-start;gap:8px}.homeSectionHead .link{white-space:nowrap}}\n'''
s=s.replace('</style>',css+'</style>',1)
p.write_text(s)
print('MOBILE OVERFLOW GUARD ADDED')

