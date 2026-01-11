import pandas as pd
import re

def analyze_japanese_tags(input_csv, column_name, output_txt):
    try:
        # 1. 读取 CSV 文件
        # 如果文件包含日语，建议指定编码为 'utf-8' 或 'shift_jis'
        df = pd.read_csv(input_csv, encoding='utf-8')
        
        if column_name not in df.columns:
            print(f"错误: 找不到列名 '{column_name}'")
            return

        # 2. 定义正则表达式
        # 匹配逻辑：以 @b 开头，中间匹配任意字符，遇到 .@< 后继续匹配，直到 @> 结束
        pattern = r'@b.*?\.@<.*?@>'
        
        found_tags = []
        
        # 3. 遍历目标列进行查找
        for text in df[column_name].dropna().astype(str):
            matches = re.findall(pattern, text)
            found_tags.extend(matches)
        
        # 4. 去重并排序（如果需要统计出现次数，可以使用 collections.Counter）
        unique_tags = sorted(list(set(found_tags)))
        
        # 5. 输出到 txt 文件
        with open(output_txt, 'w', encoding='utf-8') as f:
            for tag in unique_tags:
                f.write(tag + '\n')
                
        print(f"处理完成！共找到 {len(found_tags)} 处匹配，去重后共有 {len(unique_tags)} 个。")
        print(f"结果已保存至: {output_txt}")

    except Exception as e:
        print(f"发生错误: {e}")

input_file = 'main.csv'  # 你的 CSV 文件路径
target_column = 's'           # 目标列名
output_file = 'ruby.txt'    # 输出的 txt 文件名

analyze_japanese_tags(input_file, target_column, output_file)