"""Parse GPOS MarkBase / MarkMark / MarkLig anchors (fontTools only)."""
def anchors(f):
    gpos = f["GPOS"].table
    base = {}   # base[glyph][class_key] = (x,y)
    mark = {}   # mark[glyph] = (class_key, (x,y))  (MarkBase)
    mm_base = {}  # mark-to-mark: mm_base[mark1][class_key]
    mm_mark = {}  # mm_mark[mark2] = (class_key,(x,y))
    for li, lk in enumerate(gpos.LookupList.Lookup):
        for st in lk.SubTable:
            t = lk.LookupType
            if t == 9: t = st.ExtensionLookupType; st = st.ExtSubTable
            if t == 4:
                for g, r in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord):
                    mark.setdefault(g, ((li, r.Class), (r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate)))
                for g, br in zip(st.BaseCoverage.glyphs, st.BaseArray.BaseRecord):
                    for c, a in enumerate(br.BaseAnchor):
                        if a is not None: base.setdefault(g, {})[(li, c)] = (a.XCoordinate, a.YCoordinate)
            elif t == 6:
                for g, r in zip(st.Mark1Coverage.glyphs, st.Mark1Array.MarkRecord):
                    mm_mark.setdefault(g, ((li, r.Class), (r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate)))
                for g, br in zip(st.Mark2Coverage.glyphs, st.Mark2Array.Mark2Record):
                    for c, a in enumerate(br.Mark2Anchor):
                        if a is not None: mm_base.setdefault(g, {})[(li, c)] = (a.XCoordinate, a.YCoordinate)
    return base, mark, mm_base, mm_mark
