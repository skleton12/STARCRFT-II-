#!/usr/bin/env python3
"""폴더형 맵을 동쪽으로 넓히고, 넓힌 땅을 새 배치도(절벽 단계 격자)로 직접 만든다.

expand_map.py(거울 복사)와 달리 새 땅은 원본을 복사하지 않는다 (사용자 지시 2026-10-15: 반전 말고 새로 구성).
경계선 SEAM 서쪽은 원본 그대로, 동쪽은 layout(x, y) → 절벽 단계(0~3)로 그린다.

새 칸·꼭짓점 값은 원본 맵에서 뽑은 '단계별 대표값'을 쓴다 (2026-10-15 traynor02로 확인한 규칙):
  - 꼭짓점 절벽 단계 = 맞닿은 칸 단계 중 최댓값, 높이·절벽 높이·동기 높이 = 그 단계 평지 꼭짓점의 중앙값
  - 칸 표시(t3cellflags) = 다른 단계와 맞닿으면 3(절벽), 아니면 2
  - 텍스처(마스크·동기 정보) = 그 단계 평지 칸 중 가장 흔한 텍스처
경사로는 만들지 않는다 (단계가 다른 땅끼리는 절벽으로 막힘). 새 땅에는 장식물이 없다.
"""
import os, re, struct
from collections import Counter

import numpy as np


def _read(path, hdr, w, h, item):
    d = open(path, 'rb').read()
    a = np.frombuffer(d[hdr:hdr + w * h * item], dtype=np.uint8).reshape(h, w, item).copy()
    return d[:hdr], a, d[hdr + w * h * item:]


def _write(path, head, arr, tail, dims):
    head = bytearray(head)
    for off, val in dims:
        head[off:off + 4] = struct.pack('<I', val)
    open(path, 'wb').write(bytes(head) + arr.tobytes() + tail)


def _widen(a, new_w, fill=0):
    h, w = a.shape[:2]
    out = np.full((h, new_w) + a.shape[2:], fill, dtype=a.dtype)
    out[:, :w] = a
    return out


def build_east(map_dir, seam, new_w, layout, camera_right):
    P = lambda n: os.path.join(map_dir, n)
    old_w, h = struct.unpack('<II', open(P('mapinfo'), 'rb').read()[0x10:0x18])
    assert seam <= old_w <= new_w, (seam, old_w, new_w)
    W, VW, VH = new_w, new_w + 1, h + 1

    hc, cl, tc = _read(P('t3syncclifflevel'), 32, old_w, h, 2)
    hf, cf, tf = _read(P('t3cellflags'), 32, old_w, h, 1)
    hh, hm, th = _read(P('t3heightmap'), 32, old_w + 1, h + 1, 6)
    hs, sh, ts = _read(P('t3syncheightmap'), 64, old_w + 1, h + 1, 4)
    d = open(P('t3synctextureinfo'), 'rb').read()
    pre = len(d) - old_w * h * 8
    hx, sti, tx = _read(P('t3synctextureinfo'), pre, old_w, h, 8)
    hk, mk, tk = _read(P('t3texturemasks'), 64, old_w, h, 256)

    clv = cl.view('<u2')[..., 0]
    lv = clv // 64
    ramp = clv % 64 != 0
    hmv = hm.view('<u2')
    shv = sh.view('<u4')[..., 0]

    # 단계별 대표값 (평지: 3x3 이웃이 모두 같은 단계, 경사로 아님)
    flat = np.zeros_like(lv, dtype=bool)
    flat[1:-1, 1:-1] = True
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            flat[1:-1, 1:-1] &= lv[1 + dy:h - 1 + dy, 1 + dx:old_w - 1 + dx] == lv[1:-1, 1:-1]
    flat &= ~ramp
    tmpl_cell, tmpl_vert = {}, {}
    for L in range(4):
        ys, xs = np.nonzero(flat & (lv == L))
        if len(ys) == 0:
            continue
        common = Counter(mk[y, x].tobytes() for y, x in zip(ys, xs)).most_common(1)[0][0]
        y, x = next((y, x) for y, x in zip(ys, xs) if mk[y, x].tobytes() == common)
        tmpl_cell[L] = (mk[y, x].copy(), sti[y, x].copy(), cf[y, x, 0])
        vs = [(y, x) for y, x in zip(ys, xs)]
        a = np.array([hmv[y, x] for y, x in vs])
        s = np.array([shv[y, x] for y, x in vs])
        tmpl_vert[L] = (int(np.median(a[:, 0])), int(np.median(a[:, 1])), int(np.median(s)))

    # 새 단계 격자
    LV = _widen(lv, W)
    for x in range(seam, W):
        for y in range(h):
            LV[y, x] = layout(x, y)
    assert all(L in tmpl_cell for L in np.unique(LV[:, seam:])), '원본에 없는 단계를 썼음'

    CL = _widen(cl, W)
    CF = _widen(cf, W)
    STI = _widen(sti, W)
    MK = _widen(mk, W)
    CLv = CL.view('<u2')[..., 0]
    for x in range(seam, W):
        for y in range(h):
            L = int(LV[y, x])
            CLv[y, x] = L * 64
            nb = LV[max(0, y - 1):y + 2, max(0, x - 1):x + 2]
            CF[y, x, 0] = 3 if (nb != L).any() else 2
            MK[y, x] = tmpl_cell[L][0]
            STI[y, x] = tmpl_cell[L][1]

    HM = _widen(hm, VW)
    SH = _widen(sh, VW)
    HMv = HM.view('<u2')
    SHv = SH.view('<u4')[..., 0]
    for vx in range(seam, VW):
        for vy in range(VH):
            cells = [LV[cy, cx] for cy in (vy - 1, vy) for cx in (vx - 1, vx) if 0 <= cy < h and 0 <= cx < W]
            e = int(max(cells))
            if vx == seam and int(HMv[vy, vx, 2]) == e:
                continue  # 경계 꼭짓점은 단계가 같으면 원본 유지
            a, b, s = tmpl_vert[e]
            if vx > seam:
                HMv[vy, vx, 0] = a
            HMv[vy, vx, 1], HMv[vy, vx, 2] = b, e
            SHv[vy, vx] = s

    _write(P('t3syncclifflevel'), hc, CL, tc, [(8, W)])
    _write(P('t3cellflags'), hf, CF, tf, [(24, W)])
    _write(P('t3heightmap'), hh, HM, th, [(8, VW)])
    _write(P('t3syncheightmap'), hs, SH, ts, [(8, VW)])
    _write(P('t3synctextureinfo'), hx, STI, tx, [(8, W)])
    _write(P('t3texturemasks'), hk, MK, tk, [(12, W * 8)])
    for n in os.listdir(map_dir):
        if n.startswith('cellattribute_'):
            d = open(P(n), 'rb').read()
            a = np.frombuffer(d[4:4 + old_w * h], np.uint8).reshape(h, old_w)
            open(P(n), 'wb').write(struct.pack('<I', W * h * 8) + _widen(a, W).tobytes() + d[4 + old_w * h:])

    # 잔디 장식: 경계 동쪽 것은 지운다
    d = open(P('t3fluffdoodad'), 'rb').read()
    n = struct.unpack('<I', d[24:28])[0]
    keep = [d[28 + 9 * i:37 + 9 * i] for i in range(n) if struct.unpack('<f', d[28 + 9 * i:32 + 9 * i])[0] < seam]
    open(P('t3fluffdoodad'), 'wb').write(d[:24] + struct.pack('<I', len(keep)) + b''.join(keep) + d[28 + 9 * n:])

    t = open(P('t3terrain.xml'), encoding='utf-8', newline='').read()
    t = t.replace(f'dim="{old_w + 1} {h + 1} "', f'dim="{VW} {VH} "', 1)
    m = re.search(r'uvtiling="([-\d.e+]+) ', t)
    t = t[:m.start(1)] + f'{float(m[1]) * W / old_w:.6f}' + t[m.end(1):]
    open(P('t3terrain.xml'), 'w', encoding='utf-8', newline='').write(t)

    mi = bytearray(open(P('mapinfo'), 'rb').read())
    mi[0x10:0x14] = struct.pack('<I', W)
    i = mi.index(b'MarSara\x00') + 8  # 카메라 경계: 왼, 아래, 오른, 위
    mi[i + 8:i + 12] = struct.pack('<I', camera_right)
    camera = struct.unpack('<4I', mi[i:i + 16])
    open(P('mapinfo'), 'wb').write(bytes(mi))

    _minimap(P('minimap.tga'), lv, LV, old_w, W)
    removed = _remove_objects(P('objects'), seam)
    return dict(old_w=old_w, new_w=W, h=h, camera=camera, removed=removed,
                levels={int(L): int((LV[:, seam:] == L).sum()) for L in np.unique(LV[:, seam:])})


def _minimap(path, lv, LV, old_w, W):
    d = open(path, 'rb').read()
    tw, th = struct.unpack('<HH', d[12:16])
    bpp = d[16] // 8
    off = 18 + d[0]
    img = np.frombuffer(d[off:off + tw * th * bpp], np.uint8).reshape(th, tw, bpp)
    flip = not (d[17] & 0x20)  # TGA 기본은 아래에서 위로
    h = lv.shape[0]
    rows = lambda v: (h - 1 - min(h - 1, int((v + 0.5) * h / th))) if not flip else min(h - 1, int((v + 0.5) * h / th))
    # 원본 미니맵에서 단계별 평균색
    col = {}
    for L in np.unique(LV):
        px = [img[v, u] for v in range(th) for u in range(tw) if lv[rows(v), min(old_w - 1, int((u + 0.5) * old_w / tw))] == L]
        col[int(L)] = np.mean(px, axis=0).astype(np.uint8) if px else np.zeros(bpp, np.uint8)
    out = np.zeros_like(img)
    for v in range(th):
        y = rows(v)
        for u in range(tw):
            x = min(W - 1, int((u + 0.5) * W / tw))
            if x < old_w and LV[y, x] == lv[y, min(x, old_w - 1)] and x < old_w:
                out[v, u] = img[v, min(tw - 1, int((x + 0.5) * tw / old_w))]
            else:
                out[v, u] = col[int(LV[y, x])]
    open(path, 'wb').write(d[:off] + out.tobytes() + d[off + tw * th * bpp:])


def _remove_objects(path, seam):
    o = open(path, encoding='utf-8', newline='').read()
    n = 0

    def drop(m):
        nonlocal n
        if float(m[2]) >= seam:
            n += 1
            return ''
        return m[0]
    o = re.sub(r'    <(Object\w+) [^>]*?Position="([-\d.e]+),[^"]*"[^>]*?(/>|>.*?</\1>)\r?\n', drop, o, flags=re.S)
    open(path, 'w', encoding='utf-8', newline='').write(o)
    return n
