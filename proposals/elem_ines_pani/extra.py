# אילוצים נוספים להצעת היסודי - רץ בתוך המנוע (m, x, NONFRI, CLASSES, PE_BLOCKS, OBJ_E זמינים)
def _hrs(c,t): return [x[(c,_s,t)] for _s in NONFRI if (c,_s,t) in x]
m.Add(sum(_hrs("ד מירי","אינס"))==8); m.Add(sum(_hrs("ה תניה","אינס"))==0)   # אינס: 8 בד מירי, יוצאת מה תניה
for _c in ("ד מירי","ד אינס","ה דני","ה תניה","ו אורנה","ו שרית"):              # סימה: בדיוק 4 בכל כיתה
    _v=_hrs(_c,"סימה")
    if _v: m.Add(sum(_v)==4)
# פאני: כמה שפחות חפיפה עם בלוקי הספורט של החטיבה (ראשון 2-4, רביעי 4-6) - קנס
_pe_over=[x[(_c,(_d,_h),"פאני")] for _d,_hs in PE_BLOCKS.items() for _h in _hs for _c in CLASSES if (_c,(_d,_h),"פאני") in x]
OBJ_E = OBJ_E + 500*sum(_pe_over)
