#!/usr/bin/env python3
"""폴더형 맵의 지형을 동쪽으로 넓힌다 (거울 복사).

경계선 SEAM(칸 경계 x 좌표) 서쪽은 그대로 두고, 동쪽은 경계선을 축으로 서쪽 지형을 좌우 대칭 복사한다.
대칭이라 경계에서 지형이 끊기지 않고, 원래 좌표(유닛·지점·지역·스크립트)도 바뀌지 않는다.
원래 경계선 동쪽에 있던 지형·장식물·지점은 사라진다 (원본 2번 미션은 주로 바깥 고원).

다루는 파일 (2026-10-14 원본 traynor02로 형식 확인):
  t3heightmap      머리 32, 꼭짓점마다 6바이트 (높이 u16, 절벽 높이 u16, 절벽 단계 u16)
  t3syncheightmap  머리 64, 꼭짓점마다 4바이트
  t3syncclifflevel 머리 32, 칸마다 u16 (64 = 1단계, 64의 배수가 아니면 경사로)
  t3cellflags      머리 32 (가로·세로는 24·28), 칸마다 1바이트
  t3synctextureinfo 머리+텍스처 이름, 칸마다 8바이트
  t3texturemasks   머리 64, 칸마다 256바이트 = 8줄 x 8층 x 8칸(4비트, 상위 니블 먼저)
  cellattribute_*  머리 4 (비트 수), 칸마다 1바이트
  t3fluffdoodad    머리 28, 항목마다 9바이트 (x, y float + 종류)
  t3terrain.xml    dim, uvtiling
  mapinfo          맵 크기(0x10), 카메라 경계(오른쪽)
  minimap.tga      가로로 다시 샘플링
  objects          경계 동쪽 지형 위 물체 삭제, 서쪽 장식물을 대칭 복사
t3vertcol(버텍스 색)과 t3hardtile은 형식을 몰라 그대로 둔다. 편집기에서 저장하면 sync 파일은 다시 만들어진다.
경사로는 rampList에 기하 정보가 있어 대칭 복사하지 않고 높은 쪽 지형으로 평평하게 메운다.
"""
import math, os, re, struct

import numpy as np


def _src_cell(x, seam):
    return x if x < seam else 2 * seam - 1 - x


def _src_vert(v, seam):
    return v if v <= seam else 2 * seam - v


def _grid(path, hdr, wo, ho, item, new_w, seam, vertex=False, fix=None):
    d = open(path, 'rb').read()
    w = struct.unpack('<I', d[wo:wo + 4])[0]
    h = struct.unpack('<I', d[ho:ho + 4])[0]
    body = np.frombuffer(d[hdr:hdr + w * h * item], dtype=np.uint8).reshape(h, w, item)
    tail = d[hdr + w * h * item:]
    nw = new_w + 1 if vertex else new_w
    src = [(_src_vert if vertex else _src_cell)(x, seam) for x in range(nw)]
    out = body[:, src, :].copy()
    if fix:
        fix(out)
    head = bytearray(d[:hdr])
    head[wo:wo + 4] = struct.pack('<I', nw)
    open(path, 'wb').write(bytes(head) + out.tobytes() + tail)
    return w, h


def expand_east(map_dir, seam, new_w, flatten_ramps=True):
    P = lambda n: os.path.join(map_dir, n)
    old_w, h = struct.unpack('<II', open(P('mapinfo'), 'rb').read()[0x10:0x18])
    assert seam < old_w <= new_w and new_w <= 2 * seam, (seam, old_w, new_w)

    # 경사로 칸 (새 영역에서 평평하게 메울 대상)
    cl = np.frombuffer(open(P('t3syncclifflevel'), 'rb').read()[32:32 + old_w * h * 2], dtype='<u2').reshape(h, old_w)
    ramp = cl % 64 != 0
    ramp_new = [(y, x) for x in range(seam, new_w) for y in range(h) if ramp[y, _src_cell(x, seam)]] if flatten_ramps else []
    hi = {}
    for y, x in ramp_new:
        sx = _src_cell(x, seam)
        hi[(y, x)] = (cl[y, sx] // 64 + 1) * 64  # 높은 쪽 단계

    def fix_cliff(a):
        v = a.view('<u2').reshape(a.shape[0], a.shape[1])
        for (y, x), lv in hi.items():
            v[y, x] = lv

    _grid(P('t3syncclifflevel'), 32, 8, 12, 2, new_w, seam, fix=fix_cliff)

    # 꼭짓점: 경사로 칸에 닿은 새 꼭짓점은 같은 단계의 평지 꼭짓점 값으로
    hm = np.frombuffer(open(P('t3heightmap'), 'rb').read()[32:32 + (old_w + 1) * (h + 1) * 6], dtype='<u2').reshape(h + 1, old_w + 1, 3)
    plain = {}
    for y in range(h + 1):
        for x in range(old_w + 1):
            lv = int(hm[y, x, 2])
            cells = [(yy, xx) for yy in (y - 1, y) for xx in (x - 1, x) if 0 <= yy < h and 0 <= xx < old_w]
            if lv not in plain and cells and all(not ramp[c] and cl[c] == lv * 64 for c in cells):
                plain[lv] = (int(hm[y, x, 1]), lv)
    ramp_verts = set()
    for y, x in ramp_new:
        ramp_verts |= {(y, x), (y + 1, x), (y, x + 1), (y + 1, x + 1)}

    def fix_hm(a):
        v = a.view('<u2').reshape(a.shape[0], a.shape[1], 3)
        for (y, x) in ramp_verts:
            lv = max(hi.get((yy, xx), 0) for yy in (y - 1, y) for xx in (x - 1, x)) // 64
            if lv in plain:
                v[y, x, 1], v[y, x, 2] = plain[lv]

    _grid(P('t3heightmap'), 32, 8, 12, 6, new_w, seam, vertex=True, fix=fix_hm)
    _grid(P('t3syncheightmap'), 64, 8, 12, 4, new_w, seam, vertex=True)
    _grid(P('t3cellflags'), 32, 24, 28, 1, new_w, seam)

    d = open(P('t3synctextureinfo'), 'rb').read()
    pre = len(d) - old_w * h * 8
    _grid(P('t3synctextureinfo'), pre, 8, 12, 8, new_w, seam)

    for n in os.listdir(map_dir):
        if n.startswith('cellattribute_'):
            p = P(n)
            d = open(p, 'rb').read()
            body = np.frombuffer(d[4:4 + old_w * h], dtype=np.uint8).reshape(h, old_w)
            out = body[:, [_src_cell(x, seam) for x in range(new_w)]]
            open(p, 'wb').write(struct.pack('<I', new_w * h * 8) + out.tobytes() + d[4 + old_w * h:])

    # 텍스처 마스크: 칸 단위로 옮기고 새 영역은 칸 안 가로 순서를 뒤집는다
    d = open(P('t3texturemasks'), 'rb').read()
    cells = np.frombuffer(d[64:64 + old_w * h * 256], dtype=np.uint8).reshape(h, old_w, 8, 8, 4)
    nib = np.stack([cells >> 4, cells & 15], -1).reshape(h, old_w, 8, 8, 8)  # 줄, 층, 칸
    out = nib[:, [_src_cell(x, seam) for x in range(new_w)]].copy()
    out[:, seam:] = out[:, seam:, :, :, ::-1]
    packed = (out[..., 0::2] << 4) | out[..., 1::2]
    head = bytearray(d[:64])
    head[12:16] = struct.pack('<I', new_w * 8)
    open(P('t3texturemasks'), 'wb').write(bytes(head) + packed.astype(np.uint8).tobytes() + d[64 + old_w * h * 256:])

    # 잔디 같은 자잘한 장식: 경계 동쪽 것을 지우고 서쪽 것을 대칭 복사
    d = open(P('t3fluffdoodad'), 'rb').read()
    n = struct.unpack('<I', d[24:28])[0]
    ents = [d[28 + 9 * i:37 + 9 * i] for i in range(n)]
    keep = []
    for e in ents:
        x, y, k = struct.unpack('<ffB', e)
        if x < seam:
            keep.append(e)
            mx = 2 * seam - x
            if seam <= mx < new_w:
                keep.append(struct.pack('<ffB', mx, y, k))
    open(P('t3fluffdoodad'), 'wb').write(d[:24] + struct.pack('<I', len(keep)) + b''.join(keep) + d[28 + 9 * n:])

    t = open(P('t3terrain.xml'), encoding='utf-8', newline='').read()
    t = t.replace(f'dim="{old_w + 1} {h + 1} "', f'dim="{new_w + 1} {h + 1} "', 1)
    m = re.search(r'uvtiling="([-\d.e+]+) ', t)
    uv = float(m[1]) * new_w / old_w
    t = t[:m.start(1)] + f'{uv:.6f}' + t[m.end(1):]
    open(P('t3terrain.xml'), 'w', encoding='utf-8', newline='').write(t)

    mi = bytearray(open(P('mapinfo'), 'rb').read())
    mi[0x10:0x14] = struct.pack('<I', new_w)
    i = mi.index(b'MarSara\x00') + 8  # 타일셋 이름 뒤: 카메라 경계 왼, 아래, 오른, 위
    left, bottom, right, top = struct.unpack('<4I', mi[i:i + 16])
    new_right = min(new_w - left, 2 * seam - left)
    mi[i + 8:i + 12] = struct.pack('<I', new_right)
    open(P('mapinfo'), 'wb').write(bytes(mi))

    _minimap(P('minimap.tga'), old_w, new_w, seam)
    removed, added = _objects(P('objects'), seam, new_w)
    return dict(old_w=old_w, new_w=new_w, h=h, camera=(left, bottom, new_right, top),
                ramp_cells=len(ramp_new), removed=removed, mirrored_doodads=added)


def _minimap(path, old_w, new_w, seam):
    d = open(path, 'rb').read()
    idl = d[0]
    tw, th = struct.unpack('<HH', d[12:16])
    bpp = d[16] // 8
    off = 18 + idl
    img = np.frombuffer(d[off:off + tw * th * bpp], dtype=np.uint8).reshape(th, tw, bpp)
    cols = []
    for u in range(tw):
        x = (u + 0.5) * new_w / tw
        sx = x if x < seam else 2 * seam - x
        cols.append(min(tw - 1, int(sx * tw / old_w)))
    out = img[:, cols]
    open(path, 'wb').write(d[:off] + out.tobytes() + d[off + tw * th * bpp:])


def _objects(path, seam, new_w):
    o = open(path, encoding='utf-8', newline='').read()
    blocks = list(re.finditer(r'    <(Object\w+) [^>]*?Position="([-\d.e]+),([-\d.e]+),[^"]*"[^>]*?(/>|>.*?</\1>)\r?\n', o, re.S))
    ids = [int(x) for x in re.findall(r' Id="(\d+)"', o)]
    nid = max(ids) + 1
    out, last, removed, add = [], 0, 0, []
    for m in blocks:
        x = float(m[2])
        out.append(o[last:m.start()])
        last = m.end()
        if x >= seam:
            removed += 1
            continue
        out.append(m[0])
        mx = 2 * seam - x
        if m[1] == 'ObjectDoodad' and seam <= mx < new_w:
            b = m[0]
            b = re.sub(r'Position="[-\d.e]+,', f'Position="{mx:.4f},', b, 1)
            r = re.search(r'Rotation="([-\d.e]+)"', b)
            if r:
                b = b.replace(r[0], f'Rotation="{(math.pi - float(r[1])) % (2 * math.pi):.4f}"', 1)
            b = re.sub(r' Id="\d+"', f' Id="{nid}"', b, 1)
            nid += 1
            add.append(b)
    out.append(o[last:])
    s = ''.join(out)
    end = s.rindex('</PlacedObjects>')
    s = s[:end] + ''.join(add) + s[end:]
    open(path, 'w', encoding='utf-8', newline='').write(s)
    return removed, len(add)
