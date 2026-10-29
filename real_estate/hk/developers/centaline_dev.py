# 补充来源：中原屋苑专页（hk.centanet.com/estate/<名>/<typeCode>）的「發展商」栏
# 对象：estate_developers.csv 里维基没对上、n_trans > MINN 的屋苑；typeCode 取自 raw 成交记录，按出现次数试最多 3 个
# 顺序：estate_dev.py -> centaline_dev.py -> 再跑 estate_dev.py（合并中原结果）
# 用法：python3 -I centaline_dev.py   结果缓存到 __temp/hk_real_estate/centaline_estate.json，输出 centaline_developers.csv
import json,glob,csv,os,re,subprocess,sys,time,urllib.parse
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor
os.chdir(os.path.dirname(os.path.abspath(__file__)))
T='../../../__temp/hk_real_estate'; CACHE=f'{T}/centaline_estate.json'; MINN=int(os.environ.get('MINN',10))
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
wiki={(r['estate'],r['hma']) for r in csv.DictReader(open('estate_developers.csv',encoding='utf-8-sig')) if r['source']!='中原屋苑專頁'}  # 维基已对上的不查
tc=defaultdict(Counter); want=defaultdict(lambda:dict(n_trans=0,district=''))
for f in glob.glob(f'{T}/raw/band_*.json'):
    for x in json.load(open(f)):
        k=(x.get('bigEstateName') or x.get('estateName') or x.get('buildingName'),x.get('districtName'))
        if k in wiki: continue
        want[k]['n_trans']+=1; want[k]['district']=(x.get('scope') or {}).get('db')
        if x.get('typeCode'): tc[k][(x['typeCode'],k[0])]+=1
want={k:v for k,v in want.items() if v['n_trans']>MINN}
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def page(code,name):  # 返回 (屋苑名, 發展商)；發展商栏只在有值时出现
    if code in cache: return cache[code]
    u=f'https://hk.centanet.com/estate/{urllib.parse.quote(name.replace("/"," "))}/{code}'
    for i in range(3):
        s=subprocess.run(['curl','-sL','--max-time','30','-A',UA,u],capture_output=True,text=True).stdout
        if '<title>' in s: break
        time.sleep(3*(i+1))
    t=re.search(r'<title>([^｜<]*)',s); d=re.search(r'label-item-left[^>]*>發展商</span>\s*<span[^>]*>([^<]*)',s)
    cache[code]=[t and t.group(1).strip(),d.group(1).strip() if d else '']; time.sleep(0.3)
    return cache[code]
def one(k):
    for (code,name),_ in tc[k].most_common(3):
        title,dev=page(code,name)
        if dev: return k,code,title,dev
    return k,None,None,''
with ThreadPoolExecutor(4) as ex: res=list(ex.map(one,want))
json.dump(cache,open(CACHE,'w'),ensure_ascii=False)
with open('centaline_developers.csv','w',newline='',encoding='utf-8-sig') as fo:
    w=csv.writer(fo); w.writerow(['estate','hma','district','n_trans','typeCode','centaline_title','developer'])
    for k,code,title,dev in sorted(res,key=lambda r:-int(want[r[0]]['n_trans'])):
        if dev: w.writerow([k[0],k[1],want[k]['district'],want[k]['n_trans'],code,title,dev])
hit=[r for r in res if r[3]]
print(f'{len(hit)}/{len(want)} estates got a developer; trans {sum(int(want[r[0]]["n_trans"]) for r in hit)}/{sum(int(m["n_trans"]) for m in want.values())}')
