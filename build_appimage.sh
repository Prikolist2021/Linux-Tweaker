version: 1
script:
  # Очищаем предыдущую сборку
  - rm -rf AppDir || true
  # Создаём структуру каталогов
  - mkdir -p AppDir/usr/src
  - mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
  # Копируем основной скрипт (ваш файл переименован для ясности)
  - cp linux_tweaker.py AppDir/usr/src/main.py
  # Копируем иконку (создадим её отдельно или используйте любую PNG 256x256)
  - cp icon.png AppDir/usr/share/icons/hicolor/256x256/apps/linux-tweaker.png

AppDir:
  path: ./AppDir
  app_info:
    id: org.example.linuxtweaker
    name: Linux Tweaker
    icon: linux-tweaker
    version: 0.11
    # Точка входа — Python интерпретатор внутри AppImage
    exec: usr/bin/python3
    # Аргумент — путь к нашему скрипту
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

  # Критично: настраиваем переменные окружения для Python
  env:
    PYTHONHOME: '${APPDIR}/usr'
    PYTHONPATH: '${APPDIR}/usr/lib/python3/dist-packages'

AppImage:
  arch: x86_64
  # Автоматическое обновление через GitHub Releases (опционально)
  update-information: 'gh-releases-zsync|Prikolist2021|Linux-Tweaker|latest|Linux-Tweaker-*x86_64.AppImage.zsync'
