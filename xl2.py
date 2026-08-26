import openpyxl, io, sys
wb = openpyxl.load_workbook(r"C:/Users/asifb/Downloads/סדין תשפ_ז.xlsx", data_only=True)
def dump(name, out):
    ws = wb[name]
    with io.open(out,"w",encoding="utf-8") as f:
        for r in ws.iter_rows():
            vals = [(c.coordinate, str(c.value).strip()) for c in r if c.value is not None and str(c.value).strip()!=""]
            if vals:
                f.write(" | ".join(f"{a}={b}" for a,b in vals) + "\n")
dump('חלוקת שעות הוראה לפי צוות', 'sheet_tzevet.txt')
dump('הערות למסמך חלוקת שעות', 'sheet_hearot.txt')
dump('חלוקת שעות לכל כיתה יסודי', 'sheet_kita.txt')
dump('סדירויות', 'sheet_sedirut.txt')
