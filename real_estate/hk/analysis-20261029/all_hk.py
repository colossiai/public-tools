# 全港近 3 年成交：按尺价分段抓到 __temp/hk_real_estate/raw/，每段 <10,000 条
import json,subprocess,sys,os
from concurrent.futures import ThreadPoolExecutor
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../analysis-20261028/scripts'))  # fetch.py / q.sh 在 analysis-20261028/scripts/
OUT='../../../../__temp/hk_real_estate/raw'; os.makedirs(OUT,exist_ok=True)
edges=[0,4000,5000,6000]+list(range(6500,25001,500))+[27000,30000,35000,45000,999999]
bands=[(lo+(lo>0),hi) for lo,hi in zip(edges,edges[1:])]
def run(b):
    lo,hi=b; f=f'{OUT}/band_{lo:06d}_{hi:06d}.json'
    if os.path.exists(f) and os.path.getsize(f)>2: return f'{lo}-{hi} cached'
    body=json.dumps({'postType':'Sale','day':'Day1095','sort':'InsOrRegDate','order':'Descending','nUnitPriceRange':{'min':lo,'max':hi}})
    r=subprocess.run([sys.executable,'-I','fetch.py',body,f],capture_output=True,text=True)
    return f"{lo}-{hi} {r.stderr.strip().split(chr(13))[-1][-40:]}"
with ThreadPoolExecutor(3) as ex:
    for s in ex.map(run,bands): print(s,flush=True)
