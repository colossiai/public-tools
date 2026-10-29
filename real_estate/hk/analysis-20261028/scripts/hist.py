import json,subprocess,os,sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
for e in sorted({e for d,e in json.load(open('cands.json'))}):
    f=f"hist/{e.replace('/','_').replace(' ','_')}.json"
    if os.path.exists(f) and os.path.getsize(f)>2: continue
    body=json.dumps({'postType':'Sale','day':'Day1095','sort':'InsOrRegDate','order':'Descending','keyword':e},ensure_ascii=False)
    r=subprocess.run([sys.executable,'-I','fetch.py',body,f],capture_output=True,text=True)
    print(e, r.stderr.strip().split('\r')[-1][-40:], flush=True)
