'''LZ77 variant used by TXA v0 / PIC v0.

2-byte backreference layout:
  b1: [offset_high(4) | length(4)]
  b2: [offset_low(8)]
length = (b1 & 0x0F) + 3
offset = ((b1 >> 4) << 8) | b2
'''


def decompress_v0(input_data: bytes) -> bytes:
    marker = 1
    res = bytearray()
    p = 0
    while p < len(input_data):
        if marker == 1:
            marker = 0x100 | input_data[p]
            p += 1
        if p >= len(input_data):
            break
        if marker & 1:
            b1 = input_data[p]
            b2 = input_data[p + 1]
            p += 2
            count = (b1 & 0x0F) + 3
            offset = ((b1 & 0xF0) << 4) | b2
            for _ in range(count):
                res.append(res[-(offset + 1)])
        else:
            res.append(input_data[p])
            p += 1
        marker >>= 1
    return bytes(res)


def compress_v0(input_bytes: bytes) -> bytes:
    max_offset = 4096
    max_count = 18

    if not input_bytes:
        return b''

    n = len(input_bytes)
    pos = 0
    output = bytearray()
    hash_table = {}

    def hash3(i):
        if i + 2 >= n:
            return -1
        return (input_bytes[i] << 16) | (input_bytes[i+1] << 8) | input_bytes[i+2]

    pending = []

    def flush_pending():
        nonlocal pending
        while pending:
            chunk = pending[:8]
            pending = pending[8:]
            bitmap = 0
            chunk_bytes = bytearray()
            for i, item in enumerate(chunk):
                if isinstance(item, int):
                    bitmap |= (0 << i)
                    chunk_bytes.append(item)
                else:
                    bitmap |= (1 << i)
                    length_val, offset_val = item
                    b1 = ((offset_val >> 4) & 0xF0) | (length_val & 0x0F)
                    b2 = offset_val & 0xFF
                    chunk_bytes.extend([b1, b2])
            output.append(bitmap)
            output.extend(chunk_bytes)

    while pos < n:
        best_len = 0
        best_off = 0

        if pos + 2 < n:
            key = hash3(pos)
            if key in hash_table:
                candidate = hash_table[key]
                if pos - candidate <= max_offset:
                    ml = 0
                    max_possible = min(max_count, n - pos)
                    while ml < max_possible and input_bytes[candidate + ml] == input_bytes[pos + ml]:
                        ml += 1
                    if ml >= 3:
                        best_len = ml
                        best_off = pos - candidate

        if best_len >= 3:
            pending.append([best_len - 3, best_off - 1])
            for j in range(best_len):
                h = hash3(pos + j)
                if h >= 0:
                    hash_table[h] = pos + j
            pos += best_len
        else:
            pending.append(input_bytes[pos])
            h = hash3(pos)
            if h >= 0:
                hash_table[h] = pos
            pos += 1

    flush_pending()
    return bytes(output)
