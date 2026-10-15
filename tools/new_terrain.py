#!/usr/bin/env python3
"""폴더형 맵을 동쪽으로 넓히고, 넓힌 땅을 새 배치도(절벽 단계 격자)로 직접 만든다.

expand_map.py(거울 복사)와 달리 새 땅은 원본을 복사하지 않는다 (사용자 지시 2026-10-15: 반전 말고 새로 구성).
경계선 SEAM 서쪽은 원본 그대로, 동쪽은 layout(x, y) → 절벽 단계(0~3)로 그린다.

새 칸·꼭짓점 값은 원본 맵에서 뽑은 '단계별 대표값'을 쓴다 (2026-10-15 traynor02로 확인한 규칙):
  - 꼭짓점 절벽 단계 = 맞닿은 칸 단계 중 최댓값, 높이·절벽 높이·동기 높이 = 그 단계 평지 꼭짓점의 중앙값
  - 칸 표시(t3cellflags) = 다른 단계와 맞닿으면 3(절벽), 아니면 2
  - 텍스처(마스크·동기 정보) = 그 단계 평지 칸 중 가장 흔한 텍스처
carve: 원본 쪽 칸을 직사각형으로 다시 그린다 [(x0, y0, x1, y1, 단계)] (양 끝 포함). 길을 뚫을 때 쓰고, 그 안 장식물은 지운다.
relief(x, y, 단계) → 꼭짓점 높이 변화(게임 단위). 기복을 준다. 동기 높이는 원본에서 맞춘 1차식으로 다시 계산.
texnoise: 사용 안 함 (2026-10-15 텍스처 형식 바로잡음. 새 땅은 단계별 평균 텍스처 비중으로 칠하고 세부는 편집기에서).
scatter(LV, seam) → [(장식물 종류, x, y, 회전, 크기)]. 원본에 있는 같은 종류 장식물을 본떠 새로 놓는다.
tidy=(x_min, (y, x) 시작 칸): x_min~seam 사이 원본 땅 중 시작 칸에서 걸어서 못 가는 낮은 자투리를 3단계 고원으로 메운다.
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


def build_east(map_dir, seam, new_w, layout, camera_right, carve=(), relief=None, texnoise=None, scatter=None, tidy=None):
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
    hk, planes, tk = load_masks(P('t3texturemasks'))

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
    tmpl_cell, tmpl_vert, sync_fit = {}, {}, {}
    for L in range(4):
        ys, xs = np.nonzero(flat & (lv == L))
        if len(ys) == 0:
            continue
        blocks = np.stack([planes[:, 8 * y:8 * y + 8, 8 * x:8 * x + 8].mean(axis=(1, 2)) for y, x in zip(ys, xs)])
        weights = np.clip(np.rint(blocks.mean(0)), 0, 15).astype(np.uint8)  # 텍스처 8장의 평균 비중
        key = Counter(sti[y, x].tobytes() for y, x in zip(ys, xs)).most_common(1)[0][0]
        tmpl_cell[L] = (weights, np.frombuffer(key, np.uint8).copy(), 2)
        a = np.array([hmv[y, x] for y, x in zip(ys, xs)], dtype=float)
        sv = np.array([shv[y, x] for y, x in zip(ys, xs)], dtype=float)
        tmpl_vert[L] = (int(np.median(a[:, 0])), int(np.median(a[:, 1])), int(np.median(sv)))
        A = np.c_[a[:, 0], a[:, 1], np.ones(len(a))]
        sync_fit[L] = np.linalg.lstsq(A, sv, rcond=None)[0]  # 동기 높이 ≈ 높이·절벽 높이의 1차식
    qscale = float(re.search(r'quantizeScale="([-\d.e+]+)"', open(P('t3terrain.xml'), encoding='utf-8').read())[1])

    # 새 단계 격자
    LV = _widen(lv, W)
    for x in range(seam, W):
        for y in range(h):
            LV[y, x] = layout(x, y)
    redo = {(y, x) for x in range(seam, W) for y in range(h)}
    for x0, y0, x1, y1, L in carve:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                LV[y, x] = L
                redo.add((y, x))
    if tidy:
        x_min, start = tidy
        from collections import deque
        seen, q = {start}, deque([start])
        while q:
            y, x = q.popleft()
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < W and (ny, nx) not in seen:
                    ra = x < old_w and ramp[y, x]
                    rb = nx < old_w and ramp[ny, nx]
                    if LV[y, x] == LV[ny, nx] or ra or rb:
                        seen.add((ny, nx))
                        q.append((ny, nx))
        for x in range(x_min, seam):
            for y in range(h):
                if LV[y, x] < 3 and (y, x) not in seen and not ramp[y, x]:
                    LV[y, x] = 3
                    redo.add((y, x))
    assert all(L in tmpl_cell for L in np.unique([LV[c] for c in redo])), '원본에 없는 단계를 썼음'
    carved = {c for c in redo if c[1] < seam}
    for y, x in list(carved):  # 이웃 칸의 절벽 표시도 다시 계산
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if 0 <= y + dy < h and 0 <= x + dx < W:
                    redo.add((y + dy, x + dx))

    CL = _widen(cl, W)
    CF = _widen(cf, W)
    STI = _widen(sti, W)
    PL = np.zeros((8, h * 8, W * 8), np.uint8)
    PL[:, :, :old_w * 8] = planes
    CLv = CL.view('<u2')[..., 0]
    for y, x in redo:
        L = int(LV[y, x])
        nb = LV[max(0, y - 1):y + 2, max(0, x - 1):x + 2]
        CF[y, x, 0] = 3 if (nb != L).any() else 2
        if x >= seam or (y, x) in carved:
            CLv[y, x] = L * 64
            PL[:, 8 * y:8 * y + 8, 8 * x:8 * x + 8] = tmpl_cell[L][0][:, None, None]
            STI[y, x] = tmpl_cell[L][1]

    HM = _widen(hm, VW)
    SH = _widen(sh, VW)
    HMv = HM.view('<u2')
    SHv = SH.view('<u4')[..., 0]
    verts = {(vy, vx) for vx in range(seam, VW) for vy in range(VH)}
    for y, x in carved:
        verts |= {(y, x), (y + 1, x), (y, x + 1), (y + 1, x + 1)}
    for vy, vx in verts:
        cells = [LV[cy, cx] for cy in (vy - 1, vy) for cx in (vx - 1, vx) if 0 <= cy < h and 0 <= cx < W]
        e = int(max(cells))
        if vx <= seam and int(HMv[vy, vx, 2]) == e:
            continue  # 원본 쪽 꼭짓점은 단계가 같으면 그대로
        a, b, s = tmpl_vert[e]
        if vx > seam:
            if relief:
                a = int(np.clip(a + relief(vx, vy, e) / qscale, 0, 65535))
            HMv[vy, vx, 0] = a
        else:
            a = int(HMv[vy, vx, 0])
        HMv[vy, vx, 1], HMv[vy, vx, 2] = b, e
        c = sync_fit[e]
        SHv[vy, vx] = int(c[0] * a + c[1] * b + c[2]) if relief else s

    _write(P('t3syncclifflevel'), hc, CL, tc, [(8, W)])
    _write(P('t3cellflags'), hf, CF, tf, [(24, W)])
    _write(P('t3heightmap'), hh, HM, th, [(8, VW)])
    _write(P('t3syncheightmap'), hs, SH, ts, [(8, VW)])
    _write(P('t3synctextureinfo'), hx, STI, tx, [(8, W)])
    save_masks(P('t3texturemasks'), hk, PL, tk)
    for n in os.listdir(map_dir):
        if n.startswith('cellattribute_'):
            d = open(P(n), 'rb').read()
            a = np.frombuffer(d[4:4 + old_w * h], np.uint8).reshape(h, old_w)
            a = _widen(a, W)
            for y, x in carved:
                a[y, x] = 0  # 뚫은 길은 이동·건설 가능
            open(P(n), 'wb').write(struct.pack('<I', W * h * 8) + a.tobytes() + d[4 + old_w * h:])

    # 잔디 장식: 경계 동쪽 것은 지운다
    d = open(P('t3fluffdoodad'), 'rb').read()
    n = struct.unpack('<I', d[24:28])[0]
    keep = [d[28 + 9 * i:37 + 9 * i] for i in range(n) if struct.unpack('<f', d[28 + 9 * i:32 + 9 * i])[0] < seam]
    open(P('t3fluffdoodad'), 'wb').write(d[:24] + struct.pack('<I', len(keep)) + b''.join(keep) + d[28 + 9 * n:])

    t = open(P('t3terrain.xml'), encoding='utf-8', newline='').read()
    t = t.replace(f'dim="{old_w + 1} {h + 1} "', f'dim="{VW} {VH} "', 1)
    m = re.search(r'uvtiling="([-\d.e+]+) ', t)
    t = t[:m.start(1)] + f'{float(m[1]) * W / old_w:.6f}' + t[m.end(1):]
    t = _terrain_lists(t, old_w, W, h, hm.view('<u2')[..., 2], HMv[..., 2], seam, carved)
    open(P('t3terrain.xml'), 'w', encoding='utf-8', newline='').write(t)

    mi = bytearray(open(P('mapinfo'), 'rb').read())
    mi[0x10:0x14] = struct.pack('<I', W)
    i = mi.index(b'MarSara\x00') + 8  # 카메라 경계: 왼, 아래, 오른, 위
    mi[i + 8:i + 12] = struct.pack('<I', camera_right)
    camera = struct.unpack('<4I', mi[i:i + 16])
    open(P('mapinfo'), 'wb').write(bytes(mi))

    _vertcol(P('t3vertcol'), seam, W, h)
    _minimap(P('minimap.tga'), lv, LV, old_w, W)
    removed = _remove_objects(P('objects'), seam, carve, carved)
    placed = _add_doodads(P('objects'), scatter(LV, seam)) if scatter else 0
    return dict(old_w=old_w, new_w=W, h=h, camera=camera, removed=removed, carved=len(carved), doodads=placed,
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


def _remove_objects(path, seam, carve=(), cells=()):
    o = open(path, encoding='utf-8', newline='').read()
    n = 0

    def drop(m):
        nonlocal n
        x, y = float(m[2]), float(m[3])
        if x >= seam or (m[1] == 'ObjectDoodad' and ((int(y), int(x)) in cells or any(x0 <= x <= x1 + 1 and y0 <= y <= y1 + 1 for x0, y0, x1, y1, _ in carve))):
            n += 1
            return ''
        return m[0]
    o = re.sub(r'    <(Object\w+) [^>]*?Position="([-\d.e]+),([-\d.e]+)[^"]*"[^>]*?(/>|>.*?</\1>)\r?\n', drop, o, flags=re.S)
    open(path, 'w', encoding='utf-8', newline='').write(o)
    return n


def _terrain_lists(t, old_w, W, h, e_old, e_new, seam, carved):
    """t3terrain.xml의 블록 목록을 새 가로에 맞춘다 (GPT 검토 M02-01, 2026-10-15).

    blockTextureSetList: 8x8칸 블록마다 하나, 가로 순서 (원본 17x17 모두 tileSet 0).
    cliffCellList: 2x2칸 블록마다 하나(가로 W/2), 점유 항목만 적음. 원본에서 '블록의 3x3 꼭짓점 절벽 단계가 다르면 점유'
    규칙이 점유 1599개 중 1341개와 일치(틀린 것 0). 나머지는 편집기가 남긴 항목이라 원본 쪽은 그대로 옮긴다.
    새로 그린 블록(경계 동쪽, 뚫거나 메운 칸)은 이 규칙으로 다시 만든다: f=1, cid=0, cvar는 칸 위치로 정한 0~3.
    """
    import re as _re
    ob, nb = old_w // 8, W // 8
    sets = _re.findall(r'<blockTextureSet i="(\d+)" tileSet="(\d+)"/>', t)
    tile = {int(i): v for i, v in sets}
    m = _re.search(r'( *)<blockTextureSetList num="\d+">.*?</blockTextureSetList>', t, _re.S)
    ind = m[1]
    nl = '\r\n' if '\r\n' in t else '\n'
    rows = [f'{ind}<blockTextureSetList num="{nb * (h // 8)}">']
    for by in range(h // 8):
        for bx in range(nb):
            v = tile.get(by * ob + bx, '0') if bx < ob else '0'
            rows.append(f'{ind}    <blockTextureSet i="{by * nb + bx}" tileSet="{v}"/>')
    rows.append(f'{ind}</blockTextureSetList>')
    t = t[:m.start()] + nl.join(rows) + t[m.end():]

    oc, nc = old_w // 2, W // 2
    m = _re.search(r'( *)<cliffCellList num="\d+" numOccupied="\d+">(.*?)</cliffCellList>', t, _re.S)
    ind = m[1]
    old = {int(i): rest for i, rest in _re.findall(r'<cc i="(\d+)"( [^>]*)/>', m[2])}
    redo_blocks = {(y // 2, x // 2) for y, x in carved}
    out = {}
    for i, rest in old.items():
        by, bx = divmod(i, oc)
        if bx * 2 >= seam or (by, bx) in redo_blocks:
            continue
        out[by * nc + bx] = rest
    for by in range(h // 2):
        for bx in range(nc):
            if not (bx * 2 >= seam or (by, bx) in redo_blocks):
                continue
            blk = e_new[2 * by:2 * by + 3, 2 * bx:2 * bx + 3]
            if len(set(blk.ravel().tolist())) > 1:
                out[by * nc + bx] = f' f="1" cid="0" cvar="{(bx * 7 + by * 13) % 4}"'
    rows = [f'{ind}<cliffCellList num="{nc * (h // 2)}" numOccupied="{len(out)}">']
    rows += [f'{ind}    <cc i="{i}"{out[i]}/>' for i in sorted(out)]
    rows.append(f'{ind}</cliffCellList>')
    return t[:m.start()] + nl.join(rows) + t[m.end():]


def _vertcol(path, seam, W, h):
    """t3vertcol(버텍스 색)을 새 가로에 맞춘다 (2026-10-15, '맵을 열 수 없음' 조사에서 확인).

    형식: 머리 32(8에 항목 수), 항목 = key u32, kind u32, x0 y0 x1 y1 f32, u32, u32, n u32, n바이트.
    kind 1 = 4x4칸 블록(5x5 꼭짓점 25바이트)이 지도 전체를 (y, x) 순서로 빠짐없이 덮음 (원본 34x34=1156, ReOverhaul 56x40=2240).
    kind 2 = 칠한 자국 조각. 경계 동쪽 항목은 지우고, 새 블록은 25바이트 0xff(원본 기본값)로 채운다.
    """
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[8:12])[0]
    p, rows = 32, {}
    row = 0
    for _ in range(n):
        key, kind, x0, y0, x1, y1, u1, u2, k = struct.unpack('<IIffffIII', d[p:p + 36])
        rec = d[p:p + 36 + k]
        p += 36 + k
        if kind == 1:
            row = int(round(y0)) // 4
        if x1 <= seam + 1e-3:
            rows.setdefault(row, []).append(rec)
    tail = d[p:]
    out, count = [], 0
    for r in range(h // 4):
        recs = rows.get(r, [])
        out += recs
        count += len(recs)
        for x0 in range(seam, W, 4):
            out.append(struct.pack('<IIffffIII', 0, 1, float(x0), float(4 * r), float(x0 + 4), float(4 * r + 4), 0, 0, 25) + b'\xff' * 25)
            count += 1
    head = bytearray(d[:32])
    head[8:12] = struct.pack('<I', count)
    open(path, 'wb').write(bytes(head) + b''.join(out) + tail)


TILE = 64  # t3texturemasks: 텍스처 8장, 각 장은 (가로 칸x8) x (세로 칸x8) 픽셀, 64x64 타일 순서, 4비트(상위 니블 먼저)


def load_masks(path):
    """텍스처 마스크 → (머리, (8, 세로px, 가로px) 비중 0~15, 꼬리). 2026-10-15 원본으로 형식 확인."""
    d = open(path, 'rb').read()
    w, h = struct.unpack('<II', d[12:20])
    n = w * h * 4
    raw = np.frombuffer(d[64:64 + n], np.uint8)
    nib = np.stack([raw >> 4, raw & 15], -1).reshape(8, h // TILE, w // TILE, TILE, TILE)
    return d[:64], nib.transpose(0, 1, 3, 2, 4).reshape(8, h, w), d[64 + n:]


def save_masks(path, head, planes, tail):
    _, h, w = planes.shape
    assert h % TILE == 0 and w % TILE == 0, (h, w)
    t = planes.reshape(8, h // TILE, TILE, w // TILE, TILE).transpose(0, 1, 3, 2, 4).reshape(-1, 2)
    raw = ((t[:, 0] << 4) | t[:, 1]).astype(np.uint8)
    head = bytearray(head)
    head[12:20] = struct.pack('<II', w, h)
    open(path, 'wb').write(bytes(head) + raw.tobytes() + tail)


def _add_doodads(path, items):
    """원본에 있는 같은 종류 장식물 하나를 본떠 새 위치에 놓는다 (지면 기준 높이, 새 ID)."""
    o = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in o else '\n'
    nid = max(int(v) for v in re.findall(r' Id="(\d+)"', o)) + 1
    tmpl = {}
    for m in re.finditer(r'    <ObjectDoodad [^>]*?Type="(\w+)"[^>]*?(/>|>.*?</ObjectDoodad>)', o, re.S):
        tmpl.setdefault(m[1], m[0])
    add = []
    for kind, x, y, rot, scale in items:
        b = tmpl.get(kind)
        if b is None:
            continue
        b = re.sub(r'<Flag Index="HeightAbsolute" Value="1"/>\s*', '', b)
        b = re.sub(r'(<ObjectDoodad [^>]*?)>\s*</ObjectDoodad>', r'\1/>', b, flags=re.S)
        b = re.sub(r' Id="\d+"', f' Id="{nid}"', b, 1)
        b = re.sub(r' Position="[^"]*"', f' Position="{x:.4f},{y:.4f},0"', b, 1)
        b = re.sub(r' Rotation="[^"]*"', f' Rotation="{rot:.4f}"', b, 1) if ' Rotation="' in b else b.replace(' Position=', f' Rotation="{rot:.4f}" Position=', 1)
        b = re.sub(r' Scale="[^"]*"', f' Scale="{scale:.4f},{scale:.4f},{scale:.4f}"', b, 1)
        add.append(b + nl)
        nid += 1
    end = o.rindex('</PlacedObjects>')
    open(path, 'w', encoding='utf-8', newline='').write(o[:end] + ''.join(add) + o[end:])
    return len(add)
