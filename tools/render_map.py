#!/usr/bin/env python3
"""폴더형 맵의 지형(절벽 높이)과 유닛 위치를 그림으로 그린다. 기획용 참고 그림.

사용: python3 tools/render_map.py <맵 폴더> <출력.png> [배율]
"""
import re, struct, sys
from PIL import Image, ImageDraw

COLS = {1: (0, 120, 255), 2: (255, 0, 0), 3: (220, 220, 220), 4: (0, 200, 0), 5: (255, 140, 0),
        6: (160, 0, 0), 7: (255, 0, 255), 8: (150, 90, 40), 9: (255, 255, 0), 10: (255, 120, 120),
        11: (0, 255, 255), 12: (128, 0, 255)}
LEVEL = {0: (60, 50, 40), 1: (120, 95, 70), 2: (170, 135, 95), 3: (215, 185, 140)}


def grid(path):
    d = open(path, 'rb').read()
    w, h = struct.unpack('<II', d[8:16])
    return w, h, d


def render(mapdir, out, s=4, marks=()):
    w, h, d = grid(mapdir + '/t3syncclifflevel')
    cl = struct.unpack(f'<{w*h}H', d[32:32 + 2 * w * h])
    _, _, cf = grid(mapdir + '/t3cellflags')
    cf = cf[32:]
    mi = open(mapdir + '/mapinfo', 'rb').read()
    im = Image.new('RGB', (w * s, h * s))
    dr = ImageDraw.Draw(im)
    for y in range(h):
        for x in range(w):
            c = LEVEL.get(cl[y * w + x] // 64, (255, 255, 255))
            if cf[y * w + x] & 1:  # 시험: 비트 1 = 이동 불가로 추정
                c = tuple(v // 2 for v in c)
            dr.rectangle((x * s, (h - 1 - y) * s, x * s + s - 1, (h - y) * s - 1), fill=c)
    o = open(mapdir + '/objects', encoding='utf-8').read()
    for m in re.finditer(r'<ObjectUnit [^>]*?Position="([-\d.]+),([-\d.]+),[^"]*"[^>]*?UnitType="(\w+)" Player="(\d+)"', o):
        x, y, p = float(m[1]), float(m[2]), int(m[4])
        if p in COLS:
            X, Y = x * s, (h - y) * s
            dr.ellipse((X - 3, Y - 3, X + 3, Y + 3), fill=COLS[p], outline=(0, 0, 0))
    for g in range(0, max(w, h) + 1, 10):
        col = (90, 90, 90) if g % 20 else (40, 40, 40)
        dr.line((g * s, 0, g * s, h * s), fill=col)
        dr.line((0, (h - g) * s, w * s, (h - g) * s), fill=col)
        if g % 20 == 0:
            dr.text((g * s + 2, h * s - 12), str(g), fill=(255, 255, 255))
            dr.text((2, (h - g) * s - 12), str(g), fill=(255, 255, 255))
    for x, y, label in marks:
        X, Y = x * s, (h - y) * s
        dr.rectangle((X - 8, Y - 8, X + 8, Y + 8), outline=(255, 255, 255), width=2)
        dr.text((X + 10, Y - 6), label, fill=(255, 255, 255))
    im.save(out)
    print(out, w, h)


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 4)
