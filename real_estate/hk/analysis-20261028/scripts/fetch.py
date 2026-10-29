import json,subprocess,sys,time
body=json.loads(sys.argv[1]); out=sys.argv[2]; rows=[]; off=0; total=None
def get(b):
    for i in range(6):
        s=subprocess.run(['./q.sh',json.dumps(b,ensure_ascii=False)],capture_output=True,text=True).stdout
        try:
            d=json.loads(s)
            if 'count' in d: return d
        except ValueError: pass
        time.sleep(3*(i+1))
    raise SystemExit(f'failed at offset {b["offset"]}')
while True:
    body.update(size=100,offset=off)
    d=get(body); data=d.get('data') or []; rows+=data; off+=100; total=d['count']
    print(f"\r{len(rows)}/{total}",end='',file=sys.stderr)
    if not data or off>=total: break
    time.sleep(0.6)
json.dump(rows,open(out,'w'),ensure_ascii=False); print(file=sys.stderr)
