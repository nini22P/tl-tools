#!/bin/bash

pip install --user -r shin-tools/requirements.txt

ROOT_DIR=$(pwd)

export PATH="$ROOT_DIR:$ROOT_DIR/bin:$ROOT_DIR/assets:$PATH"

if [ ! -d "raw/data" ]; then
    bin/shin-tl rom extract raw/data.rom raw/data
fi

mkdir -p build/repatch
cp -r assets/repatch/* build/repatch/

mkdir -p build/patch

python shin-tools/mapping-tool.py mapping-config.json

vita-unmake-fself build/repatch/PCSG00901/eboot.bin
python shin-tools/patch-tool.py -b build/repatch/PCSG00901/eboot.bin.elf -c eboot-utf-8.csv -e utf-8
python shin-tools/patch-tool.py -b build/repatch/PCSG00901/eboot.bin.elf -c build/eboot-utf-16le-mapped.csv -e utf-16le
vita-make-fself build/repatch/PCSG00901/eboot.bin.elf build/repatch/PCSG00901/eboot.bin
printf '\x85\x03\xce\x1c\x10\x00\x00\x21' | dd of=build/repatch/PCSG00901/eboot.bin bs=1 seek=128 count=8 conv=notrunc
rm -f build/repatch/PCSG00901/eboot.bin.elf

fnt4-tool rebuild raw/data/rodin.fnt build/patch/rodin.fnt assets/font/SarasaGothicSC-Regular.ttf -s 64 -q 4 --letter-spacing 2 -c build/mapping.toml
fnt4-tool rebuild raw/data/matisse.fnt build/patch/matisse.fnt assets/font/NotoSerifCJKsc-Medium.otf -s 76 -q 4 --letter-spacing 2 -c build/mapping.toml
fnt4-tool rebuild raw/data/seura.fnt build/patch/seura.fnt assets/font/ChillRoundFRegularCustom.otf -s 54 -q 4 --letter-spacing 2 -c build/mapping.toml

shin-tl snr rewrite white-eternity raw/data/main.snr build/white-eternity-mapped.csv build/patch/main.snr

rm -rf build/patch/picture
python shin-tools/txa-tool.py pack -i assets/txa -o build/patch -v 1
python shin-tools/pic-tool.py pack -i assets/pic -o build/patch/picture -v 1

shin-tl rom create --rom-version white-eternity build/patch build/repatch/PCSG00901/patch.rom

echo -e "\033[32mSUCCESS!\033[0m"
read -p "Press ENTER to exit..."