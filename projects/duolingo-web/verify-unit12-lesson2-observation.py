"""Verify actual owned UI outcomes; deliberately not a visual equality verdict."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--out',required=True);a=p.parse_args();n=Path(a.native)
d=json.loads((n/'observed.json').read_text());s=d['states'];checks=[]
def check(name,fact):
 checks.append(dict(name=name,pass_=bool(fact)));assert fact,name
check('all40states and no failed journeys',len(s)==40 and all(x['failure'] is None for x in d['attempts']))
check('actual pointer navigation preserves coach','pronunciation-coach-dismiss' in s['unit12-coach-pronunciation-native']['elements'] and 'pronunciation-sound-0' in s['unit12-coach-pronunciation-native']['elements'])
check('outside click dismisses coach','pronunciation-coach-dismiss' not in s['unit12-coach-dismissed']['elements'])
r=s['unit12-radio-locked'];check('radio title/body and disabled action',all(t in r['accessible_text'] for t in ['公寓参观','完成以上全部等级才可以解锁哦！','未解锁']) and r['elements']['unit12-radio-locked']['enabled'] is False)
for state in ['unit12-lesson2-home-after','unit12-lesson2-home-restarted']:
 check(state+' lesson3of6 and coach absent','Lesson 3 of 6' in s[state]['accessible_text'] and 'pronunciation-coach-dismiss' not in s[state]['elements'])
progress=json.loads((n/'progress.json').read_text());prefs=json.loads((n/'progress.json.preferences.json').read_text())
check('second course persisted without losing first',progress['completedLessons']['duolingo-en-zh-unit12-home2-instance']==['unit12-home-2'] and progress['completedLessons']['duolingo-en-zh-unit12-home-instance']==['unit12-home-1'])
check('ordinary course preserves four hearts',progress['hearts']==4)
check('coach dismissal persisted',prefs['pronunciationCoach']=='dismissed')
Path(a.out).write_text(json.dumps(dict(status='pass',checks=checks,observation_sha256=hashlib.sha256((n/'observed.json').read_bytes()).hexdigest(),limitations=['Prepared pending coach does not reproduce source onset delay or matching493.5point background scroll.','This verifies these UI outcomes only; strict whole-image/audio equality and unexplored branches remain open.']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status='pass',checks=len(checks))))
