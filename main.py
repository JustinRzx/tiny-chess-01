import os,json,sys
from urllib.request import*
from itertools import*
LIM=2000
V={'P':100,'N':320,'B':330,'R':500,'Q':975,'K':0}
P={'P':(0,0,0,0,0,0,0,0,1,4,3,1,3,3,4,2,-2,1,1,1,1,1,2,-1,-3,0,0,0,0,0,0,-3),'N':(-8,-5,-6,-6,-2,-5,-5,-7,-2,-2,5,-2,0,3,-2,-2,-1,3,0,4,4,1,3,-2,0,1,3,2,2,3,1,0),'K':(0,4,1,-6,-5,2,6,-3,-3,0,1,0,-1,1,1,0,-6,-2,-6,-2,-7,-1,0,-4,-6,0,-3,-2,-4,-2,-1,-5)}
def pad(t):
 r=[]
 for y in range(8):
  z=(y if y<4 else 7-y)*8
  r+=[0]+list(t[z:z+8])+[0]
 return(0,)*20+tuple(r)+(0,)*20
S={k:pad(v)for k,v in P.items()};S['B']=S['R']=S['Q']=(0,)*120
M=1e5;I=2e5;nd=0
Stop=RuntimeError
N,E,W=-10,1,-1
D={'P':(N,N+N,N+W,N+E),'N':(-21,-19,-12,-8,8,12,19,21),'B':(-11,-9,9,11),'R':(-10,-1,1,10),'Q':(-11,-10,-9,-1,1,9,10,11),'K':(-11,-10,-9,-1,1,9,10,11)}
def parse(f):
 a=f.split();b=list(' '*20+' ........ '*8+' '*20);y=x=0
 for c in a[0]:
  if c=='/':y+=1;x=0
  elif c>'9':b[21+y*10+x]=c;x+=1
  else:x+=int(c)
 e=0 if a[3]=='-' else 4+ord(a[3][0])-10*int(a[3][1])
 ca=sum(1<<i for i,c in enumerate('KQkq')if c in a[2])
 b=''.join(b);s=a[1]<'c'
 if s:b=b[::-1].swapcase();e=119-e if e else 0;ca=(ca>>2)|((ca&3)<<2)
 return b,ca,e,s
def rot(pos):
 b,ca,e=pos[:3];return b[::-1].swapcase(),(ca>>2)|((ca&3)<<2),119-e if e else 0
def bad(pos):
 k=pos[0].index('k');return any(m[1]==k for m in genp(pos))
def genp(pos):
 b=pos[0];ca=pos[1]
 for i,p in enumerate(b):
  if p not in'PNBRQK':continue
  for d in D[p]:
   for j in count(i+d,d):
    q=b[j]
    if q in' PNBRQK':break
    if p=='P':
     if d in(N,N+N)and q!='.':break
     if d==N+N and(i<91+N or b[i+N]!='.'):break
     if d in(N+W,N+E)and q=='.'and j!=pos[2]:break
     if 21<=j<=28:
      yield from((i,j,x)for x in'QRBN');break
    yield i,j,''
    if p in'PNK'or q in'pnbrqk':break
    if i==91 and b[j+E]=='K'and ca&2:yield j+E,j+W,''
    if i==98 and b[j+W]=='K'and ca&1:yield j+W,j+E,''
def gen(pos):
 r=[]
 for m in genp(pos):
  i,j,_=m
  if pos[0][i]=='K'and abs(j-i)==2:
   s=i+1 if j>i else i-1
   if bad(rot(pos))or bad(make(pos,(i,s,''))):continue
  if not bad(make(pos,m)):r.append(m)
 return r
def make(pos,m):
 b=list(pos[0]);i,j,pr=m;p=b[i];b[i]='.';b[j]=p;e=0;ca=pos[1]
 if p=='P':
  if j==pos[2]:b[j+10]='.'
  if j-i==2*N:e=i+N
  if 21<=j<=28:b[j]=pr or'Q'
 if p=='K'and abs(j-i)==2:
  k=(i+j)//2;b[91 if j<i else 98]='.';b[k]='R'
 if p=='K':ca&=12
 for s in(i,j):ca&=({91:13,98:14,21:7,28:11}.get(s,15))
 return ''.join(b)[::-1].swapcase(),(ca>>2)|((ca&3)<<2),119-e if e else 0
def ev(b):
 s=0
 for i,p in enumerate(b):
  if p in'PNBRQK':s+=V[p]+10*S[p][i]
  elif p in'pnbrqk':u=p.upper();s-=V[u]+10*S[u][119-i]
 return s
def go(pos,d,a,b):
 global nd;nd+=1
 if nd>LIM:raise Stop
 ms=gen(pos)
 if not ms:return-M if bad(rot(pos)) else 0
 if d<1:
  best=ev(pos[0])
  if best>=b:return best
  if best>a:a=best
  ms=[m for m in ms if pos[0][m[1]] not in'. 'or m[2]]
 else:best=-I
 ms.sort(key=lambda m:V.get(pos[0][m[1]].upper(),0),reverse=1)
 for m in ms:
  v=-go(make(pos,m),d-1,-b,-a)
  if v>best:best=v
  if v>a:a=v
  if a>=b:return best
 return best
def uci(m,flip=0):
 i,j,p=m
 if flip:i,j=119-i,119-j
 f=lambda x:chr(97+(x-21)%10)+str(8-(x-21)//10)
 return f(i)+f(j)+p.lower()
def best_move(fen,legal):
 global nd
 pos=parse(fen);flip=pos[3];L=set(legal);ms=[m for m in gen(pos)if uci(m,flip)in L]
 if not ms:return legal[0]
 nd=0;best=ms[0]
 for d in count(1):
  if nd>LIM:break
  bm=best;bs=-I
  try:
   for m in ms:
    v=-go(make(pos,m),d-1,-I,I)
    if v>bs:bs=v;bm=m
  except Stop:break
  best=bm
 return uci(best,flip)
def post(u,d):
 return json.load(urlopen(Request(u,json.dumps(d).encode(),{'Content-Type':'application/json'})))
def run():
 u=os.environ['MAKEFUN_ENV_URL'];n=0;E=sys.stderr
 while 1:
  g=post(u+'/game',{})
  while g['status']=='your_move':g=post(u+'/move',{'game':g['game'],'move':best_move(g['fen'],g['legal_moves'])})
  if o:=g.get('outcome'):n+=1;print(f'{n}:{o} {g["reason"]}',file=E)
  if g['status']=='done':break
 print('W%d D%d L%d'%(g['wins'],g['draws'],g['losses']),file=E)
if __name__=='__main__':run()
