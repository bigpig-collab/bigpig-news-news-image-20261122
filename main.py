#!/usr/bin/env python3
"""Sunday 22 November 2026 — one page of world news. Pure stdlib.
Writes entry.png (1024x1024) into the directory given as argv[1].
Cream-paper broadsheet: serif masthead, illustrated leads and cards,
dotted world map, numbers sidebar, UTC strip, date check. All art drawn
in code. v3: COP31 collapse lead, 26 stories, tag chips, serif headlines.
"""
import sys
import zlib
import binascii

W, H = 1024, 1024
PAPER = (247, 241, 227)
INK = (26, 34, 64)
RED = (176, 30, 36)
GREY = (90, 96, 110)
CREAM2 = (238, 231, 214)
NIGHT = (16, 24, 52)
SEA = (28, 68, 110)
GOLD = (184, 134, 11)
TEAL = (15, 118, 110)
GREEN = (46, 125, 50)
PURPLE = (106, 76, 147)
SLATE = (91, 100, 112)
ORANGE = (214, 106, 24)
SKY = (168, 205, 225)
SAND = (226, 205, 160)

# ---------------------------------------------------------------- PNG writer
def _chunk(tag, data):
    out = len(data).to_bytes(4, "big") + tag + data
    return out + (binascii.crc32(tag + data) & 0xFFFFFFFF).to_bytes(4, "big")


def save_png(path, buf):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    ihdr = W.to_bytes(4, "big") + H.to_bytes(4, "big") + bytes([8, 2, 0, 0, 0])
    data = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)


# ------------------------------------------------------------------- sheet
class Sheet:
    def __init__(self):
        self.px = bytearray(PAPER * W * H)

    def dot(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def bar(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def frame(self, x, y, w, h, c, t=1):
        self.bar(x, y, w, t, c)
        self.bar(x, y + h - t, w, t, c)
        self.bar(x, y, t, h, c)
        self.bar(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        e = dx + dy
        while True:
            self.dot(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * e
            if e2 >= dy:
                e += dy
                x0 += sx
            if e2 <= dx:
                e += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.dot(xx, yy, c)

    def ring(self, cx, cy, r, c):
        import math as _m
        for a in range(360):
            self.dot(round(cx + r * _m.cos(_m.radians(a))),
                     round(cy + r * _m.sin(_m.radians(a))), c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        ys = sorted([y0, y1, y2])
        for yy in range(ys[0], ys[2] + 1):
            row = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                     (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= yy <= max(ay, by):
                    t = (yy - ay) / (by - ay)
                    row.append(ax + t * (bx - ax))
            if len(row) >= 2:
                for xx in range(int(min(row)), int(max(row)) + 1):
                    self.dot(xx, yy, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for k in range(n):
                ax, ay = pts[k]
                bx, by = pts[(k + 1) % n]
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.dot(xx, yy, c)

    def text(self, s, x, y, font, scale, c):
        cx = x
        for ch in s:
            g = font.get(ch)
            if g is None:
                g = font.get("?", (".....",) * 7)
            gw = len(g[0])
            for ry, row in enumerate(g):
                for rx, bit in enumerate(row):
                    if bit == "#":
                        self.bar(cx + rx * scale, y + ry * scale,
                                 scale, scale, c)
            cx += (gw + 1) * scale
        return cx

    def twidth(self, s, font, scale):
        w = 0
        for ch in s:
            g = font.get(ch)
            w += (len(g[0]) + 1) * scale if g else 6 * scale
        return w - scale if w else 0

    def centre(self, s, y, font, scale, c, x0=0, x1=W):
        w = self.twidth(s, font, scale)
        self.text(s, x0 + (x1 - x0 - w) // 2, y, font, scale, c)

    def para(self, lines, x, y, font, scale, c, lh=None):
        if lh is None:
            lh = (len(next(iter(font.values()))) + 2) * scale
        for ln in lines:
            self.text(ln, x, y, font, scale, c)
            y += lh
        return y


def wrap(s, font, scale, maxw):
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        w = sum((len(font.get(ch, (".....",))[0]) + 1) for ch in t) * scale
        if w <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

# ------------------------------------------------------------- sans (5x7)
SANS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    "a": (".....", ".....", ".####", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": ("..#..", ".....", "..#..", "..#..", "..#..", "..#..", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}

# ----------------------------------------------------------- serif (7x9)
SERIF = {
    "A": ("..###..", ".#...#.", ".#...#.", ".#...#.", ".#####.", ".#...#.", ".#...#.", "#.....#", "##...##"),
    "B": ("######.", "##...##", "##...##", "##...##", "######.", "##...##", "##...##", "##...##", "######."),
    "C": (".#####.", "##...##", "##.....", "##.....", "##.....", "##.....", "##...##", "##...##", ".#####."),
    "D": ("######.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "######."),
    "E": ("#######", "##.....", "##.....", "##.....", "#####..", "##.....", "##.....", "##.....", "#######"),
    "F": ("#######", "##.....", "##.....", "##.....", "#####..", "##.....", "##.....", "##.....", "##....."),
    "G": (".#####.", "##...##", "##.....", "##.....", "##.####", "##...##", "##...##", "##...##", ".#####."),
    "H": ("##...##", "##...##", "##...##", "##...##", "#######", "##...##", "##...##", "##...##", "##...##"),
    "I": ("#######", "...#...", "...#...", "...#...", "...#...", "...#...", "...#...", "...#...", "#######"),
    "J": ("....###", ".....##", ".....##", ".....##", ".....##", ".....##", "##...##", "##...##", ".#####."),
    "K": ("##...##", "##..##.", "##.##..", "##.#...", "###....", "##.#...", "##.##..", "##..##.", "##...##"),
    "L": ("##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "##.....", "#######"),
    "M": ("##...##", "###.###", "##.#.##", "##.#.##", "##...##", "##...##", "##...##", "##...##", "##...##"),
    "N": ("##...##", "##...##", "###..##", "###..##", "##.#.##", "##..###", "##..###", "##...##", "##...##"),
    "O": (".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", ".#####."),
    "P": ("######.", "##...##", "##...##", "##...##", "######.", "##.....", "##.....", "##.....", "##....."),
    "Q": (".#####.", "##...##", "##...##", "##...##", "##...##", "##...##", "##.#.##", "##..##.", ".###.##"),
    "R": ("######.", "##...##", "##...##", "##...##", "######.", "##.#...", "##..##.", "##...##", "##...##"),
    "S": (".#####.", "##...##", "##.....", "##.....", ".#####.", ".....##", ".....##", "##...##", ".#####."),
    "T": ("#######", "...#...", "...#...", "...#...", "...#...", "...#...", "...#...", "...#...", "...#..."),
    "U": ("##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", ".#####."),
    "V": ("##...##", "##...##", "##...##", "##...##", "##...##", "##...##", ".#...#.", ".#...#.", "..###.."),
    "W": ("##...##", "##...##", "##...##", "##...##", "##.#.##", "##.#.##", "###.###", "##...##", "##...##"),
    "X": ("##...##", "##...##", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#...#.", "##...##", "##...##"),
    "Y": ("##...##", "##...##", ".#...#.", "..#.#..", "...#...", "...#...", "...#...", "...#...", "...#..."),
    "Z": ("#######", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....", "##.....", "#######"),
    "0": (".#####.", "##...##", "##..###", "##.#.##", "##.#.##", "###..##", "##...##", "##...##", ".#####."),
    "1": ("...#...", "..##...", ".###...", "...#...", "...#...", "...#...", "...#...", "...#...", ".#####."),
    "2": (".#####.", "##...##", ".....##", "....##.", "...##..", "..##...", ".##....", "##.....", "#######"),
    "3": ("######.", ".....##", ".....##", ".....##", "..####.", ".....##", ".....##", "##...##", ".#####."),
    "4": ("....##.", "...##..", "..##...", ".##.#..", "##..#..", "#######", "....#..", "....#..", "....#.."),
    "5": ("#######", "##.....", "##.....", "######.", ".....##", ".....##", ".....##", "##...##", ".#####."),
    "6": (".#####.", "##...##", "##.....", "##.....", "######.", "##...##", "##...##", "##...##", ".#####."),
    "7": ("#######", ".....##", "....##.", "....##.", "...##..", "...##..", "..##...", "..##...", "..##..."),
    "8": (".#####.", "##...##", "##...##", "##...##", ".#####.", "##...##", "##...##", "##...##", ".#####."),
    "9": (".#####.", "##...##", "##...##", "##...##", ".######", ".....##", ".....##", "##...##", ".#####."),
    " ": (".......", ".......", ".......", ".......", ".......", ".......", ".......", ".......", "......."),
    ".": (".......", ".......", ".......", ".......", ".......", ".......", ".......", "..##...", "..##..."),
    ",": (".......", ".......", ".......", ".......", ".......", ".......", "..##...", "..##...", ".##...."),
    ":": (".......", "..##...", "..##...", ".......", ".......", "..##...", "..##...", ".......", "......."),
    "'": ("...##..", "...##..", "..##...", ".......", ".......", ".......", ".......", ".......", "......."),
    "-": (".......", ".......", ".......", ".......", ".#####.", ".......", ".......", ".......", "......."),
    "/": (".....##", "....##.", "....##.", "...##..", "..##...", "..##...", ".##....", ".##....", "##....."),
    "%": ("##...##", "##..##.", "....##.", "...##..", "..##...", ".##....", "##...##", "##...##", "##...##"),
    "$": ("...#...", ".#####.", "##.#.#.", "##.#...", ".#####.", "...#.##", ".#.#.##", ".#####.", "...#..."),
    "!": ("...#...", "...#...", "...#...", "...#...", "...#...", "...#...", ".......", "...#...", "...#..."),
    "?": (".#####.", "##...##", ".....##", "....##.", "...##..", "...#...", ".......", "...#...", "...#..."),
    "(": ("....##.", "...##..", "..##...", "..##...", "..##...", "..##...", "..##...", "...##..", "....##."),
    ")": (".##....", "..##...", "...##..", "...##..", "...##..", "...##..", "...##..", "..##...", ".##...."),
}

# ------------------------------------------------------------------ scenes
def _stars(seed, n, w, h):
    s = seed
    out = []
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((s % w, (s >> 9) % h))
    return out


def scene_kyiv(s, x, y, w, h):
    s.bar(x, y, w, h, NIGHT)
    for sx, sy in _stars(7, 26, w, h // 2):
        s.dot(x + sx, y + sy, (220, 220, 200))
    s.disc(x + w - 34, y + 22, 11, (232, 226, 190))
    s.disc(x + w - 34, y + 22, 8, (245, 240, 210))
    base = y + h - 26
    for bx, bw, bh in ((6, 26, 52), (38, 18, 70), (62, 30, 44), (98, 16, 62),
                       (120, 24, 38), (150, 20, 56), (176, 28, 46),
                       (210, 18, 66), (234, 26, 40), (266, 20, 58), (292, 22, 48)):
        s.bar(x + bx, base - bh, bw, bh + 26, (10, 14, 34))
        for wy in range(base - bh + 6, base - 4, 9):
            for wx in range(bx + 4, bx + bw - 3, 7):
                if (wx * 7 + wy * 3) % 11 < 4:
                    s.bar(x + wx, wy, 2, 3, (255, 214, 110))
    s.tri(x + 40, base, x + 130, base, x + 250, y + 8, (38, 52, 96))
    for dx, dy in ((60, 18), (150, 30), (230, 14), (290, 26)):
        s.disc(x + dx, y + dy, 2, (255, 220, 130))
        s.line(x + dx, y + dy, x + dx + 16, y + dy + 6, (255, 220, 130))
    for fx in (70, 200, 280):
        s.tri(x + fx, base, x + fx + 7, base - 16, x + fx + 14, base, ORANGE)
        s.tri(x + fx + 3, base - 10, x + fx + 7, base - 22, x + fx + 11,
              base - 10, (255, 190, 60))


def scene_collapse(s, x, y, w, h):
    for i in range(h - 54):
        t = i / max(1, h - 55)
        s.bar(x, y + i, w, 1, (int(232 - 30 * t), int(214 - 60 * t),
                               int(170 - 40 * t)))
    s.bar(x, y + h - 54, w, 54, (120, 96, 66))
    for r in range(3):
        for cx in range(5):
            dx = x + 14 + cx * (w // 5)
            dy = y + h - 48 + r * 14
            s.bar(dx, dy, w // 8, 9, (70, 52, 38))
            s.disc(dx + w // 16, dy - 4, 4, (232, 196, 150))
    s.bar(x + w // 2 - 40, y + h - 30, 80, 22, (60, 44, 30))
    s.bar(x + w // 2 - 46, y + h - 34, 92, 5, (90, 66, 44))
    s.bar(x + w // 2 - 14, y + h - 40, 16, 5, (120, 90, 60))
    s.bar(x + w // 2 + 4, y + h - 40, 4, 12, (90, 66, 44))
    s.bar(x + 8, y + h - 84, w - 16, 22, RED)
    s.text("NO DEAL", x + 12, y + h - 79, SANS, 2, (255, 255, 255))


def scene_bahrain(s, x, y, w, h):
    s.bar(x, y, w, h, NIGHT)
    for sx, sy in _stars(21, 22, w, h // 2):
        s.dot(x + sx, y + sy, (220, 220, 200))
    s.disc(x + w - 40, y + 24, 12, (232, 226, 190))
    s.bar(x, y + h - 46, w, 46, (14, 34, 66))
    for wy in range(y + h - 40, y + h - 4, 9):
        for wx in range(0, w, 26):
            s.bar(x + wx + (wy % 18), wy, 14, 2, (60, 110, 170))
    for hx, hw in ((20, 120), (170, 130)):
        s.poly([(x + hx, y + h - 46), (x + hx + 12, y + h - 66),
                (x + hx + hw - 12, y + h - 66), (x + hx + hw, y + h - 46)],
               (40, 44, 58))
        s.bar(x + hx + 22, y + h - 84, 10, 20, (40, 44, 58))
        s.bar(x + hx + 60, y + h - 78, 8, 14, (40, 44, 58))
    for fx in (60, 120, 230, 280):
        s.tri(x + fx, y + h - 46, x + fx + 6, y + h - 68, x + fx + 12,
              y + h - 46, ORANGE)
        s.disc(x + fx + 6, y + h - 74, 5, (90, 90, 90))
        s.disc(x + fx + 12, y + h - 82, 4, (110, 110, 110))
    s.ring(x + 150, y + 30, 16, (200, 200, 190))
    s.ring(x + 150, y + 30, 10, (200, 200, 190))
    s.line(x + 150, y + 30, x + 162, y + 18, (255, 220, 130))


def scene_ship(s, x, y, w, h):
    for i in range(max(0, h - 18)):
        t = i / max(1, h - 19)
        s.bar(x, y + i, w, 1, (int(240 - 40 * t), int(150 + 40 * t),
                               int(70 + 60 * t)))
    s.disc(x + w - 26, y + 10, 8, (250, 205, 110))
    s.bar(x, y + h - 18, w, 18, (36, 90, 140))
    for wy in range(y + h - 15, y + h - 1, 6):
        for wx in range(0, w, 22):
            s.bar(x + wx + (wy % 14), wy, 10, 2, (140, 190, 225))
    s.poly([(x + 16, y + h - 18), (x + 24, y + h - 28), (x + w - 16, y + h - 28),
            (x + w - 8, y + h - 18)], (30, 32, 40))
    for cx, c in ((36, RED), (76, (26, 34, 64)), (116, TEAL)):
        s.bar(x + cx, y + h - 40, 30, 12, c)
    for fx in (44, 84, 124):
        s.tri(x + fx, y + h - 28, x + fx + 4, y + h - 40, x + fx + 8,
              y + h - 28, ORANGE)
        s.disc(x + fx + 4, y + h - 44, 4, (80, 80, 80))


def scene_vote(s, x, y, w, h):
    s.bar(x, y, w, h, (222, 214, 196))
    s.bar(x + 14, y + 16, 62, 30, RED)
    s.bar(x + 14, y + 16, 62, 5, (140, 20, 26))
    s.bar(x + 76, y + 10, 4, 32, (60, 40, 20))
    s.bar(x + 80, y + 10, 26, 16, (250, 250, 250))
    s.line(x + 84, y + 22, x + 92, y + 12, INK)
    s.line(x + 92, y + 12, x + 102, y + 24, INK)
    s.bar(x + 120, y + 8, 56, 36, (250, 250, 244))
    s.frame(x + 120, y + 8, 56, 40, GREY)
    for ly in (16, 24, 32, 40):
        s.bar(x + 126, y + ly, 44, 2, (120, 120, 120))


def scene_f1(s, x, y, w, h):
    s.bar(x, y, w, h, NIGHT)
    for sx, sy in _stars(33, 14, w, h // 2):
        s.dot(x + sx, y + sy, (220, 220, 200))
    s.bar(x, y + h - 16, w, 4, (200, 200, 200))
    s.bar(x, y + h - 12, w, 12, (40, 40, 48))
    for cx in range(0, w, 12):
        s.bar(x + cx, y + h - 16, 6, 4, (255, 255, 255) if (cx // 12) % 2 == 0
              else (20, 20, 20))
    s.poly([(x + 20, y + h - 22), (x + 34, y + h - 30), (x + 120, y + h - 30),
            (x + 150, y + h - 22)], (200, 30, 36))
    s.bar(x + 96, y + h - 40, 22, 12, (200, 30, 36))
    s.disc(x + 48, y + h - 20, 7, (15, 15, 15))
    s.disc(x + 48, y + h - 20, 3, (180, 180, 180))
    s.disc(x + 132, y + h - 20, 7, (15, 15, 15))
    s.disc(x + 132, y + h - 20, 3, (180, 180, 180))
    s.bar(x + w - 46, y + 6, 3, 26, (200, 200, 200))
    for r in range(3):
        for c in range(4):
            s.bar(x + w - 43 + c * 10, y + 6 + r * 8, 10, 8,
                  (250, 250, 250) if (r + c) % 2 == 0 else (20, 20, 20))


def scene_cricket(s, x, y, w, h):
    s.bar(x, y, w, h, (96, 160, 80))
    s.bar(x, y + h - 14, w, 14, (150, 120, 70))
    s.bar(x + w // 2 - 30, y + 8, 60, h - 22, (190, 165, 110))
    for sx in (w // 2 - 24, w // 2 - 18, w // 2 - 12):
        s.bar(x + sx, y + 10, 3, 16, (240, 220, 160))
    s.bar(x + w // 2 - 26, y + 8, 16, 3, (240, 220, 160))
    s.line(x + 20, y + h - 20, x + 60, y + 12, (120, 70, 30))
    s.bar(x + 56, y + 10, 12, 8, (120, 70, 30))
    s.disc(x + w - 30, y + 16, 6, (200, 30, 36))
    s.disc(x + w - 30, y + 16, 2, (250, 250, 250))


def scene_boat(s, x, y, w, h):
    s.bar(x, y, w, h, (200, 225, 240))
    s.bar(x, y + h - 26, w, 26, (36, 90, 140))
    for wy in range(y + h - 22, y + h - 2, 7):
        for wx in range(0, w, 24):
            s.bar(x + wx + (wy % 16), wy, 14, 2, (140, 190, 225))
    s.poly([(x + 30, y + h - 26), (x + 44, y + h - 40), (x + w - 40, y + h - 40),
            (x + w - 26, y + h - 26)], (120, 70, 30))
    s.bar(x + 70, y + 2, 4, 10, (80, 50, 20))
    for dx in (60, 84, 108, 132):
        s.disc(x + dx, y + 6, 5, (232, 196, 150))
        s.bar(x + dx - 4, y + 10, 8, 8, (176, 30, 36))
    s.disc(x + w - 26, y + 12, 8, (250, 205, 110))


def scene_power(s, x, y, w, h):
    s.bar(x, y, w, h, (30, 32, 48))
    for bx in (30, 90, 150):
        s.line(x + bx, y + h - 6, x + bx + 12, y + 8, (140, 140, 150))
        s.line(x + bx + 24, y + h - 6, x + bx + 12, y + 8, (140, 140, 150))
        s.line(x + bx + 4, y + h - 20, x + bx + 20, y + h - 20, (140, 140, 150))
        s.line(x + bx, y + h - 6, x + bx + 24, y + h - 6, (140, 140, 150))
    s.poly([(x + 118, y + 6), (x + 106, y + 26), (x + 116, y + 26),
            (x + 104, y + 44), (x + 122, y + 20), (x + 112, y + 20),
            (x + 124, y + 6)], (255, 214, 60))
    for wy in range(y + 10, y + h - 8, 12):
        for wx in range(10, w - 10, 18):
            if (wx + wy) % 29 < 9:
                s.bar(x + wx, wy, 3, 4, (255, 214, 110))


def scene_fire(s, x, y, w, h):
    s.bar(x, y, w, h, (52, 48, 58))
    s.bar(x + 30, y + 16, 130, h - 16, (24, 22, 26))
    for wx in (44, 70, 96, 122, 148):
        s.bar(x + wx, y + 22, 8, 8, ORANGE)
    for fx in (50, 90, 130):
        s.tri(x + fx, y + 16, x + fx + 6, y + 2, x + fx + 12, y + 16, ORANGE)
        s.tri(x + fx + 3, y + 16, x + fx + 6, y + 8, x + fx + 9, y + 16,
              (255, 190, 60))
    for sx, sy, sr in ((60, 4, 4), (120, 2, 5), (160, 6, 4)):
        s.disc(x + sx, y + sy, sr, (140, 138, 134))
    s.bar(x + 10, y + h - 10, 50, 8, RED)
    s.disc(x + 20, y + h - 4, 3, (15, 15, 15))
    s.disc(x + 50, y + h - 4, 3, (15, 15, 15))


def scene_van(s, x, y, w, h):
    s.bar(x, y, w, h, (210, 216, 222))
    s.bar(x, y + h - 12, w, 12, (80, 80, 84))
    s.bar(x + 24, y + 12, 110, 26, (250, 250, 244))
    s.frame(x + 24, y + 12, 110, 26, GREY)
    s.poly([(x + 134, y + 16), (x + 158, y + 16), (x + 170, y + 38),
            (x + 134, y + 38)], (250, 250, 244))
    s.frame(x + 134, y + 16, 36, 22, GREY)
    s.disc(x + 48, y + h - 12, 7, (15, 15, 15))
    s.disc(x + 48, y + h - 12, 3, (180, 180, 180))
    s.disc(x + 146, y + h - 12, 7, (15, 15, 15))
    s.disc(x + 146, y + h - 12, 3, (180, 180, 180))
    s.bar(x + 66, y + 18, 6, 14, RED)
    s.bar(x + 61, y + 23, 16, 5, RED)


def scene_pope(s, x, y, w, h):
    s.bar(x, y, w, h, (240, 224, 190))
    s.bar(x + w // 2 - 2, y + 4, 4, 10, GOLD)
    s.bar(x + w // 2 - 6, y + 8, 12, 3, GOLD)
    s.bar(x + 10, y + 26, w - 20, 12, (250, 250, 244))
    s.bar(x + 14, y + 38, 4, h - 38, (120, 90, 60))
    s.bar(x + w - 18, y + 38, 4, h - 38, (120, 90, 60))
    for dx, c in ((30, RED), (65, TEAL), (100, (250, 250, 244)),
                  (135, GREEN), (170, PURPLE)):
        s.disc(x + dx, y + 20, 5, (232, 196, 150))
        s.bar(x + dx - 6, y + 25, 12, 6, c)
    s.bar(x + 97, y + 25, 6, 6, GOLD)
    for px in (45, 80, 120, 155):
        s.disc(x + px, y + 30, 2, (200, 200, 200))


def scene_orbit(s, x, y, w, h):
    s.bar(x, y, w, h, (10, 12, 28))
    for sx, sy in _stars(99, 18, w, h):
        s.dot(x + sx, y + sy, (220, 220, 200))
    s.disc(x + 52, y + h // 2 + 4, 14, (168, 150, 120))
    s.disc(x + 46, y + h // 2 - 2, 3, (140, 122, 96))
    s.disc(x + 58, y + h // 2 + 8, 2, (140, 122, 96))
    s.ring(x + 52, y + h // 2 + 4, 20, (150, 150, 160))
    s.ring(x + 52, y + h // 2 + 4, 23, (120, 120, 130))
    s.bar(x + 118, y + 10, 14, 8, (200, 200, 210))
    s.bar(x + 112, y + 12, 6, 4, (200, 200, 210))
    s.bar(x + 132, y + 12, 6, 4, (200, 200, 210))
    s.line(x + 118, y + 14, x + 90, y + 26, (200, 200, 210))


# --------------------------------------------------------------------- map
MAP_SPANS = [
    (0, 8, 14), (0, 45, 58), (1, 6, 20), (1, 42, 60),
    (2, 4, 22), (2, 26, 29), (2, 38, 40), (2, 42, 62),
    (3, 7, 24), (3, 27, 30), (3, 36, 36), (3, 38, 41), (3, 42, 62),
    (4, 8, 25), (4, 36, 37), (4, 38, 44), (4, 44, 62),
    (5, 8, 26), (5, 37, 45), (5, 46, 58),
    (6, 10, 27), (6, 37, 44), (6, 45, 56), (6, 60, 61),
    (7, 11, 27), (7, 37, 43), (7, 44, 48), (7, 52, 58), (7, 60, 60),
    (8, 12, 27), (8, 38, 42), (8, 44, 48), (8, 50, 52), (8, 53, 57),
    (9, 13, 27), (9, 37, 46), (9, 47, 49), (9, 50, 53), (9, 54, 57),
    (10, 13, 18), (10, 19, 26), (10, 37, 47), (10, 51, 52), (10, 54, 56),
    (11, 14, 19), (11, 38, 47), (11, 48, 48), (11, 51, 51), (11, 54, 56),
    (12, 15, 19), (12, 38, 48), (12, 54, 56),
    (13, 16, 20), (13, 39, 48), (13, 54, 56), (13, 55, 59),
    (14, 20, 23), (14, 40, 48), (14, 55, 60),
    (15, 20, 24), (15, 40, 47), (15, 56, 60),
    (16, 20, 25), (16, 41, 46), (16, 57, 60),
    (17, 21, 25), (17, 41, 45), (18, 21, 25), (18, 41, 45),
    (19, 22, 25), (19, 42, 44), (20, 22, 25), (20, 42, 44), (20, 55, 60),
    (21, 22, 25), (21, 42, 44), (21, 54, 61),
    (22, 23, 25), (22, 42, 44), (22, 54, 61),
    (23, 23, 25), (23, 42, 43), (23, 55, 60),
    (24, 23, 25), (24, 42, 43), (24, 56, 59),
    (25, 23, 24), (25, 57, 58), (25, 62, 63),
    (26, 24, 24), (26, 62, 62), (27, 24, 24), (28, 24, 24), (29, 24, 24),
]
# pins: (story number, grid col, grid row)
PINS = [(1, 37, 9), (2, 37, 6), (3, 41, 11), (4, 37, 4), (5, 52, 12),
        (6, 11, 11), (7, 58, 14), (8, 28, 18), (9, 51, 16), (10, 34, 8),
        (11, 38, 10), (12, 41, 9)]


def draw_map(s, x, y, w, h):
    s.bar(x, y, w, h, (196, 216, 228))
    s.frame(x, y, w, h, INK)
    cw, ch = w / 64.0, h / 30.0
    for r, c0, c1 in MAP_SPANS:
        for c in range(c0, c1 + 1):
            s.bar(x + int(c * cw) + 1, y + int(r * ch) + 1, 3, 3, (176, 150, 100))
    for n, c, r in PINS:
        px = x + int((c + 0.5) * cw)
        py = y + int((r + 0.5) * ch)
        s.disc(px, py, 6, RED)
        s.ring(px, py, 6, (250, 250, 250))
        s.text(str(n), px - 3 if n < 10 else px - 6, py - 4, SANS, 1,
               (255, 255, 255))

# ----------------------------------------------------------------- content
LEADS = [
    ("NO DEAL IN ANTALYA", scene_collapse,
     "1 - ANTALYA, TURKIYE - CLIMATE", "CONFIRMED",
     "COP31: NO DEAL",
     "The EU and others reject the final text, which never names fossil "
     "fuels. President Kurum: there is no consensus, so the decisions are "
     "not adopted.",
     "(Reuters, Sowetan, AsiaToday)"),
    ("186 DRONES OVERNIGHT", scene_kyiv,
     "2 - KYIV, UKRAINE - WAR", "REPORTED",
     "RUSSIA'S 186 DRONES",
     "Air defences down or jam 161 of 186 drones, 72 jet-powered. "
     "Strikes at 18 sites; a block in Dymer is destroyed, two hurt, "
     "seven feared trapped.",
     "(Ukrainian Air Force via Kyiv Independent)"),
    ("CLAIM VS DENIAL", scene_bahrain,
     "3 - MANAMA, BAHRAIN - IRAN WAR", "CLAIM",
     "Iran claims two US radars hit",
     "The IRGC says it destroyed two Patriot radars on Saturday night. "
     "Bahrain says its defences intercepted the attacks; a fire at a "
     "civilian site, no injuries.",
     "(Al Jazeera, Reuters)"),
]

CARDS = [
    ("SHIP ABLAZE", scene_ship, "GULF OF FINLAND - SEA",
     "SPARTA II", "Hit by two drones; it drifts in Finnish waters. "
     "16 crew safe.", "(Reuters)", "CONFIRMED"),
    ("723 SEATS", scene_vote, "HONG KONG - ELECTION",
     "HONG KONG", "856 candidates chase 723 seats. Turnout 98.79%, "
     "a record.", "(SCMP)", "CONFIRMED"),
    ("50 LAPS", scene_f1, "LAS VEGAS - FORMULA 1",
     "VERSTAPPEN", "35 lead changes; Norris +0.639s, Piastri 3rd.",
     "(F1)", "CONFIRMED"),
    ("720/9 DECLARED", scene_cricket, "WELLINGTON - CRICKET",
     "INDIA 720/9", "Rahul 136, Pant 128. Highest Test total ever in "
     "New Zealand.", "(ESPNcricinfo)", "CONFIRMED"),
    ("26 DEAD", scene_boat, "BAYELSA, NIGERIA - DISASTER",
     "BOAT TOLL", "Funeral barge capsizes on the Nun River. Recovery "
     "goes on.", "(RIA)", "REPORTED"),
    ("36 MISSING", scene_fire, "SERANG, INDONESIA - DISASTER",
     "CANDY FIRE", "Candy plant burns; 3 dead, 36 workers unaccounted "
     "for.", "(AP)", "REPORTED"),
    ("1,300 GUESTS", scene_pope, "VATICAN CITY - FAITH",
     "POPE 1,300", "Pope Leo XIV hosts 1,300 poor guests for lunch.", "(Vatican News)", "CONFIRMED"),
    ("3 KILLED", scene_van, "GAZA CITY - CEASEFIRE",
     "AID VAN HIT", "Three killed in Tal al-Hawa; WCK denies the van.",
     "(Reuters)", "REPORTED"),
    ("2-HR CUTS", scene_power, "TEHRAN, IRAN - ENERGY",
     "RATIONING", "Rolling cuts up to two hours a day from Sunday.",
     "(Straits Times)", "REPORTED"),
    ("MERCURY ORBIT", scene_orbit, "SPACE - ESA/JAXA",
     "MERCURY", "BepiColombo reaches Mercury after eight years.",
     "(Wires)", "CONFIRMED"),
]

BRIEFS = [
    (14, "KHARTOUM - Drones hit homes; army downs UAVs (AFP)"),
    (15, "WEMBY 50 - Spurs win 114-91; 50 pts, 19 reb (AP)"),
    (16, "KRYVYI RIH - 2 killed, 58 hurt in double-tap (AP)"),
    (17, "GAZA - 129 bodies found in central Gaza rubble (QNA)"),
    (18, "JERUSALEM - Eisenkot invites Likud talks (Reports)"),
    (19, "TRUMP - Reposts gold 'TrumpCare' card (Fox)"),
    (20, "ESTONIA - To shut Russia border 1 Dec (Reuters)"),
    (21, "EU PAYS UKRAINE - EUR 7.9bn, a record (Reports)"),
    (22, "GUPTA - Jailed 235 months over Pannun plot (AP)"),
    (23, "BOLSONARO - 71, still in intensive care (Reuters)"),
    (24, "TURIN - Zverev v Alcaraz ATP final, 17:00 (ATP)"),
    (25, "LIVERPOOL - Liverpool v Man Utd, 16:30 (PL)"),
    (26, "NEPAL - Balendra Shah starts India visit (Reports)"),
]

FIGURES = [
    ("186", "drones fired overnight"),
    ("161", "downed or suppressed"),
    ("0", "deals adopted at COP31"),
    ("720/9", "India's record total"),
    ("98.79%", "Hong Kong turnout"),
    ("1,300", "guests at Pope's lunch"),
]

REGIONS = [
    ("EUROPE 8", (31, 58, 110)),
    ("MIDDLE EAST 5", (160, 30, 34)),
    ("ASIA-PACIFIC 3", GOLD),
    ("AMERICAS 6", TEAL),
    ("AFRICA 2", GREEN),
    ("OCEANIA 1", PURPLE),
    ("WORLD 1", SLATE),
]

UTC_ITEMS = [
    "03:00 COP31 objections close",
    "06:00 plenary called",
    "08:00 161 of 186 downed",
    "09:00 HK polls close",
    "11:00 COP31 plenary slips",
    "13:30 press time",
]

DATECHECK = [
    "Left out on purpose. First reported Friday or Saturday, so not shown as Sunday's news: the Peru quake (Fri 20 Nov local) / Russia's",
    "400-drone barrage (Thu night-Fri) / missiles land in Poland (19-20 Nov) / Kyiv bridges hit (20 Nov) / ICJ Myanmar ruling (19 Nov) /",
    "Shenzhen summit (19 Nov) / Anthropic IPO priced $83 (19 Nov) / Kerch Bridge strike (17 Nov) / Nvidia SEC probe (Fri 20 Nov) / 'El Chapo",
    "Isidro' arrest (Sat 21 Nov). Tonight's real count: 186 drones, not 400. And COP31's deal was NOT adopted - the text failed at the plenary.",
]


# ------------------------------------------------------------------ layout
def kicker(s, x, y, label):
    w = s.twidth(label, SANS, 1) + 10
    s.bar(x, y, w, 14, RED)
    s.text(label, x + 5, y + 3, SANS, 1, (255, 255, 255))


CHIPCOL = {"CONFIRMED": GREEN, "REPORTED": (36, 90, 140),
           "CLAIM": GOLD, "PENDING": GREY, "ONGOING": TEAL}


def chip(s, x, y, text):
    w = s.twidth(text, SANS, 1) + 10
    s.bar(x, y, w, 13, CHIPCOL[text])
    s.text(text, x + 5, y + 3, SANS, 1, (255, 255, 255))
    return w


def draw_lead(s, x, y, w, lead):
    label, scene, place, tag, head, body, src = lead
    scene(s, x, y, w, 160)
    s.frame(x, y, w, 160, INK)
    chip(s, x + w - 4 - (s.twidth(tag, SANS, 1) + 10), y + 4, tag)
    s.text(place, x, y + 166, SANS, 1, RED)
    for i, ln in enumerate(wrap(head.upper(), SERIF, 2, w)):
        s.text(ln, x, y + 178 + i * 21, SERIF, 2, INK)
    bl = wrap(body, SANS, 1, w)[:4]
    s.para(bl, x, y + 224, SANS, 1, (40, 40, 44), lh=9)
    s.text(src, x, y + 264, SANS, 1, GREY)


def draw_card(s, x, y, w, card):
    label, scene, place, head, body, src, tag = card
    s.bar(x, y, w, 126, CREAM2)
    s.frame(x, y, w, 126, INK)
    scene(s, x + 1, y + 1, w - 2, 44)
    kicker(s, x + 5, y + 5, label)
    chip(s, x + w - 5 - (s.twidth(tag, SANS, 1) + 10), y + 28, tag)
    s.text(place, x + 4, y + 49, SANS, 1, RED)
    hl = wrap(head, SERIF, 2, w - 8)[:1]
    s.para(hl, x + 4, y + 59, SERIF, 2, INK, lh=18)
    s.para(wrap(body, SANS, 1, w - 8)[:2], x + 4, y + 89, SANS, 1,
           (40, 40, 44), lh=9)
    s.text(src, x + 4, y + 113, SANS, 1, GREY)


def build():
    s = Sheet()
    # top bar
    s.bar(0, 0, W, 20, INK)
    s.text("THE WORLD IN ONE DAY", 8, 6, SANS, 1, (247, 241, 227))
    rt = "26 STORIES - 7 REGIONS - EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    s.text(rt, W - 8 - s.twidth(rt, SANS, 1), 6, SANS, 1, (247, 241, 227))
    # masthead
    s.centre("SUNDAY 22 NOVEMBER 2026", 26, SERIF, 5, INK)
    s.centre("COP31 COLLAPSES, NO DEAL - IRAN CLAIMS RADAR HITS - "
             "186 DRONES OVER KYIV", 76, SANS, 2, RED)
    # region bar
    seg = 144
    for i, (name, col) in enumerate(REGIONS):
        x0 = 8 + i * seg
        s.bar(x0, 94, seg - 2, 16, col)
        s.centre(name, 98, SANS, 1, (255, 255, 255), x0, x0 + seg - 2)
    # UTC strip
    s.bar(0, 114, W, 15, INK)
    s.text("THE DAY IN UTC", 8, 118, SANS, 1, (255, 214, 110))
    ux = 8 + s.twidth("THE DAY IN UTC  ", SANS, 1)
    for i, it in enumerate(UTC_ITEMS):
        if i:
            ux = s.text(" - ", ux, 118, SANS, 1, (255, 214, 110))
        ux = s.text(it, ux, 118, SANS, 1, (247, 241, 227))
    # leads
    for i, lead in enumerate(LEADS):
        draw_lead(s, 8 + i * 256, 134, 248, lead)
    # numbers sidebar
    sx = 776
    s.bar(sx, 134, 240, 271, INK)
    s.text("THE DAY IN NUMBERS", sx + 10, 142, SANS, 1, (255, 214, 110))
    s.bar(sx + 10, 154, 220, 1, (70, 80, 120))
    for i, (num, lab) in enumerate(FIGURES):
        ny = 162 + i * 40
        s.text(num, sx + 10, ny, SERIF, 3, (255, 214, 110))
        s.text(lab, sx + 10, ny + 28, SANS, 1, (247, 241, 227))
        if i < 5:
            s.bar(sx + 10, ny + 38, 220, 1, (70, 80, 120))
    # day in ten header
    s.text("THE DAY IN TEN", 8, 412, SERIF, 2, INK)
    rh = "THE STORIES THAT MOVED THE WORLD TODAY"
    s.text(rh, W - 8 - s.twidth(rh, SANS, 1), 416, SANS, 1, GREY)
    s.bar(8, 426, W - 16, 1, INK)
    # cards
    for r in range(2):
        for c in range(5):
            draw_card(s, 8 + c * 203, 432 + r * 132, 195, CARDS[r * 5 + c])
    # bottom header
    s.text("WHERE IT HAPPENED", 8, 700, SERIF, 2, INK)
    s.text("ALSO ON SUNDAY - 13 MORE STORIES", 344, 700, SERIF, 2, INK)
    s.bar(8, 714, W - 16, 1, INK)
    # map + briefs
    draw_map(s, 8, 720, 322, 190)
    s.text("Pins match story numbers. 13 BepiColombo: Mercury - no pin on Earth.",
           8, 914, SANS, 1, GREY)
    bx = 344
    for col in range(2):
        items = BRIEFS[col * 7:(col + 1) * 7]
        for j, (n, t) in enumerate(items):
            s.text(str(n) + " " + t, bx + col * 336, 722 + j * 26, SANS, 1,
                   (30, 30, 34))
    # date check
    s.frame(8, 932, W - 16, 52, RED, t=2)
    s.bar(8, 932, 104, 52, RED)
    s.text("DATE", 14, 940, SANS, 2, (255, 255, 255))
    s.text("CHECK", 14, 956, SANS, 2, (255, 255, 255))
    s.para(DATECHECK, 120, 935, SANS, 1, (40, 40, 44), lh=9)
    # tag legend
    s.text("HOW TO READ THE TAGS - ONGOING still developing / REPORTED one "
           "source's claim / CLAIM a party's claim, contested / FORECAST "
           "still to happen.",
           8, 990, SANS, 1, GREY)
    # footer
    s.text("Sources: Reuters, AFP, AP, Al Jazeera, Kyiv Independent, "
           "info.gov.hk, China Daily Asia, formula1.com, ESPNcricinfo, "
           "RIA, Vanguard, Vatican News, Straits Times, RFE/RL.",
           8, 1004, SANS, 1, GREY)
    return s


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/output"
    s = build()
    save_png(out + "/entry.png", s.px)


if __name__ == "__main__":
    main()
