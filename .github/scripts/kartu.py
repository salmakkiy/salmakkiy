"""Kartu aktivitas gaya arcade piksel (senada kartu Tech Stack), dari data kontribusi GitHub.

Dipakai workflow Arcade: hasilnya didorong ke branch `output`.
"""
import base64
import json
import os
import random
import sys
import urllib.request

USER = os.environ.get("GH_USER", "salmakkiy")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/activity.svg"
DIR = os.path.dirname(os.path.abspath(__file__))

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
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    kal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    hari = [d for w in kal["weeks"] for d in w["contributionDays"]]
    return kal["totalContributions"], hari


def streak(hari):
    """Hari terakhir di kalender dianggap 'hari ini' (zona waktu pengguna); hari ini boleh masih kosong."""
    jalan = terpanjang = 0
    for d in hari:
        jalan = jalan + 1 if d["contributionCount"] > 0 else 0
        terpanjang = max(terpanjang, jalan)
    sekarang = 0
    for i, d in enumerate(reversed(hari)):
        if d["contributionCount"] > 0:
            sekarang += 1
        elif i == 0:
            continue
        else:
            break
    return sekarang, terpanjang


def svg(total, hari):
    sekarang, terpanjang = streak(hari)
    akhir = hari[-30:]
    puncak = max([d["contributionCount"] for d in akhir] + [1])
    font = base64.b64encode(open(os.path.join(DIR, "PressStart2P-Regular.ttf"), "rb").read()).decode()
    W, H = 840, 230
    random.seed(9)

    bintang = []
    for _ in range(22):
        x, y = random.randint(16, W - 16), random.randint(14, H - 14)
        if 60 < y < 200 and 30 < x < W - 30:
            continue
        s = random.choice([2, 2, 3])
        bintang.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="#d9c4ff" class="bt" style="animation-delay:{random.random()*3:.2f}s"/>')

    # tiga kotak skor gaya HUD gim
    kotak = []
    isi = [("TOTAL", total, "contributions"), ("STREAK", sekarang, "days now"), ("BEST", terpanjang, "days streak")]
    for i, (judul, angka, ket) in enumerate(isi):
        x = 34 + i * 128
        kotak.append(
            f'<g class="muncul" style="animation-delay:{0.1 + i * 0.15:.2f}s">'
            f'<rect x="{x}" y="70" width="116" height="118" rx="6" fill="#140b2b" stroke="#5b3aa0" stroke-width="2"/>'
            f'<text x="{x + 58}" y="94" text-anchor="middle" class="kecil">{judul}</text>'
            f'<text x="{x + 58}" y="146" text-anchor="middle" class="angka">{angka}</text>'
            f'<text x="{x + 58}" y="172" text-anchor="middle" class="ket">{ket}</text></g>'
        )

    # grafik batang piksel 30 hari
    gx0, gy0, lebar_g, tinggi_g = 440, 186, 366, 112
    langkah = lebar_g / len(akhir)
    blok = 6
    batang = []
    for i, d in enumerate(akhir):
        n = d["contributionCount"]
        x = gx0 + i * langkah
        if n == 0:
            batang.append(f'<rect x="{x:.1f}" y="{gy0 - blok}" width="{blok + 2}" height="{blok}" fill="#2a1d4a"/>')
            continue
        jumlah = max(1, round(n / puncak * (tinggi_g / (blok + 2))))
        for k in range(jumlah):
            t = k / max(1, tinggi_g / (blok + 2) - 1)
            warna = "#f6e7c1" if t > 0.7 else ("#d9c4ff" if t > 0.35 else "#9b7bff")
            y = gy0 - (k + 1) * (blok + 2)
            batang.append(
                f'<rect x="{x:.1f}" y="{y}" width="{blok + 2}" height="{blok}" fill="{warna}" class="naik" '
                f'style="animation-delay:{0.4 + i * 0.03 + k * 0.04:.2f}s"/>'
            )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="latar" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1a0f33"/><stop offset="1" stop-color="#2d1b57"/></linearGradient>
  <style>
    @font-face {{ font-family: 'PS2P'; src: url(data:font/ttf;base64,{font}) format('truetype'); }}
    .judul {{ font-family: 'PS2P', monospace; font-size: 14px; fill: #f6e7c1; }}
    .kecil {{ font-family: 'PS2P', monospace; font-size: 8px; fill: #b9a3e6; }}
    .angka {{ font-family: 'PS2P', monospace; font-size: 26px; fill: #f6e7c1; }}
    .ket {{ font-family: 'PS2P', monospace; font-size: 6px; fill: #8f7cc0; }}
    .muncul {{ opacity: 0; animation: muncul .5s steps(4) forwards; }}
    @keyframes muncul {{ to {{ opacity: 1; }} }}
    .naik {{ opacity: 0; animation: muncul .2s steps(2) forwards; }}
    .bt {{ animation: kelip 2.4s steps(2) infinite; }}
    @keyframes kelip {{ 50% {{ opacity: .15; }} }}
    .kursor {{ animation: kedip 1s steps(1) infinite; }}
    @keyframes kedip {{ 50% {{ opacity: 0; }} }}
  </style>
</defs>
<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="14" fill="url(#latar)" stroke="#5b3aa0" stroke-width="3"/>
{''.join(bintang)}
<text x="34" y="46" class="judul">PLAYER STATS</text><rect x="210" y="32" width="12" height="13" fill="#f6e7c1" class="kursor"/>
<text x="{gx0}" y="62" class="kecil">LAST 30 DAYS</text>
<line x1="{gx0}" y1="{gy0 + 3}" x2="{gx0 + lebar_g}" y2="{gy0 + 3}" stroke="#5b3aa0" stroke-width="2" stroke-dasharray="4 4"/>
{''.join(kotak)}
{''.join(batang)}
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
