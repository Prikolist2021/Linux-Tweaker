#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f linux_tweaker.py ]; then
  echo "Ошибка: рядом должен быть файл linux_tweaker.py" >&2
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Ошибка: нужен Docker (sudo apt install docker.io)" >&2
  exit 1
fi
rm -rf build-appimage
mkdir -p build-appimage/src
cp linux_tweaker.py build-appimage/src/
cat > build-appimage/build-inside.sh <<'EOF'
#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3 python3-pip wget ca-certificates \
  file desktop-file-utils libglib2.0-bin binutils patchelf libegl1 libgl1 libxkbcommon0 \
  libdbus-1-3 libfontconfig1 libfreetype6 libpython3.10
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller PyQt6
pyinstaller --onefile --windowed --name linux-tweaker \
  --collect-submodules PyQt6 --hidden-import PyQt6.sip src/linux_tweaker.py
mkdir -p AppDir/usr/bin AppDir/usr/share/applications \
  AppDir/usr/share/icons/hicolor/256x256/apps
cp dist/linux-tweaker AppDir/usr/bin/linux-tweaker
chmod +x AppDir/usr/bin/linux-tweaker
cat > AppDir/AppRun <<'APPRUN'
#!/bin/sh
SELF_DIR="$(dirname "$(readlink -f "$0")")"
exec "$SELF_DIR/usr/bin/linux-tweaker" "$@"
APPRUN
chmod +x AppDir/AppRun
cat > AppDir/linux-tweaker.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Linux Tweaker
Comment=System tuning GUI for Linux Mint/Ubuntu/Debian
Exec=linux-tweaker
Icon=linux-tweaker
Terminal=false
Categories=System;Settings;
DESKTOP
cp AppDir/linux-tweaker.desktop AppDir/usr/share/applications/
# Цветная иконка 256x256, рисуется Qt в offscreen-режиме
QT_QPA_PLATFORM=offscreen python3 - <<'PY'
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (QPixmap, QPainter, QColor, QLinearGradient,
                         QPainterPath, QTransform, QPen, QBrush)
from PyQt6.QtWidgets import QApplication
app = QApplication([])
S = 256
px = QPixmap(S, S); px.fill(Qt.GlobalColor.transparent)
p = QPainter(px); p.setRenderHint(QPainter.RenderHint.Antialiasing)
g = QLinearGradient(0, 0, S, S)
g.setColorAt(0, QColor("#4ec9b0")); g.setColorAt(1, QColor("#268a72"))
p.setPen(Qt.PenStyle.NoPen); p.setBrush(g)
p.drawRoundedRect(8, 8, S - 16, S - 16, 56, 56)
def gear(cx, cy, r):
    path = QPainterPath()
    for i in range(8):
        tr = QTransform().translate(cx, cy).rotate(i * 45).translate(-cx, -cy)
        path.addRect(tr.mapRect(QRectF(cx - r * 0.16, cy - r, r * 0.32, r * 0.42)))
    ring = QPainterPath()
    ring.addEllipse(QRectF(cx - r * 0.66, cy - r * 0.66, r * 1.32, r * 1.32))
    hole = QPainterPath()
    hole.addEllipse(QRectF(cx - r * 0.28, cy - r * 0.28, r * 0.56, r * 0.56))
    return path + (ring - hole)
p.fillPath(gear(S * 0.42, S * 0.45, S * 0.26), QBrush(QColor("#ffffff")))
p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#10201c"))
p.drawEllipse(int(S * 0.58), int(S * 0.58), int(S * 0.26), int(S * 0.26))
p.setPen(QPen(QColor("#ffffff"), int(S * 0.05)))
p.drawArc(int(S * 0.60), int(S * 0.60), int(S * 0.22), int(S * 0.22), 30 * 16, 200 * 16)
p.end()
px.save("AppDir/linux-tweaker.png")
PY
cp AppDir/linux-tweaker.png AppDir/usr/share/icons/hicolor/256x256/apps/linux-tweaker.png
wget -q https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget -q https://github.com/linuxdeploy/linuxdeploy-plugin-appimage/releases/download/continuous/linuxdeploy-plugin-appimage-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage linuxdeploy-plugin-appimage-x86_64.AppImage
export APPIMAGE_EXTRACT_AND_RUN=1
export ARCH=x86_64
export OUTPUT=LinuxTweaker-x86_64.AppImage
./linuxdeploy-x86_64.AppImage --appdir AppDir --output appimage
if [ -n "${HOST_UID:-}" ] && [ -n "${HOST_GID:-}" ]; then
  chown -R "$HOST_UID:$HOST_GID" /build
fi
EOF
chmod +x build-appimage/build-inside.sh
docker run --rm \
  -e HOST_UID="$(id -u)" \
  -e HOST_GID="$(id -g)" \
  -v "$PWD/build-appimage":/build \
  -w /build \
  ubuntu:22.04 \
  bash ./build-inside.sh
cp build-appimage/LinuxTweaker-x86_64.AppImage .
chmod +x LinuxTweaker-x86_64.AppImage
echo
echo "Готово: $(pwd)/LinuxTweaker-x86_64.AppImage"
echo "Запуск: ./LinuxTweaker-x86_64.AppImage"
echo
