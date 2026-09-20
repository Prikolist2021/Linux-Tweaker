version: 1
script:
  # Очищаем предыдущую сборку
  - rm -rf AppDir || true
  # Создаём структуру каталогов
  - mkdir -p AppDir/usr/src
  - mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
  - mkdir -p AppDir/usr/share/applications
  # Копируем основной скрипт
  - cp linux_tweaker.py AppDir/usr/src/main.py
  # КРИТИЧНО: копируем список пакетов для вкладки «Приложения»
  - cp tweaker_packages.py AppDir/usr/src/tweaker_packages.py
  # Копируем иконку
  - cp icon.png AppDir/usr/share/icons/hicolor/256x256/apps/linux-tweaker.png
  # Создаём .desktop-файл (нужен для меню системы)
  - |
    cat > AppDir/usr/share/applications/linux-tweaker.desktop <<'EOF'
    [Desktop Entry]
    Type=Application
    Name=Linux Tweaker
    Comment=Tuning shell for Linux Mint / Ubuntu / Debian
    Exec=linuxtweaker
    Icon=linux-tweaker
    Terminal=false
    Categories=System;Settings;
    EOF
  # Создаём AppRun-обёртку, которая запускает python3 с нашим скриптом
  - |
    cat > AppDir/AppRun <<'EOF'
    #!/bin/bash
    HERE="$(dirname "$(readlink -f "${0}")")"
    export APPDIR="${HERE}"
    # Убираем возможные помехи от родительского Python
    unset PYTHONHOME
    unset PYTHONPATH
    exec "${HERE}/usr/bin/python3" "${HERE}/usr/src/main.py" "$@"
    EOF
  - chmod +x AppDir/AppRun

AppDir:
  path: ./AppDir
  app_info:
    id: org.example.linuxtweaker
    name: Linux Tweaker
    icon: linux-tweaker
    version: 1.0
    exec: usr/bin/python3
    exec_args: "$APPDIR/usr/src/main.py $@"

  apt:
    arch: amd64
    sources:
      - sourceline: 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy main restricted universe multiverse'
        key_url: 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x871920D1991BC93C'
    include:
      - python3
      - python3-pyqt5
    exclude: []

  # ВАЖНО: не задаём PYTHONHOME, иначе Python сломается
  # на системах с другой версией Python
  env:
    PYTHONPATH: '${APPDIR}/usr/lib/python3/dist-packages'

AppImage:
  arch: x86_64
  update-information: 'gh-releases-zsync|Prikolist2021|LinuxMint_Tweaker|latest|LinuxTweaker-*x86_64.AppImage.zsync'
