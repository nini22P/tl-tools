import struct
import os
import argparse
from PIL import Image

import lz77

def decode_dict_block(data, w, h, flags):
    stride = (w + 3) & ~3
    
    is_dict = (flags & 2) != 0
    use_inline_alpha = (flags & 1) != 0

    if not is_dict:
        return None

    if len(data) < 1024:
        return None

    palette = []
    for i in range(0, 1024, 4):
        b, g, r, a = data[i:i+4]
        palette.append((r, g, b, a))

    idx_start = 1024
    idx_len = stride * h
    
    if idx_start + idx_len > len(data):
        return None
        
    encoded_data = data[idx_start : idx_start + idx_len]

    alpha_data = None
    if not use_inline_alpha:
        a_start = idx_start + idx_len
        if a_start < len(data):
            alpha_data = data[a_start:]
    
    pixels = bytearray(w * h * 4)
    ptr = 0
    
    for row in range(h):
        row_offset = row * stride
        
        row_indices = encoded_data[row_offset : row_offset + w]
        
        row_alphas = None
        if alpha_data:
            if row_offset + w <= len(alpha_data):
                row_alphas = alpha_data[row_offset : row_offset + w]
        
        for col in range(w):
            if col < len(row_indices):
                idx = row_indices[col]
            else:
                idx = 0
                
            r, g, b, a = palette[idx]
            
            if row_alphas:
                a = row_alphas[col]
            
            pixels[ptr] = r
            pixels[ptr+1] = g
            pixels[ptr+2] = b
            pixels[ptr+3] = a
            ptr += 4
            
    return pixels

def convert_file(file_path, output_path):
    file_size = os.path.getsize(file_path)
    
    with open(file_path, 'rb') as f:
        if f.read(4) != b"PIC4":
            print(f"[跳过] 不是PIC4文件: {os.path.basename(file_path)}")
            return False

        header = struct.unpack("<IIhhHHIII", f.read(28))
        eff_w, eff_h, count = header[4], header[5], header[7]

        blocks = []
        for i in range(count):
            blocks.append(struct.unpack("<HHI", f.read(8)))

        img = Image.new("RGBA", (eff_w, eff_h))
        processed_blocks = 0

        for i, (bx, by, offset) in enumerate(blocks):
            next_offset = blocks[i+1][2] if i < count - 1 else file_size
            max_len = next_offset - offset

            if offset >= file_size: continue
            f.seek(offset)
            
            tile_data = f.read(20)
            if len(tile_data) < 20: continue
            
            tile = struct.unpack("<HHHHHHHHI", tile_data)
            flags, opaque, trans, pad, unknown1, unknoown2, w, h, comp_size = tile[0], tile[1], tile[2], tile[3], tile[4], tile[5], tile[6], tile[7], tile[8]

            print(f"Block {i} ( {bx}, {by} ): {flags}, {opaque}, {trans}, {pad}, {unknown1}, {unknoown2}, {w}, {h}, {comp_size}")
            
            skip = (opaque + trans) * 8 + (pad * 2)
            f.seek(skip, 1)

            data_len = comp_size if comp_size > 0 else (max_len - 20 - skip)
            if data_len <= 0: continue
            
            raw_data = f.read(data_len)
            if not raw_data: continue

            try:
                dec_data = lz77.decompress(raw_data, seek_bits=12, backseek_nbyte=2)
            except Exception as e:
                print(f"[警告] 解压失败 Block {i}: {e}")
                continue

            if not dec_data: continue

            pixel_bytes = decode_dict_block(dec_data, w, h, flags)
            
            if pixel_bytes:
                try:
                    tile_img = Image.frombytes("RGBA", (w, h), bytes(pixel_bytes))
                    img.paste(tile_img, (bx, by))
                    processed_blocks += 1
                except ValueError as e:
                    print(f"[警告] 图像构建失败 Block {i}: {e}")

        img.save(output_path)
        print(f"[完成] {os.path.basename(file_path)} (处理块数: {processed_blocks}/{count})")
        return True

def process_batch(input_path):
    abs_input = os.path.abspath(input_path)
    
    if os.path.isfile(abs_input):
        folder = os.path.dirname(abs_input)
        name = os.path.splitext(os.path.basename(abs_input))[0]
        out_path = os.path.join(folder, name + ".png")
        convert_file(abs_input, out_path)
    
    elif os.path.isdir(abs_input):
        parent_dir = os.path.dirname(abs_input)
        folder_name = os.path.basename(abs_input)
        output_dir = os.path.join(parent_dir, folder_name + "_png")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print(f"输出目录: {output_dir}")
        
        count = 0
        for root, dirs, files in os.walk(abs_input):
            for file in files:
                if file.lower().endswith(".pic"):
                    src = os.path.join(root, file)
                    name = os.path.splitext(file)[0]
                    dst = os.path.join(output_dir, name + ".png")
                    
                    if convert_file(src, dst):
                        count += 1
        
        print(f"共处理: {count} 个文件")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="输入文件或文件夹")
    args = parser.parse_args()
    
    if os.path.exists(args.input):
        process_batch(args.input)
    else:
        print("路径不存在")