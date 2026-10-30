import json,sys,collections
P='display position box-sizing width height margin-top margin-right margin-bottom margin-left padding-top padding-right padding-bottom padding-left border-top-width border-top-style border-top-color border-left-width border-radius background-color background-image color font-family font-size font-weight font-style line-height letter-spacing text-transform text-align text-decoration-line white-space opacity gap flex-direction grid-template-columns overflow-x overflow-y cursor box-shadow list-style-type vertical-align border-collapse fill stroke backdrop-filter z-index transform'.split()
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
print('chỉ ở trước',len(set(a)-set(b)),'chỉ ở sau',len(set(b)-set(a)))
cnt=collections.Counter(); ex={}
for k in set(a)&set(b):
    if a[k]!=b[k]:
        x=a[k].split('|'); y=b[k].split('|')
        for i,(u,v) in enumerate(zip(x,y)):
            if u!=v:
                el=k.split('>')[-1]; key=(k.split()[0][:9],P[i],el.split(':')[0]); cnt[key]+=1; ex.setdefault(key,(u,v))
for k,n in cnt.most_common(60): print(n,k,ex[k][0][:50],'→',ex[k][1][:50])
