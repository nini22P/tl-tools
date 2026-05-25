@echo off

if not exist raw\data\ (
    bin\shin-tl.exe rom extract raw\data.rom raw\data || exit /b %errorlevel%
)

xcopy /Y /E assets\repatch\ build\repatch\ >nul || exit /b %errorlevel%
mkdir build\patch\ 2>nul

python create-mapping.py || exit /b %errorlevel%
python patch-tool.py -b build\repatch\PCSG00901\eboot.bin -c eboot-utf-8.csv -e utf-8 || exit /b %errorlevel%
python patch-tool.py -b build\repatch\PCSG00901\eboot.bin -c build\eboot-utf-16le-mapped.csv -e utf-16le || exit /b %errorlevel%

bin\fnt4-tool.exe rebuild raw\data\rodin.fnt build\patch\rodin.fnt assets\font\SarasaGothicSC-Regular.ttf -s 64 -q 4 --letter-spacing 2 -c build/mapping.toml || exit /b %errorlevel%
bin\fnt4-tool.exe rebuild raw\data\matisse.fnt build\patch\matisse.fnt assets\font\NotoSerifCJKsc-Medium.otf -s 76 -q 4 --letter-spacing 2 -c build/mapping.toml || exit /b %errorlevel%
bin\fnt4-tool.exe rebuild raw\data\seura.fnt build\patch\seura.fnt assets\font\ChillRoundFRegularCustom.otf -s 54 -q 4 --letter-spacing 2 -c build/mapping.toml || exit /b %errorlevel%

bin\shin-tl.exe snr rewrite white-eternity raw\data\main.snr build\white-eternity-mapped.csv build\patch\main.snr || exit /b %errorlevel%
bin\shin-tl.exe rom create --rom-version white-eternity build\patch build\repatch\PCSG00901\patch.rom || exit /b %errorlevel%

pause