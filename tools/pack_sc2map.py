#!/usr/bin/env python3
"""폴더형 .SC2Map을 편집기가 바로 여는 단일 .SC2Map(MPQ) 파일로 묶는다.

StormLib(https://github.com/ladislav-zezula/StormLib) 공유 라이브러리가 필요하다.
빌드: cmake .. -DBUILD_SHARED_LIBS=ON -DSTORM_USE_BUNDLED_LIBRARIES=ON && make
사용: STORMLIB=/경로/libstorm.so python3 tools/pack_sc2map.py <폴더.SC2Map> <출력.SC2Map>
"""
import ctypes, os, sys

MPQ_CREATE_LISTFILE = 0x00100000
MPQ_CREATE_ATTRIBUTES = 0x00200000
MPQ_CREATE_ARCHIVE_V4 = 0x03000000  # SC2는 V3 머리를 받지 않음 (StormLib 주석)
MPQ_FILE_COMPRESS = 0x00000200
MPQ_FILE_REPLACEEXISTING = 0x80000000
MPQ_COMPRESSION_ZLIB = 0x02


def pack(src_dir, out_path, lib_path):
    st = ctypes.CDLL(lib_path)
    for fn in ('SFileCreateArchive', 'SFileAddFileEx', 'SFileCloseArchive'):
        getattr(st, fn).restype = ctypes.c_bool
    files = []
    for base, _, names in os.walk(src_dir):
        for n in sorted(names):
            full = os.path.join(base, n)
            files.append((full, os.path.relpath(full, src_dir).replace(os.sep, '\\')))
    if os.path.exists(out_path):
        os.remove(out_path)
    h = ctypes.c_void_p()
    flags = MPQ_CREATE_LISTFILE | MPQ_CREATE_ATTRIBUTES | MPQ_CREATE_ARCHIVE_V4
    if not st.SFileCreateArchive(out_path.encode(), flags, len(files) + 16, ctypes.byref(h)):
        raise SystemExit('archive create failed')
    for full, name in files:
        ok = st.SFileAddFileEx(h, full.encode(), name.encode(),
                               MPQ_FILE_COMPRESS | MPQ_FILE_REPLACEEXISTING,
                               MPQ_COMPRESSION_ZLIB, MPQ_COMPRESSION_ZLIB)
        if not ok:
            raise SystemExit(f'add failed: {name}')
    if not st.SFileCloseArchive(h):
        raise SystemExit('archive close failed')
    print(out_path, len(files), 'files')


if __name__ == '__main__':
    lib = os.environ.get('STORMLIB', 'libstorm.so')
    pack(sys.argv[1], sys.argv[2], lib)
