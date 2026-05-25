import csv
import os
import json
import re

def get_control_chars(text):
    """
    Isolating engine-specific text tags allows strict structural parity checking 
    between source and target translation assets.
    """
    return re.findall(r'@(?!b)([a-zA-Z\d]+)|@v[0-9]+\.', text)

def check_critical_strings(rows, translated_col, critical_pairs):
    """
    Lore-critical terminology desyncs disrupt scenario context and may break 
    conditional scripts tied to text parsing triggers.
    """
    print("\n--- Critical String Mapping Verification Start ---")
    parsed_pairs = [(json.loads(jp_str), json.loads(cn_str)) for jp_str, cn_str in critical_pairs]
    found_errors = False
    for i, row in enumerate(rows):
        row_num = i + 2
        t_text = row.get(translated_col, '')
        for jp_str, cn_str in parsed_pairs:
            if jp_str in row.get('s', ''):
                if cn_str not in t_text:
                    print(f"❌ Error: Row {row_num} (ID: {row.get('index', 'N/A')}) missing mandatory translation: {cn_str}")
                    found_errors = True
    if not found_errors: 
        print("✅ Critical string validation passed.")
    print("--- End ---\n")
    return not found_errors

def check_control_chars(rows, original_col, translated_col):
    """
    Omitted control sequences or structural tags usually result in text layout 
    corruption or runtime game script parser crashes.
    """
    print("--- Control Token Integrity Verification Start ---")
    found_errors = False
    for i, row in enumerate(rows):
        s_text = row.get(original_col, '')
        t_text = row.get(translated_col, '')
        if not t_text: 
            continue
        s_controls = set(get_control_chars(s_text))
        t_controls = set(get_control_chars(t_text))
        missing = s_controls - t_controls
        if missing:
            print(f"⚠️ Warning: Row {i+2} missing tags: {', '.join(missing)}")
            found_errors = True
    if not found_errors: 
        print("✅ Control token integrity passed.")
    print("--- End ---\n")

def main():
    csv_path = 'main.csv'
    original_col = 's'
    translated_col = 'translated'

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

    if not os.path.exists(csv_path):
        print(f"Error: Target CSV file '{csv_path}' not found.")
        return

    rows = []
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    check_critical_strings(rows, translated_col, critical_strings)
    check_control_chars(rows, original_col, translated_col)

if __name__ == '__main__':
    main()