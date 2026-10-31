# 屋苑 -> 发展商：用维基百科公开列表（不经中原 API），对应到 raw 数据的 (estate, hma)
# 来源：zh.wikipedia「香港私人屋苑列表」（有發展商栏）、「香港資助出售房屋列表」（居屋 -> 房委會/房協）、「租者置其屋計劃」（邨 -> 房委會），
#       另外，列表里没有、成交 >=20 宗的屋苑，再查同名条目信息框的「發展商」；
#       仍没有的，合并 centaline_developers.csv（中原屋苑专页，由 centaline_dev.py 生成）
# 用法：python3 -I estate_dev.py   输出 estate_developers.csv、estate_developers_unmatched.csv
import json,re,os,glob,csv,sys,subprocess,urllib.parse
from collections import defaultdict,Counter
os.chdir(os.path.dirname(os.path.abspath(__file__)))
T='../../../__temp/hk_real_estate'; W=f'{T}/wiki'; os.makedirs(W,exist_ok=True)
PAGES=['香港私人屋苑列表','香港資助出售房屋列表','租者置其屋計劃']
def get(u): return subprocess.run(['curl','-s','--max-time','60','-A','research-script/1.0',u],capture_output=True,check=True).stdout  # python 自带 ssl 在本机证书校验失败，改用 curl
def page(p):
    f=f'{W}/{p}.json'
    if not os.path.exists(f):
        u=f'https://zh.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(p)}&prop=wikitext|revid&format=json&formatversion=2&redirects=1'
        open(f,'wb').write(get(u))
    d=json.load(open(f))['parse']; return d['wikitext'],d['revid']
# 同一公司的不同写法合并；集团改名/合并（如和记黄埔->长实）不合并，保留维基原文
ALIAS={'新鴻基地產':'新鴻基','信和置業':'信置','信和集團':'信置','恒基地產':'恒基兆業','恒基兆業地產':'恒基兆業','恆基兆業':'恒基兆業','恆基地產':'恒基兆業','恆基兆業地產':'恒基兆業',
    '長江實業':'長實','長江實業地產':'長實','長江實業集團':'長實','長實集團':'長實','新世界發展':'新世界','港鐵公司':'港鐵','地鐵公司':'港鐵','南豐集團':'南豐','南豐發展':'南豐',
    '恒隆地產':'恒隆','恆隆地產':'恒隆','恒隆集團':'恒隆','會德豐地產':'會德豐','嘉華國際':'嘉華','嘉華國際集團':'嘉華','市區重建局':'市建局','市區重建局 (香港)':'市建局',
    '香港房屋協會':'房協','麗新集團':'麗新','麗新發展':'麗新','華懋集團':'華懋','太古地產':'太古','九龍倉集團':'九龍倉','嘉里建設':'嘉里','中國海外發展':'中國海外','和記黃埔地產':'和記黃埔',
    '嘉里建設':'嘉里','麗新集團':'麗新','宏安集團':'宏安地產','華人置業集團':'華人置業','長江實業(集團)':'長實','中國海外集團':'中國海外','華置':'華人置業'}
def companies(s):  # 信息框的自由文本 -> 公司名：去括号说明，按「及/與/；」拆开，「X屬下的Y」取 X
    out=[]
    s=re.sub(r'<br\s*/?>','；',clean(s)); s=re.sub(r'<[^>]+>','',unlink(s))
    for p in re.split(r'及|與|；|;|、|，|,|/|(?<=[產業團展司局行埔])和(?!記)',re.sub(r'（[^）]*）|\([^)]*\)','',s)):
        p=p.strip(' []　|').split('屬下')[0].split('旗下')[0].strip()
        p=re.sub(r'(牽頭財團|財團|有限公司|股份有限公司|控股有限公司)$','',p).strip()
        if p and not p.startswith('{{') and len(p)<=20: out.append(ALIAS.get(p,p))
    return list(dict.fromkeys(out))
def unlink(s): return re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]',r'\1',s)
def clean(s):
    s=re.sub(r'<ref[^>]*/>|<ref[^>]*>.*?</ref>','',s,flags=re.S)
    s=re.sub(r'\{\{Sort\|[^|}]*\|([^}]*)\}\}',r'\1',s,flags=re.I)
    return s
def norm(s):  # 名称比较用：去空白、标点，括号统一
    s=unlink(s).replace('（','(').replace('）',')')
    return re.sub(r'[\s．.‧·・•\'’"「」]','',s).upper()
def tables(text):  # 逐个 wikitable：按表头找栏位，返回 (章节路径, {栏名:内容})
    sec=[]; out=[]
    for m in re.finditer(r'^(=+)\s*(.+?)\s*\1\s*$|^\{\|.*?^\|\}',text,re.M|re.S):
        if m.group(1):
            lv=len(m.group(1)); sec=sec[:lv-2]+[re.sub(r'\s*\(.*?\)','',unlink(m.group(2))).strip()]; continue
        rows=re.split(r'\n\|-[^\n]*',clean(m.group(0)))
        head=[unlink(h).strip() for h in re.split(r'!!|\n!',rows[0]+'\n'+(rows[1] if len(rows)>1 else '')) if '!' not in h[:0]]
        head=[re.sub(r'^.*\|\s*','',h) for h in re.findall(r'(?:^|\n)!\s*([^\n]*)',m.group(0)) for h in re.split(r'!!',h)]
        head=[unlink(re.sub(r'^.*\|','',h)).strip() for h in head]
        for r in rows[1:]:
            cells=[c.strip() for c in re.split(r'\n\|\||\|\||\n\|',('\n'+r.strip()) if not r.strip().startswith('!') else '')][1:]
            if len(cells)>=len(head)-1 and cells: out.append((tuple(sec),dict(zip(head,cells))))
    return out
def col(r,key): return next((v for k,v in r.items() if key in k),'')
wiki=[]; revs={}
t,revs['香港私人屋苑列表']=page('香港私人屋苑列表')
for sec,r in tables(t):
    name=col(r,'名稱'); dev=col(r,'發展商')
    devs=companies(dev)
    wiki.append(dict(name=name,district=sec[1] if len(sec)>1 else '',devs=devs,year=unlink(col(r,'入伙')).strip(),src='私人屋苑列表'))
t,revs['香港資助出售房屋列表']=page('香港資助出售房屋列表')
for sec,r in tables(t):
    if not sec or sec[0].startswith(('原本','興建')): continue  # 未落成或已改作他用的不收
    row=' '.join(r.values())
    wiki.append(dict(name=col(r,'名稱'),district=sec[0],devs=['房協' if '房協' in row or '房屋協會' in row else '房委會'],year=unlink(col(r,'入伙')).strip(),src='資助出售房屋列表'))
t,revs['租者置其屋計劃']=page('租者置其屋計劃')
for n in sorted(set(re.findall(r'\[\[(?:[^\]|]*\|)?([^\]|]*邨)\]\]',t))-{'香港公共屋邨'}):
    wiki.append(dict(name=n,district='',devs=['房委會'],year='',src='租者置其屋計劃'))
ph=defaultdict(list)
for w in wiki:
    m=re.match(r'^\s*(.+?)\s*第[一二三四五六七八九十百\dA-Za-z甲乙丙]+期',unlink(w['name']))
    if m and w['devs']: ph[(m.group(1),w['district'])].append(w)
for (b,d),ws in ph.items():
    wiki.append(dict(name=b,district=d,devs=list(dict.fromkeys(x for w in ws for x in w['devs'])),year='',src='私人屋苑列表(各期合併)'))
idx=defaultdict(list)
for w in wiki:
    for v in re.split(r'<br\s*/?>|\n',w['name']):
        v=norm(re.sub(r"'''?|\{\{.*?\}\}",'',v))
        if v: idx[v].append(w); idx[re.sub(r'\(.*?\)','',v)].append(w)  # 也收去掉括号的写法，例如 明園(香港) -> 明園
print(len(wiki),'wiki rows,',sum(bool(w['devs']) for w in wiki),'with developer',file=sys.stderr)
def dist(db):  # 中原区名 -> 十八区：'將軍澳 (西貢區)' -> '西貢', '華景 | 荔灣 (葵青區)' -> '葵青'
    m=re.search(r'\((.+)\)',db or ''); return (m.group(1) if m else (db or '')).removesuffix('區')
keys=defaultdict(lambda:dict(n=0,alts=Counter()))
for f in glob.glob(f'{T}/raw/band_*.json'):
    for x in json.load(open(f)):
        k=(x.get('bigEstateName') or x.get('estateName') or x.get('buildingName'),x.get('districtName'),(x.get('scope') or {}).get('db'))
        e=keys[k]; e['n']+=1
        for a in (x.get('bigEstateName'),x.get('estateName'),x.get('buildingName')):
            if a: e['alts'][a]+=1
out=[]; miss=[]
for (est,hma,db),e in keys.items():
    best=None
    for a in [est]+[a for a,_ in e['alts'].most_common() if a!=est]:  # 先用屋苑名，再试期数名、座名
        cands=[w for w in {id(w):w for w in idx.get(norm(a),[])}.values() if w['devs']]
        if not cands: continue
        same=[w for w in cands if w['district'] and w['district'].removesuffix('區')==dist(db)]
        if same: best=(a,same[0],'name+district'); break
        if not best and len(cands)==1 and not cands[0]['district']: best=(a,cands[0],'name_only(無地區)')  # 维基有地区但对不上的，多半是同名不同屋苑，不收
    if best:
        a,w,q=best
        out.append(dict(estate=est,hma=hma,district=db,developers='；'.join(dict.fromkeys(w['devs'])),wiki_name=unlink(re.sub(r'<br\s*/?>.*','',w['name'])).strip(),
            matched_on=a,match=q,wiki_district=w['district'],wiki_year=w['year'],source=w['src'],n_trans=e['n']))
    else: miss.append(dict(estate=est,hma=hma,district=db,n_trans=e['n']))
def articles(titles):  # 批量取条目内容，缓存到 wiki/articles.json
    f=f'{W}/articles.json'; c=json.load(open(f)) if os.path.exists(f) else {}
    todo=[t for t in titles if t not in c]
    for i in range(0,len(todo),40):
        b=todo[i:i+40]; u='https://zh.wikipedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',prop='revisions',rvprop='content',rvslots='main',titles='|'.join(b),redirects=1,format='json',formatversion=2))
        d=json.loads(get(u))['query']
        rd={x['from']:x['to'] for x in d.get('redirects',[])+d.get('normalized',[])}
        pg={p['title']:p.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('content','') for p in d.get('pages',[])}
        for t in b:
            to=t
            while to in rd: to=rd[to]
            c[t]=pg.get(to,'')
        json.dump(c,open(f,'w'),ensure_ascii=False)
    return c
MINA=20; want=[m for m in miss if m['n_trans']>=MINA]
art=articles([m['estate'] for m in want])
for m in want:
    a=art.get(m['estate'],'')
    if not a or '香港' not in a or re.search(r'\{\{\s*(disambig|消歧)',a,re.I): continue
    f=re.search(r'^\s*\|\s*(?:發展商|发展商|developer)[ \t]*=[ \t]*(\S.*)$',a,re.M|re.I)
    if not f: continue
    devs=companies(f.group(1))
    if not devs: continue
    if dist(m['district']) not in a and (m['hma'] or '~') not in a: continue  # 条目没提到该区，可能是同名的别处屋苑
    q='name+district'
    out.append(dict(m,developers='；'.join(dict.fromkeys(devs)),wiki_name=m['estate'],matched_on=m['estate'],match=q,wiki_district='',wiki_year='',source='維基條目信息框'))
    m['done']=1
miss=[m for m in miss if not m.get('done')]
# 维基仍对不上的：用 centaline_dev.py 抓到的中原屋苑专页「發展商」（如有）
if os.path.exists('centaline_developers.csv'):
    cd={(r['estate'],r['hma']):r for r in csv.DictReader(open('centaline_developers.csv',encoding='utf-8-sig'))}
    for m in miss:
        r=cd.get((m['estate'],m['hma']))
        if not r: continue
        devs=list(dict.fromkeys(ALIAS.get(d,d) for d in (x.strip() for x in r['developer'].split('/')) if d))
        out.append(dict(m,developers='；'.join(devs),wiki_name='',matched_on=r['typeCode'],match='typeCode',wiki_district='',wiki_year='',source='中原屋苑專頁'))
        m['done']=1
    miss=[m for m in miss if not m.get('done')]
# 仍对不上的：手动补充 manual_developers.csv（查不到可靠资料的旧楼不填，留在 unmatched）
if os.path.exists('manual_developers.csv'):
    md={(r['estate'],r['hma']):r for r in csv.DictReader(open('manual_developers.csv',encoding='utf-8-sig'))}
    for m in miss:
        r=md.get((m['estate'],m['hma']))
        if not r: continue
        out.append(dict(m,developers=r['developers'],wiki_name='',matched_on=m['estate'],match='manual',wiki_district='',wiki_year='',source='手動補充'))
        m['done']=1
    miss=[m for m in miss if not m.get('done')]
out.sort(key=lambda r:-r['n_trans']); miss.sort(key=lambda r:-r['n_trans'])
for f,rs in [('estate_developers.csv',out),('estate_developers_unmatched.csv',miss)]:
    with open(f,'w',newline='',encoding='utf-8-sig') as fo:
        w=csv.DictWriter(fo,fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
tot=sum(e['n'] for e in keys.values()); hit=sum(r['n_trans'] for r in out)
print(f"keys {len(out)}/{len(keys)} matched ({len(out)/len(keys):.0%}); transactions {hit}/{tot} ({hit/tot:.0%}); wiki revids {revs}")
print(Counter(r['match'] for r in out))
