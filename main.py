import os,json,urllib.request as r
ND=(18,33,31,14,-18,-33,-31,-14);KD=(1,17,16,15,-1,-17,-16,-15);BD=(17,15,-17,-15);RD=(1,16,-1,-16);DS=(0,0,ND,BD,RD,BD+RD,KD);O=(5,4,3,2)
P=(0,0,0,0,1,2,2,-4,1,-1,-2,0,0,0,0,4,1,1,2,5,2,2,4,6,10,10,10,10,0,0,0,0)
K=(4,6,2,0,4,4,0,0,-2,-4,-4,-4,-4,-6,-6,-8,-6,-8,-8,-10,-6,-8,-8,-10,-6,-8,-8,-10,-6,-8,-8,-10)
T=(0,P,P,P,P,P,K);M=(0,100,320,330,500,900,0);MATE=100000;BUD=20000
b=[];w=1;c=0;e=-1;h=0;st=[];n=0
CR=[15]*128;CR[0]=13;CR[7]=14;CR[112]=7;CR[119]=11
def parse(f):
 global b,w,c,e,h,st
 a=f.split();b=[0]*128;q=112;x=0
 for ch in a[0]:
  if ch<'1':q-=16;x=0
  elif ch<':':x+=int(ch)
  else:
   p='.PNBRQKpnbrqk'.index(ch);p=(p,6-p)[p>6];b[q+x]=p
   x+=1
 w=2*(a[1]=='w')-1;c=sum(1<<i for i,ch in enumerate('KQkq') if ch in a[2]);e=-1 if a[3]=='-' else int(a[3][1])*16+ord(a[3][0])-113;h=int(a[4]);st=[]
def at(s,v):
 for d in(17,15):
  z=s-d*v
  if not z&136 and b[z]==v:return 1
 for ds,t in((ND,2),(KD,6)):
  for d in ds:
   z=s+d
   if not z&136 and b[z]==t*v:return 1
 for ds,t in((BD,(3,5)),(RD,(4,5))):
  for d in ds:
   z=s+d
   while not z&136:
    p=b[z]
    if p:
     if p in(t[0]*v,t[1]*v):return 1
     break
    z+=d
 return 0
def mk(m):
 global w,c,e,h,st
 f=m&255;t=m>>8&255;q=m>>16;p=b[f];u=p//abs(p);y=abs(p);z=b[t];st+=[(b[:],w,c,e,h)]
 b[f]=0;b[t]=q*u if q else p
 if y==1 and t==e and f%8!=t%8:b[t-16*u]=0
 if y==6:
  c&=3+9*(u>0)
  if abs(t-f)==2:
   if t>f:b[f+1]=b[f+3];b[f+3]=0
   else:b[f-1]=b[f-4];b[f-4]=0
 c&=CR[f]&CR[t];e=(f+t)//2 if y==1 and abs(t-f)==32 else -1;h=0 if y==1 or z else h+1;w=-w
def um():
 global b,w,c,e,h
 b,w,c,e,h=st.pop()
def gen():
 u=w;A=[]
 for f in range(128):
  p=b[f]
  if f&136 or p*u<=0:continue
  y=abs(p)
  if y==1:
   T=[];t=f+u*16
   if not t&136 and not b[t]:
    T+=[t]
    if f>>4==(1,6)[u<0]:
     z=f+u*32
     if not b[z]:A.append(f|z<<8)
   for d in(15,17):
    t=f+u*d
    if not t&136 and(b[t]*u<0 or t==e):T+=[t]
   for t in T:A+=[f|t<<8|q<<16 for q in O] if t<8 or t>111 else[f|t<<8]
  else:
   for d in DS[y]:
    t=f+d
    while not t&136:
     q=b[t]
     if q*u>0:break
     A.append(f|t<<8)
     if q or y in(2,6):break
     t+=d
   if y==6:
    for d in(-2,2):
     m=d//2
     if c&(1<<((u<0)*2+(d<0))) and not any(b[f+m*i] for i in range(1,3+(d<0))) and not any(at(f+m*i,-u) for i in range(2+(d<0))):A+=[f|(f+d)<<8]
 return A
def legal():
 u=w;A=[]
 for m in gen():
  mk(m)
  if not at(b.index(6*u),-u):A+=[m]
  um()
 return A
def uci(m):
 q=m>>16
 return'%c%d%c%d'%(97+(m&7),(m>>4&15)+1,97+(m>>8&7),(m>>12&15)+1)+('pnbrq'[q-1] if q else'')
def ev():
 s=0
 for z,p in enumerate(b):
  if z&136 or not p:continue
  y=abs(p);v=(p>0)-(p<0);q=z^112 if v<0 else z;f=q&7;i=(q>>4)*4+(f if f<4 else 7-f)
  s+=v*(M[y]+5*T[y][i])
 return s
def order(A):
 return sorted(A,key=lambda m:(m>>16,b[m>>8&255]),reverse=1)
def se(d,A,B,p):
 global n
 n+=1
 if n>BUD:raise Exception
 if h>99:return 0
 if d<=0:
  z=at(b.index(6*w),-w)
  if z:best=-MATE
  else:
   v=ev()*w
   if v>=B:return v
   if v>A:A=v
   best=A
  L=legal()
  if not z:L=[m for m in L if m>>16 or b[m>>8&255] or m>>8&255==e]
  for m in order(L):
   mk(m)
   try:v=-se(0,-B,-A,p+1)
   finally:um()
   if v>best:
    best=v
    if v>A:
     A=v
     if A>=B:break
  return max(best,-MATE+p)
 a=A;best=-MATE
 for m in order(legal()):
  mk(m)
  try:v=-se(d-1,-B,-a,p+1)
  finally:um()
  if v>best:
   best=v
   if v>a:
    a=v
    if a>=B:break
 return best
def best(f):
 global n
 parse(f);L=legal()
 if not L:return
 bm=L[0];n=0
 try:
  for d in range(1,64):
   a=-MATE;B=MATE;cur=0
   for m in order(L):
    mk(m)
    try:v=-se(d-1,-B,-a,1)
    finally:um()
    if v>a:a=v;cur=m
   bm=cur
 except:pass
 return uci(bm)
if __name__=='__main__':
 po=lambda p,d:json.load(r.urlopen(r.Request(os.environ['MAKEFUN_ENV_URL']+p,json.dumps(d).encode(),{'Content-Type':'application/json'})))
 a=po('/game',{})
 while a['status']!='done':
  if a['status']!='your_move':a=po('/game',{});continue
  l=a['legal_moves']
  try:m=best(a['fen'])
  except:m=0
  if m not in l:m=l[0]
  a=po('/move',{'game':a['game'],'move':m})
