"""Split the approved review-page template (VibeEdit dev_99.37) into its CSS / JS infrastructure.
usage: extract_template.py SAVED_TEMPLATE.html OUT_DIR   -> styles.css (parts joined by /*----*/), script0..2.js, body.html"""
import re, sys, os
s = open(sys.argv[1]).read(); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
styles = re.findall(r'<style>(.*?)</style>', s, re.S)
scripts = re.findall(r'<script([^>]*)>(.*?)</script>', s, re.S)
open(out + '/styles.css', 'w').write('\n/*----*/\n'.join(styles))
for i, (a, b) in enumerate(scripts):
    open(out + '/script%d.js' % i, 'w').write(re.sub(r'data:[a-z/+-]+;base64,[A-Za-z0-9+/=]{200,}', 'DATAURI', b))
body = re.sub(r'<script.*?</script>', '<SCRIPT/>', s, flags=re.S)
body = re.sub(r'<style>.*?</style>', '<STYLE/>', body, flags=re.S)
open(out + '/body.html', 'w').write(re.sub(r'data:[a-z/+-]+;base64,[A-Za-z0-9+/=]{200,}', 'DATAURI', body))
print('styles', [len(x) for x in styles], 'scripts', [len(b) for a, b in scripts])
