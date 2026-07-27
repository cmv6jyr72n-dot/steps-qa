import http.server,json,re,os,urllib.parse,mimetypes
BASE=os.path.dirname(os.path.abspath(__file__))
DATA_FILE=os.path.join(BASE,'qa_data.json')
TEMPLATES=os.path.join(BASE,'templates')
STATIC=os.path.join(BASE,'static')
def load_data():
 with open(DATA_FILE,'r',encoding='utf-8') as f:return json.load(f)
def tokenize(text):
 t=re.findall(r'[一-鿿\w]+',text)
 r=[]
 for x in t:
  if len(x)>=1:r.append(x)
  if len(x)>3:
   for i in range(len(x)-1):r.append(x[i:i+2])
 return r
def search(query,data):
 if not query or not query.strip():return[]
 query=query.strip();ql=query.lower();qt=tokenize(query);results=[]
 for p in data.get('products',[]):
  pn=p.get('name','');pm=False
  for kp in [p['id'],p.get('category','')]:
   if kp:
    for kt in tokenize(kp):
     if kt.lower() in ql or ql in kt.lower():pm=True;break
  for nt in tokenize(pn):
   if len(nt)>=2 and (nt.lower() in ql or ql in nt.lower()):pm=True;break
  for e in p.get('entries',[]):
   score=0;mk=[];kws=e.get('keywords',[]);q=e.get('question','');a=e.get('answer','')
   for kw in kws:
    kl=kw.lower()
    if kl==ql:score+=3;mk.append(kw)
    elif kl in ql:score+=2;mk.append(kw)
    elif ql in kl:score+=2;mk.append(kw)
   for t in qt:
    if len(t)<2:continue
    tl=t.lower()
    for kw in kws:
     if tl in kw.lower() or kw.lower() in tl:
      score+=1
      if kw not in mk:mk.append(kw)
   ql1=q.lower()
   for t in qt:
    if len(t)>=2 and t.lower() in ql1:score+=2
   al=a.lower()
   for t in qt:
    if len(t)>=2 and t.lower() in al:score+=1
   if pm:score+=3
   if score>0:results.append(dict(product_id=p['id'],product_name=pn,product_category=p.get('category',''),entry_id=e.get('id',''),section=e.get('section',''),question=q,answer=a,score=score,matched_keywords=mk[:5]))
 results.sort(key=lambda x:x['score'],reverse=True)
 grouped={}
 for r in results:
  pid=r['product_id']
  if pid not in grouped:grouped[pid]=dict(product_id=pid,product_name=r['product_name'],product_category=r['product_category'],entries=[],total_score=0)
  grouped[pid]['entries'].append(dict(entry_id=r['entry_id'],section=r['section'],question=r['question'],answer=r['answer'],score=r['score']))
  grouped[pid]['total_score']+=r['score']
 return sorted(grouped.values(),key=lambda x:x['total_score'],reverse=True)
class H(http.server.SimpleHTTPRequestHandler):
 def __init__(s,*a,**kw):kw['directory']=BASE;super().__init__(*a,**kw)
 def do_GET(s):
  p=urllib.parse.urlparse(s.path)
  if p.path=='/':s.sf(os.path.join(TEMPLATES,'index.html'),'text/html')
  elif p.path=='/api/search':s.hs(p)
  elif p.path=='/api/products':s.hp()
  elif p.path.startswith('/static/'):
   fp=os.path.join(STATIC,p.path[8:])
   if os.path.isfile(fp):ct,_=mimetypes.guess_type(fp);s.sf(fp,ct or 'application/octet-stream')
   else:s.send_error(404)
  else:s.send_error(404)
 def sf(s,fp,ct):
  try:
   with open(fp,'rb') as f:data=f.read()
   s.send_response(200);s.send_header('Content-Type',ct+'; charset=utf-8');s.send_header('Content-Length',str(len(data)));s.end_headers();s.wfile.write(data)
  except FileNotFoundError:s.send_error(404)
 def hs(s,p):
  params=urllib.parse.parse_qs(p.query);query=params.get('q',[''])[0].strip()
  if not query:s.sj(dict(results=[],query='',count=0));return
  data=load_data();results=search(query,data);total=sum(len(g['entries']) for g in results)
  s.sj(dict(results=results,query=query,count=total))
 def hp(s):
  data=load_data()
  products=[dict(id=p['id'],name=p['name'],category=p['category'],entry_count=len(p.get('entries',[]))) for p in data.get('products',[])]
  s.sj(dict(products=products,company=data.get('company','')))
 def sj(s,obj):
  body=json.dumps(obj,ensure_ascii=False).encode('utf-8')
  s.send_response(200);s.send_header('Content-Type','application/json; charset=utf-8');s.send_header('Content-Length',str(len(body)));s.end_headers();s.wfile.write(body)
if __name__=='__main__':
 data=load_data();total=sum(len(p.get('entries',[])) for p in data.get('products',[]))
 print('STEPS Product QA System - '+str(len(data.get('products',[])))+' products, '+str(total)+' entries')
 print('http://0.0.0.0:5000')
 httpd=http.server.HTTPServer(('0.0.0.0',5000),H);httpd.serve_forever()
