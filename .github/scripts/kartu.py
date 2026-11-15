"""Buat kartu SVG beranimasi dari data kontribusi GitHub (tanpa layanan pihak ketiga).

Dipakai oleh workflow Snake: hasilnya ikut didorong ke branch `output`.
"""
import datetime
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "salmakkiy")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/activity.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def ambil():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    kal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    hari = [d for w in kal["weeks"] for d in w["contributionDays"]]
    return kal["totalContributions"], hari


def streak(hari):
    today = datetime.date.today().isoformat()
    jalan, terpanjang, sekarang = 0, 0, 0
    for d in hari:
        if d["date"] > today:
            break
        if d["contributionCount"] > 0:
            jalan += 1
            terpanjang = max(terpanjang, jalan)
        else:
            jalan = 0
    # streak sekarang: hitung mundur, hari ini boleh masih kosong
    for d in reversed([x for x in hari if x["date"] <= today]):
        if d["contributionCount"] > 0:
            sekarang += 1
        elif d["date"] == today and sekarang == 0:
            continue
        else:
            break
    return sekarang, terpanjang


def svg(total, hari):
    sekarang, terpanjang = streak(hari)
    akhir = [d for d in hari if d["date"] <= datetime.date.today().isoformat()][-60:]
    puncak = max([d["contributionCount"] for d in akhir] + [1])
    W, H = 840, 230
    x0, y0, lebar, tinggi = 40, 196, 760, 96
    langkah = lebar / len(akhir)
    batang = []
    for i, d in enumerate(akhir):
        n = d["contributionCount"]
        h = 3 if n == 0 else max(8, n / puncak * tinggi)
        warna = "#1e2a44" if n == 0 else "#7fb2ff"
        x = x0 + i * langkah
        batang.append(
            f'<rect x="{x:.1f}" y="{y0 - h:.1f}" width="{langkah * 0.62:.1f}" height="{h:.1f}" rx="2.5" '
            f'fill="{warna}" style="animation-delay:{i * 0.018:.3f}s"><title>{d["date"]}: {n}</title></rect>'
        )
    angka = [
        (str(total), "contributions in the last year"),
        (str(sekarang), "day streak now"),
        (str(terpanjang), "longest streak"),
    ]
    blok = []
    for i, (n, label) in enumerate(angka):
        x = 40 + i * 200
        blok.append(
            f'<g class="angka" style="animation-delay:{0.15 + i * 0.15:.2f}s">'
            f'<text x="{x}" y="70" class="besar">{n}</text>'
            f'<text x="{x}" y="92" class="label">{label}</text></g>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
  .latar {{ fill: #0b1020; }}
  .besar {{ font: 700 34px 'Segoe UI', Inter, Helvetica, Arial, sans-serif; fill: #ffffff; }}
  .label {{ font: 500 13px 'Segoe UI', Inter, Helvetica, Arial, sans-serif; fill: #8fa6c9; }}
  .judul {{ font: 600 13px 'Segoe UI', Inter, Helvetica, Arial, sans-serif; fill: #7fb2ff; letter-spacing: .12em; }}
  .angka {{ opacity: 0; animation: muncul .6s ease-out forwards; }}
  rect.b, .batang rect {{ transform-box: fill-box; transform-origin: bottom; transform: scaleY(0); animation: tumbuh .7s cubic-bezier(.2,.8,.2,1) forwards; }}
  @keyframes muncul {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes tumbuh {{ to {{ transform: scaleY(1); }} }}
</style>
<rect class="latar" width="{W}" height="{H}" rx="16"/>
<text x="{W - 40}" y="36" text-anchor="end" class="judul">LAST 60 DAYS</text>
{''.join(blok)}
<g class="batang">{''.join(batang)}</g>
</svg>
"""


def main():
    total, hari = ambil()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg(total, hari))
    print(f"ok {OUT} total={total}")


if __name__ == "__main__":
    main()
