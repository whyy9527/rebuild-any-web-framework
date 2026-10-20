"""Retain source scroll/hydration states and the newly reached unit-test branch."""
import argparse,json
from pathlib import Path
from capabilities.rebuild.discovery import frontier
B=Path('projects/duolingo-web');E=B/'evidence/english-home-scroll-v1';S=E/'source'
p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
h=json.loads((B/'evidence/english-shopping-guide-v1/history.json').read_text())
for path in sorted(S.glob('*.json')):
 d=json.loads(path.read_text())
 if 'actions' not in d:continue
 h['states'].append({'id':path.stem,'evidence':str(path),'actions':d['actions']})
states={s['id']:s for s in h['states']}
a=next(a for a in states['home-scroll-radio-after']['actions'] if a.get('href')=='/lesson/unit/12/test')
h['transitions'].append({'from':'home-scroll-radio-after','to':'home-scroll-unit-jump','action':a['id'],'outcome':'observed','evidence':str(S/'home-scroll-unit-jump.raw.txt')})
h['limitations']+=['Initial new tab viewport1192x705 is retained but excluded from same-viewport frontend freeze.','The guide right column was 10 points shorter on early observation; later stable quest card is175 points and sidebar727. Both captures retained.','Actual first radio lock and unit placement intro are source discoveries; native behaviors remain unimplemented, not successful coverage.','No matched-budget RSI effects inferred from frontend fixes or added inventory.']
f=frontier(Path.cwd(),h)
for name,data in [('history.json',h),('frontier.json',f)]: (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'states':len(h['states']),'edges':len(h['transitions']),'pending':len(f['pending'])}))
