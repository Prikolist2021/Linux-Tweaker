#!/bin/bash
set -e
# Зависимости: PyQt5 (не Qt6!) + FUSE + appimagetool
sudo apt-get update
sudo apt-get install -y python3-pyqt5 libfuse2 fuse wget
python3 -m pip install --upgrade pip pyinstaller

# Бинарник
pyinstaller --onefile --windowed --name LinuxTweaker linux_tweaker.py

# AppDir + AppRun
mkdir -p AppDir/usr/bin
cp dist/LinuxTweaker AppDir/usr/bin/
cat > AppDir/AppRun <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/LinuxTweaker" "$@"
EOF
chmod +x AppDir/AppRun

# AppImage
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage AppDir LinuxTweaker-x86_64.AppImage
echo "Готово: LinuxTweaker-x86_64.AppImage"
