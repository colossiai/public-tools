import json,subprocess,sys,os,glob
os.chdir(os.path.dirname(os.path.abspath(__file__))); os.makedirs('sino',exist_ok=True)
for lo,hi in [(0,9000),(9001,13000),(13001,18000),(18001,999999)]:
    f=f'sino/band_{lo}.json'
    if os.path.exists(f): continue
    body=json.dumps({'postType':'Sale','day':'Day1095','sort':'InsOrRegDate','order':'Descending','developers':['de098'],'nUnitPriceRange':{'min':lo,'max':hi}})
    r=subprocess.run([sys.executable,'-I','fetch.py',body,f],capture_output=True,text=True); print(lo,hi,r.stderr.strip().split('\r')[-1][-30:],flush=True)
rows=[x for f in glob.glob('sino/band_*.json') for x in json.load(open(f))]
json.dump(rows,open('sino/all.json','w'),ensure_ascii=False); print(len(rows))
