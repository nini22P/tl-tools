import csv
import argparse
import os
import sys
import shutil


def patch_binary(input_path: str, output_path: str, csv_path: str):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return

    if not os.path.exists(input_path):
        print(f"Error: Input binary {input_path} not found")
        return

    print(f"Copying {input_path} -> {output_path}...")
    shutil.copyfile(input_path, output_path)

    print(f"Reading {csv_path}...")
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Patching {output_path}...")

    with open(output_path, 'r+b') as f_bin:
        for i, row in enumerate(rows):
            offset_str = row.get('offset', '').strip()
            length_str = row.get('length', '').strip()
            translation = row.get('translation', '')
            encoding = row.get('encoding', '').strip() or 'utf-8'

            if not offset_str:
                continue

            try:
                offset = int(offset_str, 16)
                max_length = int(length_str)
            except ValueError:
                print(f"Warning: Format error at line {i+2}, skipping")
                continue

            if not translation:
                continue

            try:
                encoded_text = translation.encode(encoding)
            except Exception as e:
                print(f"Encoding error at line {i+2}: {e}")
                continue

            current_len = len(encoded_text)

            if current_len > max_length:
                print(f"Error: Translation too long at line {i+2}")
                print(f"  Original: {row.get('text', '')}")
                print(f"  Translation: {translation}")
                print(f"  Length: {current_len}, Max: {max_length}")
                sys.exit(1)

            data_to_write = encoded_text + b'\x00' * (max_length - current_len)

            f_bin.seek(offset)
            f_bin.write(data_to_write)

    print("Patching complete!")


def main():
    parser = argparse.ArgumentParser(description='Binary Patching Tool')

    parser.add_argument('-i', '--input', required=True, help='Input binary file')
    parser.add_argument('-o', '--output', required=True, help='Output binary file')
    parser.add_argument('-c', '--csv', required=True, help='CSV file path')

    args = parser.parse_args()

    patch_binary(args.input, args.output, args.csv)


if __name__ == '__main__':
    main()