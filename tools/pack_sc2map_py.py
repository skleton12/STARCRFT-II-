#!/usr/bin/env python3
"""Pack a folder-format map (X.SC2Map/ directory) into a single-file .SC2Map (MPQ, v4 header) without StormLib.

The release ZIP stores maps as folders. The user wants a single map file to open in the Editor (2026-10-24).
tools/pack_sc2map.py needs a StormLib build; this pure-Python writer is the fallback when native code can't be built.
Header is MPQ v4 (format 3, 0xD0 bytes, table MD5s) like StormLib's MPQ_CREATE_ARCHIVE_V4 (SC2 rejects the v3 header).
Files use 4096-byte sectors, each zlib-compressed when smaller. A (listfile) is added. Verify with mpyq after packing.

Usage: python3 tools/pack_sc2map.py <map folder> <output .SC2Map>
"""
import argparse, hashlib, struct, zlib
from pathlib import Path


def _crypt_table():
    table = {}
    seed = 0x00100001
    for i in range(256):
        idx = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            hi = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            table[idx] = hi | (seed & 0xFFFF)
            idx += 256
    return table


CRYPT = _crypt_table()
HASH_TYPES = {'TABLE_OFFSET': 0, 'HASH_A': 1, 'HASH_B': 2, 'TABLE': 3}


def mpq_hash(s, kind):
    seed1, seed2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in s.upper():
        c = ord(ch)
        value = CRYPT[(HASH_TYPES[kind] << 8) + c]
        seed1 = (value ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed2 = (c + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def encrypt(data, key):
    seed1, seed2 = key, 0xEEEEEEEE
    out = bytearray()
    for i in range(len(data) // 4):
        seed2 = (seed2 + CRYPT[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
        value = struct.unpack_from('<I', data, i * 4)[0]
        enc = (value ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed1 = (((~seed1 << 0x15) + 0x11111111) | (seed1 >> 0x0B)) & 0xFFFFFFFF
        seed2 = (value + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
        out += struct.pack('<I', enc)
    return bytes(out)


SECTOR_SHIFT = 3
SECTOR = 512 << SECTOR_SHIFT


def _store(data):
    """Sectored file body: offset table + sectors (zlib when smaller). Returns (bytes, flags)."""
    if not data:
        return b'', 0x80000000
    sectors = [data[i:i + SECTOR] for i in range(0, len(data), SECTOR)]
    parts = []
    for s in sectors:
        z = zlib.compress(s, 9)
        parts.append(b'\x02' + z if len(z) + 1 < len(s) else s)
    pos = 4 * (len(parts) + 1)
    offsets = [pos]
    for part in parts:
        pos += len(part); offsets.append(pos)
    return struct.pack(f'<{len(offsets)}I', *offsets) + b''.join(parts), 0x80000000 | 0x00000200  # EXISTS | COMPRESS


def pack(folder, output):
    folder = Path(folder)
    names = sorted(str(p.relative_to(folder)).replace('/', '\\') for p in folder.rglob('*') if p.is_file())
    files = [(n, (folder / n.replace('\\', '/')).read_bytes()) for n in names]
    files.append(('(listfile)', ('\r\n'.join(names) + '\r\n').encode('utf-8')))
    size = 1
    while size < len(files) * 2: size *= 2
    header_size = 0xD0
    body = bytearray()
    blocks = []
    for name, data in files:
        stored, flags = _store(data)
        blocks.append((header_size + len(body), len(stored), len(data), flags))
        body += stored
    hashes = [(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFFFFFF)] * size
    for i, (name, _) in enumerate(files):
        j = mpq_hash(name, 'TABLE_OFFSET') & (size - 1)
        while hashes[j][4] != 0xFFFFFFFF: j = (j + 1) & (size - 1)
        hashes[j] = (mpq_hash(name, 'HASH_A'), mpq_hash(name, 'HASH_B'), 0, 0, i)
    hash_enc = encrypt(b''.join(struct.pack('<IIHHI', *h) for h in hashes), mpq_hash('(hash table)', 'TABLE'))
    block_enc = encrypt(b''.join(struct.pack('<IIII', *b) for b in blocks), mpq_hash('(block table)', 'TABLE'))
    hash_pos = header_size + len(body)
    block_pos = hash_pos + len(hash_enc)
    archive_size = block_pos + len(block_enc)
    z16 = b'\0' * 16
    head = struct.pack('<4sIIHHIIII', b'MPQ\x1a', header_size, archive_size, 3, SECTOR_SHIFT, hash_pos, block_pos, size, len(blocks))
    head += struct.pack('<QHH', 0, 0, 0)                      # v2: hi-block table, high words
    head += struct.pack('<QQQ', archive_size, 0, 0)           # v3: 64-bit size, no BET/HET
    head += struct.pack('<QQQQQI', len(hash_enc), len(block_enc), 0, 0, 0, 0)  # v4 sizes, raw chunk 0
    head += hashlib.md5(block_enc).digest() + hashlib.md5(hash_enc).digest() + z16 + z16 + z16
    assert len(head) == 0xC0
    head += hashlib.md5(head).digest()
    Path(output).write_bytes(head + bytes(body) + hash_enc + block_enc)
    return names

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists(): raise SystemExit('Output must be new')
    print(len(pack(a.folder, a.output)), 'files ->', a.output)
