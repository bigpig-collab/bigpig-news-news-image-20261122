#!/usr/bin/env python3
"""news-image-20261122: one image summing up Sunday 22 November 2026.

Pure Python 3.13 standard library, no Pillow, no network. The program
paints a 1024x1024 broadsheet front page: a date masthead, three
illustrated lead panels, a figures band with six verified numbers, a
schematic world map with numbered pins, ten story cards, a 25-item
world-in-brief, a UTC timeline strip and a date-check box naming the
stories that were deliberately left out because they belong to an
earlier day. Every letter comes from a hand-built 5x7 pixel alphabet
(all caps, no serif). Output goes to /output/entry.png, or to the
directory named by MAKEFUN_OUTPUT_DIR. Two runs write identical bytes.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- alphabet
# 5x7 pixel glyphs, one row of five bits per string. "1" paints, "0" stays.
GLYPHS = {
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
BLANK = ("00000","00000","00000","00000","00000","00000","00000")


def text_w(txt, scale):
    # Pixel width of txt at this scale, no trailing gap.
    return len(txt) * 6 * scale - scale


def wrap(txt, limit):
    """Greedy word wrap, at most limit characters on a line."""
    words = txt.split(" ")
    out, cur = [], ""
    for word in words:
        if cur == "":
            cur = word
        elif len(cur) + 1 + len(word) <= limit:
            cur = cur + " " + word
        else:
            out.append(cur)
            cur = word
    if cur != "":
        out.append(cur)
    return out


# ---------------------------------------------------------------- canvas
class Sheet:
    """An RGB canvas held as one flat bytearray, 3 bytes per pixel."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            idx = (y * self.w + x) * 3
            self.px[idx:idx + 3] = c

    def rect(self, x, y, w, h, c):
        xa, ya = max(0, x), max(0, y)
        xb, yb = min(self.w, x + w), min(self.h, y + h)
        for row in range(ya, yb):
            idx = (row * self.w + xa) * 3
            self.px[idx:idx + (xb - xa) * 3] = c * (xb - xa)

    def hline(self, x, y, w, c, t=1):  # horizontal bar, t px tall
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):  # vertical bar, t px wide
        self.rect(x, y, t, h, c)

    def border(self, x, y, w, h, c, t=1):  # four bars around a box
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c):
        # Bresenham's walk from (x0, y0) to (x1, y1).
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        e = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * e
            if e2 > -dy:
                e -= dy
                x0 += sx
            if e2 < dx:
                e += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                elif abs(d2 - r * r) <= r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon, one row at a time."""
        if len(pts) == 0:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            cuts = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    cuts.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            cuts.sort()
            for k in range(0, len(cuts) - 1, 2):
                for x in range(int(cuts[k]), int(cuts[k + 1]) + 1):
                    self.set(x, y, c)

    def glyph(self, x, y, ch, scale, c):
        g = GLYPHS.get(ch, BLANK)
        for row_i, row in enumerate(g):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + col_i * scale, y + row_i * scale,
                              scale, scale, c)

    def text(self, x, y, txt, scale, c, align="l"):
        txt = txt.upper()
        if align == "c":
            x = x - text_w(txt, scale) // 2
        elif align == "r":
            x = x - text_w(txt, scale)
        for ch in txt:
            self.glyph(x, y, ch, scale, c)
            x += 6 * scale
        return x

    def para(self, x, y, txt, scale, c, width, lh=None):
        """Wrapped paragraph; returns the y just below its last line."""
        if lh is None:
            lh = 9 * scale
        per_line = max(1, (width + scale) // (6 * scale))
        for ln in wrap(txt, per_line):
            self.text(x, y, ln, scale, c)
            y += lh
        return y

    def png_bytes(self):
        buf = bytearray()
        row_bytes = self.w * 3
        for y in range(self.h):
            buf.append(0)
            buf += self.px[y * row_bytes:(y + 1) * row_bytes]
        zdata = zlib.compress(bytes(buf), 9)

        def emit(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return out

        header = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + emit(b"IHDR", header)
                + emit(b"IDAT", zdata) + emit(b"IEND", b""))


# ---------------------------------------------------------------- palette
PAPER = bytes((247, 243, 232))
INK = bytes((20, 20, 20))
NAVY = bytes((17, 24, 39))
NAVY2 = bytes((31, 41, 55))
RED = bytes((185, 28, 28))
RED_LT = bytes((254, 226, 226))
BLUE = bytes((29, 78, 216))
SKY = bytes((186, 220, 245))
SKY_DK = bytes((147, 197, 253))
LAND = bytes((210, 196, 160))
LAND2 = bytes((188, 172, 128))
GOLD = bytes((180, 83, 9))
GREEN = bytes((21, 128, 61))
GREY = bytes((107, 114, 128))
LINE = bytes((180, 175, 160))
WHITE = bytes((255, 255, 255))
YELLOW = bytes((250, 204, 21))
DUSK = bytes((55, 48, 84))
DUSK2 = bytes((76, 29, 149))
ORANGE = bytes((234, 88, 12))

# ---------------------------------------------------------------- scenes
def scene_bahrain(s, x, y, w, h):
    """Night over Bahrain: four bases, missile bursts, tankers below."""
    import math
    s.rect(x, y, w, h, DUSK2)
    # stars scattered over the night sky
    for star_x, star_y in [(22, 12), (80, 24), (150, 10), (210, 20),
                           (280, 14), (120, 34), (250, 36), (40, 40)]:
        s.rect(x + star_x, y + star_y, 3, 3, WHITE)
    # skyline: low base blocks, windows lit
    blocks = [(8, 30, 46), (46, 24, 62), (78, 28, 40), (114, 26, 58),
              (148, 30, 44), (186, 24, 66), (218, 28, 48), (254, 26, 60),
              (288, 24, 42)]
    for bx, bw, bh in blocks:
        s.rect(x + bx, y + h - 30 - bh, bw, bh, NAVY)
        for wy in range(6, bh - 6, 10):
            for wx in range(4, bw - 4, 9):
                s.rect(x + bx + wx, y + h - 30 - bh + wy, 3, 4, YELLOW)
    # four intercept bursts, rays flying out
    for cx, cy in [(60, 40), (140, 28), (220, 42), (292, 30)]:
        s.circle(x + cx, y + cy, 12, YELLOW)
        s.circle(x + cx, y + cy, 7, WHITE)
        s.circle(x + cx, y + cy, 3, RED)
        for ang in range(0, 360, 45):
            dx = int(18 * math.cos(math.radians(ang)))
            dy = int(18 * math.sin(math.radians(ang)))
            s.line(x + cx, y + cy, x + cx + dx, y + cy + dy, YELLOW)
    # the strait at the bottom: three tankers, the middle one burning
    s.rect(x, y + h - 30, w, 30, BLUE)
    s.hline(x, y + h - 30, w, SKY_DK, 2)
    for tx, burning in [(30, False), (130, True), (230, False)]:
        s.rect(x + tx, y + h - 22, 70, 10, NAVY2)
        s.rect(x + tx + 12, y + h - 30, 14, 8, NAVY2)
        if burning:
            s.circle(x + tx + 35, y + h - 30, 9, ORANGE)
            s.circle(x + tx + 35, y + h - 30, 5, YELLOW)
            s.circle(x + tx + 35, y + h - 30, 2, WHITE)


def scene_cop(s, x, y, w, h):
    """Antalya at dawn: hall, rising sun, a row of delegates' flags."""
    s.rect(x, y, w, h, SKY)
    # dawn sun with rays
    import math
    s.circle(x + w // 2, y + 58, 26, YELLOW)
    s.circle(x + w // 2, y + 58, 18, WHITE)
    for ang in range(0, 360, 30):
        dx = int(44 * math.cos(math.radians(ang)))
        dy = int(44 * math.sin(math.radians(ang)))
        s.line(x + w // 2, y + 58, x + w // 2 + dx, y + 58 + dy, YELLOW)
    # hills behind the hall
    s.poly([(x, y + h - 40), (x + 90, y + h - 78), (x + 180, y + h - 46),
            (x + 250, y + h - 80), (x + w, y + h - 52), (x + w, y + h),
            (x, y + h)], LAND2)
    # conference hall, red roofline, lit windows
    s.rect(x + 60, y + h - 62, w - 120, 62, NAVY)
    s.rect(x + 60, y + h - 62, w - 120, 8, RED)
    for wx in range(72, w - 72, 22):
        s.rect(x + wx, y + h - 48, 12, 20, YELLOW)
    # flags on the roof
    for i, fc in enumerate([RED, BLUE, GREEN, GOLD, WHITE, ORANGE]):
        fx = x + 84 + i * 34
        s.vline(fx, y + h - 84, 22, INK, 2)
        s.rect(fx + 2, y + h - 84, 18, 12, fc)
    # wall clock: dawn, 06:00
    s.circle(x + w - 46, y + 30, 16, WHITE)
    s.circle(x + w - 46, y + 30, 16, INK, fill=False)
    s.line(x + w - 46, y + 30, x + w - 46, y + 18, INK)
    s.line(x + w - 46, y + 30, x + w - 34, y + 30, INK)


def scene_sparta(s, x, y, w, h):
    """Gulf of Finland: Sparta II burning, drifting, boats alongside."""
    s.rect(x, y, w, h, SKY)
    # grey clouds drifting over the gulf
    for cx, cy in [(30, 18), (150, 10), (250, 24)]:
        s.circle(x + cx, y + cy, 12, WHITE)
        s.circle(x + cx + 22, y + cy + 4, 14, WHITE)
        s.circle(x + cx + 44, y + cy, 10, WHITE)
    # two drones diving, trails behind them
    for dx, dy in [(120, 30), (210, 22)]:
        s.rect(x + dx, y + dy, 8, 4, INK)
        s.line(x + dx, y + dy + 4, x + dx - 6, y + dy + 14, GREY)
        s.line(x + dx + 8, y + dy + 4, x + dx + 14, y + dy + 14, GREY)
    # the sea, with wave lines
    s.rect(x, y + h - 52, w, 52, BLUE)
    for wy in range(y + h - 48, y + h - 4, 10):
        s.hline(x + 10, wy, w - 20, SKY_DK, 2)
    # the ship: hull, containers, fire amidships, smoke above
    s.rect(x + 50, y + h - 84, 220, 32, NAVY2)
    s.rect(x + 50, y + h - 84, 220, 6, RED)
    s.rect(x + 70, y + h - 104, 40, 20, RED)
    s.rect(x + 120, y + h - 100, 40, 16, GOLD)
    s.rect(x + 230, y + h - 98, 24, 14, WHITE)
    s.circle(x + 185, y + h - 96, 18, ORANGE)
    s.circle(x + 185, y + h - 96, 11, YELLOW)
    s.circle(x + 185, y + h - 96, 5, WHITE)
    s.circle(x + 185, y + h - 128, 10, GREY)
    s.circle(x + 178, y + h - 142, 8, GREY)
    s.circle(x + 192, y + h - 150, 6, GREY)
    # a yellow lifeboat and a white rescue boat
    s.rect(x + 286, y + h - 40, 30, 8, YELLOW)
    s.rect(x + 292, y + h - 48, 8, 8, YELLOW)
    s.rect(x + 20, y + h - 38, 22, 7, WHITE)


# ---------------------------------------------------------------- map
def lonlat(lon, lat, mx, my, mw, mh):
    # Equirectangular projection: lon -170..190 across, lat 75..-60 down.
    px = mx + int((lon + 170.0) / 360.0 * mw)
    py = my + int((75.0 - lat) / 135.0 * mh)
    return px, py


# Rough continent outlines, as (lon, lat) rings.
CONTINENTS = {
    "NA": [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73),
           (-70, 62), (-75, 45), (-80, 32), (-90, 20), (-97, 16),
           (-105, 20), (-115, 30), (-125, 40), (-125, 49), (-140, 60),
           (-165, 60)],
    "SA": [(-80, 10), (-60, 5), (-50, -5), (-35, -8), (-40, -20),
           (-48, -28), (-58, -35), (-65, -45), (-70, -55), (-73, -40),
           (-75, -20), (-80, -5)],
    "EU": [(-10, 36), (-9, 43), (0, 46), (-2, 50), (5, 53), (8, 57),
           (18, 56), (21, 60), (28, 60), (30, 68), (40, 68), (45, 60),
           (40, 55), (35, 50), (30, 45), (28, 40), (22, 36), (15, 38),
           (10, 38), (3, 42)],
    "AF": [(-6, 35), (10, 37), (20, 32), (32, 31), (35, 28), (43, 12),
           (51, 11), (48, 0), (40, -10), (35, -20), (32, -29), (25, -34),
           (18, -35), (12, -18), (8, 4), (-8, 5), (-15, 12)],
    "AS": [(40, 68), (60, 70), (90, 75), (120, 73), (150, 70), (170, 66),
           (178, 65), (170, 60), (160, 55), (142, 50), (135, 43),
           (128, 38), (122, 30), (115, 22), (108, 12), (103, 8),
           (100, 8), (95, 15), (90, 22), (85, 20), (80, 13), (77, 8),
           (72, 20), (66, 25), (60, 25), (55, 26), (50, 29), (48, 30),
           (44, 29), (40, 35), (38, 36), (40, 45), (42, 55)],
    "OC": [(113, -22), (125, -15), (135, -12), (142, -11), (147, -19),
           (153, -27), (150, -37), (140, -38), (130, -32), (120, -34),
           (113, -26)],
}

# Pin number -> where the story happened.
PINS = [
    (1, 50.5, 26.2), (2, 30.7, 36.9), (3, 24.5, 59.9), (4, 32.2, 48.5),
    (5, -106.4, 25.5), (6, -75.2, -10.0), (7, 34.5, 31.4),
    (8, 35.2, 31.8), (9, -77.0, 38.9), (10, -46.6, -23.5),
    (11, 24.7, 59.4), (12, 85.1, 25.6), (13, -74.0, 40.7),
]


def draw_map(s, x, y, w, h):
    s.rect(x, y, w, h, SKY)
    for ring in CONTINENTS.values():
        s.poly([lonlat(lo, la, x, y, w, h) for lo, la in ring], LAND)
    # faint longitude guides
    for gx in range(x + w // 6, x + w, w // 6):
        s.vline(gx, y, h, bytes((160, 200, 230)), 1)
    # nudges so pins that sit on top of each other stay readable
    offsets = {1: (26, -4), 3: (16, -10), 4: (10, -12), 7: (-20, 14),
               8: (20, 16), 11: (-14, 6)}
    for num, lo, la in PINS:
        px, py = lonlat(lo, la, x, y, w, h)
        dx, dy = offsets.get(num, (0, 0))
        px, py = px + dx, py + dy
        s.circle(px, py, 11, RED)
        s.circle(px, py, 11, WHITE, fill=False)
        s.circle(px, py, 9, RED)
        lbl = str(num)
        s.text(px - text_w(lbl, 1) // 2, py - 4, lbl, 1, WHITE)

# ---------------------------------------------------------------- content
# (num, place, date, headline part 1, headline part 2, body)
LEADS = [
    ("1", "BAHRAIN", "SAT 21 NOV", "IRAN HITS 4 US BASES", "IN BAHRAIN",
     "DRONES AND MISSILES AT 4 BASES. IRGC CLAIMS 2 RADARS DOWN."),
    ("2", "ANTALYA", "SUN 22 NOV", "COP31 DEAL AT DAWN",
     "AFTER ALL-NIGHT TALKS",
     "NEW PACKAGE PUT TO 200 NATIONS. VOTE 06:00 GMT. FOSSIL FUELS AT STAKE."),
    ("3", "BALTIC SEA", "SAT 21 NOV", "RUSSIAN SHIP SPARTA II",
     "HIT, ON FIRE, ADRIFT",
     "2 DRONES HIT THE SANCTIONED SHIP. 16 CREW SAFE. FINLAND: LIKELY UKRAINE."),
]

# (big number, unit, what it counts)
FIGURES = [
    ("4", "US BASES", "HIT IN BAHRAIN"),
    ("3", "TANKERS", "HIT IN HORMUZ"),
    ("129", "BODIES", "FOUND IN GAZA"),
    ("6.9", "QUAKE", "PERU, 0 KILLED"),
    ("11", "KILLED", "SINALOA RAID"),
    ("2 KILLED", "60 WOUNDED", "KRYVYI RIH"),
]

# (num, place, date, headline, body)
CARDS = [
    ("4", "KRYVYI RIH", "SAT 21 NOV",
     "DOUBLE-TAP STRIKE KILLS BOY, 7, AND PARAMEDIC, 20",
     "60 WOUNDED. 25 BLOCKS DAMAGED. 3 MISSILES, 148 DRONES OVERNIGHT."),
    ("5", "SINALOA", "SAT 21 NOV",
     "MEXICO CAPTURES EL CHAPO ISIDRO, FBI TOP 10",
     "11 KILLED AS CARTEL GUNMEN BURN ROADBLOCKS. FANS FLEE GAME."),
    ("6", "PERU", "SAT 21 NOV",
     "M6.9 QUAKE SHAKES THE ANDES, FELT IN LIMA",
     "34 KM NORTH OF JUNIN, 108 KM DEEP. NO DAMAGE REPORTED."),
    ("7", "GAZA", "SAT 21 NOV",
     "129 MORE BODIES PULLED FROM THE RUBBLE",
     "CENTRAL GAZA RECOVERY ENDS PHASE 2. TOLL NOW 74,736."),
    ("8", "JERUSALEM", "SAT 21 NOV",
     "EISENKOT INVITES LIKUD TO NEW COALITION TALKS",
     "TALKS RESUME SUNDAY. 48 OF 120 SEATS, NEEDS 61 BY 6 DEC."),
    ("9", "WASHINGTON", "SAT 21 NOV",
     "TRUMP REPOSTS GOLD TRUMPCARE CARD",
     "DEMOCRAT'S UNIVERSAL PLAN SHARED, NO CAPTION. NOT AN ENDORSEMENT."),
    ("10", "BRASILIA", "SAT 21 NOV",
     "BOLSONARO TAKEN TO ICU WITH BOWEL BLOCKAGE",
     "EX-PRESIDENT STABLE, ON GASTRIC TUBE. NO DISCHARGE DATE."),
    ("11", "TALLINN", "FRI 20 NOV",
     "ESTONIA TO SHUT RUSSIA BORDER FOR 6 MONTHS",
     "ALL 5 ROAD CROSSINGS CLOSE 1 DEC. MOSCOW CRIES IRON CURTAIN."),
    ("12", "PATNA", "SAT 21 NOV",
     "MODI OPENS NITISH SETU, 19.76-KM GANGA BRIDGE",
     "PROJECTS WORTH RS 34,470 CRORE LAUNCHED IN BIHAR."),
    ("13", "WALL STREET", "FRI 20 NOV",
     "WEEK IN REVIEW: S AND P -8.6%, NASDAQ -10%",
     "FRIDAY: NASDAQ -5.28%. GOLD $3,515. BITCOIN BELOW $60,000."),
]

# The rest of the day, numbered 14 to 38, three columns of nine.
BRIEF = [
    "14 COP31: $120BN ADAPTATION TARGET CUT FROM DRAFT",  # climate
    "15 CENTCOM DENIES IRAN CLAIM OF F-16 DAMAGE",  # military
    "16 IRGC CLAIMS 2 US DRONES DOWNED OVER HORMUZ",  # military
    "17 RUSSIAN HELICOPTER IN FINNISH AIRSPACE, 4.1 KM",  # military
    "18 RUSSIA SAYS 80 DRONES DOWNED OVER LENINGRAD",  # military
    "19 DENMARK FOILS PLOT TO KILL RAPPER KYIVSTONER",  # crime
    "20 UK-EU DEAL: FOOD CHECKS END 2028, 100K VISAS",  # politics
    "21 EU PAYS UKRAINE EUR 7.9BN, LARGEST EVER",  # politics
    "22 GUPTA JAILED 235 MONTHS OVER PANNUN PLOT",  # crime
    "23 RIEMANN PROOF CLAIMED IN LEAN, NOT VERIFIED",  # science
    "24 S AFRICA: 581 WOMEN KILLED IN 3 MONTHS",  # society
    "25 CYCLONE AKVAN LANDFALL, 3 LAKH EVACUATED",  # weather
    "26 TEST: NZ 368, INDIA 159-1 AT STUMPS, DAY 2",  # sport
    "27 HOCKEY: INDIA WOMEN 4-1, MEN 3-2 OVER NZ",  # sport
    "28 JAPAN TO TRAIN LIVE-FIRE IN INDIA, A FIRST",  # military
    "29 US AIRLINES WARNED OF ATTACKS BEFORE THANKSGIVING",  # security
    "30 FRANCE SEEKS UNSC ACTION AFTER MYANMAR REJECTS ICJ",  # politics
    "31 SAUDI POSTPONES TWO DATA FORUMS TO 2027",  # tech
    "32 MAMDANI: CLOSE RIKERS ISLAND JAIL BY 2032",  # politics
    "33 PRICE UNDISPUTED WELTERWEIGHT CHAMPION",  # sport
    "34 HARRY KANE OUT FOR MONTHS, ANKLE INJURY",  # sport
    "35 DEUTSCHE LEAK: $582M EPSTEIN DEALS FLAGGED",  # finance
    "36 ANGOLA TO PAY $180M FOR 10% OF DE BEERS",  # business
    "37 COST-OF-LIVING PROTESTS SWEEP EUROPE",  # society
    "38 S AFRICA: ANC FIGHTS TO HOLD ITS CITIES",  # politics
]

# Stories per region, in the order the panel lists them.
REGIONS = ("EUROPE 13", "MIDDLE EAST 6", "NORTH AMERICA 6",
           "ASIA-PACIFIC 5", "LATIN AMERICA 3", "AFRICA 3", "OCEANIA 2")

TIMELINE = ("THE DAY IN ORDER, UTC: FRI 00:09 - PERU M6.9 QUAKE. SAT 07:00 - "
            "SPARTA II HIT. SAT PM - COP31 DEADLOCK, EISENKOT INVITES LIKUD. "
            "SAT NIGHT - IRAN HITS BAHRAIN BASES. SUN 03:00 - COP31 "
            "OBJECTION DEADLINE. 06:00 - APPROVAL SESSION.")

DATECHECK = ("DATE CHECK - NOT TODAY: 20 NOV - KYIV BRIDGES HIT. MISSILES "
             "LAND IN POLAND. 19 NOV - ICJ MYANMAR VERDICT. SHENZHEN "
             "TRILATERAL. ANTHROPIC IPO $83. 17 NOV - KERCH BRIDGE STRIKE.")


# ---------------------------------------------------------------- draw
def draw():
    s = Sheet(W, H, PAPER)
    s.rect(0, 0, W, 8, RED)  # red rule across the very top

    # ---- masthead: title, date, story count
    s.rect(0, 8, W, 100, NAVY)
    s.text(W // 2, 20, "THE WORLD IN ONE DAY", 3, YELLOW, align="c")
    s.text(W // 2, 46, "SUNDAY 22 NOVEMBER 2026", 5, WHITE, align="c")
    s.text(W // 2, 88, "38 STORIES - 7 REGIONS - ONE DAY OF WORLD NEWS",
           2, SKY_DK, align="c")

    # ---- three lead panels, each with its own scene
    panel_x, panel_w, gap = 8, 328, 12
    for i, (num, place, date, h1, h2, body) in enumerate(LEADS):
        x = panel_x + i * (panel_w + gap)
        y = 116
        s.border(x, y, panel_w, 280, INK, 2)
        if i == 0:
            scene_bahrain(s, x + 2, y + 2, panel_w - 4, 150)
        elif i == 1:
            scene_cop(s, x + 2, y + 2, panel_w - 4, 150)
        else:
            scene_sparta(s, x + 2, y + 2, panel_w - 4, 150)
        s.rect(x, y + 152, panel_w, 22, RED if i == 0 else NAVY)
        s.text(x + 8, y + 157, num + "  " + place, 2, WHITE)
        s.text(x + panel_w - 8, y + 157, date, 2, YELLOW, align="r")
        yy = s.para(x + 8, y + 180, h1 + " " + h2, 2, INK, panel_w - 16,
                    lh=17)
        s.para(x + 8, yy + 2, body, 2, NAVY2, panel_w - 16, lh=15)

    # ---- figures band: six cells, big red number on top
    fig_y, fig_h, fig_w = 404, 48, 164
    for i, (big, unit, what) in enumerate(FIGURES):
        x = 8 + i * (fig_w + 8)
        s.rect(x, fig_y, fig_w, fig_h, WHITE)
        s.border(x, fig_y, fig_w, fig_h, INK, 1)
        s.text(x + fig_w // 2, fig_y + 4, big, 3, RED, align="c")
        lines = wrap(unit + " - " + what, 26)
        ly = fig_y + 27
        for ln in lines[:2]:
            s.text(x + fig_w // 2, ly, ln, 1, INK, align="c")
            ly += 9

    # ---- map on the left, region breakdown on the right
    map_y, map_h = 460, 152
    s.border(8, map_y, 700, map_h, INK, 2)
    s.text(16, map_y + 6, "THE WORLD - PINS 1 TO 13", 2, INK)
    draw_map(s, 16, map_y + 26, 684, map_h - 32)
    reg_x = 716
    s.border(reg_x, map_y, 300, map_h, INK, 2)
    s.rect(reg_x, map_y, 300, 24, NAVY)
    s.text(reg_x + 10, map_y + 5, "HOW THE DAY BREAKS DOWN", 2, WHITE)
    yy = map_y + 30
    for reg in REGIONS:
        s.text(reg_x + 10, yy, reg, 2, INK)
        yy += 15
    s.text(reg_x + 10, yy + 2, "38 STORIES, ALL DATED", 1, GREY)

    # ---- cards grid, five across and two down
    grid_y, cell_h, cell_w = 620, 104, 196
    for i, (num, place, date, head, body) in enumerate(CARDS):
        x = 8 + (i % 5) * (cell_w + 8)
        y = grid_y + (i // 5) * (cell_h + 8)
        s.rect(x, y, cell_w, cell_h, WHITE)
        s.border(x, y, cell_w, cell_h, INK, 1)
        s.rect(x, y, cell_w, 18, NAVY2)
        s.text(x + 6, y + 3, num + " " + place, 1, WHITE)
        s.text(x + cell_w - 6, y + 3, date, 1, YELLOW, align="r")
        yy = s.para(x + 6, y + 22, head, 1, INK, cell_w - 12, lh=10)
        s.para(x + 6, yy + 1, body, 1, GREY, cell_w - 12, lh=9)

    # ---- world in brief, three columns
    brief_y = 836
    s.rect(0, brief_y, W, 24, NAVY)
    s.text(8, brief_y + 5, "THE WORLD IN BRIEF - 14 TO 38", 2, WHITE)
    s.text(W - 8, brief_y + 5, "EVERY ITEM VERIFIED 20-22 NOV", 1, SKY_DK,
           align="r")
    col_w = 328
    for col in range(3):
        x = 8 + col * (col_w + 12)
        yy = brief_y + 29
        for item in BRIEF[col * 9:(col + 1) * 9]:
            s.text(x, yy, item, 1, INK)
            yy += 10

    # ---- footer: timeline, date check, sources
    foot_y = 962
    s.hline(0, foot_y, W, INK, 2)
    cursor = s.para(8, foot_y + 4, TIMELINE, 1, INK, W - 16, lh=10)
    cursor = s.para(8, cursor + 1, DATECHECK, 1, RED, W - 16, lh=10)
    s.text(W // 2, cursor + 2,
           "SOURCES: REUTERS - BBC - CNN - AP - EURONEWS - AL JAZEERA - "
           "22 NOV 2026", 1, GREY, align="c")
    return s


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    png = draw().png_bytes()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
