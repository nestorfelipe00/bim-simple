# Genera un .ico de prueba (PNG dentro de ICO, 256 y 32 px) solo con la biblioteca estandar.
import struct, sys, zlib
def png(size):
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            m = size // 8
            border = x < m or y < m or x >= size - m or y >= size - m
            wall = (size*3//8 <= x < size*5//8)
            r, g, b = (30, 90, 160) if border else ((220, 120, 40) if wall else (245, 245, 245))
            row += bytes((r, g, b, 255))
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
imgs = [png(s) for s in (256, 48, 32, 16)]
sizes = (256, 48, 32, 16)
out = struct.pack("<HHH", 0, 1, len(imgs))
offset = 6 + 16 * len(imgs)
for s, data in zip(sizes, imgs):
    out += struct.pack("<BBBBHHII", 0 if s == 256 else s, 0 if s == 256 else s, 0, 0, 1, 32, len(data), offset)
    offset += len(data)
out += b"".join(imgs)
open(sys.argv[1], "wb").write(out)
print("ico bytes:", len(out))
