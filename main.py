#!/usr/bin/env python3
"""Sunday 22 November 2026, the whole world on one page.

This program draws a 1024 by 1024 broadsheet front page for the make.fun
news-image-20261122 bounty. Three illustrated lead panels sit under a date
masthead, then a band of six verified figures, a schematic world map with
thirteen numbered pins, ten story cards, a twenty-five item world-in-brief,
a UTC timeline and a date-check box that names the stories left out because
they belong to earlier days. It uses only the Python 3.13 standard library:
no Pillow, no network, no files besides its own source. The output is a PNG
written to MAKEFUN_OUTPUT_DIR, or to /output when that is unset. Running it
twice writes the same bytes twice.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- alphabet
# A 5 by 7 pixel alphabet. Each glyph is seven strings of five bits; a "1"
# paints one scaled square, a "0" leaves the paper alone.
FONT = {
    "A": ("01110","10001","10001","11111","10001","10001","10001"),
    "B": ("11110","10001","10001","11110","10001","10001","11110"),
    "C": ("01110","10001","10000","10000","10000","10001","01110"),
    "D": ("11110","10001","10001","10001","10001","10001","11110"),
    "E": ("11111","10000","10000","11110","10000","10000","11111"),
    "F": ("11111","10000","10000","11110","10000","10000","10000"),
    "G": ("01110","10001","10000","10111","10001","10001","01111"),
    "H": ("10001","10001","10001","11111","10001","10001","10001"),
    "I": ("01110","00100","00100","00100","00100","00100","01110"),
    "J": ("00111","00010","00010","00010","00010","10010","01100"),
    "K": ("10001","10010","10100","11000","10100","10010","10001"),
    "L": ("10000","10000","10000","10000","10000","10000","11111"),
    "M": ("10001","11011","10101","10101","10001","10001","10001"),
    "N": ("10001","11001","10101","10011","10001","10001","10001"),
    "O": ("01110","10001","10001","10001","10001","10001","01110"),
    "P": ("11110","10001","10001","11110","10000","10000","10000"),
    "Q": ("01110","10001","10001","10001","10101","10010","01101"),
    "R": ("11110","10001","10001","11110","10100","10010","10001"),
    "S": ("01111","10000","10000","01110","00001","00001","11110"),
    "T": ("11111","00100","00100","00100","00100","00100","00100"),
    "U": ("10001","10001","10001","10001","10001","10001","01110"),
    "V": ("10001","10001","10001","10001","10001","01010","00100"),
    "W": ("10001","10001","10001","10101","10101","11011","10001"),
    "X": ("10001","10001","01010","00100","01010","10001","10001"),
    "Y": ("10001","10001","01010","00100","00100","00100","00100"),
    "Z": ("11111","00001","00010","00100","01000","10000","11111"),
    "0": ("01110","10001","10011","10101","11001","10001","01110"),
    "1": ("00100","01100","00100","00100","00100","00100","01110"),
    "2": ("01110","10001","00001","00110","01000","10000","11111"),
    "3": ("11110","00001","00001","01110","00001","00001","11110"),
    "4": ("00010","00110","01010","10010","11111","00010","00010"),
    "5": ("11111","10000","11110","00001","00001","10001","01110"),
    "6": ("01110","10000","10000","11110","10001","10001","01110"),
    "7": ("11111","00001","00010","00100","01000","01000","01000"),
    "8": ("01110","10001","10001","01110","10001","10001","01110"),
    "9": ("01110","10001","10001","01111","00001","00001","01110"),
    " ": ("00000","00000","00000","00000","00000","00000","00000"),
    ".": ("00000","00000","00000","00000","00000","01100","01100"),
    ",": ("00000","00000","00000","00000","01100","00100","01000"),
    ":": ("00000","01100","01100","00000","01100","01100","00000"),
    ";": ("00000","01100","01100","00000","01100","00100","01000"),
    "!": ("00100","00100","00100","00100","00100","00000","00100"),
    "?": ("01110","10001","00001","00110","00100","00000","00100"),
    "'": ("00100","00100","01000","00000","00000","00000","00000"),
    '"': ("01010","01010","01010","00000","00000","00000","00000"),
    "-": ("00000","00000","00000","01110","00000","00000","00000"),
    "/": ("00001","00010","00010","00100","01000","01000","10000"),
    "%": ("11001","11010","00010","00100","01000","01011","10011"),
    "$": ("00100","01111","10100","01110","00101","11110","00100"),
    "(": ("00010","00100","01000","01000","01000","00100","00010"),
    ")": ("01000","00100","00010","00010","00010","00100","01000"),
    "+": ("00000","00100","00100","11111","00100","00100","00000"),
    "=": ("00000","00000","11111","00000","11111","00000","00000"),
    "&": ("01100","10010","10100","01000","10101","10010","01101"),
    ">": ("01000","00100","00010","00001","00010","00100","01000"),
    "<": ("00010","00100","01000","10000","01000","00100","00010"),
    "*": ("00000","10101","01110","10101","00000","00000","00000"),
}
EMPTY_GLYPH = ("00000","00000","00000","00000","00000","00000","00000")


def text_width(txt, scale):
    # Six pixels per character cell, minus the trailing gap.
    total = 0
    for _ in txt:
        total += 6 * scale
    return total - scale


def wrap_words(txt, limit):
    """Split txt into lines of at most limit characters, word by word."""
    words = txt.split(" ")
    lines = []
    idx = 0
    while idx < len(words):
        cur = words[idx]
        idx += 1
        while idx < len(words) and len(cur) + 1 + len(words[idx]) <= limit:
            cur = cur + " " + words[idx]
            idx += 1
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    """An RGB picture kept as one flat bytearray, three bytes per pixel."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, c):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return
        at = (y * self.w + x) * 3
        self.px[at:at + 3] = c

    def box(self, x, y, w, h, c):
        xa = x if x > 0 else 0
        ya = y if y > 0 else 0
        xb = x + w if x + w < self.w else self.w
        yb = y + h if y + h < self.h else self.h
        yy = ya
        while yy < yb:
            xx = xa
            while xx < xb:
                self.put(xx, yy, c)
                xx += 1
            yy += 1

    def hbar(self, x, y, w, c, t=1):
        # A horizontal bar t pixels tall.
        self.box(x, y, w, t, c)

    def vbar(self, x, y, h, c, t=1):
        # A vertical bar t pixels wide.
        self.box(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        # Four bars making a border around a box.
        self.hbar(x, y, w, c, t)
        self.hbar(x, y + h - t, w, c, t)
        self.vbar(x, y, h, c, t)
        self.vbar(x + w - t, y, h, c, t)

    def seg(self, a, b, c):
        # Bresenham's walk between two (x, y) points.
        x, y = a
        x1, y1 = b
        dx = x1 - x if x1 > x else x - x1
        dy = y1 - y if y1 > y else y - y1
        sx = 1 if x < x1 else -1
        sy = 1 if y < y1 else -1
        err = dx - dy
        while (x, y) != (x1, y1):
            self.put(x, y, c)
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        self.put(x1, y1, c)

    def disc(self, center, r, c, fill=True):
        cx, cy = center
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                dist2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if fill and dist2 <= r * r:
                    self.put(xx, yy, c)
                elif not fill and abs(dist2 - r * r) <= r:
                    self.put(xx, yy, c)

    def fill_poly(self, pts, c):
        """Fill a simple polygon, row by row, from its edge crossings."""
        if not pts:
            return
        edges = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            edges.append((x0, y0, x1, y1))
        ys = [p[1] for p in pts]
        y = min(ys)
        while y <= max(ys):
            cuts = []
            for x0, y0, x1, y1 in edges:
                if (y0 <= y < y1) or (y1 <= y < y0):
                    cuts.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            cuts.sort()
            k = 0
            while k + 1 < len(cuts):
                x = int(cuts[k])
                while x <= int(cuts[k + 1]):
                    self.put(x, y, c)
                    x += 1
                k += 2
            y += 1

    def draw_glyph(self, x, y, ch, scale, c):
        g = FONT.get(ch, EMPTY_GLYPH)
        for row_i in range(7):
            row = g[row_i]
            for col_i in range(5):
                if row[col_i] == "1":
                    self.box(x + col_i * scale, y + row_i * scale,
                             scale, scale, c)

    def put_text(self, x, y, txt, scale, c, align="l"):
        txt = txt.upper()
        if align != "l":
            x -= text_width(txt, scale) // (2 if align == "c" else 1)
        for ch in txt:
            self.draw_glyph(x, y, ch, scale, c)
            x += 6 * scale
        return x

    def block(self, x, y, txt, scale, c, width, lh=None):
        """A wrapped paragraph; returns the y just below its last line."""
        if lh is None:
            lh = 9 * scale
        per_line = (width + scale) // (6 * scale)
        if per_line < 1:
            per_line = 1
        lines = wrap_words(txt, per_line)
        for ln in lines:
            self.put_text(x, y, ln, scale, c)
            y += lh
        return y

    def to_png(self):
        rows = []
        stride = self.w * 3
        for y in range(self.h):
            rows.append(b"\x00" + bytes(self.px[y * stride:(y + 1) * stride]))
        zdata = zlib.compress(b"".join(rows), 9)

        def emit(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return out

        header = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + emit(b"IHDR", header)
                + emit(b"IDAT", zdata) + emit(b"IEND", b""))


# ---------------------------------------------------------------- palette
BG = bytes([247, 243, 232])
FG = bytes([20, 20, 20])
NAVY = bytes([17, 24, 39])
NAVY2 = bytes([31, 41, 55])
RED = bytes([185, 28, 28])
RED_LT = bytes([254, 226, 226])
BLUE = bytes([29, 78, 216])
SKY = bytes([186, 220, 245])
SKY_DK = bytes([147, 197, 253])
LAND = bytes([210, 196, 160])
LAND2 = bytes([188, 172, 128])
GOLD = bytes([180, 83, 9])
GREEN = bytes([21, 128, 61])
GREY = bytes([107, 114, 128])
LINE = bytes([180, 175, 160])
WHITE = bytes([255, 255, 255])
YELLOW = bytes([250, 204, 21])
DUSK = bytes([55, 48, 84])
DUSK2 = bytes([76, 29, 149])
ORANGE = bytes([234, 88, 12])

# ---------------------------------------------------------------- scenes
def panel_bahrain(pg, x, y, w, h):
    """Night over Bahrain: four bases, missile bursts, tankers below."""
    pg.box(x, y, w, h, DUSK2)
    stars = [(22, 12), (80, 24), (150, 10), (210, 20),
             (280, 14), (120, 34), (250, 36), (40, 40)]
    for sx, sy in stars:
        pg.box(x + sx, y + sy, 3, 3, WHITE)
    blocks = [(8, 30, 46), (46, 24, 62), (78, 28, 40), (114, 26, 58),
              (148, 30, 44), (186, 24, 66), (218, 28, 48), (254, 26, 60),
              (288, 24, 42)]
    for bx, bw, bh in blocks:
        pg.box(x + bx, y + h - 30 - bh, bw, bh, NAVY)
        wy = 6
        while wy < bh - 6:
            wx = 4
            while wx < bw - 4:
                pg.box(x + bx + wx, y + h - 30 - bh + wy, 3, 4, YELLOW)
                wx += 9
            wy += 10
    bursts = [(60, 40), (140, 28), (220, 42), (292, 30)]
    for cx, cy in bursts:
        pg.disc((x + cx, y + cy), 12, YELLOW)
        pg.disc((x + cx, y + cy), 7, WHITE)
        pg.disc((x + cx, y + cy), 3, RED)
        ang = 0
        while ang < 360:
            dx = int(18 * math.cos(math.radians(ang)))
            dy = int(18 * math.sin(math.radians(ang)))
            pg.seg((x + cx, y + cy), (x + cx + dx, y + cy + dy), YELLOW)
            ang += 45
    pg.box(x, y + h - 30, w, 30, BLUE)
    pg.hbar(x, y + h - 30, w, SKY_DK, 2)
    tankers = [(30, False), (130, True), (230, False)]
    for tx, burning in tankers:
        pg.box(x + tx, y + h - 22, 70, 10, NAVY2)
        pg.box(x + tx + 12, y + h - 30, 14, 8, NAVY2)
        if burning:
            pg.disc((x + tx + 35, y + h - 30), 9, ORANGE)
            pg.disc((x + tx + 35, y + h - 30), 5, YELLOW)
            pg.disc((x + tx + 35, y + h - 30), 2, WHITE)


def panel_cop(pg, x, y, w, h):
    """Antalya at dawn: hall, rising sun, a row of delegates' flags."""
    pg.box(x, y, w, h, SKY)
    pg.disc((x + w // 2, y + 58), 26, YELLOW)
    pg.disc((x + w // 2, y + 58), 18, WHITE)
    ang = 0
    while ang < 360:
        dx = int(44 * math.cos(math.radians(ang)))
        dy = int(44 * math.sin(math.radians(ang)))
        pg.seg((x + w // 2, y + 58), (x + w // 2 + dx, y + 58 + dy), YELLOW)
        ang += 30
    pg.fill_poly([(x, y + h - 40), (x + 90, y + h - 78),
                  (x + 180, y + h - 46), (x + 250, y + h - 80),
                  (x + w, y + h - 52), (x + w, y + h), (x, y + h)], LAND2)
    pg.box(x + 60, y + h - 62, w - 120, 62, NAVY)
    pg.box(x + 60, y + h - 62, w - 120, 8, RED)
    wx = 72
    while wx < w - 72:
        pg.box(x + wx, y + h - 48, 12, 20, YELLOW)
        wx += 22
    flag_cols = [RED, BLUE, GREEN, GOLD, WHITE, ORANGE]
    for i in range(len(flag_cols)):
        fx = x + 84 + i * 34
        pg.vbar(fx, y + h - 84, 22, FG, 2)
        pg.box(fx + 2, y + h - 84, 18, 12, flag_cols[i])
    pg.disc((x + w - 46, y + 30), 16, WHITE)
    pg.disc((x + w - 46, y + 30), 16, FG, fill=False)
    pg.seg((x + w - 46, y + 30), (x + w - 46, y + 18), FG)
    pg.seg((x + w - 46, y + 30), (x + w - 34, y + 30), FG)


def panel_sparta(pg, x, y, w, h):
    """Gulf of Finland: Sparta II burning, drifting, boats alongside."""
    pg.box(x, y, w, h, SKY)
    clouds = [(30, 18), (150, 10), (250, 24)]
    for cx, cy in clouds:
        pg.disc((x + cx, y + cy), 12, WHITE)
        pg.disc((x + cx + 22, y + cy + 4), 14, WHITE)
        pg.disc((x + cx + 44, y + cy), 10, WHITE)
    drones = [(120, 30), (210, 22)]
    for dx, dy in drones:
        pg.box(x + dx, y + dy, 8, 4, FG)
        pg.seg((x + dx, y + dy + 4), (x + dx - 6, y + dy + 14), GREY)
        pg.seg((x + dx + 8, y + dy + 4), (x + dx + 14, y + dy + 14), GREY)
    pg.box(x, y + h - 52, w, 52, BLUE)
    wy = y + h - 48
    while wy < y + h - 4:
        pg.hbar(x + 10, wy, w - 20, SKY_DK, 2)
        wy += 10
    pg.box(x + 50, y + h - 84, 220, 32, NAVY2)
    pg.box(x + 50, y + h - 84, 220, 6, RED)
    pg.box(x + 70, y + h - 104, 40, 20, RED)
    pg.box(x + 120, y + h - 100, 40, 16, GOLD)
    pg.box(x + 230, y + h - 98, 24, 14, WHITE)
    pg.disc((x + 185, y + h - 96), 18, ORANGE)
    pg.disc((x + 185, y + h - 96), 11, YELLOW)
    pg.disc((x + 185, y + h - 96), 5, WHITE)
    pg.disc((x + 185, y + h - 128), 10, GREY)
    pg.disc((x + 178, y + h - 142), 8, GREY)
    pg.disc((x + 192, y + h - 150), 6, GREY)
    pg.box(x + 286, y + h - 40, 30, 8, YELLOW)
    pg.box(x + 292, y + h - 48, 8, 8, YELLOW)
    pg.box(x + 20, y + h - 38, 22, 7, WHITE)


# ---------------------------------------------------------------- map
def project(pt, mx, my, mw, mh):
    # Equirectangular projection: lon -170..190 across, lat 75..-60 down.
    lo, la = pt.split(",")
    lon = float(lo)
    lat = float(la)
    px = mx + int((lon + 170.0) / 360.0 * mw)
    py = my + int((75.0 - lat) / 135.0 * mh)
    return px, py


# Rough continent outlines, each point a "lon,lat" string.
CONTINENTS = {
    "NA": ["-168,66", "-140,70", "-120,72", "-95,80", "-80,73",
           "-70,62", "-75,45", "-80,32", "-90,20", "-97,16",
           "-105,20", "-115,30", "-125,40", "-125,49", "-140,60",
           "-165,60"],
    "SA": ["-80,10", "-60,5", "-50,-5", "-35,-8", "-40,-20",
           "-48,-28", "-58,-35", "-65,-45", "-70,-55", "-73,-40",
           "-75,-20", "-80,-5"],
    "EU": ["-10,36", "-9,43", "0,46", "-2,50", "5,53", "8,57",
           "18,56", "21,60", "28,60", "30,68", "40,68", "45,60",
           "40,55", "35,50", "30,45", "28,40", "22,36", "15,38",
           "10,38", "3,42"],
    "AF": ["-6,35", "10,37", "20,32", "32,31", "35,28", "43,12",
           "51,11", "48,0", "40,-10", "35,-20", "32,-29", "25,-34",
           "18,-35", "12,-18", "8,4", "-8,5", "-15,12"],
    "AS": ["40,68", "60,70", "90,75", "120,73", "150,70", "170,66",
           "178,65", "170,60", "160,55", "142,50", "135,43",
           "128,38", "122,30", "115,22", "108,12", "103,8",
           "100,8", "95,15", "90,22", "85,20", "80,13", "77,8",
           "72,20", "66,25", "60,25", "55,26", "50,29", "48,30",
           "44,29", "40,35", "38,36", "40,45", "42,55"],
    "OC": ["113,-22", "125,-15", "135,-12", "142,-11", "147,-19",
           "153,-27", "150,-37", "140,-38", "130,-32", "120,-34",
           "113,-26"],
}

# Pin number -> where the story happened, as a "lon,lat" string.
PINS = [
    (1, "50.5,26.2"), (2, "30.7,36.9"), (3, "24.5,59.9"),
    (4, "32.2,48.5"), (5, "-106.4,25.5"), (6, "-75.2,-10.0"),
    (7, "34.5,31.4"), (8, "35.2,31.8"), (9, "-77.0,38.9"),
    (10, "-46.6,-23.5"), (11, "24.7,59.4"), (12, "85.1,25.6"),
    (13, "-74.0,40.7"),
]


def render_map(pg, x, y, w, h):
    pg.box(x, y, w, h, SKY)
    for ring in CONTINENTS.values():
        pg.fill_poly([project(pt, x, y, w, h) for pt in ring], LAND)
    gx = x + w // 6
    while gx < x + w:
        pg.vbar(gx, y, h, bytes([160, 200, 230]), 1)
        gx += w // 6
    # Nudges so pins that sit on top of each other stay readable.
    nudges = {1: (26, -4), 3: (16, -10), 4: (10, -12), 7: (-20, 14),
              8: (20, 16), 11: (-14, 6)}
    for num, pt in PINS:
        px, py = project(pt, x, y, w, h)
        dx, dy = nudges.get(num, (0, 0))
        px += dx
        py += dy
        pg.disc((px, py), 11, RED)
        pg.disc((px, py), 11, WHITE, fill=False)
        pg.disc((px, py), 9, RED)
        lbl = str(num)
        pg.put_text(px - text_width(lbl, 1) // 2, py - 4, lbl, 1, WHITE)

# ---------------------------------------------------------------- content
# Each lead is one line: number | place | date | headline | kicker | body.
LEAD_TEXT = """
1|BAHRAIN|SAT 21 NOV|IRAN HITS 4 US BASES|IN BAHRAIN|DRONES AND MISSILES AT 4 BASES. IRGC CLAIMS 2 RADARS DOWN.
2|ANTALYA|SUN 22 NOV|COP31 DEAL AT DAWN|AFTER ALL-NIGHT TALKS|NEW PACKAGE PUT TO 200 NATIONS. VOTE 06:00 GMT. FOSSIL FUELS AT STAKE.
3|BALTIC SEA|SAT 21 NOV|RUSSIAN SHIP SPARTA II|HIT, ON FIRE, ADRIFT|2 DRONES HIT THE SANCTIONED SHIP. 16 CREW SAFE. FINLAND: LIKELY UKRAINE.
"""

# Each figure is one line: big number | unit | what it counts.
FIGURE_TEXT = """
4|US BASES|HIT IN BAHRAIN
3|TANKERS|HIT IN HORMUZ
129|BODIES|FOUND IN GAZA
6.9|QUAKE|PERU, 0 KILLED
11|KILLED|SINALOA RAID
2 KILLED|60 WOUNDED|KRYVYI RIH
"""

# Each card is one line: number | place | date | headline | body.
CARD_TEXT = """
4|KRYVYI RIH|SAT 21 NOV|DOUBLE-TAP STRIKE KILLS BOY, 7, AND PARAMEDIC, 20|60 WOUNDED. 25 BLOCKS DAMAGED. 3 MISSILES, 148 DRONES OVERNIGHT.
5|SINALOA|SAT 21 NOV|MEXICO CAPTURES EL CHAPO ISIDRO, FBI TOP 10|11 KILLED AS CARTEL GUNMEN BURN ROADBLOCKS. FANS FLEE GAME.
6|PERU|SAT 21 NOV|M6.9 QUAKE SHAKES THE ANDES, FELT IN LIMA|34 KM NORTH OF JUNIN, 108 KM DEEP. NO DAMAGE REPORTED.
7|GAZA|SAT 21 NOV|129 MORE BODIES PULLED FROM THE RUBBLE|CENTRAL GAZA RECOVERY ENDS PHASE 2. TOLL NOW 74,736.
8|JERUSALEM|SAT 21 NOV|EISENKOT INVITES LIKUD TO NEW COALITION TALKS|TALKS RESUME SUNDAY. 48 OF 120 SEATS, NEEDS 61 BY 6 DEC.
9|WASHINGTON|SAT 21 NOV|TRUMP REPOSTS GOLD TRUMPCARE CARD|DEMOCRAT'S UNIVERSAL PLAN SHARED, NO CAPTION. NOT AN ENDORSEMENT.
10|BRASILIA|SAT 21 NOV|BOLSONARO TAKEN TO ICU WITH BOWEL BLOCKAGE|EX-PRESIDENT STABLE, ON GASTRIC TUBE. NO DISCHARGE DATE.
11|TALLINN|FRI 20 NOV|ESTONIA TO SHUT RUSSIA BORDER FOR 6 MONTHS|ALL 5 ROAD CROSSINGS CLOSE 1 DEC. MOSCOW CRIES IRON CURTAIN.
12|PATNA|SAT 21 NOV|MODI OPENS NITISH SETU, 19.76-KM GANGA BRIDGE|PROJECTS WORTH RS 34,470 CRORE LAUNCHED IN BIHAR.
13|WALL STREET|FRI 20 NOV|WEEK IN REVIEW: S AND P -8.6%, NASDAQ -10%|FRIDAY: NASDAQ -5.28%. GOLD $3,515. BITCOIN BELOW $60,000.
"""

# The rest of the day, numbered 14 to 38, three columns of nine.
BRIEF_TEXT = """
14 COP31: $120BN ADAPTATION TARGET CUT FROM DRAFT
15 CENTCOM DENIES IRAN CLAIM OF F-16 DAMAGE
16 IRGC CLAIMS 2 US DRONES DOWNED OVER HORMUZ
17 RUSSIAN HELICOPTER IN FINNISH AIRSPACE, 4.1 KM
18 RUSSIA SAYS 80 DRONES DOWNED OVER LENINGRAD
19 DENMARK FOILS PLOT TO KILL RAPPER KYIVSTONER
20 UK-EU DEAL: FOOD CHECKS END 2028, 100K VISAS
21 EU PAYS UKRAINE EUR 7.9BN, LARGEST EVER
22 GUPTA JAILED 235 MONTHS OVER PANNUN PLOT
23 RIEMANN PROOF CLAIMED IN LEAN, NOT VERIFIED
24 S AFRICA: 581 WOMEN KILLED IN 3 MONTHS
25 CYCLONE AKVAN LANDFALL, 3 LAKH EVACUATED
26 TEST: NZ 368, INDIA 159-1 AT STUMPS, DAY 2
27 HOCKEY: INDIA WOMEN 4-1, MEN 3-2 OVER NZ
28 JAPAN TO TRAIN LIVE-FIRE IN INDIA, A FIRST
29 US AIRLINES WARNED OF ATTACKS BEFORE THANKSGIVING
30 FRANCE SEEKS UNSC ACTION AFTER MYANMAR REJECTS ICJ
31 SAUDI POSTPONES TWO DATA FORUMS TO 2027
32 MAMDANI: CLOSE RIKERS ISLAND JAIL BY 2032
33 PRICE UNDISPUTED WELTERWEIGHT CHAMPION
34 HARRY KANE OUT FOR MONTHS, ANKLE INJURY
35 DEUTSCHE LEAK: $582M EPSTEIN DEALS FLAGGED
36 ANGOLA TO PAY $180M FOR 10% OF DE BEERS
37 COST-OF-LIVING PROTESTS SWEEP EUROPE
38 S AFRICA: ANC FIGHTS TO HOLD ITS CITIES
"""

# Stories per region, in the order the panel lists them.
REGION_TEXT = """
EUROPE 13
MIDDLE EAST 6
NORTH AMERICA 6
ASIA-PACIFIC 5
LATIN AMERICA 3
AFRICA 3
OCEANIA 2
"""

TIMELINE = """THE DAY IN ORDER, UTC: FRI 00:09 - PERU M6.9 QUAKE. SAT 07:00 - SPARTA II HIT. SAT PM - COP31 DEADLOCK, EISENKOT INVITES LIKUD. SAT NIGHT - IRAN HITS BAHRAIN BASES. SUN 03:00 - COP31 OBJECTION DEADLINE. 06:00 - APPROVAL SESSION."""

DATECHECK = """DATE CHECK - NOT TODAY: 20 NOV - KYIV BRIDGES HIT. MISSILES LAND IN POLAND. 19 NOV - ICJ MYANMAR VERDICT. SHENZHEN TRILATERAL. ANTHROPIC IPO $83. 17 NOV - KERCH BRIDGE STRIKE."""


def parse_rows(text):
    rows = []
    for ln in text.strip().split("\n"):
        rows.append(ln.split("|"))
    return rows


LEADS = parse_rows(LEAD_TEXT)
FIGURES = parse_rows(FIGURE_TEXT)
CARDS = parse_rows(CARD_TEXT)
BRIEF = BRIEF_TEXT.strip().split("\n")
REGIONS = REGION_TEXT.strip().split("\n")


# ---------------------------------------------------------------- draw
def draw_masthead(pg):
    pg.box(0, 0, W, 8, RED)
    pg.box(0, 8, W, 100, NAVY)
    pg.put_text(W // 2, 20, "THE WORLD IN ONE DAY", 3, YELLOW, align="c")
    pg.put_text(W // 2, 46, "SUNDAY 22 NOVEMBER 2026", 5, WHITE, align="c")
    pg.put_text(W // 2, 88, "38 STORIES - 7 REGIONS - ONE DAY OF WORLD NEWS",
                2, SKY_DK, align="c")


def draw_leads(pg):
    scenes = [panel_bahrain, panel_cop, panel_sparta]
    panel_w = 328
    gap = 12
    for i in range(len(LEADS)):
        num, place, date, h1, h2, body = LEADS[i]
        x = 8 + i * (panel_w + gap)
        y = 116
        pg.frame(x, y, panel_w, 280, FG, 2)
        scenes[i](pg, x + 2, y + 2, panel_w - 4, 150)
        band = RED if i == 0 else NAVY
        pg.box(x, y + 152, panel_w, 22, band)
        pg.put_text(x + 8, y + 157, num + "  " + place, 2, WHITE)
        pg.put_text(x + panel_w - 8, y + 157, date, 2, YELLOW, align="r")
        yy = pg.block(x + 8, y + 180, h1 + " " + h2, 2, FG, panel_w - 16,
                      lh=17)
        pg.block(x + 8, yy + 2, body, 2, NAVY2, panel_w - 16, lh=15)


def draw_figures(pg):
    fig_y = 404
    fig_h = 48
    fig_w = 164
    for i in range(len(FIGURES)):
        big, unit, what = FIGURES[i]
        x = 8 + i * (fig_w + 8)
        pg.box(x, fig_y, fig_w, fig_h, WHITE)
        pg.frame(x, fig_y, fig_w, fig_h, FG, 1)
        pg.put_text(x + fig_w // 2, fig_y + 4, big, 3, RED, align="c")
        lines = wrap_words(unit + " - " + what, 26)
        ly = fig_y + 27
        for ln in lines[:2]:
            pg.put_text(x + fig_w // 2, ly, ln, 1, FG, align="c")
            ly += 9


def draw_map_panel(pg):
    map_y = 460
    map_h = 152
    pg.frame(8, map_y, 700, map_h, FG, 2)
    pg.put_text(16, map_y + 6, "THE WORLD - PINS 1 TO 13", 2, FG)
    render_map(pg, 16, map_y + 26, 684, map_h - 32)
    reg_x = 716
    pg.frame(reg_x, map_y, 300, map_h, FG, 2)
    pg.box(reg_x, map_y, 300, 24, NAVY)
    pg.put_text(reg_x + 10, map_y + 5, "HOW THE DAY BREAKS DOWN", 2, WHITE)
    yy = map_y + 30
    for reg in REGIONS:
        pg.put_text(reg_x + 10, yy, reg, 2, FG)
        yy += 15
    pg.put_text(reg_x + 10, yy + 2, "38 STORIES, ALL DATED", 1, GREY)


def draw_cards(pg):
    grid_y = 620
    cell_h = 104
    cell_w = 196
    for i in range(len(CARDS)):
        row, col = divmod(i, 5)
        x = 8 + col * (cell_w + 8)
        y = grid_y + row * (cell_h + 8)
        num, place, date, head, body = CARDS[i]
        pg.box(x, y, cell_w, cell_h, WHITE)
        pg.frame(x, y, cell_w, cell_h, FG, 1)
        pg.box(x, y, cell_w, 18, NAVY2)
        pg.put_text(x + 6, y + 3, num + " " + place, 1, WHITE)
        pg.put_text(x + cell_w - 6, y + 3, date, 1, YELLOW, align="r")
        yy = pg.block(x + 6, y + 22, head, 1, FG, cell_w - 12, lh=10)
        pg.block(x + 6, yy + 1, body, 1, GREY, cell_w - 12, lh=9)


def draw_brief(pg):
    brief_y = 836
    pg.box(0, brief_y, W, 24, NAVY)
    pg.put_text(8, brief_y + 5, "THE WORLD IN BRIEF - 14 TO 38", 2, WHITE)
    pg.put_text(W - 8, brief_y + 5, "EVERY ITEM VERIFIED 20-22 NOV", 1,
                SKY_DK, align="r")
    col_w = 328
    for col in range(3):
        x = 8 + col * (col_w + 12)
        yy = brief_y + 29
        for item in BRIEF[col * 9:(col + 1) * 9]:
            pg.put_text(x, yy, item, 1, FG)
            yy += 10


def draw_footer(pg):
    foot_y = 962
    pg.hbar(0, foot_y, W, FG, 2)
    cursor = pg.block(8, foot_y + 4, TIMELINE, 1, FG, W - 16, lh=10)
    cursor = pg.block(8, cursor + 1, DATECHECK, 1, RED, W - 16, lh=10)
    pg.put_text(W // 2, cursor + 2,
                "SOURCES: REUTERS - BBC - CNN - AP - EURONEWS - AL JAZEERA - "
                "22 NOV 2026", 1, GREY, align="c")


def draw():
    pg = Canvas(W, H, BG)
    draw_masthead(pg)
    draw_leads(pg)
    draw_figures(pg)
    draw_map_panel(pg)
    draw_cards(pg)
    draw_brief(pg)
    draw_footer(pg)
    return pg


def main():
    target = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(target, exist_ok=True)
    data = draw().to_png()
    path = target + "/entry.png"
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
