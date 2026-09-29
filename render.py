#!/usr/bin/env python3
"""Original Chinese history motion film; 15s, 1080p, 30fps, original sound."""
from pathlib import Path
from functools import lru_cache
import sys,subprocess,math,wave,json,argparse,importlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
W,H,FPS,S=1920,1080,30,4/3
RW,RH=round(W*S),round(H*S)
G=(197,165,109);R=(186,49,37);P=(234,225,208);K=(20,27,29)
TAU=math.tau
CH=[("先秦","文明初生","文字与青铜","ORIGINS"),("秦汉","山河一统","制度与疆域","UNIFICATION"),("隋唐","开放交融","城市与丝路","EXCHANGE"),("宋元","知识流转","印刷与交流","INVENTION"),("明清","远航与变局","海路与时代转折","CROSSROADS"),("近现代","变革新生","工业与科技","TRANSFORMATION")]
PAL=[((18,27,28),P,G),((128,33,29),P,(230,185,111)),(P,K,R),((20,29,32),P,G),((224,213,191),K,R),((16,23,27),P,G)]
def clamp(x):return max(0.,min(1.,x))
def out(x):return 1-(1-clamp(x))**4
def smooth(x):
 x=clamp(x);return x*x*(3-2*x)
def mix(a,b,x):return tuple(round(p+(q-p)*x) for p,q in zip(a,b))
def color(c,a):return (*c,round(255*clamp(a)))
FONTS={"serif":"/System/Library/Fonts/Supplemental/Songti.ttc","sans":"/System/Library/Fonts/Supplemental/Arial Unicode.ttf","latin":"/System/Library/Fonts/Supplemental/Futura.ttc","mono":"/System/Library/Fonts/Menlo.ttc"}
fi=0
for i in range(16):
 try:
  name=ImageFont.truetype(FONTS["serif"],16,index=i).getname()
  if "SC" in name[0] and "Bold" in name[1]:fi=i;break
 except OSError:break
@lru_cache(maxsize=60)
def font(n,style="sans"):return ImageFont.truetype(FONTS[style],round(n*S),index=fi if style=="serif" else 0)
class C:
 def __init__(self):self.im=Image.new("RGBA",(RW,RH));self.d=ImageDraw.Draw(self.im)
 def line(self,pts,c,w=2,a=1):
  if len(pts)>1:self.d.line([(round(x*S),round(y*S)) for x,y in pts],fill=color(c,a),width=max(1,round(w*S)),joint="curve")
 def poly(self,pts,c,a=1):self.d.polygon([(round(x*S),round(y*S)) for x,y in pts],fill=color(c,a))
 def rect(self,box,c,a=1):self.d.rectangle(tuple(round(x*S) for x in box),fill=color(c,a))
 def circle(self,x,y,r,c,w=2,a=1):
  box=tuple(round(v*S) for v in (x-r,y-r,x+r,y+r))
  if w:self.d.ellipse(box,outline=color(c,a),width=max(1,round(w*S)))
  else:self.d.ellipse(box,fill=color(c,a))
 def text(self,s,x,y,n,c,style="sans",a=1,anchor="lt"):self.d.text((round(x*S),round(y*S)),s,font=font(n,style),fill=color(c,a),anchor=anchor)
 def tracked(self,s,x,y,n,c,space=4,a=1):
  for ch in s:self.text(ch,x,y,n,c,"latin",a);x+=font(n,"latin").getlength(ch)/S+space
SH=[
[(-.65,-.55),(-.55,-.55),(-.55,-.85),(-.32,-.85),(-.32,-.55),(.32,-.55),(.32,-.85),(.55,-.85),(.55,-.55),(.65,-.55),(.53,.27),(.35,.48),(.34,.89),(.19,.89),(.15,.50),(-.15,.50),(-.19,.89),(-.34,.89),(-.35,.48),(-.53,.27)],
[(-.72,-.72),(.72,-.72),(.72,.72),(-.72,.72)],
[(0,-.96),(.12,-.75),(.34,-.68),(.19,-.57),(.19,-.43),(.48,-.33),(.30,-.24),(.30,-.08),(.63,.03),(.42,.12),(.42,.27),(.78,.40),(.56,.49),(.56,.75),(.85,.83),(-.85,.83),(-.56,.75),(-.56,.49),(-.78,.40),(-.42,.27),(-.42,.12),(-.63,.03),(-.30,-.08),(-.30,-.24),(-.48,-.33),(-.19,-.43),(-.19,-.57),(-.34,-.68),(-.12,-.75)],
[(-.78,-.55),(.44,-.88),(.80,-.53),(.80,.60),(-.43,.91),(-.78,.55)],
[(-.90,.36),(-.61,.51),(-.63,-.54),(-.13,-.79),(-.13,.49),(.13,.49),(.13,-.96),(.77,-.57),(.13,-.21),(.13,.49),(.91,.36),(.68,.73),(-.61,.73)],
[(-.92,.73),(-.92,.15),(-.75,.15),(-.75,-.13),(-.59,-.13),(-.59,.42),(-.43,.42),(-.43,-.52),(-.31,-.64),(-.19,-.52),(-.19,.40),(-.05,.40),(-.05,-.45),(.04,-.58),(.04,-.83),(.10,-.98),(.16,-.83),(.16,-.58),(.25,-.45),(.25,.41),(.43,.41),(.43,-.35),(.57,-.70),(.69,-.35),(.69,.40),(.83,.40),(.83,.11),(.95,.11),(.95,.73)]]
def sample(ps):
 ar=np.array(ps+[ps[0]],float);cum=np.r_[0,np.cumsum(np.linalg.norm(np.diff(ar,axis=0),axis=1))]
 return np.column_stack([np.interp(np.linspace(0,cum[-1],420),cum,ar[:,i]) for i in range(2)])
CURVES=[sample(x) for x in SH]
def arc(x,y,r,s,e):return [(x+r*math.cos(a),y+r*math.sin(a)) for a in np.linspace(s,e,100)]
def emblem(c,i,t,a,col,cx=1320,cy=503,r=285,outline=True,morph=None):
 def p(x,y):return cx+x*r,cy+y*r
 def ln(ps,w=2,op=1):c.line([p(x,y) for x,y in ps],col,w*r/285,a*op)
 if outline:
  pp=[p(x,y) for x,y in (CURVES[i] if morph is None else morph)];c.line(pp,col,4.2*r/285,a)
  j=int((t*.21%1)*419);c.line(pp[max(0,j-25):j+1],mix(col,P,.28),5.5*r/285,a*.95)
  c.circle(*pp[j],3,col,0,a)
 if i==0:
  ln([(-.64,-.47),(.64,-.47)],4);ln([(-.58,-.35),(.58,-.35)],1.5,.7);ln([(-.48,.25),(-.28,.41),(.28,.41),(.48,.25)],2.5)
  for s in [-1,1]:
   ln([(s*.06,-.21),(s*.40,-.21),(s*.40,.08),(s*.15,.08),(s*.15,-.07),(s*.30,-.07)],3);ln([(s*.06,.20),(s*.35,.20)],2)
  ln([(0,-.26),(0,.30)],2,.6)
  for x in [-.43,.43]:ln([(x,-.78),(x,-.55)],2,.8)
 elif i==1:
  for q,w in [(.63,3),(.56,1.4)]:ln([(-q,-q),(q,-q),(q,q),(-q,q),(-q,-q)],w)
  for s,y in [("一",-.45),("统",.03)]:c.text(s,*p(-.30,y),166*r/285,col,"serif",a)
 elif i==2:
  for y,w in [(-.64,.30),(-.30,.45),(.06,.61),(.43,.77)]:
   ln([(-w,y),(0,y-.14),(w,y)],3);ln([(-w*.90,y+.05),(w*.90,y+.05)],1.5,.6)
  for y,w in [(-.54,.16),(-.21,.26),(.15,.37),(.52,.50)]:
   for x in [-w,0,w]:ln([(x,y),(x,y+.18)],2,.9)
  ln([(-.83,.88),(.83,.88)],2);ln([(-.25,.78),(-.25,.54),(.25,.54),(.25,.78)],3)
  for k in range(2):ln([(-1.25+2.5*j/99,.99+.07*k-.14*math.sin(j/99*TAU+t)) for j in range(100)],1.7,.45)
 elif i==3:
  chars="天地文山海月日字流"
  for row in range(3):
   for column in range(3):
    x,y=p(-.65+column*.39,-.45+row*.38-column*.11);b=.29*r;sk=.078*r
    c.line([(x,y),(x+b,y-sk),(x+b,y+b-sk),(x,y+b),(x,y)],col,2*r/285,a)
    c.line([(x,y+b),(x+.055*r,y+b+.07*r),(x+b+.055*r,y+b-sk+.07*r),(x+b,y+b-sk)],col,1.2*r/285,a*.5)
    c.text(chars[row*3+column],x+.042*r,y+.032*r,53*r/285,col,"serif",a)
  ln([(-.78,.55),(-.43,.91),(-.43,-.21),(-.78,-.55)],2,.5)
 elif i==4:
  ln([(-.65,-.81),(-.65,.49)],3);ln([(.13,-1.04),(.13,.50)],3)
  for q in np.linspace(0,1,7):
   ln([(-.62,-.53+q*1.02),(-.13,-.79+q*1.28)],1.6,.8);ln([(.13,-.95+q*.74),(.77-.64*q,-.57+.36*q)],1.6,.8)
  ln([(-.80,.47),(.80,.47)],3);ln([(-.56,.62),(.64,.62)],1.4)
  for k in range(3):ln([(-1.10+2.2*j/99,.85+k*.095+.03*math.sin(j/99*TAU*3+t*2-k)) for j in range(100)],1.8,.8-k*.2)
 else:
  for x,top in [(-.84,.23),(-.66,-.03),(-.32,-.48),(.09,-.40),(.55,-.26),(.89,.21)]:
   for yy in np.arange(top,.62,.13):ln([(x-.028,yy),(x+.028,yy)],1.3,.55)
  ln([(-1.07+2.15*j/99,.85+.085*math.sin(j/99*math.pi)) for j in range(100)],2.2,.8)
  q=t*.65%1;x,y=p(-1.02+1.98*q,.86+.085*math.sin(q*math.pi));c.rect((x-36,y-11,x+36,y+3),col,a)
  for k in range(2):c.line([p(1.18*math.cos(z),.36*math.sin(z)-.7+k*.1) for z in np.linspace(-math.pi*.95,math.pi*.1,120)],col,1.3,a*.4)
@lru_cache(maxsize=8)
def background(i):
 bg=PAL[min(5,i)][0];rng=np.random.default_rng(917)
 yy,xx=np.mgrid[0:RH,0:RW].astype(np.float32);xx/=RW;yy/=RH
 rad=np.exp(-(((xx-.69)/.37)**2+((yy-.46)/.53)**2));grain=rng.normal(0,.9,(RH,RW));vig=-4*((xx-.5)**2+(yy-.5)**2)
 ar=np.empty((RH,RW,3),np.uint8)
 for k in range(3):ar[:,:,k]=np.clip(bg[k]+rad*(8 if i not in [2,4] else 2)+grain+vig,0,255)
 return Image.fromarray(ar).convert("RGBA")
def chrome(c,t,col,acc):
 c.line([(86,102),(1834,102)],col,1,.22);c.tracked("CHINA / A HISTORY IN MOTION",88,67,17,col,3,.8)
 c.text("中国历史",1832,64,21,col,a=.8,anchor="rt");c.line([(86,982),(1834,982)],col,1,.22)
 c.tracked("A CONTINUUM OF CIVILIZATION",88,1007,13,col,2,.5)
 c.text(f"00:{int(t):02d} / 00:15",1832,1003,18,col,"mono",.65,"rt")
 c.rect((86,974,86+1748*clamp(t/15),976),acc,.85)
def ribbon(c,t,a=.7,final=False):
 for k in range(9):
  pp=[]
  for j in range(150):
   x=-130+2180*j/149;y=722+100*math.sin(j/149*TAU*.76-t*.40)+26*math.sin(j/149*TAU*1.8+t*.5)+(k-4)*3.6*math.sin(j/149*math.pi)
   pp.append((x,y-(100 if final else 0)))
  c.line(pp,R,1.35,a*(.18 if k!=4 else .55))
def scene(t):
 i=min(5,int(t/2));u=t-i*2;e=smooth(u/.43) if i else 1;prev=max(0,i-1)
 bg=Image.blend(background(prev),background(i),e) if i and e<1 else background(i).copy()
 col=mix(PAL[prev][1],PAL[i][1],e);acc=mix(PAL[prev][2],PAL[i][2],e);c=C();chrome(c,t,col,acc);ribbon(c,t)
 c.text(CH[i][0][0],746,211,550,col,"serif",.035)
 cx,cy=1320,503+6*math.sin(t*1.4)
 for r,op in [(340,.30),(358,.13),(405,.075)]:c.circle(cx,cy,r*out(t/.75),col,1,op)
 for k in range(72):
  z=TAU*k/72+t*.055;r=368 if k%6 else 380
  c.line([(cx+358*math.cos(z),cy+358*math.sin(z)),(cx+r*math.cos(z),cy+r*math.sin(z))],acc,1.4,.52 if k%6==0 else .25)
 c.line(arc(cx,cy,340,-2+t*.15,-.75+t*.15),acc,3,.85)
 c.circle(cx+340*math.cos(-.75+t*.15),cy+340*math.sin(-.75+t*.15),4.5,acc,0)
 c.text("FORM / "+f"{i+1:02}",cx,cy-439,14,col,"mono",.55,"mt")
 reveal=out((u-.06)/.48) if i else out(t/.8)
 if i and e<1:emblem(c,prev,t,1-e,acc,cx,cy,outline=False)
 emblem(c,i,t,reveal,acc,cx,cy,r=285+8*math.sin(t*.8),morph=CURVES[prev]*(1-e)+CURVES[i]*e)
 c.tracked("CHAPTER "+f"{i+1:02}",133,230,18,acc,5,out(u/.3))
 c.text(CH[i][0],129,307+24*(1-out((u-.04)/.42)),52,col,"serif",out((u-.04)/.38))
 for j,ch in enumerate(CH[i][1]):
  v=out((u-.10-j*.035)/.47);c.text(ch,123+j*126,414+60*(1-v),119,col,"serif",v)
 c.line([(135,585),(204,585)],acc,3,out((u-.25)/.35))
 c.text(CH[i][2],134,616+15*(1-reveal),29,col,a=reveal*.8);c.tracked(CH[i][3],136,677,14,acc,4,reveal*.70)
 c.line([(155,907),(1765,907)],col,1.3,.2);c.line([(155,907),(155+1610*min(1,t/12),907)],acc,2.3,.75)
 for j,ch in enumerate(CH):
  x=155+j*322;active=j==i;c.circle(x,907,5 if active else 3,acc if t>=2*j else col,0,.95 if active else .45)
  c.text(ch[0],x,932,22,acc if active else col,a=1 if active else .52,anchor="mt")
  if active:c.text(f"{j+1:02}",x,866,15,acc,"mono",anchor="mt")
 if i and u<.32:
  x=-460+2860*out(u/.32);a=math.sin(math.pi*u/.32)
  c.poly([(x-105,-60),(x+105,-60),(x-150,1140),(x-350,1140)],R,.92*a);c.line([(x+111,-60),(x-144,1140)],G,1.5,.6*a)
 im=Image.alpha_composite(bg,c.im)
 if t<.2:im=Image.blend(Image.new("RGBA",(RW,RH),(*PAL[0][0],255)),im,out(t/.2))
 return im
def finale(t):
 u=t-12;c=C();chrome(c,t,P,G);ribbon(c,t,.8,True)
 for k in range(5):c.circle(960,476,205+k*92+32*out(u/1.5),G,1,.075)
 c.line(arc(960,476,416,-math.pi*.9+u*.08,-math.pi*.53+u*.08),R,5,.65);e=out((u-.10)/.6)
 c.tracked("ONE THREAD. MANY ERAS.",684,261+20*(1-e),19,G,4,e*.85)
 for j,ch in enumerate("一脉千年"):
  v=out((u-.18-j*.07)/.75);c.text(ch,543+j*213,367+85*(1-v),185,P,"serif",v)
 c.text("中国历史 · 15秒掠影",960,641+20*(1-e),29,P,a=e*.85,anchor="mt");c.line([(851,593),(1069,593)],G,2,e*.75)
 for j,ch in enumerate(CH):
  v=out((u-.35-j*.045)/.72);x=300+j*264;y=819+80*(1-v)
  if j<5:c.line([(x+71,y),(x+193,y)],G,1,v*.25)
  c.circle(x,y,68,G,1,v*.35);c.line([(x+qx*51,y+qy*51) for qx,qy in CURVES[j]],G,1.8,v*.92)
  c.text(ch[0],x,914,22,P,a=v*.70,anchor="mt")
 c.text("文明在时间中生长",960,692,21,G,a=out((u-.7)/.6)*.65,anchor="mt")
 v=out((u-.8)/.5);c.rect((1525,406,1617,498),R,v);c.text("华",1571,417,67,P,"serif",v,"mt")
 im=Image.alpha_composite(background(6),c.im)
 if u<.48:im=Image.blend(scene(11.999),im,smooth(u/.48))
 return im
def frame(t):return (scene(t) if t<12 else finale(t)).convert("RGB").resize((W,H),Image.Resampling.LANCZOS)
def sound():
 sr=48000;n=sr*15;music=np.zeros((n,2),float);rng=np.random.default_rng(88)
 def add(sig,start,amp=.3,pan=0):
  j=round(start*sr)
  if j<0:sig=sig[-j:];j=0
  sig=sig[:max(0,n-j)]
  if len(sig)==0:return
  music[j:j+len(sig),0]+=sig*amp*math.sqrt((1-pan)/2);music[j:j+len(sig),1]+=sig*amp*math.sqrt((1+pan)/2)
 def pluck(f,dur=2.1):
  t=np.arange(round(dur*sr))/sr;s=np.zeros_like(t)
  for k in range(1,8):s+=np.sin(TAU*f*(k+.0012*k*k)*t+.13*k)*np.exp(-t*(1.4+k*.65))/(k**1.2)
  return s*np.minimum(1,t/.007)
 notes=[62,69,74,76,62,67,69,74,64,69,76,79,67,74,76,81,69,76,79,81,74,81,86,88,86,81,79,76,74,74]
 for k,m in enumerate(notes):
  sig=pluck(440*2**((m-69)/12));add(sig,k*.5,.18 if k%4 else .23,(-1 if k%2 else 1)*.24);add(sig,k*.5+.175,.048,(-1 if k%2 else 1)*-.35)
 for onset in np.arange(0,14.1,.5):
  t=np.arange(int(.38*sr))/sr;phase=TAU*(47*t+42*.026*(1-np.exp(-t/.026)))
  add(np.sin(phase)*np.exp(-t*14)*np.minimum(1,t/.002),onset,.36 if onset%2==0 else .12)
  if onset%1==.5:
   t=np.arange(int(.075*sr))/sr;noise=rng.standard_normal(len(t));add(np.diff(noise,prepend=0)*np.exp(-t*78),onset,.022,.3)
 for onset in [2,4,6,8,10,12]:
  t=np.arange(int(.38*sr))/sr;noise=rng.standard_normal(len(t));noise=np.convolve(noise,np.ones(13)/13,mode="same")
  add(noise*np.sin(np.pi*t/.38)**2,onset-.19,.15,-.12);add(pluck(880,1.6)+.45*pluck(1320,1.6),onset,.06,.25)
 t=np.arange(3*sr)/sr
 for f in [146.832,220,293.665]:add(np.sin(TAU*f*t)*np.sin(np.minimum(t/.6,1)*np.pi/2)*np.exp(-t*.8),12,.072)
 for seconds,gain in [(.071,.10),(.137,.08),(.229,.055)]:
  shift=round(seconds*sr);music[shift:]+=music[:-shift,::-1].copy()*gain
 music*=np.minimum(1,np.arange(n)/sr/.025)[:,None];music*=np.minimum(1,(n-1-np.arange(n))/sr/.75)[:,None]
 music=np.tanh(music*1.5);music=music/max(.001,np.max(np.abs(music)))*.84
 p=ROOT/"original-score.wav"
 with wave.open(str(p),"wb") as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((music*32767).astype("<i2").tobytes())
 return p
def ffmpeg():
 import imageio_ffmpeg
 return imageio_ffmpeg.get_ffmpeg_exe()
def stills():
 (ROOT/"frames").mkdir(exist_ok=True);sheet=Image.new("RGB",(1920,1080))
 for j,t in enumerate([1.1,3.1,5.1,7.1,9.1,11.1,12.25,13.7,14.9]):
  im=frame(t);im.save(ROOT/"frames"/f"frame-{t:05.2f}.png");sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),((j%3)*640,(j//3)*360));print(f"still {t}",flush=True)
 sheet.save(ROOT/"storyboard.jpg",quality=93);frame(14.1).save(ROOT/"poster.jpg",quality=94)
def film():
 exe=ffmpeg();audio=sound();output=ROOT/"china-in-motion.mp4";temp=ROOT/"picture.mp4"
 args=[exe,"-y","-hide_banner","-loglevel","warning","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(temp)]
 with open(ROOT/"render.log","w") as log:
  p=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(450):
    p.stdin.write(frame(i/FPS).tobytes())
    if i%60==0:print(f"render {i}/450",flush=True)
   p.stdin.close()
   if p.wait()!=0:raise RuntimeError((ROOT/"render.log").read_text())
  except Exception:p.kill();raise
 subprocess.run([exe,"-y","-hide_banner","-loglevel","error","-i",str(temp),"-i",str(audio),"-c:v","copy","-c:a","aac","-b:a","256k","-t","15","-movflags","+faststart",str(output)],check=True)
 check=subprocess.run([exe,"-hide_banner","-i",str(output),"-f","null","-"],capture_output=True,text=True,check=True)
 (ROOT/"verification.log").write_text(check.stderr)
 (ROOT/"manifest.json").write_text(json.dumps({"title":"一脉千年","duration":15,"width":W,"height":H,"fps":FPS,"frames":450,"chapters":[{"from":i*2,"to":i*2+2,"era":x[0],"theme":x[1]} for i,x in enumerate(CH)],"finale":[12,15],"music":"original pentatonic synthesis"},ensure_ascii=False,indent=2))
 print(f"DONE {output} ({output.stat().st_size/1024/1024:.1f} MB)",flush=True)
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--stills",action="store_true");args=parser.parse_args();ROOT.mkdir(parents=True,exist_ok=True);print(f"font index {fi}",flush=True)
 if args.stills:stills()
 else:film()
