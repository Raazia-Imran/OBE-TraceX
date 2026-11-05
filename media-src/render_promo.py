"""Reproducible original motion graphics and synthesized music. No student data."""
from pathlib import Path
import math, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT=Path(sys.argv[1] if len(sys.argv)>1 else 'private-data/promo');OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS,DURATION=1080,1920,24,60
FONT='/usr/share/fonts/truetype/open-sans/OpenSans-'
def font(size,bold=False):return ImageFont.truetype(FONT+('Bold' if bold else 'Regular')+'.ttf',size)
F={n:font(n) for n in [19,22,25,28,30,34,40,46,54,62,70,80]}; B={n:font(n,True) for n in [22,25,28,30,34,40,46,54,62,70,80,90]}
SCRIPT=ImageFont.truetype('/usr/share/fonts/opentype/urw-base35/Z003-MediumItalic.otf',172)
CYAN=(115,232,235);LILAC=(182,155,255);WHITE=(237,241,255);MUTED=(162,179,209)
y,x=np.mgrid[0:H,0:W];g=np.exp(-((x-W*.35)**2/(W*.75)**2+(y-H*.45)**2/(H*.35)**2));bg=np.empty((H,W,3),np.uint8)
for c,(a,b) in enumerate([(7,22),(14,21),(31,45)]):bg[:,:,c]=a+b*g
BACKGROUND=Image.fromarray(bg)

def music():
 sr=48000;t=np.arange(sr*DURATION)/sr;mix=np.zeros((len(t),2),np.float64);rng=np.random.default_rng(17)
 def hz(n):return 440*2**((n-69)/12)
 def add(start,length,notes,level=.1,pan=0,pluck=False):
  a=int(start*sr);b=min(len(t),a+int(length*sr));u=np.arange(b-a)/sr;signal=np.zeros(len(u))
  for n in notes:signal+=np.sin(2*np.pi*hz(n)*u)+.13*np.sin(2*np.pi*hz(n)*2.002*u)
  envelope=(1-np.exp(-u/(.012 if pluck else .35)))*np.exp(-u/(.5 if pluck else 6))*np.minimum(1,np.maximum(0,(length-u)/(.22 if pluck else .6)))
  signal=signal*envelope*level/len(notes);mix[a:b,0]+=signal*(1-pan*.35);mix[a:b,1]+=signal*(1+pan*.35)
 chords=[[50,57,62,65],[46,53,58,62],[53,60,65,69],[48,55,60,64]]
 for k in range(25):add(k*2.4,4.6,chords[k%4],.20,(-1)**k*.3)
 motif=[74,77,81,79,77,74,72,69,70,74,77,76,74,72,69,72]
 for k in range(96):
  start=k*.6+1.2
  if start<58:add(start,1.5,[motif[k%len(motif)]],.11,math.sin(k)*.65,True)
 for k in range(100):
  a=int(k*.6*sr);n=min(int(.3*sr),len(t)-a);u=np.arange(n)/sr
  kick=np.sin(2*np.pi*(46*u+6*(1-np.exp(-u*30))))*np.exp(-u*22)*.10
  mix[a:a+n]+=kick[:,None]
  if k%2:
   n=min(int(.09*sr),len(t)-a);noise=rng.normal(0,1,n);noise=np.r_[0,np.diff(noise)];mix[a:a+n]+=noise[:,None]*np.exp(-np.arange(n)/sr*65)[:,None]*.012
 fade=np.minimum(1,t/2)*np.minimum(1,(DURATION-t)/3);mix*=fade[:,None];mix=np.tanh(mix*1.6);mix=mix/max(abs(mix.min()),abs(mix.max()))*.82
 with wave.open(str(OUT/'original-score.wav'),'wb') as file:file.setnchannels(2);file.setsampwidth(2);file.setframerate(sr);file.writeframes((mix*32767).astype('<i2').tobytes())

LOGO=Image.new('RGBA',(256,256));ld=ImageDraw.Draw(LOGO);ld.rounded_rectangle((0,0,255,255),60,fill=(18,28,52))
ld.polygon([(50,56),(98,56),(136,104),(170,56),(212,56),(156,130),(210,200),(160,200),(124,152),(90,200),(46,200),(102,126)],fill=LILAC)
ld.polygon([(50,56),(98,56),(208,200),(160,200)],fill=CYAN);ld.line([(40,216),(90,216),(124,174)],fill=(239,189,112),width=6);ld.ellipse((200,40,216,56),fill=(241,215,151))

def text(draw,xy,content,face,color=WHITE,anchor=None,spacing=14):
 draw.multiline_text(xy,content,font=face,fill=color,anchor=anchor,spacing=spacing)
def line(draw,points,color=CYAN,width=3):draw.line(points,fill=color,width=width,joint='curve')
def card(draw,box,color=(23,36,62),outline=(68,84,118),radius=26):draw.rounded_rectangle(box,radius,fill=color,outline=outline,width=2)
def check(draw,cx,cy):line(draw,[(cx-10,cy),(cx-2,cy+8),(cx+13,cy-10)],CYAN,4)
def icon(draw,kind,cx,cy,scale=1):
 z=lambda a:int(a*scale)
 if kind=='lock':
  draw.arc((cx-z(26),cy-z(60),cx+z(26),cy+z(2)),180,360,fill=CYAN,width=z(5));card(draw,(cx-z(40),cy-z(28),cx+z(40),cy+z(38)),radius=z(12));draw.ellipse((cx-z(5),cy-z(6),cx+z(5),cy+z(4)),fill=CYAN);line(draw,[(cx,cy),(cx,cy+z(17))],CYAN,z(4))
 elif kind=='sheet':
  card(draw,(cx-z(49),cy-z(50),cx+z(49),cy+z(50)),radius=z(12))
  for n in [-23,0,23]:line(draw,[(cx-z(32),cy+z(n)),(cx+z(32),cy+z(n))],CYAN,z(2))
  for n in [-10,12]:line(draw,[(cx+z(n),cy-z(30)),(cx+z(n),cy+z(30))],LILAC,z(2))
 else:
  card(draw,(cx-z(42),cy-z(55),cx+z(42),cy+z(55)),radius=z(12))
  for n in [-25,-3,19]:line(draw,[(cx-z(23),cy+z(n)),(cx+z(23),cy+z(n))],MUTED,z(3))
  draw.ellipse((cx+z(12),cy+z(22),cx+z(43),cy+z(53)),fill=(49,110,112));check(draw,cx+z(28),cy+z(38))

def logo(image,cx,cy,size=180,opacity=1):
 mark=LOGO.resize((size,size),Image.Resampling.LANCZOS)
 if opacity<1:mark.putalpha(mark.getchannel('A').point(lambda p:int(p*opacity)))
 image.paste(mark,(int(cx-size/2),int(cy-size/2)),mark)

SCENES=[
 (6,'INTRODUCING','OBE-TraceX','Automated Outcome-Based Education\nEvaluation & Grading Portal.'),
 (7,'THE PURPOSE','Every evaluation.\nOne clear picture.','Connecting assessment, academic review\nand the final group record.'),
 (8,'01 / EVALUATE','Six rubric forms.\nA structured start.','Evaluator responses enter linked sheets.\nSeat numbers identify each student.'),
 (8,'02 / CONSOLIDATE','One master.\nConnected results.','Existing formulas consolidate marks.\nn8n generates individual reports.'),
 (8,'03 / RECONCILE','Students connected.\nGroups assembled.','Official seat numbers match the roster.\nMissing or conflicting marks are flagged.'),
 (8,'04 / APPROVE','Review. Approve.\nPreserve.','Coordinator controls. HOD visibility.\nFrozen results retain their history.'),
 (8,'05 / EXPORT','Original templates.\nA complete record.','After approval and template verification:\ngroup D1–D7 Word and PDF exports.'),
 (7,'OBE-TraceX','Every outcome,\ntraced.','Automated Outcome-Based Education\nEvaluation & Grading Portal.')]
STARTS=np.cumsum([0]+[x[0] for x in SCENES]);

def frame(t):
 idx=min(7,int(np.searchsorted(STARTS,t,side='right')-1));duration,kicker,title,body=SCENES[idx];u=t-STARTS[idx];p=min(1,u/1.2);ease=1-(1-p)**3
 image=BACKGROUND.copy();draw=ImageDraw.Draw(image)
 # Stable identity, generous title area and portrait-safe margins.
 logo(image,115,121,66);text(draw,(167,97),'OBE-TraceX',B[28]);text(draw,(167,134),'PROJECT SHOWCASE',F[19],MUTED)
 text(draw,(84,237),kicker,B[22],CYAN)
 if idx==0:
  layer=Image.new('RGBA',(W,240));d=ImageDraw.Draw(layer);d.text((76,20),title,font=SCRIPT,fill=WHITE)
  reveal=int(930*min(1,max(0,(u-.4)/3.0)));layer.alpha_composite(Image.new('RGBA',(1,1)))
  mask=Image.new('L',layer.size);ImageDraw.Draw(mask).rectangle((0,0,reveal,240),fill=255);layer.putalpha(Image.fromarray(np.minimum(np.array(layer.getchannel('A')),np.array(mask))));image.paste(layer,(0,305),layer)
 else:text(draw,(82,int(308+(1-ease)*22)),title,B[70],spacing=12)
 text(draw,(86,513 if idx==0 else 535),body,F[30],MUTED,spacing=13)
 # Main motion canvas.
 top=690;bottom=1458
 card(draw,(66,top,1014,bottom),color=(13,25,47),outline=(48,63,95),radius=38)
 floaty=math.sin(t*.8)*12;cx=540;cy=1050+floaty
 if idx in [0,1,7]:
  for rx,ry in [(370,210),(260,310)]:draw.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),outline=(48,69,104),width=2)
  pts=[(cx+370*math.cos(a),cy+210*math.sin(a)) for a in np.linspace(t*.4,t*.4+2.6,70)];line(draw,pts,CYAN,4)
  for k,kind in enumerate(['form','sheet','lock','document']):
   a=k*math.pi/2+.6;xx=cx+325*math.cos(a);yy=cy+235*math.sin(a);icon(draw,kind,int(xx),int(yy),.9)
  logo(image,cx,cy,250+int(8*math.sin(t)))
  text(draw,(cx,1386),'ASSESSMENT  /  REVIEW  /  RECORD',F[22],MUTED,anchor='mm')
 elif idx==2:
  for k in range(6):
   xx=260+(k%3)*280;yy=890+(k//3)*310+math.sin(t+k)*9
   card(draw,(xx-108,yy-100,xx+108,yy+119),outline=CYAN if (int(u)%6)==k else (63,75,116))
   icon(draw,'form',xx,int(yy-8),.8);text(draw,(xx,yy+78),'D'+str(k+1),B[25],CYAN,anchor='mm')
 elif idx==3:
  for xx,label,kind in [(260,'FORM RESPONSES','form'),(820,'MASTER WORKBOOK','sheet')]:
   icon(draw,kind,xx,930,1.7);text(draw,(xx,1084),label,B[22],WHITE,anchor='mm')
  line(draw,[(380,930),(700,930)],(68,89,129),4)
  for k in range(4):
   xx=380+((u*.24+k*.25)%1)*320;draw.ellipse((xx-6,924,xx+6,936),fill=CYAN)
  icon(draw,'document',540,1250,1.0);line(draw,[(820,1140),(820,1250),(630,1250)],LILAC,3);text(draw,(540,1385),'n8n · INDIVIDUAL REPORTS',F[25],LILAC,anchor='mm')
 elif idx==4:
  for k in range(3):
   yy=845+k*175;card(draw,(125,yy-52,465,yy+62));draw.ellipse((155,yy-18,195,yy+22),fill=(101,84,168));text(draw,(224,yy-20),'SEAT NUMBER',F[22],WHITE)
   route=[(480,yy+4),(570,yy+4),(660,1050)];line(draw,route,(64,87,124),3)
   portion=(u*.26+k*.3)%1;xx=480+portion*180;pointy=(yy+4)+(1050-(yy+4))*portion;draw.ellipse((xx-5,pointy-5,xx+5,pointy+5),fill=CYAN)
  card(draw,(665,930,950,1180),outline=CYAN);logo(image,807,1010,90);text(draw,(807,1110),'PROJECT GROUP',B[22],CYAN,anchor='mm');text(draw,(540,1360),'STUDENT → OFFICIAL ROSTER → GROUP',F[22],MUTED,anchor='mm')
 elif idx==5:
  icon(draw,'lock',540,990,2.6)
  for k,label in enumerate(['REVIEWED','FROZEN','RECORDED']):
   xx=245+k*295;card(draw,(xx-118,1210,xx+118,1310));check(draw,xx-80,1260);text(draw,(xx+12,1260),label,B[22],WHITE,anchor='mm')
  text(draw,(540,1390),'APPROVALS WITH A TRACEABLE HISTORY',F[22],MUTED,anchor='mm')
 elif idx==6:
  for k in range(7):
   xx=210+(k%4)*218;yy=900+(k//4)*270+math.sin(t+k)*6
   icon(draw,'document',int(xx),int(yy),1.15);text(draw,(xx,yy+99),'D'+str(k+1),B[25],CYAN,anchor='mm')
  text(draw,(540,1390),'GROUP DOCUMENTS · WORD + PDF',F[25],LILAC,anchor='mm')
 # Scene takeaway, progress, honest project state.
 labels=['TRACKING. ANALYSIS. EXECUTION.','FROM FIRST EVALUATION TO FINAL RECORD','STRUCTURED DATA. CLEAR IDENTITIES.','EXISTING AUTOMATION, CONNECTED.','CONSISTENT STUDENT AND GROUP MATCHING.','CONTROLLED ACCESS. PROTECTED RECORDS.','VERIFIED QEC REFERENCES. PRINTABLE OUTPUTS.','BUILT FOR FYDP ASSESSMENT.']
 text(draw,(540,1548),labels[idx],B[22],CYAN,anchor='mm')
 if idx==7:
  text(draw,(540,1630),'Department of Software Engineering',F[25],WHITE,anchor='mm');text(draw,(540,1678),'NED University of Engineering & Technology',F[22],MUTED,anchor='mm')
 else:
  text(draw,(540,1640),f'{idx+1:02d}  /  08',F[25],MUTED,anchor='mm')
 for k in range(8):
  xx=84+k*115;fill=CYAN if k<idx else (61,74,106);draw.rounded_rectangle((xx,1760,xx+93,1766),3,fill=fill)
  if k==idx:draw.rounded_rectangle((xx,1760,xx+max(1,93*u/duration),1766),3,fill=LILAC)
 text(draw,(84,1811),'OBE-TraceX',B[25],WHITE);text(draw,(996,1818),'DEVELOPMENT SHOWCASE',F[19],MUTED,anchor='ra')
 # Smooth fade boundaries; no flashes.
 fade=min(1,u/.45,(duration-u)/.45)
 if fade<1:image=Image.blend(BACKGROUND,image,max(0,fade))
 return image

if __name__=='__main__':
 music();print('Original stereo score composed.',flush=True)
 for tm in [3,10,17,25,34,41,49,57]:frame(tm).save(OUT/f'preview-{tm:02d}.jpg',quality=90)
 command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(OUT/'original-score.wav'),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(DURATION),'-movflags','+faststart',str(OUT/'OBE-TraceX-Promo-60s.mp4')]
 process=subprocess.Popen(command,stdin=subprocess.PIPE)
 for i in range(DURATION*FPS):
  process.stdin.write(frame(i/FPS).tobytes())
  if i%(FPS*10)==0:print('Rendered seconds:',i//FPS,flush=True)
 process.stdin.close();code=process.wait();assert code==0
 print('Completed:',OUT/'OBE-TraceX-Promo-60s.mp4',flush=True)
