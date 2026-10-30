import sys
from fontTools.ttLib import TTFont
p=sys.argv[1]; f=TTFont(p); G=f["GSUB"].table
recs=G.FeatureList.FeatureRecord; order=sorted(range(len(recs)),key=lambda i:(recs[i].FeatureTag,i)); remap={o:n for n,o in enumerate(order)}
G.FeatureList.FeatureRecord=[recs[i] for i in order]
for sr in G.ScriptList.ScriptRecord:
    for ls in ([sr.Script.DefaultLangSys] if sr.Script.DefaultLangSys else [])+[l.LangSys for l in sr.Script.LangSysRecord]:
        ls.FeatureIndex=sorted(remap[i] for i in ls.FeatureIndex)
f.save(p)
