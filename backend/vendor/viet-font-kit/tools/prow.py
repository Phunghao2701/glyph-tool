import sys
from PIL import Image, ImageDraw, ImageFont
# prow.py out.png size font:text ...
size=int(sys.argv[2]); rows=sys.argv[3:]
H=int(size*1.45); im=Image.new('L',(2400,H*len(rows)+20),255); d=ImageDraw.Draw(im)
for k,r in enumerate(rows):
    fn,t=r.split(':',1); ft=ImageFont.truetype(fn,size)
    y=k*H+int(size*0.25)
    d.text((20,y),t,font=ft,fill=0,features=['-calt'])
im=im.crop(im.getbbox() and (0,0,min(2400,im.getbbox()[2]+30),im.size[1])); im.save(sys.argv[1])
