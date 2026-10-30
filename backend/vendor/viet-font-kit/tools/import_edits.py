"""Đọc file CHỈNH SỬA của bản Free (người dùng 27/10) — vfk-chinh-sua-<font>-rN.json do nút “Xuất chỉnh sửa” trên trang duyệt tạo ra
(hoặc đoạn chữ người dùng dán vào chat: dòng đầu là tiêu đề, phần sau là JSON). Cùng nội dung như đọc db của artifact bản Pro:
  docs["fontvn/<slug>-rN"]              góp ý từng mục (notesR10: V Xem trước · R Chỉnh dấu · C Bàn vẽ), summary = tóm tắt đọc được ngay
  docs[".../batch/p"]                    thông số Đồng loạt → batch_apply.py
  docs["fontvn/<slug>-r1/horn/v1"]       thanh Chi tiết (râu, dấu hỏi, dáng nét `shape`) → quick_vn mark_shape …
  docs[".../out/name"]                   tên font xuất → stamp.py
  docs[".../glyphs/<id>"]                chữ vẽ ở Bàn vẽ (như db collection glyphs)
usage: import_edits.py EXPORT.json|.txt OUT_DIR
  → OUT_DIR/db/<đường dẫn>.json (mỗi doc một file, như ArtifactData out_dir), OUT_DIR/batch_params.json, OUT_DIR/mark_shape.json; in tóm tắt.
build by @nhatmotion"""
import sys, os, json

src, out = sys.argv[1], sys.argv[2]
raw = open(src, encoding='utf-8').read()
i = raw.find('{')
if i < 0: sys.exit('không thấy JSON trong ' + src)
D = json.loads(raw[i:raw.rfind('}') + 1])
if D.get('kind') != 'vfk-edits': print('⚠ không phải file xuất của Việt Font Kit (kind=%r) — vẫn đọc thử' % D.get('kind'))
docs = D.get('docs', {})
os.makedirs(out, exist_ok=True)
for k, v in docs.items():
    p = os.path.join(out, 'db', k + '.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(v, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('Font: %s · trang %s · kit %s · xuất lúc %s · %d mục dữ liệu' % (D.get('font'), D.get('dock'), D.get('kitver'), D.get('exportedAt'), len(docs)))
main = docs.get(D.get('dock', ''), {})
if main.get('summary'): print('\n== Tóm tắt trang ==\n' + main['summary'])
NAME = {'V': 'Xem trước', 'R': 'Chỉnh dấu', 'C': 'Bàn vẽ'}
notes = {k: v for k, v in main.items() if k.startswith('notes')}
for nk, nv in notes.items():
    for sec, txt in (nv or {}).items():
        if (txt or '').strip(): print('\n[góp ý %s · %s] %s' % (nk, NAME.get(sec, sec), txt.strip()))
for k, v in docs.items():
    if k.endswith('/batch/p'):
        P = v.get('p', v); json.dump({'p': P}, open(os.path.join(out, 'batch_params.json'), 'w'), indent=1)
        ch = {kk: {f: x for f, x in pv.items() if x != (100 if f == 'sc' else 0)} for kk, pv in P.items()}
        ch = {kk: x for kk, x in ch.items() if x}
        print('\n[Đồng loạt] ' + (json.dumps(ch, ensure_ascii=False) if ch else 'không đổi') + ('  → batch_apply.py FONT %s/batch_params.json OUT' % out if ch else ''))
    elif k.endswith('/horn/v1'):
        s = v.get('shape') or {}
        ms = {'acute': {'h': s.get('sh', 100), 't': s.get('st', 100)}, 'grave': {'h': s.get('fh', 100), 't': s.get('ft', 100)},
              'tilde': {'h': s.get('xh', 100), 't': s.get('xt', 100)}, 'dot': {'round': s.get('nr', 0)}}
        json.dump({'mark_shape': ms}, open(os.path.join(out, 'mark_shape.json'), 'w'), indent=1)
        print('\n[Chi tiết] dáng nét: %s · nhóm khác: %s' % (json.dumps(ms), ', '.join(x for x in v if x not in ('shape', 'at', 'updatedAt'))))
    elif k.endswith('/out/name'):
        print('\n[Tên font xuất] %s (%s)' % (v.get('name'), v.get('ps')))
g = [k for k in docs if '/glyphs/' in k and (docs[k] or {}).get('touched')]
if g: print('\n[Bàn vẽ] %d chữ đã vẽ: %s — đọc %s/db/…/glyphs/' % (len(g), ', '.join(k.rsplit('/', 1)[1] for k in g), out))
