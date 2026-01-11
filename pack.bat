python create-mapping.py && \
fnt4-tool rebuild data/rodin.fnt patch/rodin.fnt font/SarasaGothicSC-Regular.ttf -s 64 -q 4 --letter-spacing 2 -c mapping.toml && \
fnt4-tool rebuild data/matisse.fnt patch/matisse.fnt font/NotoSerifCJKsc-Medium.otf -s 76 -q 4 --letter-spacing 2 -c mapping.toml && \
fnt4-tool rebuild data/seura.fnt patch/seura.fnt font/ChillRoundFRegularCustom.otf -s 54 -q 4 --letter-spacing 2 -c mapping.toml && \
shin-tl snr rewrite white-eternity data/main.snr main-mapped.csv patch/main.snr && \
shin-tl rom create --rom-version white-eternity patch repatch/PCSG00901/patch.rom
pause