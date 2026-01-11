import csv
import os
import toml
import json
import re

def is_valid_sjis_slot(char):
    """
    检查字符是否符合 Shift-JIS 双字节编码的基本要求
    """
    try:
        b = char.encode('shift_jis', errors='strict')
    except:
        return False
    if len(b) != 2:
        return False
    lead, trail = b[0], b[1]
    # 尾字节 >= 0x80 是双字节 Shift-JIS 编码的常见特性，避开 0x40-0x7E 范围更安全
    if trail < 0x80:
        return False
    return True

def is_cjk_ideograph(char):
    """
    检查一个字符是否属于主要的 CJK 统一表意文字 (汉字) 块。
    """
    code_int = ord(char)
    return 0x4E00 <= code_int <= 0x9FFF

def get_control_chars(text):
    """
    从文本中提取所有以 '@' 开头的控制字符序列。
    """
    return re.findall(r'@(?!b)([a-zA-Z\d]+)|@v[0-9]+\.', text)

def check_critical_strings(rows, translated_col, critical_pairs):
    """
    检查 CSV 行中是否满足关键的日语/译文对应关系。
    """
    print("\n--- 关键字符串对应关系检查开始 ---")
    parsed_pairs = [(json.loads(jp_str), json.loads(cn_str)) for jp_str, cn_str in critical_pairs]
    found_errors = False
    for i, row in enumerate(rows):
        row_num = i + 2
        t_text = row.get(translated_col, '')
        for jp_str, cn_str in parsed_pairs:
            if jp_str in row.get('s', ''):
                if cn_str not in t_text:
                    print(f"❌ 错误: 第 {row_num} 行 (ID: {row.get('index', 'N/A')}) 缺失关键译文: {cn_str}")
                    found_errors = True
    if not found_errors: print("✅ 关键字符串检查通过。")
    print("--- 检查结束 ---\n")
    return not found_errors

def check_control_chars(rows, original_col, translated_col):
    """
    检查翻译文本是否保留了原始日文中的控制字符。
    """
    print("--- 控制字符保留检查开始 ---")
    found_errors = False
    for i, row in enumerate(rows):
        s_text = row.get(original_col, '')
        t_text = row.get(translated_col, '')
        if not t_text: continue
        s_controls = set(get_control_chars(s_text))
        t_controls = set(get_control_chars(t_text))
        missing = s_controls - t_controls
        if missing:
            print(f"⚠️ 警告: 第 {i+2} 行缺失控制符: {', '.join(missing)}")
            found_errors = True
    if not found_errors: print("✅ 控制字符检查通过。")
    print("--- 检查结束 ---\n")

def main():
    csv_path = 'main.csv'
    original_col = 's'
    translated_col = 'translated'
    metadata_path = 'metadata.toml'
    mapping_output = 'mapping.toml'
    csv_output = 'main-mapped.csv'

    critical_strings = [
        ['"ゆきゆき"', '"雪雪"'],
        ['"雪々"', '"雪々"'],
        ['"@bルーン.@<能力@>"', '"@bｒｕｎｅ.@<能力@>"'],
        ['"@bエルフィン.@<能力者@>"','"@bｅｌｆｉｎ.@<能力者@>"'],
        ['"@bエルフ.@<妖精@>"','"@bｅｌｆ.@<妖精@>"'],
        ['"@bアイルーン.@<特化型能力@>"', '"@bｉ　ｒｕｎｅ.@<特化型能力@>"'],
        ['"@bテレパシー.@<精神感応能力@>"', '"@bｔｅｌｅｐａｔｈｙ.@<精神感应能力@>"'],
        ['"@bサイコキネシス.@<念動能力@>"', '"@bｐｓｙｃｈｏｋｉｎｅｓｉｓ.@<念动能力@>"'],
        ['"@bクレヤボヤンス.@<遠隔透視能力@>"', '"@bｃｌａｉｒ　ｖｏｙａｎｃｅ.@<远隔透视能力@>"'],
        ['"@bテレポート.@<空間移動能力@>"', '"@bｔｅｌｅｐｏｒｔ.@<空间移动能力@>"'],
        ['"@bアポーツ.@<遠隔移動能力@>"', '"@bａｐｐｏｒｔｓ.@<远隔移动能力@>"'],
        ['"@bヒュプノ.@<催眠能力@>"', '"@bｈｙｐｎｏ.@<催眠能力@>"'],
        ['"@bサイコメトリー.@<接触感応能力@>"', '"@bｐｓｙｃｈｏｍｅｔｒｙ.@<接触感应能力@>"'],
        ['"@bパイロキネシス.@<発火能力@>"', '"@bｐｙｒｏｋｉｎｅｓｉｓ.@<发火能力@>"'],
        ['"@bアニミズム.@<精霊信仰@>"','"@bａｎｉｍｉｓｉｍ.@<精灵信仰@>"'],
        ['"@bアポー.@<遠隔移動@>"', '"@bａｐｐｏｒｔ.@<远隔移动@>"'],
        ['"@bエムパシー.@<共感能力@>"','"@bｅｍｐａｔｈｙ.@<共感能力@>"'],
        ['"@bエルフィンノーツ.@<能力飛行士@>"','"@bｅｌｆｉｎ　ｎａｕｔ.@<能力飞行员@>"'],
        ['"@bサイコメトリー.@<触感応能力@>"','"@bｐｓｙｃｈｏｍｅｔｒｙ.@<接触感应能力@>"'],
        ['"@bサイミッシング.@<無効化能力@>"','"@bｐｓｉ　ｍｉｓｓｉｎｇ.@<无效化能力@>"'],
        ['"@bテラフォーミング.@<環境改造能力@>"','"@bｔｅｒｒａｆｏｒｍｉｎｇ.@<环境改造能力@>"'],
        ['"@bテレポート.@<移動能力@>"','"@bｔｅｌｅｐｏｒｔ.@<空间移动能力@>"'],
        ['"@bデジャヴ.@<過去視能力@>"','"@bｄéｊàｖｕ.@<过去视能力@>"'],
        ['"@bトワイライトシンドローム.@<黄昏症候群@>"','"@bｔｗｉｌｉｇｈｔ　ｓｙｎｄｒｏｍｅ.@<黄昏症候群@>"'],
        ['"@bヒーリング.@<治癒能力@>"','"@bｈｅａｌｉｎｇ.@<治愈能力@>"'],
        ['"@bプレコグニション.@<予知能力@>"','"@bｐｒｅｃｏｇｎｉｔｉｏｎ.@<预知能力@>"'],
        ['"@bミスディレクション.@<不可視能力@>"','"@bｍｉｓｄｉｒｅｃｔｉｏｎ.@<不可视能力@>"'],
        ['"@bラグナロク.@<神々の黄昏@>"','"@bｒａｇｎａｒｏｋ.@<诸神黄昏@>"'],
        ['"@bリカレンス.@<回帰能力@>"','"@bｒｅｃｕｒｒｅｎｃｅ.@<回归能力@>"'],
        ['"@bルーン.@<光@>"','"@bｒｕｎｅ.@<光@>"'],
        ['"@bルーン.@<雪々@>"','"@bｒｕｎｅ.@<雪々@>"'],
        ['"@bアストラエア.@<星々の欠片@>"', '"@bａｓｔｒａｌ　ａｉｒ.@<星星的碎片@>"'],
        ['"@bねんぱ.@<念波@>"', '"念波"'],
    ]

    if not (os.path.exists(csv_path) and os.path.exists(metadata_path)):
        print("错误: 找不到 CSV 或 metadata 文件。")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        meta_data = toml.load(f)
    
    version = meta_data.get('version', 'v0').lower()
    print(f"检测到 FNT4 版本: {version.upper()}")
    
    font_inventory = {}
    glyphs_section = meta_data.get('glyphs', {})
    iterator = glyphs_section.values() if isinstance(glyphs_section, dict) else glyphs_section
    
    for g in iterator:
        if not g.get('char_code'): continue
        raw_code = int(g['char_code'], 16)
        try:
            if version == 'v1':
                char_obj = chr(raw_code)
            else:
                if raw_code <= 0xFF:
                    char_obj = raw_code.to_bytes(1, 'big').decode('shift_jis')
                else:
                    char_obj = raw_code.to_bytes(2, 'big').decode('shift_jis')
            
            if char_obj:
                font_inventory[char_obj] = raw_code
        except:
            continue

    needed_chars = set()    # 译文中需要但字库中没有的字符
    chars_in_csv = set()    # 整个 CSV 中出现过的字符
    rows = []
    
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            t_text = row.get(translated_col, '')
            s_text = row.get(original_col, '')
            
            for c in t_text:
                if ord(c) >= 0x80:
                    chars_in_csv.add(c)
                    if c not in font_inventory:
                        needed_chars.add(c)
            for c in s_text:
                if ord(c) >= 0x80:
                    chars_in_csv.add(c)
            rows.append(row)
    check_critical_strings(rows, translated_col, critical_strings)
    check_control_chars(rows, original_col, translated_col)

    potential_slots = [
        c for c in font_inventory.keys()
        if is_cjk_ideograph(c) and is_valid_sjis_slot(c) and c not in needed_chars
    ]

    # 优先级排序：先用 CSV 里没出现过的，再用原文里出现的
    unused_slots = sorted([c for c in potential_slots if c not in chars_in_csv], key=lambda x: font_inventory[x])
    fallback_slots = sorted([c for c in potential_slots if c in chars_in_csv], key=lambda x: font_inventory[x])
    
    final_candidates = unused_slots + fallback_slots
    missing_chars = sorted(list(needed_chars))

    print(f"译文缺口: {len(missing_chars)} | 空闲槽位: {len(unused_slots)} | 备用槽位: {len(fallback_slots)}")

    if len(missing_chars) > len(final_candidates):
        print(f"❌ 警告: 槽位不足! 无法处理所有新字符。")
        missing_chars = missing_chars[:len(final_candidates)]

    final_mapping = {}
    trans_table = {}
    for i, cn_char in enumerate(missing_chars):
        slot_jp_char = final_candidates[i]
        final_mapping[slot_jp_char] = cn_char
        trans_table[ord(cn_char)] = slot_jp_char

    with open(mapping_output, 'w', encoding='utf-8') as f:
        f.write("# 替换映射表: [日文字符(槽位)] = [中文字符(目标)]\n[replace]\n")
        for k, v in final_mapping.items():
            f.write(f"{json.dumps(k, ensure_ascii=False)} = {json.dumps(v, ensure_ascii=False)}\n")

    with open(csv_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            orig = row.get(translated_col, '')
            if orig:
                row[translated_col] = orig.translate(trans_table)
            writer.writerow(row)

    print(f"✅ 完成！已生成 {mapping_output} 和 {csv_output}。")

if __name__ == '__main__':
    main()