#!/usr/bin/env python3
"""Render entry.png for make.fun news-image-20261120 (Aa / zoelicious4843).

BUILD-TIME ONLY. Uses Pillow + the system DejaVu TrueType fonts
(/usr/share/fonts/truetype/dejavu/) — real TTF glyphs, no hand-made
stroke font, no hand-made PNG encoder. Pillow writes the PNG.

Layout + all 27 stories + facts follow hidden_files prompt-aa.md, with
the factual corrections from top5/NOTES.md addendum (agent-2 verification):
  - Kyiv 20 Nov = waves of ballistic missiles (no "~30" figure: monitoring
    channels only); the 19 Nov embassy strikes live in DATE CHECK.
  - Akvan gusts 90 km/h at landfall (forecast 110); 300,000+ evacuated.
  - Markets brief drops the conflicting Nikkei close; uses MSCI -7% week.
  - Iowa = Army DELAYS the 68-barrel blast to Monday 23 Nov (lawsuit).
  - GTA VI = Sensor Tower's latest $2.36bn / 24.6m copies [ESTIMATE].
  - EU-UK summit = food / carbon-market / youth-mobility deals agreed.

Run:  python3 render.py   (writes entry.png next to this file)
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024
M = 28  # margin

NAVY = (12, 27, 46)
PANEL = (18, 40, 63)
PANEL2 = (15, 34, 54)
GOLD = (217, 164, 65)
CREAM = (242, 234, 216)
DIM = (201, 191, 169)
FAINT = (160, 172, 186)
TEAL = (30, 110, 106)
TEAL_LT = (64, 160, 152)
RED = (192, 57, 43)
RED_LT = (224, 110, 95)
WHITE = (255, 255, 255)
SEA = (16, 58, 74)
ORANGE = (232, 120, 40)

FD = "/usr/share/fonts/truetype/dejavu"
SERIF_B = os.path.join(FD, "DejaVuSerif-Bold.ttf")
SERIF = os.path.join(FD, "DejaVuSerif.ttf")
SANS_B = os.path.join(FD, "DejaVuSans-Bold.ttf")
SANS = os.path.join(FD, "DejaVuSans.ttf")


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    """Greedy word wrap by measured width. Returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, xy, text, font, fill, max_w, leading=None):
    x, y = xy
    leading = leading or int(font.size * 1.28)
    lines = wrap(draw, text, font, max_w)
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


def fit_font(draw, text, path, start, max_w, min_size=10):
    """Largest size <= start whose text fits max_w."""
    size = start
    while size > min_size:
        f = F(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 1
    return F(path, min_size)


# --- coarse continent polygons (lon, lat), equirectangular inside disc ---
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-55, 60),
     (-60, 47), (-75, 35), (-80, 25), (-97, 16), (-105, 20), (-117, 32),
     (-125, 40), (-124, 48), (-140, 60), (-168, 66)],
    # South America
    [(-80, 10), (-60, 8), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -45), (-70, -55), (-73, -40), (-70, -20),
     (-77, -12), (-80, 10)],
    # Africa
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28),
     (43, 12), (51, 11), (48, 0), (40, -15), (35, -25), (28, -33),
     (20, -35), (15, -27), (12, -18), (9, 0), (8, 4), (-8, 5), (-17, 15)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (25, 65), (20, 70),
     (15, 68), (10, 64), (5, 60), (0, 55), (-5, 50), (-10, 36)],
    # Asia
    [(30, 36), (35, 42), (40, 45), (48, 47), (55, 51), (60, 55), (70, 60),
     (75, 68), (85, 70), (100, 72), (115, 73), (130, 72), (145, 70),
     (160, 66), (162, 60), (158, 52), (142, 45), (140, 40), (130, 35),
     (127, 33), (120, 30), (110, 20), (105, 10), (100, 8), (95, 15),
     (90, 22), (85, 20), (80, 13), (77, 8), (72, 20), (66, 25), (60, 25),
     (55, 27), (50, 30), (45, 30), (40, 35), (35, 36), (30, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (129, -32), (132, -32),
     (137, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -22), (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20), (113, -22)],
]


def in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def on_land(lon, lat):
    return any(in_poly(lon, lat, p) for p in CONTINENTS)


def project(cx, cy, r, lon, lat):
    """Equirectangular map inside the disc; lat range -60..75."""
    x = cx + r * (lon / 180.0)
    y = cy - r * ((lat + 2) / 78.0)
    return x, y


def draw_globe(draw, cx, cy, r):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SEA,
                 outline=GOLD, width=3)
    lon = -180
    while lon <= 180:
        lat = -58
        while lat <= 74:
            if on_land(lon, lat):
                x, y = project(cx, cy, r, lon, lat)
                if (x - cx) ** 2 + (y - cy) ** 2 < (r - 6) ** 2:
                    draw.ellipse([x - 2.2, y - 2.2, x + 2.2, y + 2.2],
                                 fill=GOLD)
            lat += 7
        lon += 7
    draw.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14],
                 outline=(90, 110, 140), width=1)


def draw_pin(draw, cx, cy, r, lon, lat, num):
    x, y = project(cx, cy, r, lon, lat)
    draw.ellipse([x - 10, y - 10, x + 10, y + 10], fill=RED,
                 outline=WHITE, width=2)
    f = F(SANS_B, 11)
    tw = draw.textlength(str(num), font=f)
    draw.text((x - tw / 2, y - 8), str(num), font=f, fill=WHITE)


def draw_spiral(draw, cx, cy, rmax):
    for k in range(5):
        rr = rmax * (k + 1) / 5.0
        a0 = k * 55
        a1 = a0 + 250
        col = WHITE if k % 2 == 0 else TEAL_LT
        draw.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a1,
                 fill=col, width=3)


def draw_missiles(draw, x, y):
    for i, (dx, dy) in enumerate([(0, 0), (14, 10), (28, 22)]):
        draw.line([x + dx, y + dy, x + dx + 26, y + dy - 12],
                  fill=ORANGE, width=3)
        draw.ellipse([x + dx + 26 - 3, y + dy - 12 - 3,
                      x + dx + 26 + 3, y + dy - 12 + 3], fill=(255, 200, 90))


def draw_sun(draw, cx, cy, r):
    for i in range(8):
        a = math.radians(i * 45)
        x0 = cx + int(math.cos(a) * (r + 4))
        y0 = cy + int(math.sin(a) * (r + 4))
        x1 = cx + int(math.cos(a) * (r + 12))
        y1 = cy + int(math.sin(a) * (r + 12))
        draw.line([x0, y0, x1, y1], fill=GOLD, width=3)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD,
                 outline=(180, 130, 40), width=2)


def icon_chart(draw, x, y, s):
    pts = [(x, y + s * 0.7), (x + s * 0.3, y + s * 0.45),
           (x + s * 0.55, y + s * 0.6), (x + s, y + s * 0.15)]
    draw.line(pts, fill=RED_LT, width=3, joint="curve")
    draw.line([x, y + s, x + s, y + s], fill=FAINT, width=2)


def icon_cricket(draw, x, y, s):
    draw.line([x + s * 0.2, y + s * 0.9, x + s * 0.7, y + s * 0.15],
              fill=(222, 184, 120), width=6)
    draw.ellipse([x + s * 0.62, y + s * 0.05, x + s * 0.95, y + s * 0.38],
                 fill=RED, outline=WHITE, width=1)


def icon_rocket(draw, x, y, s):
    draw.polygon([(x + s * 0.5, y), (x + s * 0.75, y + s * 0.45),
                  (x + s * 0.5, y + s * 0.35), (x + s * 0.25, y + s * 0.45)],
                 fill=CREAM)
    draw.polygon([(x + s * 0.5, y + s * 0.35), (x + s * 0.72, y + s * 0.75),
                  (x + s * 0.5, y + s * 0.95), (x + s * 0.28, y + s * 0.75)],
                 fill=ORANGE)
    draw.ellipse([x + s * 0.42, y + s * 0.18, x + s * 0.58, y + s * 0.34],
                 fill=TEAL_LT)


def icon_flags(draw, x, y, s):
    draw.line([x + s * 0.25, y, x + s * 0.25, y + s], fill=FAINT, width=2)
    draw.line([x + s * 0.75, y, x + s * 0.75, y + s], fill=FAINT, width=2)
    draw.rectangle([x + s * 0.25, y + s * 0.08, x + s * 0.62, y + s * 0.42],
                   fill=(40, 70, 160))
    draw.rectangle([x + s * 0.38, y + s * 0.08, x + s * 0.75, y + s * 0.42],
                   fill=(200, 40, 40), outline=WHITE, width=1)


def icon_megaphone(draw, x, y, s):
    draw.polygon([(x + s * 0.1, y + s * 0.4), (x + s * 0.55, y + s * 0.15),
                  (x + s * 0.55, y + s * 0.65), (x + s * 0.1, y + s * 0.55)],
                 fill=CREAM)
    draw.rectangle([x + s * 0.55, y + s * 0.15, x + s * 0.68, y + s * 0.65],
                   fill=RED_LT)
    draw.line([x + s * 0.2, y + s * 0.55, x + s * 0.2, y + s * 0.85],
              fill=CREAM, width=3)


def icon_boat(draw, x, y, s):
    draw.polygon([(x + s * 0.05, y + s * 0.55), (x + s * 0.95, y + s * 0.55),
                  (x + s * 0.8, y + s * 0.85), (x + s * 0.2, y + s * 0.85)],
                 fill=(222, 184, 120))
    draw.line([x + s * 0.5, y + s * 0.05, x + s * 0.5, y + s * 0.55],
              fill=FAINT, width=2)
    draw.polygon([(x + s * 0.5, y + s * 0.08), (x + s * 0.85, y + s * 0.45),
                  (x + s * 0.5, y + s * 0.45)], fill=WHITE)


def main():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # ================= HEADER 0-140 =================
    f_kick = F(SANS_B, 14)
    d.text((M, 14), "THE WORLD IN ONE DAY  ·  27 STORIES  ·  6 CONTINENTS",
           font=f_kick, fill=GOLD)
    right = "FRIDAY'S NEWS — ONE PAGE"
    d.text((W - M - d.textlength(right, font=f_kick), 14), right,
           font=f_kick, fill=FAINT)
    f_mast = fit_font(d, "Friday 20 November 2026", SERIF_B, 56, W - 2 * M)
    d.text((M, 34), "Friday 20 November 2026", font=f_mast, fill=CREAM)
    d.line([M, 108, W - M, 108], fill=GOLD, width=2)
    f_sub = F(SERIF, 17)
    d.text((M, 116), "One day of world news — a storm, missiles, a climate "
           "deadline, a market rout.", font=f_sub, fill=DIM)

    # ================= HERO 140-540 =================
    gcx, gcy, gr = 318, 340, 168
    draw_globe(d, gcx, gcy, gr)
    # vignettes around the globe (labels kept clear of the orbit ring)
    draw_missiles(d, 78, 168)                       # Kyiv trails, top-left
    d.text((66, 196), "KYIV", font=F(SANS_B, 12), fill=ORANGE)
    draw_spiral(d, 520, 268, 26)                    # Akvan spiral, right
    d.text((500, 300), "AKVAN", font=F(SANS_B, 12), fill=TEAL_LT)
    draw_sun(d, 512, 500, 15)                       # COP31 sun, bottom-right
    d.text((492, 524), "COP31", font=F(SANS_B, 12), fill=GOLD)
    # numbered pins (space story 6 has no place on the globe).
    # Europe pins nudged apart so 2/3/7/8 do not touch.
    for lon, lat, num in [(77, 21, 1), (36, 55, 2), (28, 33, 3),
                          (127, 37, 4), (174, -41, 5), (-2, 55, 7),
                          (10, 38, 8), (-17, 14, 9)]:
        draw_pin(d, gcx, gcy, gr, lon, lat, num)
    f_cap = F(SANS, 10)
    d.text((M, 518), "Pins mark stories 1–5 and 7–9 on the globe.",
           font=f_cap, fill=FAINT)

    # hero cards, x 560-996
    heroes = [
        ("1", "ODISHA · STORM", "Cyclone Akvan comes ashore in India",
         "Severe storm crosses the coast near Gopalpur on Friday morning; "
         "300,000+ evacuated, 423 rescue teams, 9,341 shelters; winds "
         "gusting to 90 km/h. (IMD, The Hindu)"),
        ("2", "KYIV · WAR", "Missiles rain on Kyiv overnight",
         "Waves of ballistic missiles after midnight damage three bridges "
         "over the Dnipro; fires burn in districts. "
         "(Kyiv Independent, UNN)"),
        ("3", "ANTALYA · CLIMATE", "COP31 ends its last day without a deal",
         "The final draft drops every mention of fossil fuels and the "
         "$120bn figure; hosts push a \u201c35 by 35\u201d goal; the text is "
         "due by midnight. (UN News, Reuters)"),
    ]
    card_x0, card_x1 = 560, W - M
    card_h, gap = 128, 8
    y = 140
    for num, kicker, head, deck in heroes:
        d.rectangle([card_x0, y, card_x1, y + card_h], fill=PANEL)
        d.rectangle([card_x0, y, card_x0 + 4, y + card_h], fill=GOLD)
        d.ellipse([card_x0 + 14, y + 12, card_x0 + 40, y + 38], fill=GOLD)
        fb = F(SANS_B, 15)
        tw = d.textlength(num, font=fb)
        d.text((card_x0 + 27 - tw / 2, y + 15), num, font=fb, fill=NAVY)
        tx = card_x0 + 50
        d.text((tx, y + 10), kicker, font=F(SANS_B, 12), fill=GOLD)
        f_head = F(SERIF_B, 22)
        hy = draw_wrapped(d, (tx, y + 30), head, f_head, CREAM,
                          card_x1 - tx - 12, leading=25)
        deck_end = draw_wrapped(d, (tx, hy + 2), deck, F(SANS, 12), DIM,
                                card_x1 - tx - 12, leading=14.5)
        assert deck_end <= y + card_h, (num, deck_end, y + card_h)
        y += card_h + gap

    # ================= BY THE NUMBERS 548-614 =================
    stats = [
        ("300,000", "EVACUATED AHEAD OF AKVAN"),
        ("49,097", "DOW CLOSE, BELOW 50,000"),
        ("−7%", "ASIA'S WORST WEEK SINCE 2020"),
        ("118", "PHILLIPS' HISTORIC CENTURY"),
        ("9,341", "SHELTERS OPEN IN ODISHA"),
        ("2.2%", "JAPAN CORE INFLATION"),
    ]
    d.line([M, 548, W - M, 548], fill=(60, 80, 110), width=1)
    col_w = (W - 2 * M) / 6
    f_num = F(SANS_B, 29)
    f_lab = F(SANS_B, 9.5)
    for i, (num, lab) in enumerate(stats):
        cx = M + col_w * i
        d.text((cx + 6, 556), num, font=f_num, fill=GOLD)
        draw_wrapped(d, (cx + 6, 588), lab, f_lab, DIM, col_w - 12,
                     leading=11)
    d.line([M, 614, W - M, 614], fill=(60, 80, 110), width=1)

    # ================= RAIL 622-814 =================
    rail = [
        ("SEOUL / TOKYO · MARKETS", "Asia's markets sink as the AI trade unwinds",
         "Asia-Pacific −7% for the week, worst since 2020; KOSPI −4.7%. "
         "(Reuters)",
         icon_chart),
        ("WELLINGTON · CRICKET", "Phillips makes history with 118",
         "First batter ever with Test, ODI and T20I centuries vs India in "
         "one year. (Reuters, ICC)",
         icon_cricket),
        ("SPACE", "BepiColombo counts down to Mercury",
         "ESA–JAXA probe ends its 8-year trip; orbit insertion set for "
         "Saturday. (ESA)",
         icon_rocket),
        ("BRUSSELS · EUROPE", "Burnham's first EU–UK reset summit",
         "EU–UK reset summit: food, carbon and youth-mobility deals "
         "agreed. (EU Council)",
         icon_flags),
        ("ROME · LABOUR", "Italy's CGIL holds a 24-hour general strike",
         "Unions march in about 100 squares against the 2027 budget; "
         "transport hit. (CGIL, AFP)",
         icon_megaphone),
        ("SENEGAL · MIGRATION", "Migrant boat capsizes off Senegal",
         "Four bodies recovered from a boat carrying 50–100 people. "
         "(Al Jazeera)",
         icon_boat),
    ]
    rw = (W - 2 * M - 2 * 12) / 3
    rh = 92
    for idx, (kicker, head, deck, icon) in enumerate(rail):
        col, row = idx % 3, idx // 3
        x0 = M + col * (rw + 12)
        y0 = 622 + row * (rh + 8)
        d.rectangle([x0, y0, x0 + rw, y0 + rh], fill=PANEL2)
        icon(d, x0 + 10, y0 + 10, 30)
        tx = x0 + 50
        d.text((tx, y0 + 7), kicker, font=F(SANS_B, 10.5), fill=GOLD)
        f_rh = F(SANS_B, 15)
        hy = draw_wrapped(d, (tx, y0 + 24), head, f_rh, CREAM,
                          x0 + rw - tx - 8, leading=18)
        deck_end = draw_wrapped(d, (tx, hy + 1), deck, F(SANS, 11.5), DIM,
                                x0 + rw - tx - 8, leading=14)
        assert deck_end <= y0 + rh - 2, (kicker, deck_end, y0 + rh)
        assert len(wrap(d, deck, F(SANS, 11.5), x0 + rw - tx - 8)) <= 2, kicker

    # ================= ALSO ON 822-938 =================
    d.text((M, 822), "ALSO ON FRIDAY 20 NOVEMBER — 18 MORE STORIES",
           font=F(SANS_B, 13), fill=GOLD)
    also = [
        "10 TOKYO — Japan core inflation 2.2%; a BoJ hike is eyed. (Reuters)",
        "11 BEIJING — China holds lending rates for an 18th month. (Reuters)",
        "12 SAN SALVADOR — Bukele files to run for a third term. (AP)",
        "13 BARCELONA — Cancer pill shrinks tumours 60.7% in early trial. (Reuters)",
        "14 FLORIDA — St Johns River hits a record 18.3 ft; schools shut. (AP)",
        "15 IOWA — Army delays blowing up 68 barrels of explosive to Monday. (AP)",
        "16 SEOUL — Ruling party moves to impeach Chief Justice Cho Hee-dae. (SBS)",
        "17 BRASILIA — Lula visits Raoni as Indigenous land is recognised. (Al Jazeera)",
        "18 COPENHAGEN — Denmark approves a Greenland defence bill. (AFP)",
        "19 JAKARTA — Indonesia passes an asset-forfeiture bill. (Reuters)",
        "20 HORMUZ — Four attacks on commercial vessels in 96 hours. (UKMTO)",
        "21 DOHA — U17 World Cup: Australia stun Argentina 2–0. (FIFA)",
        "22 TURIN — Alcaraz–Cobolli, Medvedev–Tiafoe close ATP Finals groups. (ATP)",
        "23 TONGA — Emergency declared as El Niño drought bites. (RNZ)",
        "24 WASHINGTON — Pentagon puts US war cost vs Iran at $48.3bn. (Reuters)",
        "25 NEW YORK — GTA VI day one: Sensor Tower counts 24.6m copies, $2.36bn [EST].",
        "26 SHENZHEN — Trump heads home after the summit with Xi and Putin. (CNN)",
        "27 GLOBAL — The UN marks World Children's Day. (UN)",
    ]
    f_also = F(SANS, 10.5)
    col_w2 = (W - 2 * M - 20) / 2
    for i, line in enumerate(also):
        col, row = i // 9, i % 9
        x = M + col * (col_w2 + 20)
        yy = 840 + row * 10.5
        f = f_also
        while d.textlength(line, font=f) > col_w2 and f.size > 8:
            f = F(SANS, f.size - 1)
        d.text((x, yy), line, font=f, fill=DIM)

    # ================= DATE CHECK 940-998 =================
    d.rectangle([M, 940, W - M, 998], outline=RED, width=2)
    d.text((M + 10, 945), "DATE CHECK — LEFT OUT",
           font=F(SANS_B, 12), fill=RED_LT)
    dc = ("First reported Thu 19 Nov, so NOT Friday's news: the "
          "Trump–Xi–Putin summit itself · Anthropic's $83 IPO pricing and "
          "Nasdaq debut · the ICJ's Rohingya genocide verdict · the Kyiv "
          "embassy strikes · GTA VI's midnight launch · the $190.4m Van "
          "Gogh sale · Voyager 1's one light-day (crossed 18 Nov) · the "
          "Senate's 48–51 Iran war-powers vote · the US–Venezuela military "
          "deal · Fiji's drought · Han Duck-soo's acquittal · the Crimea "
          "bridge attack · the Houthi strike on Riyadh's PIF tower · "
          "Trump's remarks delaying an Iran war to 2027.")
    dc_end = draw_wrapped(d, (M + 10, 962), dc, F(SANS, 10), CREAM,
                          W - 2 * M - 20, leading=11.5)
    assert dc_end <= 998, dc_end

    # ================= FOOTER 1000-1020 =================
    d.text((M, 1003), "Every story here happened, or was first reported, on "
           "Friday 20 November 2026. Sources: Reuters, AP, AFP, BBC, IMD, "
           "The Hindu, UN News, ESA, ICC. Original drawings.",
           font=F(SANS, 10), fill=FAINT)

    out = os.path.join(HERE, "entry.png")
    img.save(out, optimize=True)
    print("wrote", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
