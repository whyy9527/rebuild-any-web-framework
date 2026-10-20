"""Keep v63 intact; append actual stage2 home, entries and reload evidence."""
import argparse
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];E=BASE/'evidence/english-stage2-home-v1'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True)
out=Path(p.parse_args().out_dir);out.mkdir(parents=True,exist_ok=False)
c=json.loads((BASE/'frontend-english-v63.json').read_text());prior=c['requirements'][:];reference=dict(states={});aliases={}
cases=[('stage2-'+stem,'stage2-home-source-02-'+stem) for stem in ['home-before','lesson-popover','sections-after-lesson','lesson-dismiss','story-entry','story-return','guide','guide-return','radio-entry','radio-return']]
cases += [('stage2-home-after-restart','stage2-source-reload-after-reload'),('stage2-home-revisit','stage2-source-reload-before-reload'),('stage2-sections-after-restart','stage2-source-prepared-sections-prepared')]
for state,stem in cases:
    path=E/'source'/(stem+'.json');s=json.loads(path.read_text());image=str(path.with_suffix('.png').relative_to(ROOT));ev=[str(path.relative_to(ROOT)),image]
    assert s['viewport']==dict(width=1200,height=732)
    aliases[state]={}
    texts=list(dict.fromkeys(t['text'] for t in s['text_runs']))
    reference['states'][state]=dict(accessible_text=texts,elements={},capture=dict(path=image,content_rect_points=[0,0,1200,732],window_points=[1200,732],backing_scale=1))
    def add(suffix,kind,**kw):c['requirements'].append(dict(id=state+'-'+suffix,state=state,kind=kind,evidence=ev,**kw))
    add('whole','image_pixels',reference_image=image,pixels=[1200,732])
    for i,text in enumerate(texts):add('text-'+str(i),'accessible_text',text=text)
    for i,a in enumerate(s['actions']):
        key='stage2-action-'+str(i);reference['states'][state]['elements'][key]={k:a[k] for k in ['rect','role','enabled']}
        native={'学习':'nav-learn','发音':'nav-pronunciation','排行榜':'nav-leaderboards','特别任务':'nav-quests','宝石小店':'nav-shop','个人档案':'nav-profile','更多':'nav-more','返回':'sections-return','继续':'sections-continue-2','复习':'sections-review-1','查看排行榜':'view-leaderboards','显示全部':'view-quests','打开这个部分的指南':'open-guide'}.get(a['name'])
        if a.get('href')=='/sections' and a['rect'][0]>=256:native='open-sections'
        if a['name'].startswith('跳至第 '):native='sections-jump-'+a['name'].split()[1]
        if native:aliases[state][key]=native
        add(key+'-geometry','element_geometry',element=key,rect=a['rect'],tolerance_points=0)
        if a['role'] is not None:add(key+'-role','element_role',element=key,role=a['role'])
        add(key+'-enabled','element_boolean',element=key,field='enabled',expected=a['enabled'])
    add('audio','pending',description='Actual aligned application audio output remains unverified; no silence inference from absent player after radio click')
c.update(revision='english-v64',parent_revision='english-v63',changes=['Actual lesson and locked story popovers, stage2 guide, radio-triggered scrolling/virtualized unit inventory','Actual client reload retains stage2/score10/gems530 but daily progress changes50/50 to0/50','Explicit scroll-top source preparation for unlocked section comparison; no server-reset claim'])
assert c['requirements'][:len(prior)]==prior
assert len({r['id'] for r in c['requirements']})==len(c['requirements'])
for name,data in [('contract.json',c),('reference.json',reference),('aliases.json',aliases)]:
    (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(prior=len(prior),requirements=len(c['requirements']),new_states=len(cases))))
