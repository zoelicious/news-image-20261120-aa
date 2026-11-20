#!/usr/bin/env python3
"""Render entry.png for make.fun news-image-20261120 (Aa / zoelicious4843).

Concept: "THE WORLD AT A GLANCE" - one hero globe on a deep-navy editorial
page, three biggest stories orbiting it, six illustrated briefs, ALSO ON list,
DATE CHECK footer. Everything is drawn by this program at render time:
own PNG encoder (zlib/struct), own stroke font embedded below, own vector
illustrations. Stdlib only, no network, fully deterministic.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
NAVY = (12, 27, 46)        # page background
NAVY2 = (18, 40, 63)       # card panel
NAVY3 = (23, 52, 82)       # lighter panel edge
GOLD = (217, 164, 65)      # accents, masthead rule, globe dots
GOLD_LT = (232, 190, 110)
CREAM = (242, 234, 216)    # main text
CREAM_DIM = (198, 190, 168)
TEAL = (46, 140, 130)      # globe ocean
TEAL_DK = (20, 56, 74)     # globe disc
TEAL_LT = (120, 200, 190)
RED = (196, 62, 48)        # date-check border / pins
RED_LT = (224, 110, 92)
ORANGE = (232, 130, 48)    # missile streaks
WHITE = (255, 255, 255)
GREY = (140, 152, 168)     # source tags
BLUE_EU = (58, 92, 180)

# ------------------------------------------------------------------ canvas --
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def rect(self, x0, y0, x1, y1, c, lw=1):
        self.fill_rect(x0, y0, x1, y0 + lw, c)
        self.fill_rect(x0, y1 - lw, x1, y1, c)
        self.fill_rect(x0, y0, x0 + lw, y1, c)
        self.fill_rect(x1 - lw, y0, x1, y1, c)

    def fill_circle(self, cx, cy, r, c):
        r = int(round(r))
        if r <= 0:
            return
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def ring(self, cx, cy, r, c, lw=2):
        """Circle outline of width lw."""
        for k in range(lw):
            rr = r - k
            if rr <= 0:
                break
            steps = max(24, int(2 * math.pi * rr))
            for i in range(steps):
                a = 2 * math.pi * i / steps
                self.set(int(round(cx + rr * math.cos(a))),
                         int(round(cy + rr * math.sin(a))), c)

    def fill_poly(self, pts, c):
        """Scanline fill, even-odd. pts: list of (x, y) floats."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(self.h - 1, int(math.floor(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    t = (y - y1p) / (y2p - y1p)
                    xs.append(x1 + t * (x2 - x1))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa = max(0, int(math.ceil(xs[j])))
                xb = min(self.w, int(math.floor(xs[j + 1])) + 1)
                if xb > xa:
                    row = bytes(c) * (xb - xa)
                    k = (y * self.w + xa) * 3
                    self.buf[k:k + len(row)] = row

    def line(self, x0, y0, x1, y1, c, w=1):
        """Thick line as a filled quad + round caps."""
        x0, y0, x1, y1 = float(x0), float(y0), float(x1), float(y1)
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        if L < 0.001:
            self.fill_circle(int(round(x0)), int(round(y0)), max(1, w / 2), c)
            return
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        self.fill_poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                        (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], c)
        r = w / 2
        self.fill_circle(int(round(x0)), int(round(y0)), r, c)
        self.fill_circle(int(round(x1)), int(round(y1)), r, c)

    def polyline(self, pts, c, w=1):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, w)

    def arc(self, cx, cy, r, a0, a1, c, w=1, steps=48):
        pts = []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.polyline(pts, c, w)

    def ellipse(self, cx, cy, rx, ry, c, w=1, steps=72):
        pts = []
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        self.polyline(pts, c, w)

# -------------------------------------------------------------------- PNG ---
def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter None
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------- stroke font --
# Grid: caps y 0..7 (baseline 7), x-height y 2..7, descenders to y 9.
# Each glyph: (advance, [stroke, ...]); a stroke is a tuple of (x, y) points.
FONT = {
 'A': (6, [((0,7),(3,0),(6,7)), ((1,5),(5,5))]),
 'B': (6, [((0,0),(0,7)), ((0,0),(4,0),(5,1),(5,3),(4,4),(0,4)),
               ((4,4),(5,5),(5,6),(4,7),(0,7))]),
 'C': (6, [((5,1),(4,0),(1,0),(0,1),(0,6),(1,7),(4,7),(5,6))]),
 'D': (6, [((0,0),(0,7)), ((0,0),(4,0),(5,1),(5,6),(4,7),(0,7))]),
 'E': (6, [((0,0),(0,7)), ((0,0),(5,0)), ((0,3),(4,3)), ((0,7),(5,7))]),
 'F': (6, [((0,0),(0,7)), ((0,0),(5,0)), ((0,3),(4,3))]),
 'G': (6, [((5,1),(4,0),(1,0),(0,1),(0,6),(1,7),(4,7),(5,6),(5,4),(3,4))]),
 'H': (6, [((0,0),(0,7)), ((6,0),(6,7)), ((0,3),(6,3))]),
 'I': (4, [((2,0),(2,7)), ((0,0),(4,0)), ((0,7),(4,7))]),
 'J': (6, [((5,0),(5,6),(4,7),(1,7),(0,6),(0,5))]),
 'K': (6, [((0,0),(0,7)), ((5,0),(0,3)), ((1,4),(5,7))]),
 'L': (6, [((0,0),(0,7),(5,7))]),
 'M': (7, [((0,7),(0,0),(3,4),(6,0),(6,7))]),
 'N': (7, [((0,7),(0,0),(6,7),(6,0))]),
 'O': (7, [((1,0),(5,0),(6,1),(6,6),(5,7),(1,7),(0,6),(0,1),(1,0))]),
 'P': (6, [((0,7),(0,0),(4,0),(5,1),(5,3),(4,4),(0,4))]),
 'Q': (7, [((1,0),(5,0),(6,1),(6,6),(5,7),(1,7),(0,6),(0,1),(1,0)),
               ((4,5),(6,7))]),
 'R': (6, [((0,7),(0,0),(4,0),(5,1),(5,3),(4,4),(0,4)), ((3,4),(6,7))]),
 'S': (6, [((5,1),(4,0),(1,0),(0,1),(0,3),(1,4),(4,4),(5,5),(5,6),(4,7),(1,7),(0,6))]),
 'T': (6, [((0,0),(6,0)), ((3,0),(3,7))]),
 'U': (7, [((0,0),(0,6),(1,7),(5,7),(6,6),(6,0))]),
 'V': (7, [((0,0),(3,7),(6,0))]),
 'W': (8, [((0,0),(2,7),(4,3),(6,7),(8,0))]),
 'X': (6, [((0,0),(6,7)), ((6,0),(0,7))]),
 'Y': (6, [((0,0),(3,3),(6,0)), ((3,3),(3,7))]),
 'Z': (6, [((0,0),(6,0),(0,7),(6,7))]),
 'a': (6, [((5,3),(4,2),(1,2),(0,3),(0,6),(1,7),(4,7),(5,6),(5,3)),
               ((5,2),(5,7))]),
 'b': (6, [((0,0),(0,7)), ((0,4),(4,4),(5,5),(5,6),(4,7),(0,7))]),
 'c': (6, [((5,3),(4,2),(1,2),(0,3),(0,6),(1,7),(4,7),(5,6))]),
 'd': (6, [((0,3),(1,2),(4,2),(5,3),(5,6),(4,7),(1,7),(0,6),(0,3)),
               ((5,0),(5,7))]),
 'e': (6, [((5,5),(4,7),(1,7),(0,6),(0,3),(1,2),(4,2),(5,3),(5,4),(0,4))]),
 'f': (5, [((4,1),(3,0),(2,1),(2,7)), ((1,4),(4,4))]),
 'g': (6, [((5,3),(4,2),(1,2),(0,3),(0,6),(1,7),(4,7),(5,6),(5,3)),
               ((5,6),(5,8),(4,9),(1,9),(0,8))]),
 'h': (6, [((0,0),(0,7)), ((0,4),(1,3),(4,3),(5,4),(5,7))]),
 'i': (3, [((1,2),(1,7)), ((1,0),(1,0))]),
 'j': (4, [((3,2),(3,8),(2,9),(1,9),(0,8)), ((3,0),(3,0))]),
 'k': (6, [((0,0),(0,7)), ((4,2),(0,5),(5,7))]),
 'l': (3, [((1,0),(1,7))]),
 'm': (7, [((0,2),(0,7)), ((0,2),(1,2),(2,3)), ((2,2),(2,7)),
               ((2,2),(4,2),(5,3),(5,7))]),
 'n': (6, [((0,7),(0,2),(1,2),(2,3),(2,7))]),
 'o': (6, [((1,2),(4,2),(5,3),(5,6),(4,7),(1,7),(0,6),(0,3),(1,2))]),
 'p': (6, [((0,2),(0,9)), ((0,4),(4,4),(5,5),(5,6),(4,7),(0,7))]),
 'q': (6, [((0,3),(1,2),(4,2),(5,3),(5,6),(4,7),(1,7),(0,6),(0,3)),
               ((5,2),(5,9))]),
 'r': (5, [((0,7),(0,2),(1,2),(3,3))]),
 's': (6, [((4,3),(3,2),(1,2),(0,3),(0,4),(1,5),(3,5),(4,6),(4,7),(3,7),(1,7))]),
 't': (5, [((3,0),(3,7),(4,7)), ((1,3),(4,3))]),
 'u': (6, [((0,2),(0,6),(1,7),(3,7),(4,6),(4,2))]),
 'v': (6, [((0,2),(2,7),(4,2))]),
 'w': (8, [((0,2),(1,7),(2,4),(3,7),(4,2)), ((4,2),(5,7),(6,4),(7,7),(8,2))]),
 'x': (6, [((0,2),(4,7)), ((4,2),(0,7))]),
 'y': (6, [((0,2),(2,6),(4,2)), ((2,6),(2,9),(1,9))]),
 'z': (6, [((0,2),(4,2),(0,7),(4,7))]),
 '0': (7, [((1,0),(5,0),(6,1),(6,6),(5,7),(1,7),(0,6),(0,1),(1,0))]),
 '1': (5, [((2,1),(3,0),(3,7)), ((1,7),(4,7))]),
 '2': (6, [((0,1),(1,0),(4,0),(5,1),(5,3),(0,7),(5,7))]),
 '3': (6, [((0,1),(1,0),(4,0),(5,1),(5,3),(4,4)), ((4,4),(5,5),(5,6),(4,7),(1,7),(0,6))]),
 '4': (6, [((4,0),(0,5),(5,5)), ((4,0),(4,7))]),
 '5': (6, [((5,0),(0,0),(0,3),(4,3),(5,4),(5,6),(4,7),(1,7),(0,6))]),
 '6': (6, [((5,0),(4,0),(1,0),(0,1),(0,6),(1,7),(4,7),(5,6),(5,4),(4,3),(0,3))]),
 '7': (6, [((0,0),(5,0),(2,7))]),
 '8': (6, [((1,0),(4,0),(5,1),(5,3),(4,4),(1,4),(0,3),(0,1),(1,0)),
               ((1,4),(4,4),(5,5),(5,6),(4,7),(1,7),(0,6),(0,5),(1,4))]),
 '9': (6, [((5,7),(5,1),(4,0),(1,0),(0,1),(0,4),(1,5),(4,5),(5,4))]),
 ' ': (3, []),
 '.': (3, [((1,7),(1,7))]),
 ',': (3, [((1,6),(1,7),(0,9))]),
 ':': (3, [((1,3),(1,3)), ((1,7),(1,7))]),
 ';': (3, [((1,3),(1,3)), ((1,6),(1,7),(0,9))]),
 '!': (3, [((1,0),(1,5)), ((1,7),(1,7))]),
 '?': (6, [((1,1),(2,0),(4,0),(5,1),(5,3),(4,4),(3,4),(2,5)), ((2,7),(2,7))]),
 "'": (3, [((2,0),(1,2))]),
 '"': (5, [((1,0),(0,2)), ((4,0),(3,2))]),
 '(': (4, [((3,0),(1,2),(1,5),(3,7))]),
 ')': (4, [((1,0),(3,2),(3,5),(1,7))]),
 '-': (6, [((0,4),(5,4))]),
 '|': (3, [((1,0),(1,7))]),
 '/': (6, [((4,0),(0,7))]),
 '%': (8, [((1,0),(2,0),(2,2),(1,2),(1,0)), ((5,5),(6,5),(6,7),(5,7),(5,5)),
               ((6,0),(1,7))]),
 '$': (6, [((5,1),(4,0),(1,0),(0,1),(0,3),(1,4),(4,4),(5,5),(5,6),(4,7),(1,7),(0,6)),
               ((3,0),(3,7))]),
 '+': (6, [((1,4),(5,4)), ((3,2),(3,6))]),
 '=': (6, [((0,3),(5,3)), ((0,5),(5,5))]),
 '*': (6, [((3,1),(3,6)), ((1,2),(5,5)), ((5,2),(1,5))]),
 '~': (6, [((0,4),(1,3),(2,4),(3,3),(4,4),(5,3))]),
 '&': (7, [((5,0),(4,0),(2,1),(1,3),(2,5),(4,5),(6,7)), ((6,3),(5,2),(3,3),(1,5),(0,7))]),
}

def glyph_adv(ch):
    return FONT.get(ch, FONT['?'])[0]

def text_width(text, scale, tracking=0.0):
    w = 0.0
    for ch in text:
        w += glyph_adv(ch) * scale + tracking
    return w - tracking if text else 0.0

def draw_text(cv, x, y, text, scale, color, weight=1.0, tracking=0.0):
    """Draw text; (x, y) is the top-left of the cap area. Returns end x."""
    lw = max(1.0, scale * 1.05 * weight)
    cx = float(x)
    for ch in text:
        adv, strokes = FONT.get(ch, FONT['?'])
        for st in strokes:
            pts = [(cx + px * scale, y + py * scale) for (px, py) in st]
            if len(pts) == 1:
                cv.fill_circle(int(round(pts[0][0])), int(round(pts[0][1])),
                               max(1.0, lw / 2), color)
            else:
                cv.polyline(pts, color, lw)
        cx += adv * scale + tracking
    return cx

def wrap_text(text, scale, max_w, tracking=0.0):
    """Greedy word wrap. Returns list of lines."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if text_width(trial, scale, tracking) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

def draw_para(cv, x, y, text, scale, color, max_w, leading, weight=1.0, tracking=0.0):
    """Draw wrapped paragraph; returns y after last line."""
    for line in wrap_text(text, scale, max_w, tracking):
        draw_text(cv, x, y, line, scale, color, weight, tracking)
        y += leading
    return y

# ------------------------------------------------------------------- globe --
# Continents as (lon, lat) polygons; sampled on a grid, drawn as dots.
CONTINENTS = {
 'africa': [(-17,15),(-16,20),(-10,28),(-5,35),(0,36),(10,37),(15,32),(20,32),
            (30,31),(32,31),(35,28),(38,22),(43,12),(48,11),(51,11),(48,2),
            (42,-5),(40,-12),(36,-18),(33,-26),(28,-33),(20,-35),(16,-29),
            (14,-22),(12,-18),(13,-12),(9,-1),(9,4),(4,6),(-8,5),(-13,8),
            (-17,12),(-17,15)],
 'europe': [(-10,36),(-9,38),(-9,43),(-2,44),(-2,48),(-4,49),(0,50),(2,51),
            (5,53),(7,55),(8,57),(10,59),(12,58),(18,56),(21,55),(24,58),
            (24,60),(28,60),(30,62),(25,65),(20,70),(18,69),(14,67),(12,65),
            (5,60),(5,58),(0,55),(-2,52),(-5,50),(-8,48),(-10,44),(-10,36)],
 'asia': [(28,36),(30,40),(33,42),(35,44),(38,47),(40,50),(42,55),(45,60),
          (50,62),(55,66),(60,69),(68,70),(75,72),(85,74),(95,76),(105,77),
          (115,74),(125,72),(135,71),(145,71),(155,70),(165,69),(175,66),
          (178,65),(172,62),(165,60),(160,58),(158,52),(155,50),(150,59),
          (145,55),(142,50),(140,42),(138,36),(134,34),(130,32),(127,34),
          (124,38),(121,32),(118,28),(112,22),(108,15),(106,10),(103,2),
          (100,5),(97,12),(94,17),(91,22),(88,22),(84,19),(80,14),(77,8),
          (74,14),(71,20),(67,24),(62,25),(58,26),(54,27),(51,28),(49,30),
          (46,29),(43,24),(41,18),(39,21),(36,27),(34,28),(31,30),(29,31),
          (28,36)],
 'namerica': [(-168,66),(-165,60),(-158,58),(-152,60),(-145,60),(-140,60),
              (-135,58),(-130,55),(-126,50),(-124,44),(-121,38),(-118,34),
              (-114,30),(-110,26),(-106,24),(-102,20),(-97,17),(-94,17),
              (-91,15),(-87,13),(-84,12),(-81,9),(-79,9),(-80,12),(-82,18),
              (-84,24),(-81,26),(-80,30),(-78,34),(-75,37),(-72,41),
              (-70,43),(-66,45),(-64,47),(-60,47),(-56,50),(-55,52),
              (-58,55),(-62,58),(-66,60),(-70,62),(-75,62),(-80,64),
              (-85,66),(-92,66),(-100,68),(-110,68),(-120,69),(-130,69),
              (-140,70),(-150,70),(-160,70),(-168,66)],
 'samerica': [(-79,9),(-77,8),(-75,11),(-72,12),(-68,11),(-64,10),(-60,8),
              (-56,6),(-53,5),(-50,0),(-46,-2),(-42,-3),(-38,-5),(-35,-8),
              (-36,-12),(-38,-16),(-40,-21),(-44,-24),(-48,-27),(-52,-32),
              (-56,-35),(-58,-38),(-62,-41),(-66,-45),(-68,-50),(-69,-53),
              (-71,-54),(-73,-50),(-73,-44),(-73,-37),(-72,-30),(-71,-22),
              (-70,-18),(-74,-15),(-78,-10),(-80,-5),(-81,-1),(-80,3),
              (-79,7),(-79,9)],
 'australia': [(113,-22),(114,-28),(115,-33),(118,-35),(122,-34),(126,-32),
               (130,-32),(133,-33),(136,-35),(139,-37),(142,-38),(146,-39),
               (149,-37),(150,-35),(152,-32),(153,-28),(152,-25),(150,-22),
               (148,-20),(146,-19),(144,-15),(142,-11),(141,-13),(139,-17),
               (137,-12),(136,-15),(134,-12),(132,-11),(130,-13),(128,-14),
               (126,-14),(124,-16),(122,-17),(120,-20),(117,-20),(114,-21),
               (113,-22)],
 'greenland': [(-46,60),(-42,64),(-38,66),(-32,68),(-26,70),(-22,70),
               (-20,73),(-22,76),(-30,76),(-38,76),(-46,76),(-54,75),
               (-58,72),(-56,68),(-54,64),(-50,61),(-46,60)],
 'uk': [(-5,50),(-3,53),(-5,56),(-4,58),(-2,57),(0,54),(1,52),(0,51),
        (-2,50),(-5,50)],
 'japan': [(130,31),(132,33),(134,34),(136,35),(138,35),(139,37),(140,39),
           (141,41),(142,43),(143,44),(144,44),(142,42),(141,39),(139,36),
           (137,35),(135,34),(133,33),(131,32),(130,31)],
 'madagascar': [(44,-16),(46,-15),(49,-16),(50,-18),(49,-21),(47,-24),
                (45,-25),(44,-22),(43,-19),(44,-16)],
 'newzealand': [(167,-45),(169,-44),(171,-42),(173,-41),(175,-38),(177,-38),
                (175,-40),(173,-42),(171,-44),(169,-46),(167,-45)],
 'seasia': [(95,6),(97,9),(99,11),(101,13),(103,10),(104,8),(103,2),(105,0),
            (107,-2),(109,-4),(111,-6),(113,-8),(116,-9),(119,-9),(121,-10),
            (122,-8),(120,-5),(118,-2),(116,0),(113,2),(110,1),(107,0),
            (104,2),(101,4),(98,6),(95,6)],
 'borneo': [(109,1),(111,2),(114,4),(117,6),(119,5),(118,2),(117,-1),
            (115,-3),(112,-4),(110,-3),(109,0),(109,1)],
 'newguinea': [(131,-1),(134,-2),(137,-3),(140,-4),(143,-6),(146,-7),
               (148,-9),(150,-10),(147,-8),(144,-7),(141,-5),(138,-4),
               (135,-3),(132,-2),(131,-1)],
}

def _inside_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < xin:
                inside = not inside
    return inside

def ortho(lon, lat, lon0=55.0, lat0=20.0):
    """Orthographic projection. Returns (x, y, z) in unit-sphere coords."""
    la, lo = math.radians(lat), math.radians(lon)
    la0, lo0 = math.radians(lat0), math.radians(lon0)
    x = math.cos(la) * math.sin(lo - lo0)
    y = math.cos(la0) * math.sin(la) - math.sin(la0) * math.cos(la) * math.cos(lo - lo0)
    z = math.sin(la0) * math.sin(la) + math.cos(la0) * math.cos(la) * math.cos(lo - lo0)
    return x, y, z

def draw_globe(cv, cx, cy, r):
    cv.fill_circle(cx, cy, r, TEAL_DK)
    cv.ring(cx, cy, r, GOLD, 3)
    seen = set()
    for poly in CONTINENTS.values():
        lons = [p[0] for p in poly]; lats = [p[1] for p in poly]
        lat = math.floor(min(lats) / 3) * 3
        while lat <= max(lats):
            # keep projected dot spacing even: widen lon step near poles
            lon_step = max(3.0, 3.0 / max(0.25, math.cos(math.radians(lat))))
            lon = math.floor(min(lons) / 3) * 3
            while lon <= max(lons):
                if _inside_poly(lon + 1.5, lat + 1.5, poly):
                    x, y, z = ortho(lon + 1.5, lat + 1.5)
                    if z > 0.03:
                        sx = cx + int(round(x * r))
                        sy = cy - int(round(y * r))
                        cell = (sx // 8, sy // 8)
                        if cell not in seen:
                            seen.add(cell)
                            cv.fill_circle(sx, sy, 3, GOLD)
                lon += lon_step
            lat += 3

def draw_pin(cv, cx, cy, r, num, lon, lat):
    x, y, z = ortho(lon, lat)
    if z <= 0.03:
        return None
    sx = cx + int(round(x * r))
    sy = cy - int(round(y * r))
    cv.fill_circle(sx, sy, 10, RED)
    cv.ring(sx, sy, 10, WHITE, 2)
    s = str(num)
    tw = text_width(s, 1.6, 0)
    draw_text(cv, sx - tw / 2, sy - 6, s, 1.6, WHITE, 1.3)
    return (sx, sy)

# ------------------------------------------------------------------- icons --
def icon_chart(cv, x, y, s, c):
    # axes + falling line + arrowhead
    cv.line(x, y + 34 * s, x + 40 * s, y + 34 * s, c, 2)
    cv.line(x, y, x, y + 34 * s, c, 2)
    pts = [(x + 4 * s, y + 8 * s), (x + 14 * s, y + 14 * s), (x + 22 * s, y + 12 * s),
           (x + 30 * s, y + 22 * s), (x + 38 * s, y + 28 * s)]
    cv.polyline(pts, RED_LT, 3)
    cv.fill_poly([(x + 38 * s, y + 28 * s), (x + 32 * s, y + 26 * s),
                  (x + 37 * s, y + 21 * s)], RED_LT)

def icon_cricket(cv, x, y, s, c):
    # stumps + bat + ball
    for k in range(3):
        cv.line(x + (6 + k * 6) * s, y + 6 * s, x + (6 + k * 6) * s, y + 26 * s, GOLD, 2)
    cv.line(x + 4 * s, y + 4 * s, x + 20 * s, y + 4 * s, GOLD, 2)
    cv.fill_poly([(x + 26 * s, y + 34 * s), (x + 30 * s, y + 34 * s),
                  (x + 36 * s, y + 12 * s), (x + 32 * s, y + 10 * s)], c)
    cv.fill_circle(x + 34 * s, y + 6 * s, 4, RED_LT)

def icon_rocket(cv, x, y, s, c):
    cv.fill_poly([(x + 20 * s, y + 2 * s), (x + 28 * s, y + 16 * s),
                  (x + 24 * s, y + 28 * s), (x + 16 * s, y + 28 * s),
                  (x + 12 * s, y + 16 * s)], c)
    cv.fill_circle(x + 20 * s, y + 14 * s, 3, NAVY)
    cv.fill_poly([(x + 12 * s, y + 24 * s), (x + 8 * s, y + 32 * s),
                  (x + 15 * s, y + 28 * s)], RED_LT)
    cv.fill_poly([(x + 28 * s, y + 24 * s), (x + 32 * s, y + 32 * s),
                  (x + 25 * s, y + 28 * s)], RED_LT)
    cv.fill_poly([(x + 17 * s, y + 28 * s), (x + 23 * s, y + 28 * s),
                  (x + 20 * s, y + 38 * s)], ORANGE)

def icon_flags(cv, x, y, s, c):
    cv.line(x + 8 * s, y + 4 * s, x + 8 * s, y + 34 * s, c, 2)
    cv.line(x + 30 * s, y + 4 * s, x + 30 * s, y + 34 * s, c, 2)
    cv.fill_poly([(x + 8 * s, y + 4 * s), (x + 26 * s, y + 8 * s),
                  (x + 8 * s, y + 14 * s)], BLUE_EU)
    cv.fill_poly([(x + 30 * s, y + 4 * s), (x + 12 * s, y + 8 * s),
                  (x + 30 * s, y + 14 * s)], RED)
    cv.fill_circle(x + 14 * s, y + 9 * s, 1, GOLD)
    cv.fill_circle(x + 18 * s, y + 9 * s, 1, GOLD)

def icon_megaphone(cv, x, y, s, c):
    cv.fill_poly([(x + 6 * s, y + 16 * s), (x + 26 * s, y + 6 * s),
                  (x + 26 * s, y + 28 * s), (x + 6 * s, y + 20 * s)], c)
    cv.fill_poly([(x + 26 * s, y + 6 * s), (x + 32 * s, y + 2 * s),
                  (x + 32 * s, y + 32 * s), (x + 26 * s, y + 28 * s)], RED_LT)
    cv.line(x + 10 * s, y + 20 * s, x + 14 * s, y + 32 * s, c, 3)
    cv.line(x + 34 * s, y + 8 * s, x + 38 * s, y + 6 * s, GOLD, 2)
    cv.line(x + 34 * s, y + 26 * s, x + 38 * s, y + 28 * s, GOLD, 2)

def icon_boat(cv, x, y, s, c):
    cv.fill_poly([(x + 4 * s, y + 22 * s), (x + 36 * s, y + 22 * s),
                  (x + 30 * s, y + 32 * s), (x + 10 * s, y + 32 * s)], c)
    cv.line(x + 20 * s, y + 6 * s, x + 20 * s, y + 22 * s, c, 2)
    cv.fill_poly([(x + 20 * s, y + 6 * s), (x + 20 * s, y + 20 * s),
                  (x + 32 * s, y + 20 * s)], GOLD)
    cv.line(x + 2 * s, y + 36 * s, x + 12 * s, y + 36 * s, TEAL_LT, 2)
    cv.line(x + 16 * s, y + 38 * s, x + 30 * s, y + 38 * s, TEAL_LT, 2)

def icon_cyclone(cv, x, y, s, c):
    cx, cy = x + 18 * s, y + 18 * s
    for k, (r0, r1, a0, a1) in enumerate([(4, 10, 0.0, 4.2), (10, 15, 0.6, 4.8),
                                         (15, 18, 1.2, 5.2)]):
        pts = []
        for i in range(21):
            t = i / 20
            a = a0 + (a1 - a0) * t
            r = (r0 + (r1 - r0) * t) * s
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        cv.polyline(pts, c if k != 2 else TEAL_LT, 2.5)
    cv.fill_circle(cx, cy, 3, GOLD)

def icon_missile(cv, x, y, s, c):
    for k, (x0, y0, x1, y1) in enumerate(((2, 2, 30, 16), (6, 14, 34, 26), (2, 26, 28, 34))):
        cv.line(x + x0 * s, y + y0 * s, x + x1 * s, y + y1 * s, ORANGE, 2.5)
        cv.fill_circle(x + x1 * s, y + y1 * s, 3, GOLD_LT)
        cv.fill_circle(x + x0 * s, y + y0 * s, 1.5, ORANGE)
    cv.fill_rect(x + 2 * s, y + 32 * s, x + 14 * s, y + 38 * s, NAVY3)
    cv.fill_rect(x + 16 * s, y + 28 * s, x + 26 * s, y + 38 * s, NAVY3)
    cv.fill_rect(x + 28 * s, y + 34 * s, x + 38 * s, y + 38 * s, NAVY3)

def icon_sun(cv, x, y, s, c):
    cx, cy = x + 18 * s, y + 18 * s
    cv.fill_circle(cx, cy, 11 * s, GOLD)
    for k in range(8):
        a = math.pi * k / 4
        cv.line(cx + 14 * s * math.cos(a), cy + 14 * s * math.sin(a),
                cx + 19 * s * math.cos(a), cy + 19 * s * math.sin(a), GOLD, 2.5)

# -------------------------------------------------------------------- data --
HERO = [
 ("1", "ODISHA - STORM", "Cyclone Akvan comes ashore in India",
  "Severe storm crosses the coast near Gopalpur on Friday morning; 300,000+ "
  "evacuated, 423 rescue teams out, schools shut. (IMD, The Hindu)"),
 ("2", "KYIV - WAR", "Missiles rain on Kyiv overnight",
  "Waves of missiles after midnight damage three Dnipro bridges; fires burn "
  "in districts. Putin vowed a 'painful' reply. (UNN)"),
 ("3", "ANTALYA - CLIMATE", "COP31 ends its last day without a deal",
  "Final draft drops all fossil-fuel wording and the $120bn figure; hosts "
  "push a '35 by 35' goal. Text due by midnight. (Reuters)"),
]

NUMBERS = [
 ("300,000", "EVACUATED AHEAD OF AKVAN"),
 ("~30", "BALLISTIC MISSILES AT KYIV"),
 ("-7%", "ASIA'S WORST WEEK SINCE 2020"),
 ("118", "PHILLIPS' HISTORIC CENTURY"),
 ("9,341", "SHELTERS OPEN IN ODISHA"),
 ("2.2%", "JAPAN CORE INFLATION"),
]

RAIL = [
 ("4", "SEOUL / TOKYO - MARKETS", "Asia's markets sink as the AI trade unwinds",
  "Nikkei -4.5%, KOSPI -4.7%, SoftBank -16%; Dow down 1,101. (Reuters)", "chart"),
 ("5", "WELLINGTON - CRICKET", "Phillips makes history with 118",
  "First batter ever with Test, ODI and T20I tons vs India in one year. (Reuters)", "cricket"),
 ("6", "SPACE", "BepiColombo counts down to Mercury",
  "ESA-JAXA probe ends its 8-year trip; orbit insertion set for Saturday. (ESA)", "rocket"),
 ("7", "BRUSSELS - EUROPE", "Burnham's first EU-UK reset summit",
  "Costa and von der Leyen host the new UK prime minister. (EU Council)", "flags"),
 ("8", "ROME - LABOUR", "Italy's CGIL holds a 24-hour strike",
  "Unions march in 100 squares against the 2027 budget; transport hit. (AFP)", "megaphone"),
 ("9", "SENEGAL - MIGRATION", "Migrant boat capsizes off Senegal",
  "Four bodies recovered from a boat carrying 50-100 people. (Al Jazeera)", "boat"),
]

ALSO_ON = [
 "10 TOKYO - Japan core inflation up 2.2%",
 "11 BEIJING - China holds lending rates, 18th month",
 "12 SAN SALVADOR - Bukele files for a third term",
 "13 BARCELONA - Cancer pill shrinks tumours 60.7%",
 "14 FLORIDA - St Johns River hits record 18.3 ft",
 "15 IOWA - Army to blow up 68 barrels at noon",
 "16 SEOUL - Ruling party moves to impeach top judge",
 "17 BRASILIA - Lula visits Raoni; land recognised",
 "18 COPENHAGEN - Denmark approves Greenland bill",
 "19 JAKARTA - Indonesia passes asset-seizure bill",
 "20 HORMUZ - Four attacks on vessels in 96 hours",
 "21 DOHA - U17 World Cup: Australia stun Argentina",
 "22 TURIN - ATP Finals groups close in Turin",
 "23 TONGA - Drought emergency as El Nino bites",
 "24 WASHINGTON - US war cost vs Iran: $48.3bn",
 "25 NEW YORK - GTA VI day one: 1.7m copies, $1.65bn",
 "26 SHENZHEN - Trump heads home after the summit",
 "27 GLOBAL - UN marks World Children's Day",
]

DATE_CHECK = ("First reported Thu 19 Nov, NOT Friday's news: the Trump-Xi-Putin "
 "summit itself - Anthropic's $83 IPO debut - the ICJ Rohingya verdict - the "
 "Kyiv embassy strikes - GTA VI midnight launch - the $190.4m Van Gogh sale - "
 "Voyager 1 one light-day (18 Nov) - the Senate 48-51 Iran vote - the "
 "US-Venezuela deal - Fiji drought declaration - Han Duck-soo acquittal - the "
 "Crimea bridge attack - the Houthi strike on Riyadh's PIF tower.")

PINS = [(1, 85, 20), (2, 30.5, 50.5), (3, 33, 37), (4, 133, 36),
        (7, 2, 52), (8, 14, 42), (9, -17.4, 14.7)]

ICONS = {"chart": icon_chart, "cricket": icon_cricket, "rocket": icon_rocket,
         "flags": icon_flags, "megaphone": icon_megaphone, "boat": icon_boat}

# ------------------------------------------------------------------ layout --
def _all_strings():
    out = ["Friday 20 November 2026"]
    for h in HERO:
        out += list(h[1:])
    for n in NUMBERS:
        out += list(n)
    for r in RAIL:
        out += list(r[1:4])
    out += ALSO_ON
    out.append(DATE_CHECK)
    return out

def draw_header(cv):
    draw_text(cv, 28, 16, "THE WORLD IN ONE DAY  |  27 STORIES  |  6 CONTINENTS",
              1.7, GOLD, 1.1, tracking=1.2)
    right = "FRIDAY'S NEWS - ONE PAGE"
    draw_text(cv, 1024 - 28 - text_width(right, 1.5, 0.8), 18, right,
              1.5, GREY, 1.0, tracking=0.8)
    title = "Friday 20 November 2026"
    sc = min(6.8, 968.0 / text_width(title, 1.0, 0))
    draw_text(cv, 28, 40, title, sc, CREAM, 1.25)
    cv.fill_rect(28, 102, 996, 104, GOLD)
    draw_text(cv, 28, 110,
              "One day of world news - a storm, missiles, a climate deadline, a market rout.",
              2.0, CREAM_DIM, 1.0)

def draw_hero_card(cv, x, y, w, h, num, kicker, headline, summary):
    cv.fill_rect(x, y, x + w, y + h, NAVY2)
    cv.fill_rect(x, y, x + 5, y + h, GOLD)
    cv.fill_circle(x + 30, y + 26, 16, GOLD)
    tw = text_width(num, 2.2, 0)
    draw_text(cv, x + 30 - tw / 2, y + 15, num, 2.2, NAVY, 1.3)
    draw_text(cv, x + 54, y + 18, kicker, 1.6, GOLD, 1.1, tracking=0.6)
    lines = wrap_text(headline, 2.9, w - 32)[:2]
    yy = y + 42
    for ln in lines:
        draw_text(cv, x + 16, yy, ln, 2.9, CREAM, 1.25)
        yy += 22
    max_sum = max(1, int((y + h - 6 - (yy + 2)) // 13.5))
    slines = wrap_text(summary, 1.65, w - 32)[:max_sum]
    for ln in slines:
        draw_text(cv, x + 16, yy + 2, ln, 1.65, CREAM_DIM, 1.0)
        yy += 13.5

def draw_hero(cv):
    gx, gy, gr = 300, 344, 160
    cv.ellipse(gx, gy, 222, 210, (96, 110, 128), 2)
    draw_globe(cv, gx, gy, gr)
    for num, lon, lat in PINS:
        draw_pin(cv, gx, gy, gr, num, lon, lat)
    # orbiting vignettes
    icon_cyclone(cv, 428, 232, 1.5, CREAM)
    draw_text(cv, 424, 302, "AKVAN", 1.6, GOLD, 1.1, tracking=0.8)
    icon_missile(cv, 96, 128, 1.0, ORANGE)
    draw_text(cv, 100, 176, "KYIV", 1.6, GOLD, 1.1, tracking=0.8)
    icon_sun(cv, 420, 452, 1.2, GOLD)
    draw_text(cv, 420, 506, "COP31", 1.6, GOLD, 1.1, tracking=0.8)
    draw_para(cv, 140, 518,
              "Pins mark stories 1-4 and 7-9. Wellington and Mercury lie beyond "
              "this side of the globe.", 1.35, GREY, 340, 11)
    ys = [132, 278, 424]
    for (num, kicker, headline, summary), y in zip(HERO, ys):
        draw_hero_card(cv, 540, y, 456, 136, num, kicker, headline, summary)

def draw_numbers(cv):
    y0, y1 = 568, 628
    cv.fill_rect(28, y0, 996, y0 + 1, NAVY3)
    cv.fill_rect(28, y1, 996, y1 + 1, NAVY3)
    cw = 968 / 6
    for i, (val, lab) in enumerate(NUMBERS):
        cx = 28 + cw * i + cw / 2
        tw = text_width(val, 3.2, 0)
        draw_text(cv, cx - tw / 2, y0 + 6, val, 3.2, GOLD, 1.2)
        for j, ln in enumerate(wrap_text(lab, 1.25, cw - 16)):
            lw_ = text_width(ln, 1.25, 0)
            draw_text(cv, cx - lw_ / 2, y0 + 35 + j * 11, ln, 1.25, CREAM_DIM, 1.0)
        if i:
            cv.fill_rect(28 + cw * i, y0 + 6, 28 + cw * i + 1, y1 - 6, NAVY3)

def draw_rail(cv):
    xs = [28, 352, 676]
    ys = [636, 730]
    for idx, (num, kicker, headline, summary, icon) in enumerate(RAIL):
        x, y = xs[idx % 3], ys[idx // 3]
        cv.fill_rect(x, y, x + 316, y + 88, NAVY2)
        ICONS[icon](cv, x + 10, y + 8, 1.0, CREAM)
        draw_text(cv, x + 58, y + 12, kicker, 1.4, GOLD, 1.1, tracking=0.4)
        lines = wrap_text(headline, 1.9, 248)[:2]
        yy = y + 28
        for ln in lines:
            draw_text(cv, x + 58, yy, ln, 1.9, CREAM, 1.2)
            yy += 15
        max_sum = max(1, int((y + 88 - 4 - (yy + 4)) // 11))
        for ln in wrap_text(summary, 1.4, 296)[:max_sum]:
            draw_text(cv, x + 10, yy + 4, ln, 1.4, CREAM_DIM, 1.0)
            yy += 11

def draw_also_on(cv):
    draw_text(cv, 28, 824, "ALSO ON FRIDAY 20 NOVEMBER", 1.7, RED_LT, 1.2, tracking=0.6)
    draw_text(cv, 28 + text_width("ALSO ON FRIDAY 20 NOVEMBER", 1.7, 0.6) + 12,
              824, "- 18 MORE STORIES", 1.7, GREY, 1.0, tracking=0.6)
    xs = [28, 352, 676]
    for i, item in enumerate(ALSO_ON):
        col, row = i // 6, i % 6
        draw_text(cv, xs[col], 842 + row * 12, item, 1.25, CREAM_DIM, 1.0)

def draw_date_check(cv):
    cv.fill_rect(28, 922, 996, 984, (16, 34, 56))
    cv.rect(28, 922, 996, 984, RED, 2)
    draw_text(cv, 40, 930, "DATE CHECK - LEFT OUT", 1.7, RED_LT, 1.25, tracking=0.6)
    draw_para(cv, 40, 948, DATE_CHECK, 1.45, CREAM, 944, 13)

def draw_footer(cv):
    draw_text(cv, 28, 992,
              "Every story here happened, or was first reported, on Friday 20 November 2026.",
              1.3, GREY, 1.0)
    draw_text(cv, 28, 1004,
              "Sources: Reuters, AP, AFP, BBC, IMD, The Hindu, UN News, ESA, ICC. Original drawings.",
              1.3, GREY, 1.0)

def build():
    for s in _all_strings():
        assert s.isascii(), "non-ASCII text: %r" % s
    cv = Canvas(W, H, NAVY)
    cv.rect(6, 6, 1018, 1018, NAVY3, 2)
    draw_header(cv)
    draw_hero(cv)
    draw_numbers(cv)
    draw_rail(cv)
    draw_also_on(cv)
    draw_date_check(cv)
    draw_footer(cv)
    return cv

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, cv)
    import hashlib
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s (%d bytes) sha256=%s" % (path, size, sha))

if __name__ == "__main__":
    main()
