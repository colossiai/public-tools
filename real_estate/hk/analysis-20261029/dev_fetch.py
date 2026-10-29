# 按发展商代码抓近 3 年成交（Sale，含一手），按尺价分段（每段 <10,000 条），存到 __temp/hk_real_estate/dev_<code>/
# 用法：python3 -I dev_fetch.py de183
import json,subprocess,sys,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../analysis-20261028/scripts'))
code=sys.argv[1]; OUT=f'../../../../__temp/hk_real_estate/dev_{code}'; os.makedirs(OUT,exist_ok=True)
def body(lo,hi,**kw): return {'postType':'Sale','day':'Day1095','sort':'InsOrRegDate','order':'Descending','developers':[code],'nUnitPriceRange':{'min':lo,'max':hi},**kw}
def count(lo,hi): return json.loads(subprocess.run(['./q.sh',json.dumps(body(lo,hi,size=1,offset=0))],capture_output=True,text=True).stdout)['count']
def bands(lo,hi):
    if count(lo,hi)<9900 or hi-lo<200: return [(lo,hi)]
    m=(lo+hi)//2 if hi<100000 else 40000
    return bands(lo,m)+bands(m+1,hi)
for lo,hi in bands(0,999999):
    f=f'{OUT}/band_{lo:06d}_{hi:06d}.json'
    if os.path.exists(f) and os.path.getsize(f)>2: continue
    r=subprocess.run([sys.executable,'-I','fetch.py',json.dumps(body(lo,hi)),f],capture_output=True,text=True)
    print(lo,hi,r.stderr.strip().split('\r')[-1][-30:],flush=True)
