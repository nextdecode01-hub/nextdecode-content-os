import json
from pathlib import Path
p=Path('data/nvidia_model_evaluation.v1.json');d=json.loads(p.read_text())
d['tested_models']=3
d.setdefault('multimodal_results',[])
d['multimodal_results']=[x for x in d['multimodal_results'] if x.get('model')!='nvidia/nemotron-3.5-super-vl-120b-a12b']
d['multimodal_results'].append({'provider':'nvidia','model':'nvidia/nemotron-3.5-super-vl-120b-a12b','role':'visual_qa','text_only':{'http_status':200,'latency_ms':2705,'content_present':True},'image_understanding':{'http_status':200,'latency_ms':4254,'content_present':True,'transport':'streaming','sample':'A red stop sign is prominently displayed in the foreground.'},'non_streaming_image_attempt':{'http_status':200,'latency_ms':61141,'content_present':False,'finish_reason':'length','note':'Reasoning consumed the output budget before final answer.'},'status':'provisional_multimodal_candidate','quota':'unknown'})
d['selection_note']='Exploratory exact-model qualification; no candidate approved for production. Nemotron Super VL passed initial image understanding but requires evaluation on project frames/contact sheets.'
p.write_text(json.dumps(d,indent=2)+'\n')
print('recorded Super VL multimodal evidence')
