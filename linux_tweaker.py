#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Tweaker v1.0 (PyQt5)
Графическая оболочка тюнинга Linux Mint / Ubuntu / Debian на PyQt5.

Полный порт Tkinter-версии v0.6.0:
  - все твики (26), категории, справки
  - вкладка «Приложения» с удалением пакетов через apt
  - бэкапы с timestamp и очисткой старых
  - атомарная запись файлов (tmp + mv)
  - детект применённых настроек, откат, dry-run
  - RU/EN, светлая/тёмная тема
  - mount-опции (noatime), commit= для ext2/3/4
  - симлинки compatdata для Steam
  - PipeWire с пресетами, max_map_count, shutdown_timeout, tmpfs /tmp
  - плавные анимации: hover, появление бейджей, прогресс

Лицензия: MIT
"""
import sys
import os
import re
import subprocess
import time
import shutil
import glob
import pwd
import grp
import threading
import traceback
import faulthandler
from datetime import datetime

from PyQt5.QtCore import (Qt, QObject, QThread, pyqtSignal, QTimer,
                          QPropertyAnimation, QEasingCurve, QRect, QRectF,
                          QSize, QPoint, QParallelAnimationGroup,
                          QSequentialAnimationGroup)
from PyQt5.QtGui import (QIcon, QPixmap, QPainter, QColor, QPen, QBrush,
                         QPainterPath, QLinearGradient, QFont, QTextCursor,
                         QFontDatabase)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QCheckBox, QLineEdit, QComboBox, QTextEdit,
                             QTextBrowser, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QScrollArea,
                             QFrame, QInputDialog, QMessageBox, QMenu,
                             QDialog, QGraphicsOpacityEffect, QSplitter,
                             QSizePolicy, QSpacerItem, QProgressBar,
                             QStyle, QStyleOption)

# ============================================================================
# БЛОК 1. КОНСТАНТЫ
# ============================================================================

APP_NAME = "Linux Tweaker"
APP_VERSION = "1.0"
APP_BUILD_DATE = "20.09.2026"
GITHUB_URL = "https://github.com/Prikolist2021/LinuxMint_Tweaker"
LICENSE_NAME = "MIT"

COMMIT_OK_FS = {"ext2", "ext3", "ext4"}
LOCK_FILE = os.path.join(os.path.expanduser("~"), ".linux-tweaker.lock")

MAX_MAP_COUNT_VALUES = ["65530", "524288", "1048576", "2147483642"]
MAX_MAP_COUNT_DEFAULT = "1048576"

COMMIT_MIN = 1
COMMIT_MAX = 3600
COMMIT_DEFAULT = "60"

SWAPPINESS_MIN = 0
SWAPPINESS_MAX = 200
SWAPPINESS_DEFAULT_DISK = "10"
SWAPPINESS_DEFAULT_ZRAM = "150"

TMPFS_SIZE_DEFAULT = "512M"
TMPFS_SIZE_REGEX = r"[0-9]+[MmGgKk]?"

SUDO_TIMEOUT_DEFAULT = 180
SUDO_TIMEOUT_APT = 900
SUDO_TIMEOUT_GRUB = 300
SUDO_TIMEOUT_INITRAMFS = 600

TIMEOUT_QUICK = 5
TIMEOUT_DPKG_QUERY = 60
TIMEOUT_APT_SIMULATE = 60
TIMEOUT_PKG_SIZE = 30

BACKUP_KEEP_LAST = 5

SHUTDOWN_TIMEOUT_VALUES = ["5s", "8s", "10s", "15s", "20s", "30s", "45s", "60s"]
SHUTDOWN_TIMEOUT_DEFAULT = "8s"
SHUTDOWN_TIMEOUT_SYSTEM_DEFAULT = "90s"

PIPEWIRE_PRESETS = {
    "default": {"min": 512, "quantum": 4096, "max": 8192,
                "label_ru": "Обычный", "label_en": "Default",
                "desc_ru": "подходит большинству пользователей",
                "desc_en": "suitable for most users"},
    "gaming": {"min": 256, "quantum": 1024, "max": 2048,
               "label_ru": "Для игр", "label_en": "Gaming",
               "desc_ru": "минимальная задержка, но может быть треск",
               "desc_en": "minimal latency, but may crackle"},
    "recording": {"min": 1024, "quantum": 8192, "max": 16384,
                  "label_ru": "Для записи", "label_en": "Recording",
                  "desc_ru": "без треска, но с задержкой 0.1–0.2 с",
                  "desc_en": "no crackle, but 0.1–0.2 s latency"},
}
PIPEWIRE_PRESET_DEFAULT = "default"

APPS_CATEGORY_ORDER = {
    "ru": ["Офис", "Графика", "Интернет", "Мультимедиа",
           "Игры", "Утилиты", "Прочее"],
    "en": ["Office", "Graphics", "Internet", "Multimedia",
           "Games", "Utilities", "Other"],
}

SYSTEM_PACKAGE_MASKS = (
    "mint-meta-", "ubuntu-desktop", "xubuntu-", "kubuntu-",
    "lubuntu-", "cinnamon", "mate-desktop", "xfce4",
    "gnome-shell", "ubuntu-minimal", "ubuntu-standard",
)

ZFS_UNITS = [
    "zfs-import-cache.service", "zfs-load-module.service",
    "zfs-mount.service", "zfs-share.service", "zfs-volume-wait.service",
    "zfs-import.target", "zfs.target", "zfs-volumes.target",
]

# ============================================================================
# БЛОК 2. ТЕМЫ
# ============================================================================

THEMES = {
    "light": {
        "bg": "#f5f5f5", "panel": "#ffffff", "fg": "#1e1e1e", "gray": "#616161",
        "border": "#d0d0d0", "tab": "#e4e4e4", "tab_hover": "#d8d8d8",
        "accent": "#2e9e83", "accent2": "#268a72", "accent_fg": "#ffffff",
        "button": "#e4e4e4", "button_hover": "#d8d8d8", "button_dis": "#ececec",
        "fg_dis": "#9a9a9a", "entry": "#ffffff", "terminal": "#ffffff",
        "terminal_fg": "#1e1e1e", "sel": "#cde4f7", "scroll": "#b0b0b0",
        "row_hover": "#ececec", "green": "#2e7d32", "green_bg": "#e2f0e3",
        "gray_bg": "#e8e8e8", "red": "#c62828", "yellow": "#b26a00",
        "blue": "#1565c0", "orange": "#e65100",
    },
    "dark": {
        "bg": "#1e1e1e", "panel": "#252526", "fg": "#d4d4d4", "gray": "#9a9a9a",
        "border": "#3c3c3c", "tab": "#2d2d30", "tab_hover": "#38383d",
        "accent": "#4ec9b0", "accent2": "#3aa794", "accent_fg": "#10201c",
        "button": "#3a3d41", "button_hover": "#46494e", "button_dis": "#2d2d30",
        "fg_dis": "#6a6a6a", "entry": "#333333", "terminal": "#0c0c0c",
        "terminal_fg": "#d4d4d4", "sel": "#094771", "scroll": "#5a5a5a",
        "row_hover": "#2a2d2e", "green": "#4ec9b0", "green_bg": "#17352f",
        "gray_bg": "#2f2f2f", "red": "#f44747", "yellow": "#d7ba7d",
        "blue": "#569cd6", "orange": "#ce9178",
    },
}

# ============================================================================
# БЛОК 3. OPTIONS_META
# ============================================================================

OPTIONS_META = {
    "journald": {
        "ru": ("Логи в ОЗУ (journald)", "Переносит журнал системы в оперативную память и ограничивает его 50 МБ. Бережёт SSD. Работает сразу.", "Логи системы", "хранение журналов systemd в ОЗУ (50 МБ)"),
        "en": ("Logs in RAM (journald)", "Moves the system log to RAM and caps it at 50 MB. Saves SSD. Works immediately.", "System logs", "systemd journals stored in RAM (50 MB)")},
    "audit": {
        "ru": ("audit=0 (GRUB)", "Отключает фоновую запись каждого действия системы. Убирает лишнюю нагрузку. Нужна перезагрузка.", "Ядро и загрузка", "фоновая запись действий"),
        "en": ("audit=0 (GRUB)", "Stops background logging of every system action. Removes extra load. Needs reboot.", "Kernel & boot", "background action logging")},
    "raid": {
        "ru": ("raid=noautodetect (GRUB)", "Пропускает поиск RAID при загрузке, если его нет. Экономит несколько секунд. ВНИМАНИЕ: не включайте, если у вас есть RAID. Нужна перезагрузка.", "Ядро и загрузка", "поиск RAID"),
        "en": ("raid=noautodetect (GRUB)", "Skips RAID probe at boot when you have none. Saves a few seconds. WARNING: do not enable with RAID. Needs reboot.", "Kernel & boot", "RAID probe")},
    "nmi_watchdog": {
        "ru": ("nmi_watchdog=0 (GRUB)", "Отключает служебные прерывания отладки. Убирает микро-фризы в играх. Нужна перезагрузка.", "Ядро и загрузка", "прерывания отладки"),
        "en": ("nmi_watchdog=0 (GRUB)", "Disables debug interrupts. Removes micro-stutters in games. Needs reboot.", "Kernel & boot", "debug interrupts")},
    "itco_wdt": {
        "ru": ("iTCO_wdt blacklist", "Дополнительный способ заглушить NMI watchdog, если параметр ядра не сработал. Модуль iTCO_wdt включает watchdog заново после загрузки. Работает только на Intel. Нужна перезагрузка.", "Ядро и загрузка", "Intel watchdog"),
        "en": ("iTCO_wdt blacklist", "Extra step to silence NMI watchdog when the kernel parameter did not help. Intel only. Needs reboot.", "Kernel & boot", "Intel watchdog")},
    "zfs_services": {
        "ru": ("ZFS: отключение и удаление", "Останавливает и маскирует ZFS-службы — они перестают участвовать в загрузке. Кнопка дополнительно удаляет zfsutils-linux и zfs-zed, чтобы модуль ядра вообще не загружался. Доступна только если ZFS-пулы не найдены.", "Ядро и загрузка", "службы ZFS"),
        "en": ("ZFS: disable and remove", "Stops and masks ZFS services so they no longer take part in boot. The button additionally removes zfsutils-linux and zfs-zed so the kernel module is never loaded. Available only if no ZFS pools are found.", "Kernel & boot", "ZFS services")},
    "shutdown_timeout": {
        "ru": ("Быстрое выключение", "Сокращает ожидание закрытия приложений при выключении с 90 до 8 секунд. Полезно, если игры или тяжёлые программы не закрываются сами. Нужна перезагрузка.", "Ядро и загрузка", "быстрое выключение ПК"),
        "en": ("Fast shutdown", "Cuts app-close timeout at shutdown from 90 to 8 seconds. Useful when games or heavy apps do not close themselves. Needs reboot.", "Kernel & boot", "fast shutdown")},
    "corectrl": {
        "ru": ("CoreCtrl (Polkit)", "Разрешает управлять вентиляторами и частотами AMD без пароля. Работает сразу.", "Видеокарта и графика", "управление AMD без пароля"),
        "en": ("CoreCtrl (Polkit)", "Allows controlling AMD fans and clocks without a password. Works immediately.", "GPU & graphics", "AMD control without password")},
    "ppfeaturemask": {
        "ru": ("amdgpu.ppfeaturemask", "Открывает драйверу AMD полный контроль над питанием карты. Нужна перезагрузка.", "Видеокарта и графика", "контроль питания AMD"),
        "en": ("amdgpu.ppfeaturemask", "Gives the AMD driver full power control of the card. Needs reboot.", "GPU & graphics", "AMD power control")},
    "nvidia_modeset": {
        "ru": ("nvidia-drm.modeset=1 (GRUB)", "Включает корректный вывод NVIDIA для Wayland и переключения режимов. Нужна перезагрузка.", "Видеокарта и графика", "вывод NVIDIA"),
        "en": ("nvidia-drm.modeset=1 (GRUB)", "Enables proper NVIDIA output for Wayland and mode switching. Needs reboot.", "GPU & graphics", "NVIDIA output")},
    "vrr": {
        "ru": ("VRR/FreeSync", "Убирает разрывы картинки в играх на мониторе с FreeSync. Нужен перезаход в сеанс.", "Видеокарта и графика", "плавная картинка"),
        "en": ("VRR/FreeSync", "Removes screen tearing in games on a FreeSync monitor. Requires re-login.", "GPU & graphics", "smooth picture")},
    "radv": {
        "ru": ("RADV_PERFTEST=sam", "Даёт процессору доступ ко всей видеопамяти сразу. Небольшой прирост FPS. Нужен перезаход.", "Видеокарта и графика", "доступ ко всей видеопамяти"),
        "en": ("RADV_PERFTEST=sam", "Gives the CPU access to all VRAM at once. Small FPS gain. Requires re-login.", "GPU & graphics", "full VRAM access")},
    "mesa": {
        "ru": ("MESA_SHADER_CACHE_MAX_SIZE=4G", "Увеличивает кэш шейдеров, игры меньше подтормаживают в первые минуты. Нужен перезаход.", "Видеокарта и графика", "кэш шейдеров"),
        "en": ("MESA_SHADER_CACHE_MAX_SIZE=4G", "Enlarges the shader cache so games stutter less at start. Requires re-login.", "GPU & graphics", "shader cache")},
    "pipewire": {
        "ru": ("PipeWire", "Убирает треск и щелчки звука, увеличив буферы звукового сервера. Нужен перезаход в сеанс.", "Звук", "чистый звук"),
        "en": ("PipeWire", "Removes sound crackling by enlarging sound-server buffers. Requires re-login.", "Sound", "clean sound")},
    "bbr": {
        "ru": ("TCP BBR", "Ускоряет интернет и убирает задержки на нестабильных каналах. Работает сразу.", "Сеть", "быстрый интернет"),
        "en": ("TCP BBR", "Speeds up internet and cuts latency on unstable links. Works immediately.", "Network", "faster internet")},
    "swap": {
        "ru": ("Тюнинг swap", "Настраивает, как охотно система выгружает память в подкачку. Меньше обращений к диску. Работает сразу.", "Память и swap", "поведение подкачки"),
        "en": ("Swap tuning", "Sets how eagerly memory goes to swap. Fewer disk accesses. Works immediately.", "Memory & swap", "swap behaviour")},
    "zram": {
        "ru": ("zram-swap", "Создаёт сжатую память в ОЗУ вместо дискового swap. Ускоряет работу при нехватке памяти. Нужна перезагрузка.", "Память и swap", "сжатая память в ОЗУ"),
        "en": ("zram-swap", "Creates compressed memory in RAM instead of disk swap. Speeds up low-RAM use. Needs reboot.", "Memory & swap", "compressed RAM")},
    "zswap": {
        "ru": ("zswap (GRUB)", "Держит сжатую память в ОЗУ перед записью в swap. Меньше обращений к диску. Нужна перезагрузка. Требует наличия swap.", "Память и swap", "сжатый кэш перед swap"),
        "en": ("zswap (GRUB)", "Keeps compressed memory in RAM before swap. Fewer disk accesses. Needs reboot. Requires swap to be present.", "Memory & swap", "compressed cache before swap")},
    "thp": {
        "ru": ("Крупные блоки памяти (THP)", "Система может выдавать память крупными блоками (2 МБ) вместо мелких (4 КБ). Это ускоряет игры и программы. Значения: madvise — только по запросу (рекомендуется), always — всем подряд, never — выключено.", "Память и swap", "крупные блоки памяти"),
        "en": ("Large memory blocks (THP)", "The system can hand out memory in large 2 MB blocks instead of small 4 KB ones. This speeds up games and apps. Values: madvise — on request only (recommended), always — to everyone, never — off.", "Memory & swap", "large memory blocks")},
    "sysctl_cache": {
        "ru": ("Кэш VFS (sysctl)", "Дольше держит кэш файлов в памяти, файлы открываются быстрее. Работает сразу.", "Ядро и загрузка", "кэш файлов"),
        "en": ("VFS cache (sysctl)", "Keeps file cache in RAM longer so files open faster. Works immediately.", "Kernel & boot", "file cache")},
    "sysctl_numa": {
        "ru": ("Миграция NUMA (sysctl)", "Отключает перенос памяти между ядрами, убирает паузы в играх. Работает сразу.", "Ядро и загрузка", "перенос памяти"),
        "en": ("NUMA migration (sysctl)", "Stops memory moving between cores, removes game stalls. Works immediately.", "Kernel & boot", "memory moving")},
    "reisub": {
        "ru": ("REISUB (Magic SysRq)", "Даёт безопасную перезагрузку при полном зависании через Alt+PrtSc и клавиши R E I S U B. Работает сразу.", "Ядро и загрузка", "безопасная перезагрузка"),
        "en": ("REISUB (Magic SysRq)", "Enables safe reboot on full freeze via Alt+PrtSc and R E I S U B keys. Works immediately.", "Kernel & boot", "safe reboot")},
    "ntsync": {
        "ru": ("ntsync (модуль ядра)", "Ускоряет игры под Wine/Proton за счёт быстрой синхронизации потоков. Работает сразу (нужно ядро 6.14+).", "Игры и совместимость", "быстрые игры под Wine"),
        "en": ("ntsync (kernel module)", "Speeds up Wine/Proton games via faster thread sync. Works immediately (needs kernel 6.14+).", "Gaming & compatibility", "faster Wine games")},
    "max_map_count": {
        "ru": ("vm.max_map_count", "Лимит областей памяти у одного процесса. Некоторые игры под Proton падают, если лимит исчерпан. Рекомендуется 1048576. Ускорения не даёт, только совместимость.", "Игры и совместимость", "лимит областей памяти"),
        "en": ("vm.max_map_count", "Limit of memory mappings per process. Some Proton games crash when the limit is exhausted. 1048576 is recommended. No speed gain, compatibility only.", "Gaming & compatibility", "memory mapping limit")},
    "ntfs3": {
        "ru": ("ntfs3 драйвер", "Включает быстрый драйвер NTFS-дисков вместо медленного. ВНИМАНИЕ: только если у вас есть NTFS-диски. Нужна перезагрузка.", "Диски и файловые системы", "быстрый NTFS"),
        "en": ("ntfs3 driver", "Enables the fast NTFS driver instead of the slow one. WARNING: only if you have NTFS disks. Needs reboot.", "Drives & filesystems", "fast NTFS")},
    "commit": {
        "ru": ("commit=NN (fstab, только ext3/ext4)", "Реже сбрасывает служебную информацию на диск, меньше износа SSD. Работает ТОЛЬКО на ext3/ext4 — для NTFS, FAT32, exFAT, btrfs, xfs параметр не поддерживается и приведёт к ошибке монтирования (система может упасть в emergency-режим). ВНИМАНИЕ: при сбое питания возможна потеря последних записей. Нужна перезагрузка.", "Диски и файловые системы", "реже запись на ext4"),
        "en": ("commit=NN (fstab, ext3/ext4 only)", "Flushes disk metadata less often, less SSD wear. Works ONLY on ext3/ext4 — NTFS, FAT32, exFAT, btrfs, xfs do not support it and will fail to mount (system may drop into emergency mode). WARNING: power loss may lose last writes. Needs reboot.", "Drives & filesystems", "less ext4 disk writing")},
    "tmpfs_tmp": {
        "ru": ("/tmp в ОЗУ (tmpfs, эксперимент)", "Монтирует /tmp в оперативной памяти. Меньше записей на диск, но данные исчезают при перезагрузке. НЕ включайте при гибернации, работе с большими временными файлами и малом объёме ОЗУ.", "Диски и файловые системы", "/tmp в оперативной памяти"),
        "en": ("/tmp in RAM (tmpfs, experimental)", "Mounts /tmp in RAM. Fewer disk writes, but data disappears on reboot. Do NOT enable with hibernation, large temp files or low RAM.", "Drives & filesystems", "/tmp in RAM")},
    "aliases": {
        "ru": ("Команды в .bashrc", "Добавляет удобные команды терминала для обновления и очистки. Работает в новых терминалах.", "Удобство", "команды терминала"),
        "en": ("Commands in .bashrc", "Adds handy terminal commands for updating and cleaning. Works in new terminals.", "Convenience", "terminal commands")},
    "autoupdate": {
        "ru": ("Автообновления", "Сам обновляет систему и Flatpak по расписанию. При включении автоматически глушит apt-daily.timer, apt-daily-upgrade.timer и unattended-upgrades, чтобы не было двойной работы. ВНИМАНИЕ: отключите встроенное автообновление Mint. Работает сразу.", "Обновления", "автообновление по расписанию"),
        "en": ("Auto-updates", "Auto-updates system and Flatpak on schedule. When enabled, automatically masks apt-daily.timer, apt-daily-upgrade.timer and unattended-upgrades to avoid double work. WARNING: disable Mint's built-in auto-update. Works immediately.", "Updates", "scheduled auto-update")},
}

CAT_ORDER = {
    "ru": ["Видеокарта и графика", "Ядро и загрузка", "Логи системы", "Звук",
           "Сеть", "Память и swap", "Диски и файловые системы",
           "Игры и совместимость", "Удобство", "Обновления"],
    "en": ["GPU & graphics", "Kernel & boot", "System logs", "Sound", "Network",
           "Memory & swap", "Drives & filesystems", "Gaming & compatibility",
           "Convenience", "Updates"],
}

# ============================================================================
# БЛОК 4. SERVICES_META + SERVICES_HELP
# ============================================================================

SERVICES_META = {
    "avahi-daemon.service": {
        "ru": "Поиск устройств в домашней сети: принтеров, телевизоров, Chromecast. Не нужен, если у вас нет сетевого принтера.",
        "en": "Finds devices on your home network: printers, TVs, Chromecast. Not needed without a network printer."},
    "avahi-daemon.socket": {
        "ru": "Сокет, который будит службу avahi при обращении из сети. Сам по себе бесполезен без службы avahi.",
        "en": "Socket that wakes the avahi service on network request. Useless on its own without the avahi service."},
    "bluetooth.service": {
        "ru": "Служба Bluetooth: беспроводные мыши, клавиатуры, наушники, геймпады, файлообмен. Не отключайте, если пользуетесь Bluetooth-устройствами.",
        "en": "Bluetooth service: wireless mice, keyboards, headphones, gamepads, file transfer. Do not disable if you use Bluetooth devices."},
    "cups-browsed.service": {
        "ru": "Ищет сетевые принтеры автоматически. Не нужен, если принтера нет или он подключён по USB.",
        "en": "Auto-discovers network printers. Not needed without a printer or with a USB printer."},
    "cups.service": {
        "ru": "Печать и сканирование. Не нужно, если у вас нет принтера или сканера.",
        "en": "Printing and scanning. Not needed without a printer or scanner."},
    "cups.socket": {
        "ru": "Сокет, который будит службу печати при обращении. Сам по себе бесполезен без службы cups.",
        "en": "Socket that wakes the print service on request. Useless on its own without the cups service."},
    "ModemManager.service": {
        "ru": "Работа с мобильными модемами через USB или сим-карту. Не нужна, если интернет по Wi-Fi или кабелю.",
        "en": "Handles mobile modems via USB or SIM. Not needed if internet is Wi-Fi or cable."},
    "openvpn.service": {
        "ru": "Встроенный VPN-сервер. Не нужен, если вы не поднимаете собственный VPN.",
        "en": "Built-in VPN server. Not needed unless you run your own VPN."},
    "lvm2-monitor.service": {
        "ru": "Следит за объединением дисков в один большой (LVM). Не нужен при обычной установке Mint/Ubuntu.",
        "en": "Watches disks joined into one big volume (LVM). Not needed on a standard Mint/Ubuntu install."},
    "switcheroo-control.service": {
        "ru": "Переключает встроенную и отдельную графику на ноутбуках. Не нужен на настольном ПК.",
        "en": "Switches integrated and discrete graphics on laptops. Not needed on a desktop."},
    "touchegg.service": {
        "ru": "Распознаёт жесты тачпада и сенсора. Не нужен на настольном ПК без сенсора.",
        "en": "Recognizes touchpad and touchscreen gestures. Not needed on a desktop without a touchscreen."},
    "zfs-zed.service": {
        "ru": "Следит за дисковыми массивами ZFS и предупреждает о проблемах. Не нужен без ZFS.",
        "en": "Watches ZFS disk arrays and warns on problems. Not needed without ZFS."},
    "kerneloops.service": {
        "ru": "Отправляет разработчикам отчёты о сбоях ядра. На домашнем ПК это лишняя нагрузка и трафик.",
        "en": "Sends kernel crash reports to developers. On a home PC this is extra load and traffic."},
    "rsyslog.service": {
        "ru": "Пишет подробные журналы системы на диск. Отключение экономит место и уменьшает износ SSD; важные сообщения остаются в журнале systemd.",
        "en": "Writes detailed system logs to disk. Disabling saves space and reduces SSD wear; important messages remain in the systemd journal."},
    "apt-daily.timer": {
        "ru": "Ежедневно скачивает списки пакетов и обновления в фоне. Если вы включили автообновления в твикере, этот таймер глушится автоматически.",
        "en": "Downloads package lists and updates daily in the background. If you enable auto-updates in the tweaker, this timer is masked automatically."},
    "apt-daily-upgrade.timer": {
        "ru": "Ежедневно устанавливает обновления в фоне. Может конфликтовать с автообновлениями твикера. Глушится автоматически при их включении.",
        "en": "Installs updates daily in the background. May conflict with the tweaker's auto-updates. Masked automatically when they are enabled."},
    "unattended-upgrades.service": {
        "ru": "Устанавливает обновления безопасности автоматически. Если вы управляете обновлениями сами, служба не нужна.",
        "en": "Installs security updates automatically. If you manage updates yourself, the service is not needed."},
    "apport.service": {
        "ru": "Собирает краш-репорты (отчёты о падениях программ) и предлагает отправить их разработчикам. На домашнем ПК не нужна: только занимает место в /var/crash и показывает всплывающие окна при падении приложений.",
        "en": "Collects crash reports (reports about program crashes) and offers to send them to developers. Not needed on a home PC: only fills /var/crash and shows popups when apps crash."},
}

SERVICES_ORDER = list(SERVICES_META.keys())

SERVICES_HELP = {
    "avahi-daemon.service": {
        "ru": "Avahi — это служба, которая ищет устройства в локальной сети без настройки. Она использует протокол mDNS/DNS-SD: устройства сами объявляют о себе, и вы видите их в списке доступных принтеров, колонок, телевизоров. Например, включив Chromecast, вы сразу видите его в браузере — это работа Avahi.\n\nНа домашнем ПК без сетевого принтера и без Chromecast/AirPlay служба не нужна. Она периодически рассылает пакеты в сеть, но делает это вхолостую.\n\nОтключение безопасно. Если позже захотите снова найти сетевое устройство — включите службу обратно.",
        "en": "Avahi is a service that discovers devices on your local network without setup. It uses the mDNS/DNS-SD protocol: devices announce themselves, and you see them in the list of available printers, speakers, TVs.\n\nOn a home PC without a network printer and without Chromecast/AirPlay, the service is unneeded. It periodically broadcasts into the network, but does so idle.\n\nDisabling is safe. If you later want to find a network device again, re-enable the service."},
    "avahi-daemon.socket": {
        "ru": "Сокет — это как «розетка», которая «будит» службу Avahi, когда в сеть приходит первый запрос. У сокета и службы общая задача: пока никто не ищет устройства, Avahi может спать и не занимать ресурсы.\n\nЭтот сокет бесполезен сам по себе, без службы Avahi. Если Avahi отключена, сокет тоже не нужен.\n\nОтключайте его вместе со службой Avahi.",
        "en": "A socket is like a “plug” that wakes the Avahi service when the first network request arrives. The socket and the service share a task: while nobody is looking for devices, Avahi can sleep and use no resources.\n\nThis socket is useless on its own without the Avahi service. If Avahi is disabled, the socket is unneeded too.\n\nDisable it together with the Avahi service."},
    "bluetooth.service": {
        "ru": "Bluetooth — это служба для беспроводных устройств: мыши, клавиатуры, наушники, колонки, геймпады, а также передача файлов между устройствами. Демон bluetoothd работает в фоне и обслуживает подключение и отключение устройств.\n\nЕсли вы не пользуетесь Bluetooth вообще, службу можно отключить. Выигрыш в загрузке минимальный — доли секунды, — но пропадает фоновая активность и закрывается поверхность атаки.\n\nВНИМАНИЕ: после отключения Bluetooth-устройства перестанут подключаться. Если у вас беспроводная мышь, клавиатура или наушники — не отключайте.",
        "en": "Bluetooth is a service for wireless devices: mice, keyboards, headphones, speakers, gamepads, and file transfer between devices. The bluetoothd daemon runs in the background and handles connecting and disconnecting devices.\n\nIf you do not use Bluetooth at all, the service can be disabled. The boot-time gain is minimal — fractions of a second — but background activity disappears and the attack surface shrinks.\n\nWARNING: after disabling, Bluetooth devices will stop connecting. If you use a wireless mouse, keyboard or headphones — do not disable."},
    "cups-browsed.service": {
        "ru": "cups-browsed — это часть системы печати CUPS. Она автоматически ищет сетевые принтеры и добавляет их в список доступных.\n\nДома эта служба не нужна, если у вас нет сетевого принтера. Если принтер подключён по USB, служба тоже бесполезна — она ищет только сетевые устройства.\n\nОтключение безопасно.",
        "en": "cups-browsed is part of the CUPS printing system. It automatically discovers network printers and adds them to the list of available ones.\n\nAt home the service is unneeded if you have no network printer. If the printer is connected via USB, the service is also useless — it only looks for network devices.\n\nDisabling is safe."},
    "cups.service": {
        "ru": "CUPS — это служба печати и сканирования. Все программы, которые что-то печатают или сканируют, обращаются к ней.\n\nЕсли у вас нет принтера или сканера, CUPS просто висит в фоне и не делает ничего полезного. Отключение освобождает память и убирает фоновую активность.\n\nОтключение безопасно.",
        "en": "CUPS is the printing and scanning service. Every program that prints or scans talks to it.\n\nIf you have no printer or scanner, CUPS just idles in the background doing nothing useful. Disabling it frees memory and removes background activity.\n\nDisabling is safe."},
    "cups.socket": {
        "ru": "Сокет — это «розетка», которая будит службу печати CUPS, когда какая-то программа пытается что-то напечатать. Пока никто не печатает, CUPS может не работать.\n\nЭтот сокет бесполезен без службы CUPS. Если вы отключили CUPS, сокет тоже не нужен.\n\nОтключайте его вместе со службой CUPS.",
        "en": "A socket is a “plug” that wakes the CUPS print service when a program tries to print. While nobody prints, CUPS does not have to run.\n\nThis socket is useless without the CUPS service. If you disabled CUPS, the socket is unneeded too.\n\nDisable it together with the CUPS service."},
    "ModemManager.service": {
        "ru": "ModemManager — это служба для работы с мобильными модемами. Она управляет устройствами, которые подключаются к компьютеру через USB или встроены в ноутбук и работают через сим-карту.\n\nНа стационарном ПК без модема эта служба не нужна. Более того, она иногда мешает устройствам, которые определяются как последовательный порт (serial port): Arduino, переходники USB-Serial, отладочные платы.\n\nЕсли у вас есть такие устройства и они работают нестабильно — отключение ModemManager часто решает проблему.",
        "en": "ModemManager is a service for mobile modems. It manages devices plugged in via USB or built into a laptop and working via SIM.\n\nOn a desktop PC without a modem the service is unneeded. Moreover, it sometimes interferes with devices that appear as serial ports: Arduino, USB-Serial adapters, development boards.\n\nIf you have such devices and they work unreliably, disabling ModemManager often fixes the problem."},
    "openvpn.service": {
        "ru": "OpenVPN — это система для создания защищённых туннелей между компьютерами. Служба openvpn.service относится к серверной части: она принимает входящие подключения от других устройств. Если вы обычно используете VPN-клиент (например, подключаетесь к коммерческому VPN), это не та служба.\n\nДома эту службу держат только те, кто поднимает собственный VPN-сервер.\n\nОтключение безопасно.",
        "en": "OpenVPN is a system for creating secure tunnels between computers. The openvpn.service unit is the server side: it accepts incoming connections from other devices. If you usually use a VPN client (for example, connecting to a commercial VPN), that is not this service.\n\nAt home only those who run their own VPN server keep this service.\n\nDisabling is safe."},
    "lvm2-monitor.service": {
        "ru": "LVM — это способ объединить несколько дисков или разделов в один большой «виртуальный» диск. Служба lvm2-monitor следит за состоянием таких объединений и уведомляет о проблемах.\n\nПри обычной установке Linux Mint или Ubuntu LVM не используется. Диски и разделы подключаются напрямую.\n\nОтключение безопасно. Не отключайте, если вы специально настраивали LVM.",
        "en": "LVM is a way to combine several disks or partitions into one big “virtual” disk. The lvm2-monitor service watches such unions and reports problems.\n\nA standard Linux Mint or Ubuntu install does not use LVM. Disks and partitions are attached directly.\n\nDisabling is safe. Do not disable it if you specifically configured LVM."},
    "switcheroo-control.service": {
        "ru": "Switcheroo — это служба для ноутбуков с двумя видеокартами (обычно встроенной Intel и отдельной NVIDIA или AMD). Она позволяет переключаться между картами.\n\nНа настольном ПК с одной видеокартой эта служба не нужна.\n\nОтключение безопасно. Если у вас ноутбук с двумя картами, лучше оставить.",
        "en": "Switcheroo is a service for laptops with two GPUs (usually an integrated Intel and a discrete NVIDIA or AMD). It lets you switch between them.\n\nOn a desktop PC with a single GPU the service is unneeded.\n\nDisabling is safe. If you have a laptop with two GPUs, better leave it enabled."},
    "touchegg.service": {
        "ru": "Touchegg — это служба, которая распознаёт мультитач-жесты на тачпадах и сенсорных экранах.\n\nНа настольном ПК без сенсорного ввода эта служба не нужна.\n\nОтключение безопасно. Если у вас ноутбук с тачпадом и вы пользуетесь жестами — оставьте включённой.",
        "en": "Touchegg is a service that recognizes multitouch gestures on touchpads and touchscreens.\n\nOn a desktop PC without touch input the service is unneeded.\n\nDisabling is safe. If you have a laptop with a touchpad and use gestures, keep it enabled."},
    "zfs-zed.service": {
        "ru": "ZFS — это современная файловая система с поддержкой дисковых массивов. ZED — это демон ZFS, который следит за состоянием массивов и предупреждает о проблемах с дисками.\n\nНа домашнем ПК с обычными файловыми системами (ext4, btrfs) ZFS не используется.\n\nОтключение безопасно. Не отключайте, если у вас действительно есть ZFS-пулы.",
        "en": "ZFS is a modern file system with disk arrays. ZED is the ZFS daemon that watches array health and warns about disk problems.\n\nOn a home PC with conventional file systems (ext4, btrfs) ZFS is not used.\n\nDisabling is safe. Do not disable it if you actually have ZFS pools."},
    "kerneloops.service": {
        "ru": "kerneloops — это служба, которая собирает отчёты о сбоях ядра (kernel oops) и отправляет их разработчикам. Информация уходит на сервер проекта.\n\nНа домашнем ПК эта служба приносит мало пользы. Она лишь добавляет фоновую нагрузку и исходящий трафик.\n\nОтключение безопасно. Оставьте включённой, если хотите помогать разработчикам ядра.",
        "en": "kerneloops is a service that collects reports about kernel crashes (kernel oops) and sends them to developers. The information goes to the project's server.\n\nOn a home PC the service brings little benefit. It only adds background load and outgoing traffic.\n\nDisabling is safe. Keep it enabled if you want to help kernel developers."},
    "rsyslog.service": {
        "ru": "rsyslog — это служба, которая постоянно пишет подробные журналы системы в текстовые файлы на диске. Каждую секунду она дописывает туда события: запуск служб, ошибки, вход пользователей.\n\nОтключение освобождает место в /var/log и уменьшает износ SSD. Важные сообщения при этом никуда не пропадают — они идут в журнал systemd, который смотрится командой journalctl.\n\nОтключение безопасно и работает сразу.",
        "en": "rsyslog is a service that constantly writes detailed system logs into text files on the disk. Every second it appends events: service starts, errors, user logins.\n\nDisabling it frees space in /var/log and reduces SSD wear. Important messages are not lost — they go to the systemd journal, which you can view with journalctl.\n\nDisabling is safe and works immediately."},
    "apt-daily.timer": {
        "ru": "apt-daily.timer — это systemd-таймер, который раз в сутки запускает загрузку свежих списков пакетов и обновлений в фоне.\n\nПроблема в том, что если вы уже включили автообновления в твикере, этот таймер начинает работать параллельно и создаёт двойную нагрузку. Твикер глушит его автоматически при включении автообновлений.\n\nОтключайте его вручную только если вы вообще не хотите, чтобы система что-то скачивала в фоне.",
        "en": "apt-daily.timer is a systemd timer that once a day fetches fresh package lists and updates in the background.\n\nThe problem is that if you have already enabled auto-updates in the tweaker, this timer runs in parallel and creates a double load. The tweaker masks it automatically when auto-updates are enabled.\n\nDisable it manually only if you do not want the system to download anything in the background at all."},
    "apt-daily-upgrade.timer": {
        "ru": "apt-daily-upgrade.timer — это дополнение к apt-daily.timer: он не просто скачивает списки пакетов, а устанавливает обновления в фоне.\n\nЕсли вы включили автообновления в твикере, этот таймер дублирует их работу. Твикер глушит его автоматически.\n\nОтключайте вручную только если вы точно управляете обновлениями сами.",
        "en": "apt-daily-upgrade.timer complements apt-daily.timer: it not only downloads package lists but actually installs updates in the background.\n\nIf you enabled auto-updates in the tweaker, this timer duplicates their work. The tweaker masks it automatically.\n\nDisable it manually only if you truly manage updates yourself."},
    "unattended-upgrades.service": {
        "ru": "unattended-upgrades — это служба, которая устанавливает обновления безопасности автоматически, без вашего участия.\n\nНа домашнем ПК это удобно, если вы не хотите думать об обновлениях. Но если вы уже управляете обновлениями через твикер, служба становится лишней. Твикер глушит её автоматически при включении автообновлений.\n\nЕсли вы не включаете автообновления в твикере и не управляете обновлениями вручную — лучше оставить службу включённой.",
        "en": "unattended-upgrades is a service that installs security updates automatically, without your involvement.\n\nOn a home PC this is convenient if you do not want to think about updates. But if you already manage updates through the tweaker, the service becomes redundant. The tweaker masks it automatically when auto-updates are enabled.\n\nIf you do not enable auto-updates in the tweaker and do not manage updates manually — better leave the service enabled."},
    "apport.service": {
        "ru": "Apport — это система сбора краш-репортов в Ubuntu и Linux Mint. Когда какая-то программа падает, Apport перехватывает это, сохраняет дамп памяти в /var/crash и предлагает отправить отчёт разработчикам.\n\nНа домашнем ПК эта служба почти всегда не нужна. Она тратит немного ресурсов на перехват падений, накапливает дампы в /var/crash (которые потом надо чистить), и показывает всплывающее окно при падении любой программы — даже если вам это неинтересно.\n\nОтключение безопасно: если у вас упадёт приложение, вы просто не получите всплывающее окно и не сможете отправить баг-репорт. Сама программа от этого работать не перестанет.\n\nЕсли вы активно помогаете разработчикам Ubuntu/Mint и отправляете баг-репорты — оставьте службу включённой.",
        "en": "Apport is the crash-report collection system in Ubuntu and Linux Mint. When a program crashes, Apport catches it, saves a memory dump in /var/crash and offers to send a report to developers.\n\nOn a home PC this service is almost always unneeded. It spends a little resources on catching crashes, accumulates dumps in /var/crash (which you then have to clean), and shows a popup whenever any program crashes — even if you are not interested.\n\nDisabling is safe: if an app crashes, you simply will not get a popup and will not be able to send a bug report. The app itself will not stop working because of this.\n\nIf you actively help Ubuntu/Mint developers and send bug reports — keep the service enabled."},
}

# ============================================================================
# БЛОК 5. OPTIONS_HELP (сокращённые тексты — полные в Tkinter-версии)
# ============================================================================

def _help_block(ru, en):
    return {"ru": ru, "en": en}

OPTIONS_HELP = {
    "journald": _help_block(
        "Журнал systemd — это запись всех событий системы: запуск служб, ошибки, подключения устройств. Обычно он хранится на диске и со временем разрастается до сотен мегабайт.\n\nЭта опция переносит журнал в оперативную память и ограничивает его 50 мегабайтами. Диск перестаёт получать постоянные записи, а значит, меньше изнашивается.\n\nНе включайте, если вы привыкли разбирать старые проблемы по логам: после перезагрузки журнал в памяти исчезнет.\n\nОпция применяется сразу, перезагрузка не нужна.",
        "The systemd journal records all system events: service starts, errors, device plugs. It usually lives on disk and grows to hundreds of megabytes over time.\n\nThis option moves the journal into RAM and caps it at 50 MB. The disk stops getting constant writes, which means less wear.\n\nDo not enable it if you are used to troubleshooting by reading old logs: after a reboot the journal in RAM disappears.\n\nThe option applies immediately, no reboot needed."),
    "itco_wdt": _help_block(
        "Этот твик — дополнение к «nmi_watchdog=0 (GRUB)». На многих системах с Intel-чипсетом после загрузки ядра модуль iTCO_wdt снова включает NMI watchdog, даже если вы передали параметр nmi_watchdog=0. В итоге /proc/sys/kernel/nmi_watchdog снова становится 1, и микро-фризы возвращаются.\n\nРешение — заблокировать модуль iTCO_wdt, чтобы он вообще не загружался.\n\nПроверить состояние после перезагрузки: cat /proc/sys/kernel/nmi_watchdog — должно быть 0.",
        "This tweak complements «nmi_watchdog=0 (GRUB)». On many systems with an Intel chipset, the iTCO_wdt module re-enables the NMI watchdog after the kernel is loaded — even if you passed nmi_watchdog=0.\n\nThe fix is to block the iTCO_wdt module entirely.\n\nCheck the state after reboot: cat /proc/sys/kernel/nmi_watchdog — should be 0."),
    "zfs_services": _help_block(
        "ZFS — это файловая система и менеджер томов, который используется на серверах и NAS. На домашнем ПК его обычно не ставят, но некоторые дистрибутивы (Ubuntu, Mint) устанавливают пакеты ZFS «на всякий случай».\n\nПроблема: даже если ZFS не используется, его службы запускаются при загрузке и тянут за собой systemd-udev-settle.service. В итоге загрузка замедляется без пользы.\n\nЭтот твик делает две вещи. Первое — останавливает и маскирует ZFS-службы (обратимо). Второе — кнопка «Удалить пакеты (осторожно)» полностью удаляет zfsutils-linux и zfs-zed (необратимо).\n\nПеред удалением твикер проверяет, используется ли ZFS. Если найден хотя бы один пул — кнопка серой.",
        "ZFS is a file system and volume manager used on servers and NAS. It is usually not installed on a home PC, but some distributions (Ubuntu, Mint) install ZFS packages «just in case».\n\nThe problem: even if ZFS is not used, its services run at boot and pull in systemd-udev-settle.service.\n\nThis tweak does two things. First — stops and masks ZFS services (reversible). Second — the «Remove packages (careful)» button fully removes zfsutils-linux and zfs-zed (irreversible).\n\nBefore removal the tweaker checks whether ZFS is used. If at least one pool is found — the button is greyed out."),
    "shutdown_timeout": _help_block(
        "По умолчанию systemd ждёт 90 секунд, пока приложения и службы закроются при выключении ПК. Если какая-то программа не отвечает, система показывает «A stop job is running» и висит все 90 секунд.\n\nЭтот твик сокращает ожидание до 5–60 секунд (по умолчанию 8). Выключение становится быстрым.\n\nВНИМАНИЕ: если приложение в момент выключения сохраняло данные (база, торрент, редактор), его могут убить до завершения записи. Для обычного домашнего ПК риск минимальный, но для систем с базами данных — не включайте.",
        "By default systemd waits 90 seconds for apps and services to close at shutdown. If some program does not respond, the system shows «A stop job is running» and hangs the full 90 seconds.\n\nThis tweak cuts the wait to 5–60 seconds (8 by default).\n\nWARNING: if an app was saving data at shutdown (database, torrent, editor), it may be killed before finishing the write."),
    "corectrl": _help_block(
        "CoreCtrl — это программа для тонкой настройки видеокарт AMD. Она позволяет менять частоты, управлять вентиляторами, задавать лимиты питания и следить за температурой.\n\nПо умолчанию все действия CoreCtrl требуют пароль администратора. Данная опция создаёт правило Polkit, которое разрешает вашей группе пользователей управлять видеокартой без пароля.\n\nНе включайте, если у вас не AMD или вы не пользуетесь CoreCtrl.",
        "CoreCtrl is a tool for fine-tuning AMD graphics cards. It lets you change clocks, control fans, set power limits and monitor temperature.\n\nBy default every CoreCtrl action asks for the admin password. This option creates a Polkit rule that allows your user group to control the GPU without a password.\n\nDo not enable it if you do not have an AMD GPU or do not use CoreCtrl."),
    "ppfeaturemask": _help_block(
        "На старых ядрах драйвер amdgpu блокирует часть функций управления питанием видеокарты AMD. Параметр amdgpu.ppfeaturemask=0xffffffff снимает блокировку и открывает драйверу полный контроль над частотами и питанием.\n\nНе включайте, если у вас не AMD или вы не собираетесь настраивать частоты.\n\nПараметр добавляется в GRUB, изменения вступают в силу после перезагрузки.",
        "On older kernels the amdgpu driver blocks some AMD GPU power-management features. The parameter amdgpu.ppfeaturemask=0xffffffff lifts the block.\n\nDo not enable it if you do not have AMD or do not plan to tune clocks.\n\nThe parameter is added to GRUB, changes take effect after a reboot."),
    "nvidia_modeset": _help_block(
        "Для проприетарного драйвера NVIDIA нужен специальный режим вывода видео — kernel modesetting (KMS). Без него система работает с устаревшим способом вывода, из-за чего не запускается Wayland и возможны проблемы при переключении видеорежимов.\n\nНе включайте, если у вас не NVIDIA.",
        "The proprietary NVIDIA driver needs a special video-output mode — kernel modesetting (KMS). Without it Wayland does not work, and mode switching may glitch.\n\nDo not enable it if you do not have NVIDIA."),
    "vrr": _help_block(
        "VRR (он же FreeSync или Adaptive Sync) — это переменная частота обновления монитора. Обычно монитор обновляется с фиксированной частотой, например 60 Гц. Если игра выдаёт 47 FPS, кадры попадают на разные обновления, и картинка «рвётся». С VRR монитор подстраивается под текущий FPS.\n\nНе включайте, если у вас монитор без поддержки FreeSync, видеокарта не AMD, или вы работаете в Wayland.",
        "VRR (also known as FreeSync or Adaptive Sync) is a variable monitor refresh rate. If a game outputs 47 FPS, frames land on different refreshes and the picture tears. With VRR the monitor adapts to the current FPS.\n\nDo not enable it if your monitor does not support FreeSync, your GPU is not AMD, or you run Wayland."),
    "radv": _help_block(
        "SAM (Smart Access Memory) или Resizable BAR — это технология, при которой процессор получает доступ ко всей видеопамяти сразу, а не кусками по 256 МБ. Обычно это даёт небольшой прирост FPS в играх.\n\nНе включайте, если у вас не AMD или старая материнская плата без поддержки Resizable BAR.",
        "SAM (Smart Access Memory) or Resizable BAR is a technology where the CPU gets access to all VRAM at once instead of chunks of 256 MB. It usually gives a small FPS gain.\n\nDo not enable it if you do not have AMD or have an old motherboard without Resizable BAR support."),
    "mesa": _help_block(
        "MESA — это набор графических библиотек, которые используют игры и программы для вывода картинки. Одна из функций MESA — кэширование скомпилированных шейдеров.\n\nПо умолчанию кэш MESA небольшой, и когда он переполняется, старые шейдеры удаляются. Если увеличить кэш до 4 ГБ, шейдеры останутся, и игра будет запускаться сразу плавно.",
        "MESA is a set of graphics libraries that games and applications use to render the picture. One of MESA's features is caching compiled shaders.\n\nBy default the MESA cache is small, and when it overflows, old shaders are deleted. If you raise the cache to 4 GB, shaders stay, and the game launches smoothly right away."),
    "pipewire": _help_block(
        "PipeWire — это звуковой сервер, который передаёт звук от приложений к колонкам и наушникам. У него есть настройка размера буферов: маленькие буферы дают низкую задержку, но на некоторых системах вызывают треск и щелчки. Большие буферы убирают артефакты, но добавляют небольшую задержку.\n\nЕсть три режима на выбор:\n\n• Обычный — подходит большинству пользователей.\n• Для игр — минимальная задержка звука; может вызывать треск на слабых системах.\n• Для записи — максимальная стабильность; звук может отставать на 0.1–0.2 секунды. Для музыкантов не подходит.",
        "PipeWire is the sound server that hands audio from applications to speakers and headphones. It has a buffer-size setting: small buffers give low latency but on some systems cause crackling and pops.\n\nThere are three modes:\n\n• Default — suitable for most users.\n• Gaming — minimal audio latency; may crackle on weak systems.\n• Recording — maximum stability; sound may lag by 0.1–0.2 seconds. Not suitable for musicians."),
    "bbr": _help_block(
        "BBR — это современный алгоритм управления перегрузками TCP, разработанный Google. Он определяет, с какой скоростью отправлять данные по сети, чтобы не перегружать канал и не терять пакеты. Старый алгоритм CUBIC работает хорошо на стабильных каналах, но BBR выигрывает на нестабильных.\n\nНа Wi-Fi, VPN, мобильном интернете скорость загрузки становится выше, а задержки — меньше.",
        "BBR is a modern TCP congestion-control algorithm developed by Google. It decides at what rate to send data over the network so the link is not overloaded. The older CUBIC algorithm works well on stable links, but BBR wins on unstable ones.\n\nOn Wi-Fi, VPN, mobile internet, download speed increases and latency drops."),
    "swap": _help_block(
        "Swap (подкачка) — это область на диске или в сжатой памяти, куда система складывает редко используемые данные, когда оперативной памяти не хватает. Насколько охотно система это делает — задаётся числом vm.swappiness от 0 до 200.\n\nВысокое значение (например, 150) означает: система активно переносит данные в swap. Это выгодно, если swap — это zram (сжатая память в ОЗУ). Низкое значение (10) означает: система старается держать данные в ОЗУ. Это выгодно, если swap на диске.",
        "Swap is a region on disk or in compressed memory where the system stores rarely used data when RAM runs low. How eagerly it does this is controlled by vm.swappiness, a number from 0 to 200.\n\nA high value (say 150) means the system actively moves data to swap. This is good if swap is zram. A low value (10) means the system tries to keep data in RAM. This is good if swap is on a disk."),
    "zram": _help_block(
        "zram — это сжатая область в оперативной памяти, которую система использует как дополнительную память. Когда ОЗУ не хватает, данные не сбрасываются на диск, а сжимаются в памяти. Скорость обращения к сжатой памяти намного выше, чем к диску, а ресурс SSD не расходуется.\n\nНе включайте, если у вас много оперативной памяти (16 ГБ и больше). Также опция не имеет смысла, если пакет zram-generator не установлен.",
        "zram is a compressed area in RAM used by the system as extra memory. When RAM runs low, data is not written to disk — it is compressed in memory. Accessing compressed memory is much faster than accessing the disk.\n\nDo not enable it if you have plenty of RAM (16 GB or more). Also it makes no sense if zram-generator is not installed."),
    "zswap": _help_block(
        "zswap — это сжатый кэш в оперативной памяти, который стоит перед обычным swap. Когда системе нужно выгрузить страницу памяти, она сначала пробует сжать её и оставить в zswap. Только если zswap переполнен, данные уходят на диск.\n\nВАЖНО: zswap требует наличия swap. Если в системе swap отсутствует, параметры не сработают.",
        "zswap is a compressed cache in RAM that sits in front of regular swap. When the system needs to swap out a page, it first tries to compress it and keep it in zswap. Only when zswap overflows does data go to disk.\n\nIMPORTANT: zswap requires swap to be present."),
    "thp": _help_block(
        "Память компьютера делится на страницы — небольшие кусочки. Обычно это страницы по 4 КБ. Когда программа работает с большими объёмами данных, системе приходится управлять миллионами таких мелких страниц, и это отнимает время.\n\nРежим THP (Transparent Huge Pages) позволяет выдавать память крупными страницами по 2 МБ. Управлять ими проще, поэтому игры и тяжёлые программы работают чуть быстрее. Есть три режима: always — выдавать крупные страницы всем, madvise — только тем программам, которые сами попросят (самый безопасный), never — не использовать вообще.\n\nРекомендуется значение madvise.",
        "Computer memory is divided into pages — small chunks. Normally these are 4 KB pages. THP (Transparent Huge Pages) mode lets the system hand out memory in large 2 MB pages.\n\nThere are three modes: always — hand out large pages to everyone, madvise — only to programs that explicitly ask (safest), never — do not use at all.\n\nThe recommended value is madvise."),
    "sysctl_cache": _help_block(
        "Ядро Linux держит в оперативной памяти кэш файлов и папок — те данные, которые недавно читались с диска. Когда кэш переполняется, ядро освобождает его часть. Параметр vfs_cache_pressure говорит ядру, насколько агрессивно освобождать кэш.\n\nЗначение по умолчанию — 100. Опция ставит 50, то есть ядро будет освобождать кэш в два раза реже.\n\nНе включайте, если у вас мало оперативной памяти (меньше 4 ГБ).",
        "The Linux kernel keeps a cache of files and folders in RAM. The vfs_cache_pressure parameter tells the kernel how aggressively to free the cache.\n\nThe default value is 100. This option sets 50, meaning the kernel will free the cache half as often.\n\nDo not enable it if you have little RAM (less than 4 GB)."),
    "sysctl_numa": _help_block(
        "NUMA — это архитектура памяти на серверах с несколькими процессорами. На домашнем ПК NUMA нет — процессор один. Но механизм балансировки всё равно работает и создаёт микропаузы в работе, особенно в играх. Отключение этой балансировки убирает паузы.",
        "NUMA is a memory architecture on servers with several processors. A home PC has no NUMA — one CPU. But the balancing mechanism still runs and causes micro-pauses, especially in games. Disabling this balancing removes the pauses."),
    "reisub": _help_block(
        "Magic SysRq — это набор аварийных команд ядра, которые вызываются сочетанием Alt+PrtSc и определённой буквы. Они работают даже когда система полностью зависла. Самая полезная последовательность — R E I S U B.\n\nКаждая буква означает: R — вернуть управление клавиатуре, E — вежливо завершить процессы, I — убить оставшиеся, S — синхронизировать данные с диском, U — перемонтировать диски в режим только для чтения, B — перезагрузиться.",
        "Magic SysRq is a set of emergency kernel commands triggered by Alt+PrtSc and a certain letter. They work even when the system is completely frozen. The most useful sequence is R E I S U B.\n\nEach letter means: R — reclaim keyboard, E — politely terminate processes, I — kill the rest, S — sync data to disk, U — remount disks read-only, B — reboot."),
    "ntsync": _help_block(
        "ntsync — это новый модуль ядра, который ускоряет синхронизацию потоков в Wine и Proton. Игры под Windows активно используют примитивы синхронизации (мьютексы, события, семафоры), и их реализация в Wine долго была медленной. ntsync делает её значительно быстрее.\n\nНе включайте, если у вас ядро старше 6.14 без патча.",
        "ntsync is a new kernel module that speeds up thread synchronization in Wine and Proton. Windows games heavily use synchronization primitives, and their implementation in Wine was slow for a long time. ntsync makes it significantly faster.\n\nDo not enable it if your kernel is older than 6.14 without a patch."),
    "max_map_count": _help_block(
        "vm.max_map_count — это лимит областей памяти у одного процесса. Каждый раз, когда программа выделяет память через mmap, ядро создаёт «область памяти». Если лимит исчерпан, программа падает с ошибкой «Cannot allocate memory».\n\nНекоторые игры под Proton создают очень много областей памяти. Если лимит исчерпан, игра вылетает при запуске.\n\nРекомендуемое значение — 1048576. ВАЖНО: этот твик не ускоряет игры и не исправляет обычную нехватку памяти. Он нужен только для совместимости.",
        "vm.max_map_count is the limit of memory mappings per process. Every time a program allocates memory via mmap, the kernel creates a “memory area”. If the limit is exhausted, the program crashes.\n\nSome Proton games create a very large number of memory areas. If the limit is exhausted, the game crashes at startup.\n\nThe recommended value is 1048576. IMPORTANT: this tweak does not speed up games and does not fix ordinary RAM shortage."),
    "ntfs3": _help_block(
        "NTFS — это файловая система Windows. Linux умеет читать и писать на неё двумя способами: через старый медленный драйвер ntfs-3g в пользовательском пространстве и через новый быстрый ntfs3 внутри ядра.\n\nLinux Mint по умолчанию блокирует ntfs3 и использует ntfs-3g. Эта опция снимает блокировку, и NTFS-диски начинают работать заметно быстрее.\n\nВНИМАНИЕ: не включайте, если у вас нет NTFS-дисков. Если у вас есть NTFS-диск с важными данными, сделайте резервную копию.",
        "NTFS is the Windows file system. Linux can read and write it two ways: through the old slow ntfs-3g driver in userspace, and through the new fast ntfs3 driver inside the kernel.\n\nLinux Mint blocks ntfs3 by default. This option lifts the block, and NTFS disks start working noticeably faster.\n\nWARNING: do not enable it if you have no NTFS disks."),
    "commit": _help_block(
        "Параметр commit=NN заставляет файловую систему реже сбрасывать накопленные данные на диск: не раз в 5 секунд по умолчанию, а раз в NN секунд. Это уменьшает число операций записи и продлевает жизнь SSD.\n\nВАЖНО: параметр понимают ТОЛЬКО файловые системы семейства ext — ext2, ext3, ext4. Для NTFS, FAT32, exFAT, btrfs, xfs, f2fs и других он неизвестен: ядро может проигнорировать или отказаться монтировать раздел.\n\nВНИМАНИЕ: чем больше интервал, тем выше риск потерять последние данные при внезапном отключении питания. Разумно 60–120 секунд.",
        "The commit=NN parameter makes the file system flush accumulated data to disk less often. This reduces write operations and extends SSD life.\n\nIMPORTANT: only file systems of the ext family support this — ext2, ext3, ext4. For NTFS, FAT32, exFAT, btrfs, xfs, f2fs and others the parameter is unknown.\n\nWARNING: the longer the interval, the higher the risk of losing the latest written data on sudden power loss."),
    "tmpfs_tmp": _help_block(
        "РАСШИРЕННЫЙ ТВИК. Включайте только если понимаете риск.\n\nМонтирует /tmp как tmpfs — то есть в оперативной памяти. Файлы в /tmp исчезают при перезагрузке, диск не получает постоянные записи.\n\nВНИМАНИЕ — несколько важных предупреждений:\n\n1. ГИБЕРНАЦИЯ. tmpfs использует оперативную память и его страницы могут быть выгружены в swap. Если swap-раздел мал или отсутствует, гибернация может сломаться.\n\n2. ПОТЕРА ДАННЫХ. Всё, что лежит в /tmp, исчезнет после выключения или перезагрузки.\n\n3. РАЗМЕР. Параметр size=512M — это верхний предел, а не резервирование. Если приложение попытается записать больше, оно упадёт с ошибкой «no space left on device».",
        "ADVANCED TWEAK. Enable only if you understand the risk.\n\nMounts /tmp as tmpfs — that is, in RAM. Files in /tmp disappear on reboot, the disk gets no constant writes.\n\nWARNING — several important notes:\n\n1. HIBERNATION. tmpfs uses RAM and its pages can be swapped out. If the swap partition is small or absent, hibernation may break.\n\n2. DATA LOSS. Everything in /tmp disappears after shutdown or reboot.\n\n3. SIZE. The size=512M parameter is an upper limit, not a reservation. If an application tries to write more, it crashes with «no space left on device»."),
    "aliases": _help_block(
        "В Linux много рутинных действий в терминале: обновление пакетов, очистка кэша, проверка места на диске. Эта опция добавляет в ваш .bashrc готовый набор команд: upd (обновить списки пакетов), upgr (обновить пакеты), update_all (полное обновление системы, включая Flatpak), clean (очистка ненужных пакетов), space (показать свободное место), mem (очистить кэш памяти), fix (починить сломанные пакеты) и другие.\n\nОпция применяется сразу, но команды появятся только в новых терминалах.",
        "Linux has many routine terminal actions: updating packages, clearing cache, checking disk space. This option adds a ready set of commands to your .bashrc: upd, upgr, update_all, clean, space, mem, fix and others.\n\nThe option applies immediately, but the commands only appear in new terminals."),
    "autoupdate": _help_block(
        "Обновления системы нужно ставить регулярно — это вопросы безопасности и свежих функций. Эта опция создаёт systemd-таймер, который сам запускает обновление APT и Flatpak в выбранное время.\n\nПри включении этой опции твикер автоматически глушит apt-daily.timer, apt-daily-upgrade.timer, unattended-upgrades.service и (если есть) mintupdate-automation-upgrade.timer. Это нужно, чтобы обновления не запускались дважды.\n\nВНИМАНИЕ: в Linux Mint есть встроенное автообновление (mintupdate). Твикер глушит только его systemd-таймер, но настройки самого mintupdate остаются как есть.",
        "System updates need to be installed regularly — it is a matter of security and fresh features. This option creates a systemd timer that runs APT and Flatpak updates at the chosen time.\n\nWhen this option is enabled, the tweaker automatically masks apt-daily.timer, apt-daily-upgrade.timer, unattended-upgrades.service and (if present) mintupdate-automation-upgrade.timer.\n\nWARNING: Linux Mint has a built-in auto-update (mintupdate). The tweaker masks only its systemd timer, but the mintupdate settings themselves remain untouched."),
}

# ============================================================================
# БЛОК 6. OPTION_FILES + STR
# ============================================================================

OPTION_FILES = {
    "journald": ["/etc/systemd/journald.conf"],
    "audit": ["/etc/default/grub"],
    "raid": ["/etc/default/grub"],
    "nmi_watchdog": ["/etc/default/grub"],
    "itco_wdt": ["/etc/modprobe.d/nmi-watchdog.conf"],
    "zfs_services": ["/etc/default/zfs"],
    "shutdown_timeout": ["/etc/systemd/system.conf"],
    "corectrl": ["/etc/polkit-1/rules.d/90-corectrl.rules",
                 "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"],
    "ppfeaturemask": ["/etc/default/grub"],
    "nvidia_modeset": ["/etc/default/grub"],
    "vrr": ["/etc/X11/xorg.conf.d/20-amdgpu.conf"],
    "radv": ["/etc/environment"],
    "mesa": ["/etc/environment"],
    "pipewire": ["{home}/.config/pipewire/pipewire.conf.d/10-sound.conf"],
    "bbr": ["/etc/sysctl.d/99-bbr.conf"],
    "swap": ["/etc/sysctl.d/99-gaming-swap.conf"],
    "zram": ["/etc/systemd/zram-generator.conf"],
    "zswap": ["/etc/default/grub"],
    "thp": ["/etc/default/grub"],
    "sysctl_cache": ["/etc/sysctl.d/99-gaming-sysctl.conf"],
    "sysctl_numa": ["/etc/sysctl.d/99-gaming-sysctl.conf"],
    "reisub": ["/etc/sysctl.d/99-sysrq.conf"],
    "ntsync": ["/etc/modules-load.d/ntsync.conf"],
    "max_map_count": ["/etc/sysctl.d/99-gaming-mmap.conf"],
    "ntfs3": ["/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"],
    "commit": ["/etc/fstab"],
    "tmpfs_tmp": ["/etc/fstab"],
    "aliases": ["{home}/.bashrc"],
    "autoupdate": ["/etc/systemd/system/biweekly-upgrade.timer",
                   "/etc/systemd/system/biweekly-upgrade.service"],
}

STR = {
    "ru": {
        "tab_tune": "Тюнинг", "tab_serv": "Службы", "tab_stat": "Статус",
        "tab_apps": "Приложения",
        "btn_apply": "Применить выбранное", "btn_rollback": "Откатить выбранное",
        "btn_selall": "Выбрать все", "btn_selnone": "Снять выделение",
        "btn_about": "О твикере", "btn_close": "Закрыть",
        "theme_dark": "Тёмная тема", "theme_light": "Светлая тема",
        "lbl_dry": "Сухой прогон", "lbl_terminal": "Терминальный вывод:",
        "lbl_search": "Поиск:", "btn_search_clear": "Сбросить",
        "lbl_show_only_available": "Только доступное",
        "search_no_results": "Ничего не найдено по запросу «%s».",
        "lbl_group": "Группа:", "lbl_value": "Значение:",
        "lbl_schedule": "Расписание:", "lbl_mode": "Режим:",
        "ready": "Готово", "running": "Выполнение...", "done": "Готово",
        "applied_yes": "✓ применено", "applied_no": "не применено",
        "applied_manual": "применено (изменён вручную)",
        "applied_unknown": "неизвестно",
        "btn_file": "файл", "btn_q": "?",
        "btn_check_status": "проверить",
        "btn_remove_zfs": "Удалить пакеты (осторожно)",
        "btn_remove_zfs_unavailable": "Удалить пакеты (недоступно)",
        "menu_copy": "Копировать", "menu_copy_all": "Копировать всё",
        "menu_select_all": "Выделить всё",
        "svc_name": "Служба", "svc_state": "Состояние", "svc_run": "Запуск",
        "svc_desc": "Описание", "svc_help": "?",
        "svc_hint": "Клик по первой колонке — отметить службу; клик по заголовку — сортировка; «?» — подробности.",
        "svc_on": "работает", "svc_onoff": "не запущена",
        "svc_off": "остановлена", "svc_masked": "заблокирована",
        "svc_na": "нет в системе",
        "run_yes": "работает", "run_no": "остановлена",
        "svc_on_sel": "Включить выбранные", "svc_off_sel": "Отключить выбранные",
        "svc_col_sel": "✓",
        "sort_asc": "▲", "sort_desc": "▼",
        "svc_hdr_name": "Служба", "svc_hdr_state": "Состояние",
        "svc_hdr_desc": "Описание",
        "stat_refresh": "Обновить статус",
        "st_hw": "ИНФОРМАЦИЯ О СИСТЕМЕ", "st_parts": "РАЗДЕЛЫ СИСТЕМЫ",
        "st_tweaks": "ТВИКИ", "st_services": "СЛУЖБЫ",
        "st_kernel": "ПАРАМЕТРЫ ЯДРА",
        "st_timer": "Таймер автообновлений",
        "st_enabled": "включён", "st_disabled": "отключён",
        "st_masked": "заблокирован", "st_notfound": "не найден",
        "part_dev": "Устройство", "part_mount": "Точка монтирования",
        "part_fs": "ФС", "part_total": "Всего", "part_free": "Свободно",
        "os_lbl": "ОС", "gpu_lbl": "Видеокарта",
        "screen_lbl": "Разрешение экрана",
        "swap_lbl": "Файл подкачки", "kernel_lbl": "Ядро",
        "de_lbl": "Оболочка", "ram_lbl": "ОЗУ", "cpu_lbl": "Процессор",
        "disk_lbl": "Диск", "driver_lbl": "Драйвер видеокарты",
        "user_lbl": "Пользователь", "home_lbl": "Домашняя папка",
        "hz": "Гц", "ram_hint": "(тип и частота — после ввода sudo)",
        "w_yes": "да", "w_no": "нет", "no_swap": "отсутствует",
        "gb": "ГБ", "free_w": "свободно", "swap_file": "файл",
        "swap_part": "раздел",
        "yes": "ПРИМЕНЕНО", "no": "НЕ ПРИМЕНЕНО",
        "unknown": "НЕИЗВЕСТНО",
        "sched_cur": "Текущее: %s", "sched_none": "не настроено",
        "mount_title": "Диски: параметры монтирования",
        "mount_desc": "Добавит опцию noatime в /etc/fstab (меньше служебных обращений к диску, полезно для SSD и NTFS; noatime покрывает и каталоги). Вступает в силу после перезагрузки.",
        "steam_title": "Steam: симлинки compatdata",
        "steam_desc": "Создаст ссылку compatdata на ~/.steam/steam/steamapps/compatdata для библиотек Steam на NTFS-разделах, чтобы игры видели данные Proton/Wine из домашней папки.",
        "mount_short": "параметры монтирования",
        "steam_short": "симлинк compatdata",
        "commit_title": "commit=NN (только ext3/ext4)",
        "commit_desc": "Параметр commit= понимают ТОЛЬКО ext2/ext3/ext4. Для NTFS, FAT32, exFAT, btrfs, xfs он приведёт к ошибке монтирования. Ниже — только подходящие разделы: отметьте те, к которым добавить commit.",
        "commit_none": "Подходящих разделов (ext2/ext3/ext4) не найдено. Твик commit= недоступен.",
        "commit_value_label": "Значение (сек):",
        "mmc_value_label": "Значение:",
        "tmpfs_size_label": "Размер:",
        "cur_value": "сейчас: %s",
        "nmi_now_active": "сейчас: активен",
        "nmi_now_off": "сейчас: отключён",
        "commit_not_set": "—",
        "commit_default_hint": "по умолчанию: 5 сек",
        "tmpfs_already": "(/tmp уже в tmpfs)",
        "journald_volatile": "ОЗУ (volatile)",
        "journald_persistent": "диск (persistent)",
        "journald_none": "выключено",
        "journald_auto": "auto (по умолчанию)",
        "kern_sw": "как часто данные уходят в подкачку",
        "kern_vfs": "сколько кэша файлов держится в памяти",
        "kern_numa": "перемещение памяти между ядрами",
        "kern_thp": "крупные блоки памяти",
        "kern_bbr": "ускорение сети на слабых каналах",
        "thp_cur": "сейчас: %s",
        "thp_val_always": "всем подряд", "thp_val_madvise": "по запросу",
        "thp_val_never": "выключено",
        "kn_hdr_param": "Параметр", "kn_hdr_val": "Значение",
        "kn_hdr_desc": "Описание", "kn_hdr_status": "Статус",
        "tw_name": "Твик", "kn_param": "Параметр", "kn_val": "Значение",
        "sudo_title": "sudo", "sudo_prompt": "Пароль sudo (попытка %d из 3):",
        "sudo_wrong": "Неверный пароль или нет прав sudo.",
        "autoupdate_warn": "Включено автообновление по расписанию. Твикер автоматически отключит apt-daily, apt-daily-upgrade и unattended-upgrades, чтобы обновления не выполнялись дважды. Встроенное автообновление Mint (mintupdate) останется как есть — отключите его вручную, если не хотите дублирования.",
        "shutdown_timeout_warn": "ВНИМАНИЕ: этот твик сокращает время ожидания закрытия приложений при выключении ПК с 90 до 8 секунд (по умолчанию).\n\nЕсли в момент выключения приложение сохраняло данные (база данных, торрент, редактор), его могут убить до завершения записи.\n\nДля обычного домашнего ПК риск минимальный. Для систем с базами данных или активной записью — не включайте.\n\nИзменения вступают в силу после перезагрузки.",
        "viewer": "Просмотр файла",
        "viewer_ext": "Открыть во внешнем редакторе",
        "about_title": "О твикере",
        "about_purpose": "Графическая оболочка тюнинга для Linux Mint / Ubuntu / Debian и других systemd-дистрибутивов: твики производительности, логов, дисков, сети и игр с откатом и бэкапами.",
        "about_author": "Автор", "about_author_name": "Дмитрий Свистунов",
        "about_ver": "Версия", "about_license": "Лицензия",
        "about_disclaimer": "ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ\n\nТвикер изменяет системные файлы (GRUB, fstab, sysctl, systemd-юниты, конфиги приложений) и может удалять пакеты. Все изменения вы делаете на свой страх и риск. Перед применением твиков убедитесь, что у вас есть резервная копия важных данных и загрузочная флешка на случай проблем с загрузкой. Автор не несёт ответственности за потерю данных, отказ загрузки или нестабильную работу системы. Бэкапы изменённых файлов сохраняются в ~/system-tuneup-backups/.",
        "zfs_remove_title": "Удаление пакетов ZFS",
        "zfs_remove_body": "Твикер проверил: ZFS-пулов нет, ZFS-монтирований нет, записей в /etc/fstab и /etc/crypttab нет.\n\nЕсли вы устанавливали ZFS вручную и используете его вне стандартных мест — удаление приведёт к потере доступа к данным.\n\nОтмена возможна только через «sudo apt install zfsutils-linux», при этом прежнее состояние служб не восстановится.\n\nУдалить пакеты zfsutils-linux и zfs-zed?",
        "disabled_reason": "недоступно: %s",
        "msg_run": "Скрипт уже запущен. Дождитесь завершения.",
        "msg_noopt": "Отметьте хотя бы одну опцию.",
        "msg_sel": "Сначала отметьте службы в первой колонке.",
        "msg_nofile": "Файл ещё не существует. Пути, где опция вносит изменения:",
        "msg_close": "Прервать выполнение и закрыть?",
        "msg_running_title": "Уже запущено",
        "msg_running_text": "Linux Tweaker уже запущен.",
        "result_ok": "Готово: %d применено, %d пропущено, %d ошибок",
        "reason_raid": "у вас есть RAID",
        "reason_itco_not_intel": "не Intel-чипсет",
        "reason_itco_no_module": "модуль iTCO_wdt не поддерживается ядром",
        "reason_itco_watchdog_off": "NMI watchdog уже отключён",
        "reason_itco_grub_missing": "сначала примените nmi_watchdog=0",
        "reason_zfs_not_installed": "пакеты ZFS не установлены",
        "reason_amd_only": "только для AMD",
        "reason_nvidia_only": "только для NVIDIA",
        "reason_no_swap": "swap не обнаружен",
        "reason_no_zram": "нет zram-generator",
        "reason_mint_only": "только для Linux Mint",
        "reason_pipewire_inactive": "PipeWire не используется",
        "reason_no_ntfs": "нет NTFS-разделов",
        "apps_search": "Поиск:",
        "apps_refresh": "Обновить",
        "apps_clear": "Снять выделение",
        "apps_remove": "Удалить выбранное",
        "apps_empty": "Из списка ничего не установлено.",
        "apps_unsupported": "Функция недоступна в этом дистрибутиве.\nУдаление пакетов поддерживается только в системах на базе Debian, Ubuntu или Linux Mint.",
        "apps_no_list": "Список пакетов не найден (tweaker_packages.py отсутствует).",
        "apps_selected": "Выбрано: %d пакетов, ~%s",
        "apps_selected_none": "Ничего не выбрано",
        "apps_confirm_title": "Удаление пакетов",
        "apps_confirm_will_remove": "Будут удалены:",
        "apps_confirm_deps": "Вместе с ними apt хочет удалить (зависимости):",
        "apps_confirm_size": "Будет освобождено примерно:",
        "apps_confirm_system_warn": "ВНИМАНИЕ: apt также хочет удалить системные пакеты:",
        "apps_confirm_system_hint": "Это может сломать систему. Продолжайте, только если понимаете, что делаете.",
        "apps_confirm_no_rollback": "Отмена невозможна. Конфиги будут стёрты.",
        "apps_confirm_btn": "Удалить",
        "apps_cancel": "Отмена",
        "apps_done": "Удалено %d пакетов, освобождено ~%s",
        "apps_done_dry": "[Сухой прогон] Будет удалено %d пакетов",
        "apps_failed": "Не удалось удалить пакеты.",
        "apps_installed": "установлен",
        "apps_careful_mark": "⚠",
    },
    "en": {
        "tab_tune": "Tuning", "tab_serv": "Services", "tab_stat": "Status",
        "tab_apps": "Applications",
        "btn_apply": "Apply selected", "btn_rollback": "Rollback selected",
        "btn_selall": "Select all", "btn_selnone": "Deselect",
        "btn_about": "About", "btn_close": "Close",
        "theme_dark": "Dark theme", "theme_light": "Light theme",
        "lbl_dry": "Dry run", "lbl_terminal": "Terminal output:",
        "lbl_search": "Search:", "btn_search_clear": "Reset",
        "lbl_show_only_available": "Available only",
        "search_no_results": "Nothing found for query “%s”.",
        "lbl_group": "Group:", "lbl_value": "Value:",
        "lbl_schedule": "Schedule:", "lbl_mode": "Mode:",
        "ready": "Ready", "running": "Running...", "done": "Done",
        "applied_yes": "✓ applied", "applied_no": "not applied",
        "applied_manual": "applied (modified manually)",
        "applied_unknown": "unknown",
        "btn_file": "file", "btn_q": "?",
        "btn_check_status": "check",
        "btn_remove_zfs": "Remove packages (careful)",
        "btn_remove_zfs_unavailable": "Remove packages (unavailable)",
        "menu_copy": "Copy", "menu_copy_all": "Copy all",
        "menu_select_all": "Select all",
        "svc_name": "Service", "svc_state": "State", "svc_run": "Running",
        "svc_desc": "Description", "svc_help": "?",
        "svc_hint": "Click the first column to mark a service; click a header to sort; “?” opens details.",
        "svc_on": "running", "svc_onoff": "not running", "svc_off": "stopped",
        "svc_masked": "blocked", "svc_na": "not installed",
        "run_yes": "running", "run_no": "stopped",
        "svc_on_sel": "Enable selected", "svc_off_sel": "Disable selected",
        "svc_col_sel": "✓",
        "sort_asc": "▲", "sort_desc": "▼",
        "svc_hdr_name": "Service", "svc_hdr_state": "State",
        "svc_hdr_desc": "Description",
        "stat_refresh": "Refresh status",
        "st_hw": "SYSTEM INFORMATION", "st_parts": "SYSTEM PARTITIONS",
        "st_tweaks": "TWEAKS", "st_services": "SERVICES",
        "st_kernel": "KERNEL PARAMETERS",
        "st_timer": "Auto-update timer",
        "st_enabled": "enabled", "st_disabled": "disabled",
        "st_masked": "blocked", "st_notfound": "not found",
        "part_dev": "Device", "part_mount": "Mount point",
        "part_fs": "FS", "part_total": "Total", "part_free": "Free",
        "os_lbl": "OS", "gpu_lbl": "GPU",
        "screen_lbl": "Screen resolution",
        "swap_lbl": "Swap", "kernel_lbl": "Kernel",
        "de_lbl": "Desktop", "ram_lbl": "RAM", "cpu_lbl": "CPU",
        "disk_lbl": "Disk", "driver_lbl": "GPU driver",
        "user_lbl": "User", "home_lbl": "Home folder",
        "hz": "Hz", "ram_hint": "(type & speed after sudo)",
        "w_yes": "yes", "w_no": "no", "no_swap": "none",
        "gb": "GB", "free_w": "free", "swap_file": "file",
        "swap_part": "partition",
        "yes": "APPLIED", "no": "NOT APPLIED",
        "unknown": "UNKNOWN",
        "sched_cur": "Current: %s", "sched_none": "not configured",
        "mount_title": "Disks: mount options",
        "mount_desc": "Adds the noatime option to /etc/fstab entries (less disk wear; noatime already covers directories). Takes effect after reboot.",
        "steam_title": "Steam: compatdata symlinks",
        "steam_desc": "Creates a compatdata symlink to ~/.steam/steam/steamapps/compatdata for Steam libraries on NTFS partitions so games can see Proton/Wine data from the home folder.",
        "mount_short": "mount options",
        "steam_short": "compatdata symlink",
        "commit_title": "commit=NN (ext3/ext4 only)",
        "commit_desc": "Only ext2/ext3/ext4 understand commit=. For NTFS, FAT32, exFAT, btrfs, xfs it will fail to mount. Below are only suitable partitions: tick the ones to add commit to.",
        "commit_none": "No suitable partitions (ext2/ext3/ext4) found. commit= tweak is unavailable.",
        "commit_value_label": "Value (sec):",
        "mmc_value_label": "Value:",
        "tmpfs_size_label": "Size:",
        "cur_value": "now: %s",
        "nmi_now_active": "now: active",
        "nmi_now_off": "now: off",
        "commit_not_set": "—",
        "commit_default_hint": "default: 5 sec",
        "tmpfs_already": "(/tmp already in tmpfs)",
        "journald_volatile": "RAM (volatile)",
        "journald_persistent": "disk (persistent)",
        "journald_none": "disabled",
        "journald_auto": "auto (default)",
        "kern_sw": "how often data goes to swap",
        "kern_vfs": "how much file cache stays in RAM",
        "kern_numa": "memory moving between CPU cores",
        "kern_thp": "large memory blocks",
        "kern_bbr": "faster network on unstable links",
        "thp_cur": "now: %s",
        "thp_val_always": "always on", "thp_val_madvise": "on request",
        "thp_val_never": "off",
        "kn_hdr_param": "Parameter", "kn_hdr_val": "Value",
        "kn_hdr_desc": "Description", "kn_hdr_status": "Status",
        "tw_name": "Tweak", "kn_param": "Parameter", "kn_val": "Value",
        "sudo_title": "sudo", "sudo_prompt": "sudo password (attempt %d of 3):",
        "sudo_wrong": "Wrong password or no sudo rights.",
        "autoupdate_warn": "Scheduled auto-update enabled. The tweaker will automatically mask apt-daily, apt-daily-upgrade and unattended-upgrades so updates do not run twice. Mint's built-in auto-update (mintupdate) is left as is — disable it manually if you do not want duplicates.",
        "shutdown_timeout_warn": "WARNING: this tweak cuts the app-close timeout at shutdown from 90 to 8 seconds (default).\n\nIf an app was saving data at shutdown (database, torrent, editor), it may be killed before finishing the write.\n\nFor a normal home PC the risk is minimal. For systems with databases or active writes — do not enable.\n\nChanges take effect after a reboot.",
        "viewer": "File viewer",
        "viewer_ext": "Open in external editor",
        "about_title": "About",
        "about_purpose": "A graphical tuning shell for Linux Mint / Ubuntu / Debian and other systemd distributions: performance, logs, disk, network and gaming tweaks with rollback and backups.",
        "about_author": "Author", "about_author_name": "Dmitry Svistunov",
        "about_ver": "Version", "about_license": "License",
        "about_disclaimer": "DISCLAIMER\n\nThis tweaker modifies system files (GRUB, fstab, sysctl, systemd units, application configs) and can remove packages. You use it at your own risk. Before applying tweaks, make sure you have a backup of important data and a bootable USB stick in case of boot problems. The author is not responsible for data loss, boot failure or system instability. Backups of modified files are stored in ~/system-tuneup-backups/.",
        "zfs_remove_title": "ZFS package removal",
        "zfs_remove_body": "The tweaker checked: no ZFS pools, no ZFS mounts, no entries in /etc/fstab or /etc/crypttab.\n\nIf you installed ZFS manually and use it outside standard locations, removal will cut off access to your data.\n\nRollback is possible only via «sudo apt install zfsutils-linux», and the previous state of the services will not be restored.\n\nRemove packages zfsutils-linux and zfs-zed?",
        "disabled_reason": "unavailable: %s",
        "msg_run": "A job is already running. Wait for it to finish.",
        "msg_noopt": "Tick at least one option.",
        "msg_sel": "Tick services in the first column first.",
        "msg_nofile": "This file appears after applying the option. Paths the option modifies:",
        "msg_close": "Interrupt the job and close?",
        "msg_running_title": "Already running",
        "msg_running_text": "Linux Tweaker is already running.",
        "result_ok": "Done: %d applied, %d skipped, %d failed",
        "reason_raid": "RAID detected",
        "reason_itco_not_intel": "not an Intel system",
        "reason_itco_no_module": "iTCO_wdt module not available",
        "reason_itco_watchdog_off": "NMI watchdog already disabled",
        "reason_itco_grub_missing": "apply nmi_watchdog=0 first",
        "reason_zfs_not_installed": "ZFS packages not installed",
        "reason_amd_only": "AMD only",
        "reason_nvidia_only": "NVIDIA only",
        "reason_no_swap": "no swap found",
        "reason_no_zram": "zram-generator not installed",
        "reason_mint_only": "Linux Mint only",
        "reason_pipewire_inactive": "PipeWire is not in use",
        "reason_no_ntfs": "no NTFS partitions",
        "apps_search": "Search:",
        "apps_refresh": "Refresh",
        "apps_clear": "Deselect",
        "apps_remove": "Remove selected",
        "apps_empty": "Nothing from the list is installed.",
        "apps_unsupported": "This feature is not available on this distribution.\nPackage removal is only supported on Debian, Ubuntu or Linux Mint based systems.",
        "apps_no_list": "Package list not found (tweaker_packages.py is missing).",
        "apps_selected": "Selected: %d packages, ~%s",
        "apps_selected_none": "Nothing selected",
        "apps_confirm_title": "Package removal",
        "apps_confirm_will_remove": "The following will be removed:",
        "apps_confirm_deps": "Together with them apt wants to remove (dependencies):",
        "apps_confirm_size": "About to free:",
        "apps_confirm_system_warn": "WARNING: apt also wants to remove system packages:",
        "apps_confirm_system_hint": "This may break the system. Continue only if you understand what you are doing.",
        "apps_confirm_no_rollback": "This cannot be undone. Configs will be deleted.",
        "apps_confirm_btn": "Remove",
        "apps_cancel": "Cancel",
        "apps_done": "Removed %d packages, freed ~%s",
        "apps_done_dry": "[Dry run] Would remove %d packages",
        "apps_failed": "Failed to remove packages.",
        "apps_installed": "installed",
        "apps_careful_mark": "⚠",
    },
}

# ============================================================================
# БЛОК 7. ИМПОРТ СПИСКА ПАКЕТОВ
# ============================================================================

try:
    from tweaker_packages import REMOVABLE_PACKAGES
except ImportError:
    try:
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        from tweaker_packages import REMOVABLE_PACKAGES
    except ImportError:
        REMOVABLE_PACKAGES = {}

# ============================================================================
# БЛОК 8. УТИЛИТЫ
# ============================================================================

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            pass
        except Exception:
            pass
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    return True

def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(LOCK_FILE)
    except Exception:
        pass

def decode_bytes(v):
    if v is None:
        return ""
    return v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)

def lines_in(content):
    if content is None:
        return []
    return content.splitlines()

def cpu_model():
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "?"

def ram_total_gb():
    try:
        with open("/proc/meminfo", "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    return int(line.split()[1]) / 1024.0 / 1024.0
    except Exception:
        pass
    return None

def desktop_name():
    d = (os.environ.get("XDG_CURRENT_DESKTOP", "") + " " +
         os.environ.get("DESKTOP_SESSION", "")).lower()
    for key, name in [("cinnamon", "Cinnamon"), ("xfce", "XFCE"),
                      ("mate", "MATE"), ("plasma", "KDE Plasma"),
                      ("kde", "KDE Plasma"), ("gnome", "GNOME"),
                      ("lxqt", "LXQt"), ("lxde", "LXDE"),
                      ("openbox", "Openbox"), ("budgie", "Budgie"),
                      ("pantheon", "Pantheon")]:
        if key in d:
            return name
    return os.environ.get("XDG_CURRENT_DESKTOP", "") or "?"

def detect_lang():
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val:
            return "ru" if val.lower().startswith("ru") else "en"
    return "en"

def is_debian_based():
    try:
        if os.path.exists("/etc/debian_version"):
            return True
        with open("/etc/os-release", "r", encoding="utf-8",
                  errors="replace") as f:
            content = f.read().lower()
        return ("debian" in content or "ubuntu" in content
                or "mint" in content or "id_like=debian" in content)
    except Exception:
        return False

def zram_generator_present():
    return any(os.path.exists(p) for p in (
        "/usr/lib/systemd/system-generators/zram-generator",
        "/lib/systemd/system-generators/zram-generator"))

def _is_removable_device(dev):
    try:
        base = os.path.basename(dev)
        m = re.match(r"^(sd[a-z]+|hd[a-z]+|vd[a-z]+|nvme\d+n\d+|mmcblk\d+)", base)
        if not m:
            return False
        disk = m.group(1)
        rm_path = "/sys/block/%s/removable" % disk
        if os.path.exists(rm_path):
            with open(rm_path, "r") as f:
                return f.read().strip() == "1"
    except Exception:
        pass
    return False

def parse_mounts():
    items = []
    try:
        with open("/proc/mounts", "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                dev, mp, fstype, opts = parts[0], parts[1], parts[2], parts[3]
                mp = mp.replace("\\040", " ").replace("\\011", "\t") \
                       .replace("\\012", "\n").replace("\\134", "\\")
                if not dev.startswith("/dev/"):
                    continue
                if fstype not in ("ext2", "ext3", "ext4", "xfs", "btrfs",
                                  "f2fs", "ntfs", "ntfs3", "vfat", "exfat",
                                  "fuseblk"):
                    continue
                if "rw" not in opts.split(","):
                    continue
                if _is_removable_device(dev):
                    continue
                items.append({"dev": dev, "mp": mp, "fstype": fstype})
    except Exception:
        pass
    return items

def find_steam_libraries(user_home):
    libs = []
    for vdf in (os.path.join(user_home, ".steam", "steam", "steamapps",
                             "libraryfolders.vdf"),
                os.path.join(user_home, ".local", "share", "Steam",
                             "steamapps", "libraryfolders.vdf")):
        if not os.path.isfile(vdf):
            continue
        try:
            with open(vdf, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = re.search(r'"path"\s+"([^"]+)"', line)
                    if m:
                        p = m.group(1).replace("\\\\", "/")
                        sa = os.path.join(p, "steamapps")
                        if os.path.isdir(sa) and sa not in libs:
                            libs.append(sa)
        except Exception:
            pass
    for pat in ("/media/*/Steam/steamapps", "/mnt/*/Steam/steamapps",
                "/run/media/*/*/Steam/steamapps"):
        for p in glob.glob(pat):
            if os.path.isdir(p) and p not in libs:
                libs.append(p)
    return libs

def fs_supports_commit(fstype):
    return (fstype or "").lower() in COMMIT_OK_FS

def format_size(bytes_val):
    try:
        b = float(bytes_val)
    except Exception:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024 or unit == "GB":
            return "%.1f %s" % (b, unit)
        b /= 1024.0
    return "?"

def human_size(bytes_val):
    try:
        b = float(bytes_val)
    except Exception:
        return "?"
    for unit, div in (("T", 1024 ** 4), ("G", 1024 ** 3),
                      ("M", 1024 ** 2), ("K", 1024)):
        if b >= div:
            val = b / div
            if val >= 100:
                return "%.0f%s" % (val, unit)
            elif val >= 10:
                return "%.1f%s" % (val, unit)
            else:
                return "%.2f%s" % (val, unit)
    return "%.0fB" % b

def pipewire_active():
    try:
        r = subprocess.run(["pgrep", "-x", "pipewire"],
                           capture_output=True, timeout=TIMEOUT_QUICK)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    try:
        r = subprocess.run(["pgrep", "-x", "pulseaudio"],
                           capture_output=True, timeout=TIMEOUT_QUICK)
        if r.returncode == 0:
            return False
    except Exception:
        pass
    for pkg in ("pipewire", "pipewire-pulse", "pipewire-bin"):
        try:
            r = subprocess.run(["dpkg-query", "-W", "-f=${Status}", pkg],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            if r.returncode == 0 and "install ok installed" in r.stdout:
                return True
        except Exception:
            continue
    return False

def nmi_watchdog_active():
    try:
        with open("/proc/sys/kernel/nmi_watchdog", "r") as f:
            return f.read().strip() == "1"
    except Exception:
        return False

def nmi_watchdog_in_grub():
    try:
        with open("/etc/default/grub", "r", encoding="utf-8",
                  errors="replace") as f:
            content = f.read()
    except Exception:
        return False
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        m = re.match(r"^\s*GRUB_CMDLINE_LINUX(?:_DEFAULT)?=(.*)$", line)
        if m:
            raw = m.group(1).strip().strip('"').strip("'")
            if "nmi_watchdog=0" in raw.split():
                return True
    return False

def zfs_packages_installed():
    for pkg in ("zfsutils-linux", "zfs-zed"):
        try:
            r = subprocess.run(["dpkg-query", "-W", "-f=${Status}", pkg],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            if r.returncode == 0 and "install ok installed" in r.stdout:
                return True
        except Exception:
            pass
    return False

def zfs_in_use():
    try:
        r = subprocess.run(["zpool", "list", "-H", "-o", "name"],
                           capture_output=True, text=True,
                           timeout=TIMEOUT_QUICK)
        if r.returncode == 0 and r.stdout.strip():
            return True
    except Exception:
        pass
    try:
        r = subprocess.run(["findmnt", "-t", "zfs", "-n", "-o", "TARGET"],
                           capture_output=True, text=True,
                           timeout=TIMEOUT_QUICK)
        if r.returncode == 0 and r.stdout.strip():
            return True
    except Exception:
        pass
    for path in ("/etc/fstab", "/etc/crypttab"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                if "zfs" in f.read().lower():
                    return True
        except Exception:
            pass
    return False

def zfs_units_masked():
    masked = 0
    present = 0
    for unit in ZFS_UNITS:
        try:
            r = subprocess.run(["systemctl", "is-enabled", unit],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            state = r.stdout.strip()
            if state in ("", "not-found"):
                continue
            present += 1
            if state == "masked":
                masked += 1
        except Exception:
            continue
    return present > 0 and masked == present

def tmpfs_tmp_mounted():
    try:
        with open("/proc/mounts", "r", encoding="utf-8",
                  errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3 and parts[1] == "/tmp" \
                        and parts[2] == "tmpfs":
                    return True
    except Exception:
        pass
    return False

def fstab_has_tmp_tmpfs():
    try:
        with open("/etc/fstab", "r", encoding="utf-8",
                  errors="replace") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                parts = s.split()
                if len(parts) >= 3 and parts[1] == "/tmp" \
                        and parts[2] == "tmpfs":
                    return True
    except Exception:
        pass
    return False

def installed_packages_set():
    try:
        r = subprocess.run(["dpkg-query", "-W",
                            "-f=${Package}\t${Status}\n"],
                           capture_output=True, text=True,
                           timeout=TIMEOUT_DPKG_QUERY)
        installed = set()
        for line in r.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2 and "install ok installed" in parts[1]:
                installed.add(parts[0])
        return installed
    except Exception:
        return set()

def estimate_packages_size(pkgs):
    if not pkgs:
        return "0 B"
    try:
        r = subprocess.run(["dpkg-query", "-W",
                            "-f=${Installed-Size}\n"] + pkgs,
                           capture_output=True, text=True,
                           timeout=TIMEOUT_PKG_SIZE)
        total_kb = 0
        for line in r.stdout.splitlines():
            try:
                total_kb += int(line.strip())
            except Exception:
                pass
        return format_size(total_kb * 1024)
    except Exception:
        return "?"

def apt_dry_run_purge(pkgs):
    if not pkgs:
        return ([], [], [], True)
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    try:
        r = subprocess.run(["apt-get", "-s", "purge", "-y"] + list(pkgs),
                           capture_output=True, text=True,
                           timeout=TIMEOUT_APT_SIMULATE, env=env)
        if r.returncode != 0:
            return (list(pkgs), [], [], False)
        output = decode_bytes(r.stdout) + "\n" + decode_bytes(r.stderr)
    except Exception:
        return (list(pkgs), [], [], False)
    removed = []
    in_block = False
    for line in output.splitlines():
        if "The following packages will be REMOVED" in line:
            in_block = True
            continue
        if in_block:
            if not line.strip():
                break
            for token in line.split():
                token = token.strip().strip(",")
                if token and not token.startswith("("):
                    removed.append(token)
    removed_norm = [p.split(":")[0] for p in removed]
    explicit = [p for p in pkgs if p in removed_norm]
    deps = [p for p in removed_norm if p not in explicit]
    system_hits = [p for p in removed_norm
                   if any(p.startswith(m) for m in SYSTEM_PACKAGE_MASKS)]
    return (explicit, deps, system_hits, True)

# ============================================================================
# БЛОК 9. ИКОНКИ (упрощённые — нативные через QStyle)
# ============================================================================

def app_icon(kind, size=32, color="#4ec9b0"):
    """Рисует простую иконку-пиктограмму. Используется там, где нет
    подходящей тематической иконки."""
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    c = size / 2.0
    r = size * 0.36
    pen = QPen(QColor(color), max(2, int(size * 0.1)))
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    if kind == "logo":
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor(color))
        grad.setColorAt(1, QColor("#3aa794"))
        p.setPen(Qt.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(2, 2, size - 4, size - 4, size * 0.24, size * 0.24)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(int(c - r * 0.5), int(c - r * 0.5),
                      int(r), int(r))
    elif kind == "gear":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        for i in range(8):
            tr = QTransform().translate(c, c).rotate(i * 45.0).translate(-c, -c)
            rect = QRectF(c - r * 0.16, c - r, r * 0.32, r * 0.42)
            p.drawRect(tr.mapRect(rect))
        p.drawEllipse(QRectF(c - r * 0.66, c - r * 0.66, r * 1.32, r * 1.32))
        p.setBrush(QColor("#ffffff") if color != "#ffffff" else QColor(color))
        p.drawEllipse(QRectF(c - r * 0.28, c - r * 0.28, r * 0.56, r * 0.56))
    elif kind == "services":
        for i, y in enumerate((0.3, 0.5, 0.7)):
            p.drawLine(int(size * 0.2), int(size * y),
                       int(size * 0.8), int(size * y))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(color))
            p.drawEllipse(int(size * (0.35 + 0.15 * i)) - 3,
                          int(size * y) - 3, 6, 6)
            p.setPen(pen)
    elif kind == "status":
        p.setPen(QPen(QColor(color), max(2, int(size * 0.1))))
        path = QPainterPath()
        path.moveTo(size * 0.15, size * 0.6)
        path.lineTo(size * 0.35, size * 0.6)
        path.lineTo(size * 0.5, size * 0.3)
        path.lineTo(size * 0.65, size * 0.75)
        path.lineTo(size * 0.85, size * 0.5)
        p.drawPath(path)
    elif kind == "apps":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        for i in range(3):
            p.drawRoundedRect(int(size * 0.15), int(size * (0.2 + i * 0.25)),
                              int(size * 0.7), int(size * 0.18), 3, 3)
    elif kind == "apply":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        p.drawEllipse(2, 2, size - 4, size - 4)
        p.setPen(QPen(QColor("#ffffff"), max(2, int(size * 0.12))))
        path = QPainterPath()
        path.moveTo(size * 0.28, size * 0.52)
        path.lineTo(size * 0.45, size * 0.68)
        path.lineTo(size * 0.74, size * 0.34)
        p.drawPath(path)
    elif kind == "rollback":
        p.setPen(QPen(QColor(color), max(2, int(size * 0.1))))
        p.drawArc(int(size * 0.2), int(size * 0.2),
                  int(size * 0.6), int(size * 0.6), 40 * 16, 260 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        p.drawEllipse(int(size * 0.62), int(size * 0.12),
                      int(size * 0.2), int(size * 0.2))
    elif kind == "on":
        p.setPen(QPen(QColor(color), max(2, int(size * 0.12))))
        p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.5))
        p.drawArc(int(size * 0.28), int(size * 0.34),
                  int(size * 0.44), int(size * 0.44), 30 * 16, 300 * 16)
    elif kind == "off":
        p.setPen(QPen(QColor(color), max(2, int(size * 0.12))))
        p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.5))
        p.drawRect(int(size * 0.3), int(size * 0.5),
                   int(size * 0.4), int(size * 0.28))
    elif kind == "selall":
        p.drawRect(int(size * 0.2), int(size * 0.2),
                   int(size * 0.6), int(size * 0.6))
        p.drawLine(int(size * 0.32), int(size * 0.5), int(size * 0.45), int(size * 0.62))
        p.drawLine(int(size * 0.45), int(size * 0.62), int(size * 0.7), int(size * 0.36))
    elif kind == "selnone":
        p.drawRect(int(size * 0.2), int(size * 0.2),
                   int(size * 0.6), int(size * 0.6))
    p.end()
    return QIcon(px)

# ============================================================================
# БЛОК 10. SUDOMANAGER
# ============================================================================

class SudoManager:
    def __init__(self):
        self.prompt_password = None
        self.show_error = None
        self.authenticated = False
        self._keepalive = False
        self._keepalive_lock = threading.Lock()

    def _cached(self):
        if os.geteuid() == 0:
            return True
        try:
            return subprocess.run(["sudo", "-n", "true"], capture_output=True,
                                  timeout=3).returncode == 0
        except Exception:
            return False

    def authenticate(self):
        if self._cached():
            self.authenticated = True
            self._start_keepalive()
            return True
        for attempt in range(1, 4):
            password = self.prompt_password(attempt) if self.prompt_password else None
            if password is None:
                return False
            if not password:
                continue
            try:
                res = subprocess.run(["sudo", "-S", "-v"],
                                     input=(password + "\n").encode(),
                                     capture_output=True, timeout=15)
                if res.returncode == 0:
                    self.authenticated = True
                    self._start_keepalive()
                    return True
                err = decode_bytes(res.stderr).strip()
                if self.show_error:
                    self.show_error(err)
            except Exception as e:
                if self.show_error:
                    self.show_error(str(e))
        return False

    def ensure(self):
        if self._cached():
            self.authenticated = True
            self._start_keepalive()
            return True
        return self.authenticate()

    def run(self, args, input=None, env=None, timeout=SUDO_TIMEOUT_DEFAULT):
        if os.geteuid() == 0:
            return subprocess.run(list(args), input=input, env=env,
                                  capture_output=True, timeout=timeout)
        if not self._cached():
            raise PermissionError("Sudo session expired. Press Apply again.")
        return subprocess.run(["sudo", "-n"] + list(args), input=input,
                              env=env, capture_output=True, timeout=timeout)

    def _start_keepalive(self):
        if os.geteuid() == 0:
            return
        with self._keepalive_lock:
            if self._keepalive:
                return
            self._keepalive = True

        def loop():
            while True:
                time.sleep(50)
                try:
                    if not self._cached():
                        break
                    subprocess.run(["sudo", "-n", "-v"], capture_output=True, timeout=5)
                except Exception:
                    pass
            with self._keepalive_lock:
                self._keepalive = False
            self.authenticated = False
        threading.Thread(target=loop, daemon=True).start()

# ============================================================================
# БЛОК 11. SYSTEMSTATE
# ============================================================================

class SystemState:
    def __init__(self):
        self.gpu = "Unknown"
        self.gpu_model = ""
        self.has_raid = False
        self.has_swap = False
        self.swap_type = ""
        self.ntsync = False
        self.cinnamon = False
        self.has_flatpak = False
        self.user_name = "root"
        self.user_home = "/root"
        self.is_intel = False
        self.has_itco_module = False
        self.zfs_installed = False
        self.zfs_used = False
        self.pipewire_active = False
        self.nmi_watchdog_active = False
        self.nmi_watchdog_in_grub = False
        self.current_max_map_count = "1048576"
        self.has_ntfs_partitions = False

    def detect(self):
        try:
            self.user_name = self._real_user()
        except Exception:
            self.user_name = "root"
        try:
            self.user_home = pwd.getpwnam(self.user_name).pw_dir
        except Exception:
            self.user_home = os.path.expanduser("~")

        try:
            res = subprocess.run(["lspci"], capture_output=True, text=True,
                                 timeout=TIMEOUT_QUICK)
            for raw in res.stdout.splitlines():
                line = raw.lower()
                if ("vga" in line or "3d controller" in line
                        or "display controller" in line):
                    if "amd" in line or "radeon" in line:
                        self.gpu = "AMD"
                    elif "nvidia" in line:
                        self.gpu = "NVIDIA"
                    elif "intel" in line:
                        self.gpu = "Intel"
                    else:
                        continue
                    desc = raw.split(": ", 1)[1] if ": " in raw else raw
                    cleaned = re.sub(r"^[^\[]*\[[^\]]*\]\s*", "", desc)
                    cleaned = re.sub(r"\(rev [^)]*\)", "", cleaned).strip()
                    self.gpu_model = cleaned or desc.strip()
                    break
        except Exception:
            pass

        try:
            if os.path.isfile("/proc/mdstat"):
                with open("/proc/mdstat", "r", encoding="utf-8",
                          errors="replace") as f:
                    if re.search(r"^md\d+", f.read(), re.M):
                        self.has_raid = True
        except Exception:
            pass
        try:
            res = subprocess.run(["lsblk", "-n", "-o", "TYPE"],
                                 capture_output=True, text=True,
                                 timeout=TIMEOUT_QUICK)
            if "raid" in res.stdout:
                self.has_raid = True
        except Exception:
            pass

        self._detect_swap()
        self.ntsync = os.path.exists("/dev/ntsync")
        d = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        s = os.environ.get("DESKTOP_SESSION", "").lower()
        self.cinnamon = "cinnamon" in d or s == "cinnamon"
        self.has_flatpak = bool(shutil.which("flatpak"))

        self.is_intel = False
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8",
                      errors="replace") as f:
                if "GenuineIntel" in f.read():
                    self.is_intel = True
        except Exception:
            pass

        self.has_itco_module = False
        try:
            r = subprocess.run(["modinfo", "iTCO_wdt"],
                               capture_output=True, timeout=TIMEOUT_QUICK)
            self.has_itco_module = (r.returncode == 0)
        except Exception:
            pass

        self.zfs_installed = zfs_packages_installed()
        self.zfs_used = zfs_in_use()
        self.pipewire_active = pipewire_active()
        self.nmi_watchdog_active = nmi_watchdog_active()
        self.nmi_watchdog_in_grub = nmi_watchdog_in_grub()
        try:
            with open("/proc/sys/vm/max_map_count", "r") as f:
                self.current_max_map_count = f.read().strip()
        except Exception:
            pass
        self.has_ntfs_partitions = self._detect_ntfs_partitions()

    def _detect_swap(self):
        self.has_swap = False
        self.swap_type = ""
        try:
            res = subprocess.run(["swapon", "--show=TYPE", "--noheadings"],
                                 capture_output=True, text=True,
                                 timeout=TIMEOUT_QUICK)
            out = res.stdout.strip()
            if out:
                self.has_swap = True
                if "zram" in out:
                    self.swap_type = "zram"
                elif "partition" in out:
                    self.swap_type = "partition"
                else:
                    self.swap_type = "file"
        except Exception:
            pass

    def _detect_ntfs_partitions(self):
        try:
            res = subprocess.run(["lsblk", "-no", "FSTYPE"],
                                 capture_output=True, text=True,
                                 timeout=TIMEOUT_QUICK)
            for line in res.stdout.splitlines():
                if line.strip() in ("ntfs", "ntfs3"):
                    return True
        except Exception:
            pass
        return False

    def _real_user(self):
        for var in ("SUDO_USER", "PKEXEC_USER"):
            v = os.environ.get(var)
            if v and v != "root":
                return v
        if os.getuid() != 0:
            return pwd.getpwuid(os.getuid()).pw_name
        v = os.environ.get("USER")
        if v and v != "root":
            return v
        try:
            for pw in pwd.getpwall():
                if pw.pw_uid >= 1000 and pw.pw_name not in ("nobody", "nfsnobody"):
                    if os.path.isdir(pw.pw_dir) and pw.pw_dir.startswith("/home/"):
                        return pw.pw_name
            for pw in pwd.getpwall():
                if pw.pw_uid >= 1000 and pw.pw_name not in ("nobody", "nfsnobody"):
                    return pw.pw_name
        except Exception:
            pass
        return "root"

# ============================================================================
# БЛОК 12. SYSTEMOPS: БАЗА
# ============================================================================

class SystemOps:
    APT_DAILY_UNITS = [
        "apt-daily.timer", "apt-daily-upgrade.timer",
        "apt-daily.service", "apt-daily-upgrade.service",
        "unattended-upgrades.service",
        "mintupdate-automation-upgrade.timer",
        "mintupdate-automation-upgrade.service",
    ]

    def __init__(self, sudo, state, log, dry_run):
        self.sudo = sudo
        self.state = state
        self.log = log
        self.dry_run = dry_run
        self.grub_changed = False
        self.mount_items = []
        self.commit_targets = []
        self.backup_dir = os.path.join(state.user_home, "system-tuneup-backups")

    # ─── Бэкапы ─────────────────────────────────────────────────────────

    def _safe_backup_name(self, path):
        safe = path.lstrip("/").replace("/", "_")
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        return "%s.%s.bak" % (safe, ts)

    def _prune_backups(self, path):
        try:
            safe = path.lstrip("/").replace("/", "_")
            pattern = os.path.join(self.backup_dir, safe + ".*.bak")
            files = sorted(glob.glob(pattern),
                           key=lambda p: os.path.getmtime(p),
                           reverse=True)
            for old in files[BACKUP_KEEP_LAST:]:
                try:
                    os.remove(old)
                except Exception:
                    pass
        except Exception:
            pass

    def backup_file(self, path):
        if self.dry_run:
            return True
        try:
            if not self.path_exists(path):
                return True
            content = self.read_file(path)
            if content is None:
                self.log("[WARN] cannot read %s for backup" % path, "warning")
                return False
            os.makedirs(self.backup_dir, exist_ok=True)
            try:
                os.chmod(self.backup_dir, 0o700)
            except Exception:
                pass
            bp = os.path.join(self.backup_dir, self._safe_backup_name(path))
            with open(bp, "w", encoding="utf-8") as f:
                f.write(content)
            try:
                os.chmod(bp, 0o600)
            except Exception:
                pass
            if self.state.user_name and self.state.user_name != "root":
                try:
                    pw = pwd.getpwnam(self.state.user_name)
                    os.chown(bp, pw.pw_uid, pw.pw_gid)
                except Exception:
                    pass
            self._prune_backups(path)
            self.log("[BACKUP] %s" % os.path.basename(bp), "info")
            return True
        except Exception as e:
            self.log("[WARN] backup %s: %s" % (path, e), "warning")
            return False

    # ─── Запуск команд ──────────────────────────────────────────────────

    def sudo_run(self, args, input=None, ok_msg=None, err_msg=None,
                 ignore_error=False, timeout=None, env=None):
        if self.dry_run:
            self.log("[DRY RUN] " + " ".join(args), "warning")
            return True
        if timeout is None:
            timeout = SUDO_TIMEOUT_DEFAULT
        try:
            res = self.sudo.run(args, input=input, timeout=timeout, env=env)
        except PermissionError as e:
            self.log(str(e), "error")
            return False
        except subprocess.TimeoutExpired:
            self.log("Command timed out: " + " ".join(args), "error")
            return False
        except Exception as e:
            self.log("Command error: %s" % e, "error")
            return False
        if res.returncode == 0:
            if ok_msg:
                self.log(ok_msg, "success")
            return True
        if not ignore_error:
            err = decode_bytes(res.stderr).strip()
            msg = err_msg or "Command failed: " + " ".join(args)
            if err:
                self.log("[ERR] %s\n%s" % (msg, err), "error")
            else:
                self.log("[ERR] %s" % msg, "error")
        return False

    # ─── Файловые операции ──────────────────────────────────────────────

    def path_exists(self, path):
        if os.path.exists(path):
            return True
        try:
            return subprocess.run(["sudo", "-n", "test", "-e", path],
                                  capture_output=True,
                                  timeout=TIMEOUT_QUICK).returncode == 0
        except Exception:
            return False

    def read_file(self, path):
        if not self.path_exists(path):
            return ""
        try:
            res = subprocess.run(["sudo", "-n", "cat", path],
                                 capture_output=True, timeout=TIMEOUT_QUICK)
            if res.returncode == 0:
                return decode_bytes(res.stdout)
        except Exception:
            pass
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return None

    def atomic_write(self, path, content, chmod="644", owner=None, mkdir=False):
        if self.dry_run:
            self.log("[DRY RUN] atomic write: %s" % path, "warning")
            return True
        if mkdir:
            d = os.path.dirname(path)
            if d:
                self.sudo_run(["mkdir", "-p", d], ignore_error=True)
        tmp = path + ".tmp-tweaker"
        try:
            try:
                res = self.sudo.run(["tee", tmp], input=content.encode())
            except PermissionError as e:
                self.log(str(e), "error")
                return False
            except Exception as e:
                self.log("Write error %s: %s" % (tmp, e), "error")
                return False
            if res.returncode != 0:
                self.log("Cannot write %s" % tmp, "error")
                self.sudo_run(["rm", "-f", tmp], ignore_error=True)
                return False
            if chmod:
                self.sudo_run(["chmod", chmod, tmp], ignore_error=True)
            if owner:
                self.sudo_run(["chown", owner, tmp], ignore_error=True)
            if not self.sudo_run(["mv", "-f", tmp, path],
                                 err_msg="Cannot move %s -> %s" % (tmp, path)):
                self.sudo_run(["rm", "-f", tmp], ignore_error=True)
                return False
            return True
        except Exception as e:
            self.log("atomic_write %s: %s" % (path, e), "error")
            self.sudo_run(["rm", "-f", tmp], ignore_error=True)
            return False

    def write_file(self, path, content, chmod="644", owner=None, mkdir=False,
                   backup=True):
        if not backup:
            return self.atomic_write(path, content, chmod=chmod,
                                     owner=owner, mkdir=mkdir)
        ok_backup = self.backup_file(path)
        if not ok_backup:
            self.log("Backup failed for %s, write aborted" % path, "error")
            return False
        return self.atomic_write(path, content, chmod=chmod,
                                 owner=owner, mkdir=mkdir)

    def write_user_file(self, path, content, backup=True):
        if self.dry_run:
            self.log("[DRY RUN] user write: %s" % path, "warning")
            return True
        try:
            d = os.path.dirname(path)
            if d:
                os.makedirs(d, exist_ok=True)
            if backup and os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8",
                              errors="replace") as f:
                        old = f.read()
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    bp = path + "." + ts + ".bak"
                    with open(bp, "w", encoding="utf-8") as f:
                        f.write(old)
                    self.log("[BACKUP] %s" % os.path.basename(bp), "info")
                except Exception as e:
                    self.log("[WARN] backup %s: %s" % (path, e), "warning")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            try:
                os.chmod(path, 0o644)
            except Exception:
                pass
            return True
        except Exception as e:
            self.log("User write error %s: %s" % (path, e), "error")
            return False

    def remove_user_file(self, path):
        if self.dry_run:
            self.log("[DRY RUN] user rm %s" % path, "warning")
            return True
        try:
            if os.path.exists(path):
                os.remove(path)
                self.log("✓ removed %s" % path, "success")
            return True
        except Exception as e:
            self.log("User remove error %s: %s" % (path, e), "error")
            return False

    def verify_fstab(self):
        if self.dry_run:
            return True
        try:
            res = self.sudo.run(["findmnt", "--verify", "--verbose"],
                                timeout=SUDO_TIMEOUT_DEFAULT)
        except Exception as e:
            self.log("findmnt --verify error: %s" % e, "warning")
            return True
        if res.returncode != 0:
            err = (decode_bytes(res.stdout).strip() + " " +
                   decode_bytes(res.stderr).strip())
            self.log("fstab verify FAILED: %s" % err.strip(), "error")
            return False
        return True

    def ensure_line(self, path, line, pattern, chmod="644", mkdir=False):
        if self.dry_run:
            self.log("[DRY RUN] %s: %s" % (path, line), "warning")
            return True
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        lines = lines_in(content)
        new_lines, replaced, changed = [], False, False
        try:
            rx = re.compile(pattern)
        except re.error:
            rx = re.compile(re.escape(line))
        for old in lines:
            if rx.match(old.strip()):
                if not replaced:
                    if old != line:
                        changed = True
                    new_lines.append(line)
                    replaced = True
                else:
                    changed = True
            else:
                new_lines.append(old)
        if not replaced:
            new_lines.append(line)
            changed = True
        if not changed:
            self.log("Already configured: %s" % path, "info")
            return True
        return self.write_file(path, "\n".join(new_lines) + "\n",
                               chmod=chmod, mkdir=mkdir, backup=True)

    # ─── systemd ────────────────────────────────────────────────────────

    def unit_exists(self, name):
        try:
            res = subprocess.run(["systemctl", "list-unit-files", name,
                                  "--no-legend", "--no-pager"],
                                 capture_output=True, timeout=TIMEOUT_QUICK)
            for line in decode_bytes(res.stdout).splitlines():
                parts = line.split()
                if parts and parts[0] == name:
                    return True
        except Exception:
            pass
        return False

    def service_enabled(self, name):
        if not self.unit_exists(name):
            return "not-found"
        try:
            res = subprocess.run(["systemctl", "is-enabled", name],
                                 capture_output=True, timeout=TIMEOUT_QUICK)
            return decode_bytes(res.stdout).strip() or "unknown"
        except Exception:
            return "unknown"

    def service_active(self, name):
        try:
            res = subprocess.run(["systemctl", "is-active", name],
                                 capture_output=True, timeout=TIMEOUT_QUICK)
            return decode_bytes(res.stdout).strip() or "unknown"
        except Exception:
            return "unknown"

    def _spices(self):
        if not self.state.cinnamon:
            return False
        if shutil.which("cinnamon-spice-updater"):
            return True
        return os.path.exists("/usr/bin/cinnamon-spice-updater")

    # ─── GRUB ───────────────────────────────────────────────────────────

    @staticmethod
    def _grub_key(param):
        return param.split("=")[0]

    def add_grub_params(self, params):
        if self.dry_run:
            self.log("[DRY RUN] GRUB add: " + " ".join(params), "warning")
            return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        keys = {self._grub_key(p) for p in params}
        lines, found, changed = [], False, False
        for line in lines_in(content):
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                found = True
                raw = m.group(1).strip().strip('"').strip("'")
                old_parts = [p for p in raw.split() if p]
                kept = [p for p in old_parts if self._grub_key(p) not in keys]
                new_parts = kept + list(params)
                new_line = 'GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(new_parts) + '"'
                if old_parts != new_parts:
                    changed = True
                lines.append(new_line)
            else:
                lines.append(line)
        if not found:
            lines.append('GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(params) + '"')
            changed = True
        if not changed:
            self.log("GRUB already has params", "info")
            return True
        if not self.write_file(path, "\n".join(lines) + "\n", backup=True):
            return False
        self.grub_changed = True
        self.log("GRUB: params added", "success")
        return True

    def _grub_set_param(self, token):
        if self.dry_run:
            self.log("[DRY RUN] GRUB set: %s" % token, "warning")
            return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        key = self._grub_key(token)
        lines, found, changed = [], False, False
        for line in lines_in(content):
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                found = True
                raw = m.group(1).strip().strip('"').strip("'")
                old_parts = [p for p in raw.split() if p]
                kept = [p for p in old_parts if self._grub_key(p) != key]
                new_parts = kept + [token]
                new_line = 'GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(new_parts) + '"'
                if old_parts != new_parts:
                    changed = True
                lines.append(new_line)
            else:
                lines.append(line)
        if not found:
            lines.append('GRUB_CMDLINE_LINUX_DEFAULT="' + token + '"')
            changed = True
        if not changed:
            self.log("GRUB already has %s" % token, "info")
            return True
        if not self.write_file(path, "\n".join(lines) + "\n", backup=True):
            return False
        self.grub_changed = True
        self.log("GRUB: %s set" % token, "success")
        return True

    def _remove_grub_params(self, params):
        if self.dry_run:
            self.log("[DRY RUN] GRUB remove: " + " ".join(params), "warning")
            return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if not content:
            self.log("GRUB not found", "warning")
            return False
        keys = {self._grub_key(p) for p in params}
        new_lines, changed = [], False
        for line in lines_in(content):
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                raw = m.group(1).strip().strip('"').strip("'")
                old_parts = [p for p in raw.split() if p]
                new_parts = [p for p in old_parts if self._grub_key(p) not in keys]
                new_lines.append('GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(new_parts) + '"')
                if old_parts != new_parts:
                    changed = True
            else:
                new_lines.append(line)
        if not changed:
            self.log("GRUB params not found", "info")
            return True
        if not self.write_file(path, "\n".join(new_lines) + "\n", backup=True):
            return False
        self.grub_changed = True
        self.log("✓ GRUB params removed", "success")
        return True

    def finalize_grub(self):
        if not self.grub_changed:
            return
        if self.dry_run:
            self.log("[DRY RUN] update-grub", "warning")
            self.grub_changed = False
            return
        ug = shutil.which("update-grub")
        if not ug and os.path.exists("/usr/sbin/update-grub"):
            ug = "/usr/sbin/update-grub"
        gm = shutil.which("grub-mkconfig")
        if not gm and os.path.exists("/usr/sbin/grub-mkconfig"):
            gm = "/usr/sbin/grub-mkconfig"
        if ug:
            self.sudo_run([ug], ok_msg="GRUB updated", err_msg="update-grub failed",
                          timeout=SUDO_TIMEOUT_GRUB)
        elif gm:
            self.sudo_run([gm, "-o", "/boot/grub/grub.cfg"],
                          ok_msg="GRUB updated", err_msg="grub-mkconfig failed",
                          timeout=SUDO_TIMEOUT_GRUB)
        else:
            self.log("update-grub / grub-mkconfig not found", "warning")
        self.grub_changed = False

    # ─── apply: базовые твики ───────────────────────────────────────────

    def apply_journald(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] journald volatile 50M", "warning")
            return True
        path = "/etc/systemd/journald.conf"
        if not self.path_exists(path):
            content = ""
        else:
            content = self.read_file(path)
            if content is None:
                self.log("Cannot read %s" % path, "error")
                return False
        if (re.search(r"^\s*Storage\s*=\s*volatile\s*$", content, re.M)
                and re.search(r"^\s*RuntimeMaxUse\s*=\s*50M\s*$", content, re.M)):
            self.log("journald already configured", "info")
            return True
        out = []
        inserted = False
        for line in lines_in(content):
            if (re.match(r"^\s*(Storage|RuntimeMaxUse)\s*=", line)
                    and not line.lstrip().startswith("#")):
                out.append("# " + line)
                continue
            out.append(line)
            if re.match(r"^\s*\[Journal\]\s*$", line) and not inserted:
                out += ["Storage=volatile", "RuntimeMaxUse=50M"]
                inserted = True
        if not inserted:
            out = ["[Journal]", "Storage=volatile", "RuntimeMaxUse=50M"] + out
        if not self.write_file(path, "\n".join(out) + "\n", backup=True):
            return False
        if not self.sudo_run(["systemctl", "restart", "systemd-journald"],
                             ignore_error=True):
            self.log("journald written but restart failed", "warning")
        self.sudo_run(["journalctl", "--vacuum-size=200M",
                       "--vacuum-time=1months"], ignore_error=True)
        self.log("✓ journald → volatile (50M)", "success")
        return True

    def apply_audit(self, params=None):
        return self.add_grub_params(["audit=0"])

    def apply_raid(self, params=None):
        if self.state.has_raid:
            self.log("RAID detected, skipping", "warning")
            return None
        return self.add_grub_params(["raid=noautodetect"])

    def apply_nmi_watchdog(self, params=None):
        return self.add_grub_params(["nmi_watchdog=0"])

    def apply_itco_wdt(self, params=None):
        if not getattr(self.state, "is_intel", False):
            self.log("Not an Intel system, skipping", "warning")
            return None
        if not getattr(self.state, "has_itco_module", False):
            self.log("iTCO_wdt module not available, skipping", "warning")
            return None
        path = "/etc/modprobe.d/nmi-watchdog.conf"
        content = ("blacklist iTCO_wdt\n"
                   "blacklist iTCO_vendor_support\n"
                   "install iTCO_wdt /bin/false\n"
                   "install iTCO_vendor_support /bin/false\n")
        if not self.write_file(path, content, chmod="644", mkdir=True):
            return False
        self.log("✓ iTCO_wdt blacklisted (needs reboot)", "success")
        return True

    def rollback_itco_wdt(self, params=None):
        self._rm("/etc/modprobe.d/nmi-watchdog.conf")
        self.sudo_run(["modprobe", "-r", "iTCO_wdt"], ignore_error=True)
        self.log("✓ iTCO_wdt blacklist removed", "success")
        return True

    def apply_shutdown_timeout(self, params=None):
        params = params or {}
        val = str(params.get("shutdown_timeout_value",
                             SHUTDOWN_TIMEOUT_DEFAULT)).strip()
        if val not in SHUTDOWN_TIMEOUT_VALUES:
            self.log("Bad shutdown timeout value: %s" % val, "error")
            return False
        if self.dry_run:
            self.log("[DRY RUN] shutdown timeout = %s" % val, "warning")
            return True
        path = "/etc/systemd/system.conf"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        lines = lines_in(content)
        new_lines = []
        seen_start = seen_stop = False
        for line in lines:
            s = line.strip()
            if s.startswith("#DefaultTimeoutStartSec="):
                new_lines.append("DefaultTimeoutStartSec=%s" % val)
                seen_start = True
            elif s.startswith("#DefaultTimeoutStopSec="):
                new_lines.append("DefaultTimeoutStopSec=%s" % val)
                seen_stop = True
            elif re.match(r"^\s*DefaultTimeoutStartSec\s*=", line):
                new_lines.append("DefaultTimeoutStartSec=%s" % val)
                seen_start = True
            elif re.match(r"^\s*DefaultTimeoutStopSec\s*=", line):
                new_lines.append("DefaultTimeoutStopSec=%s" % val)
                seen_stop = True
            else:
                new_lines.append(line)
        if not seen_start:
            new_lines.append("DefaultTimeoutStartSec=%s" % val)
        if not seen_stop:
            new_lines.append("DefaultTimeoutStopSec=%s" % val)
        if not self.write_file(path, "\n".join(new_lines) + "\n", backup=True):
            return False
        self.sudo_run(["systemctl", "daemon-reexec"], ignore_error=True)
        self.log("✓ shutdown timeout set to %s" % val, "success")
        return True

    def rollback_shutdown_timeout(self, params=None):
        path = "/etc/systemd/system.conf"
        content = self.read_file(path)
        if not content:
            self.log("File not found: %s" % path, "info")
            return True
        lines = lines_in(content)
        new_lines = []
        for line in lines:
            if re.match(r"^\s*DefaultTimeoutStartSec\s*=", line):
                new_lines.append("#DefaultTimeoutStartSec=%s"
                                 % SHUTDOWN_TIMEOUT_SYSTEM_DEFAULT)
            elif re.match(r"^\s*DefaultTimeoutStopSec\s*=", line):
                new_lines.append("#DefaultTimeoutStopSec=%s"
                                 % SHUTDOWN_TIMEOUT_SYSTEM_DEFAULT)
            else:
                new_lines.append(line)
        if not self.write_file(path, "\n".join(new_lines) + "\n", backup=True):
            return False
        self.sudo_run(["systemctl", "daemon-reexec"], ignore_error=True)
        self.log("✓ shutdown timeout reset to 90s", "success")
        return True

    # ─── ZFS ────────────────────────────────────────────────────────────

    def apply_zfs_services(self, params=None):
        if self.dry_run:
            for u in ZFS_UNITS:
                self.log("[DRY RUN] systemctl disable --now %s" % u, "warning")
                self.log("[DRY RUN] systemctl mask %s" % u, "warning")
            return True
        ok_any = False
        for u in ZFS_UNITS:
            if not self.unit_exists(u):
                continue
            self.sudo_run(["systemctl", "disable", "--now", u], ignore_error=True)
            if self.sudo_run(["systemctl", "mask", u], ignore_error=True):
                ok_any = True
        if ok_any:
            self.log("✓ ZFS services masked", "success")
        return ok_any

    def rollback_zfs_services(self, params=None):
        if self.dry_run:
            for u in ZFS_UNITS:
                self.log("[DRY RUN] systemctl unmask %s" % u, "warning")
                self.log("[DRY RUN] systemctl enable %s" % u, "warning")
            return True
        for u in ZFS_UNITS:
            if not self.unit_exists(u):
                continue
            self.sudo_run(["systemctl", "unmask", u], ignore_error=True)
            self.sudo_run(["systemctl", "enable", u], ignore_error=True)
        self.log("✓ ZFS services unmasked", "success")
        return True

    def apply_zfs_remove_packages(self, params=None):
        if zfs_in_use():
            self.log("ZFS is in use, aborting package removal", "error")
            return False
        if not zfs_packages_installed():
            self.log("ZFS packages not installed", "info")
            return True
        if self.dry_run:
            self.log("[DRY RUN] apt purge zfs-zed zfsutils-linux", "warning")
            return True
        env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
        if not self.sudo_run(
                ["apt-get", "purge", "-y", "zfs-zed", "zfsutils-linux"],
                err_msg="apt purge ZFS failed",
                timeout=SUDO_TIMEOUT_APT, env=env):
            return False
        self.sudo_run(["apt-get", "autoremove", "-y"], ignore_error=True,
                      timeout=SUDO_TIMEOUT_APT, env=env)
        if not self.sudo_run(["update-initramfs", "-u", "-k", "all"],
                             ignore_error=True,
                             timeout=SUDO_TIMEOUT_INITRAMFS):
            self.log("update-initramfs failed after ZFS removal", "warning")
        if not self.sudo_run(["update-grub"], ignore_error=True,
                             timeout=SUDO_TIMEOUT_GRUB):
            self.log("update-grub failed after ZFS removal", "warning")
        self.log("✓ ZFS packages removed", "success")
        return True

    def rollback_zfs_remove_packages(self, params=None):
        self.log("Rollback of ZFS package removal is not supported. "
                 "Run 'sudo apt install zfsutils-linux' manually.", "warning")
        return False

    # ─── CoreCtrl ───────────────────────────────────────────────────────

    def _polkit_is_new(self):
        try:
            res = subprocess.run(["pkaction", "--version"],
                                 capture_output=True, text=True,
                                 timeout=TIMEOUT_QUICK)
            m = re.search(r"(\d+)\.(\d+)",
                          (res.stdout or "") + (res.stderr or ""))
            if m:
                return int(m.group(1)) > 0 or int(m.group(2)) >= 106
        except Exception:
            pass
        return os.path.isdir("/etc/polkit-1/rules.d")

    def apply_corectrl(self, params=None):
        params = params or {}
        group = params.get("corectrl_group", "").strip() or self.state.user_name
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", group):
            self.log("Bad group name: %s" % group, "error")
            return False
        if self.dry_run:
            self.log("[DRY RUN] CoreCtrl polkit rule for %s" % group, "warning")
            return True
        try:
            grp.getgrnam(group)
        except KeyError:
            self.log("Group not found: %s" % group, "error")
            return False
        if self._polkit_is_new():
            content = ("polkit.addRule(function(action, subject) {\n"
                       '    if ((action.id == "org.corectrl.helper.init" ||\n'
                       '         action.id == "org.corectrl.helperkiller.init") &&\n'
                       "        subject.local == true && subject.active == true &&\n"
                       '        subject.isInGroup("' + group + '")) {\n'
                       "        return polkit.Result.YES;\n"
                       "    }\n"
                       "});\n")
            path = "/etc/polkit-1/rules.d/90-corectrl.rules"
        else:
            content = ("[User permissions]\n"
                       "Identity=unix-group:" + group + "\n"
                       "Action=org.corectrl.*\nResultActive=yes\n")
            path = "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"
        if self.write_file(path, content, chmod="644", mkdir=True):
            pdir = os.path.dirname(path)
            if pdir and os.path.isdir(pdir):
                self.sudo_run(["chmod", "755", pdir], ignore_error=True)
            self.log("✓ CoreCtrl configured for %s" % group, "success")
            return True
        return False

    def rollback_corectrl(self, params=None):
        self._rm("/etc/polkit-1/rules.d/90-corectrl.rules")
        self._rm("/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla")
        self.log("✓ CoreCtrl rule removed", "success")
        return True

    def apply_ppfeaturemask(self, params=None):
        return self.add_grub_params(["amdgpu.ppfeaturemask=0xffffffff"])

    def apply_nvidia_modeset(self, params=None):
        return self.add_grub_params(["nvidia-drm.modeset=1"])

    def apply_vrr(self, params=None):
        if self.state.gpu not in ("AMD", "Unknown"):
            self.log("VRR is AMD-only", "warning")
            return None
        if self.dry_run:
            self.log("[DRY RUN] VRR config", "warning")
            return True
        content = ('Section "Device"\n    Identifier "AMD"\n'
                   '    Driver "amdgpu"\n'
                   '    Option "VariableRefresh" "true"\nEndSection\n')
        if self.write_file("/etc/X11/xorg.conf.d/20-amdgpu.conf", content,
                           chmod="644", mkdir=True):
            self.log("✓ VRR/FreeSync enabled", "success")
            return True
        return False

    def apply_radv(self, params=None):
        return self.ensure_line("/etc/environment", "RADV_PERFTEST=sam",
                                r"^\s*RADV_PERFTEST=.*")

    def apply_mesa(self, params=None):
        return self.ensure_line("/etc/environment",
                                "MESA_SHADER_CACHE_MAX_SIZE=4G",
                                r"^\s*MESA_SHADER_CACHE_MAX_SIZE=.*")

    def apply_pipewire(self, params=None):
        params = params or {}
        if not self.state.pipewire_active:
            self.log("PipeWire not active, skipping", "warning")
            return None
        preset_key = params.get("pipewire_preset", PIPEWIRE_PRESET_DEFAULT)
        if preset_key not in PIPEWIRE_PRESETS:
            preset_key = PIPEWIRE_PRESET_DEFAULT
        p = PIPEWIRE_PRESETS[preset_key]
        d = os.path.join(self.state.user_home, ".config", "pipewire",
                         "pipewire.conf.d")
        path = os.path.join(d, "10-sound.conf")
        content = ("context.properties = {\n"
                   "    default.clock.min-quantum = %d\n"
                   "    default.clock.quantum = %d\n"
                   "    default.clock.max-quantum = %d\n"
                   "}\n" % (p["min"], p["quantum"], p["max"]))
        if not self.write_user_file(path, content, backup=True):
            return False
        self.log("✓ PipeWire configured (%s)" % preset_key, "success")
        return True

    def apply_bbr(self, params=None):
        path = "/etc/sysctl.d/99-bbr.conf"
        content = ("net.core.default_qdisc=fq\n"
                   "net.ipv4.tcp_congestion_control=bbr\n")
        if not self.write_file(path, content, chmod="644", mkdir=True):
            return False
        self.sudo_run(["modprobe", "tcp_bbr"], ignore_error=True)
        if not os.path.exists("/sys/module/tcp_bbr"):
            self.log("tcp_bbr module not available in this kernel", "warning")
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        try:
            r = subprocess.run(["sysctl", "-n",
                                "net.ipv4.tcp_congestion_control"],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            cur = r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            cur = ""
        if cur != "bbr":
            self.log("BBR written but not active (current: %s)" % (cur or "?"),
                     "warning")
            return False
        self.log("✓ TCP BBR enabled", "success")
        return True

    def apply_swap(self, params=None):
        params = params or {}
        if not self.state.has_swap:
            self.log("No swap found, skipping", "warning")
            return None
        val = params.get("swap_value", "").strip()
        if not val:
            val = (SWAPPINESS_DEFAULT_ZRAM if self.state.swap_type == "zram"
                   else SWAPPINESS_DEFAULT_DISK)
        try:
            iv = int(val)
            if iv < SWAPPINESS_MIN or iv > SWAPPINESS_MAX:
                raise ValueError
        except ValueError:
            self.log("Bad swappiness: %s (%d-%d)"
                     % (val, SWAPPINESS_MIN, SWAPPINESS_MAX), "error")
            return False
        if self.dry_run:
            self.log("[DRY RUN] swappiness=%d" % iv, "warning")
            return True
        path = "/etc/sysctl.d/99-gaming-swap.conf"
        ex = self.read_file(path)
        if ex and re.search(r"^vm\.swappiness=%d$" % iv, ex, re.M):
            self.log("swappiness already %d" % iv, "info")
            return True
        if not self.write_file(path, "vm.swappiness=%d\n" % iv,
                               chmod="644", mkdir=True):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        try:
            r = subprocess.run(["sysctl", "-n", "vm.swappiness"],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            cur = r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            cur = ""
        if cur != str(iv):
            self.log("swappiness written but not active (current: %s)"
                     % (cur or "?"), "warning")
            return False
        self.log("✓ swappiness=%d" % iv, "success")
        return True

    def apply_zram(self, params=None):
        if not zram_generator_present():
            self.log("zram-generator not installed", "warning")
            return None
        path = "/etc/systemd/zram-generator.conf"
        content = ("[zram0]\nzram-size = ram-size / 2\n"
                   "compression-algorithm = zstd\n")
        if self.write_file(path, content, chmod="644", mkdir=True):
            self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
            self.log("✓ zram configured (reboot to activate)", "success")
            return True
        return False

    def apply_zswap(self, params=None):
        if not self.state.has_swap:
            self.log("No swap found, zswap skipped", "warning")
            return None
        pl = ["zswap.enabled=1", "zswap.compressor=zstd"]
        if os.path.exists("/sys/module/z3fold"):
            pl.append("zswap.zpool=z3fold")
        return self.add_grub_params(pl)

    def apply_thp(self, params=None):
        params = params or {}
        val = params.get("thp_value", "madvise")
        return self._grub_set_param("transparent_hugepage=%s" % val)

    def _sysctl_set(self, key, val):
        if self.dry_run:
            self.log("[DRY RUN] %s=%s" % (key, val), "warning")
            return True
        path = "/etc/sysctl.d/99-gaming-sysctl.conf"
        content = self.read_file(path) or ""
        rx = re.compile(r"^\s*%s\s*=" % re.escape(key))
        out, replaced = [], False
        for l in lines_in(content):
            if rx.match(l):
                out.append("%s=%s" % (key, val))
                replaced = True
            else:
                out.append(l)
        if not replaced:
            out.append("%s=%s" % (key, val))
        if not self.write_file(path, "\n".join(out) + "\n",
                               chmod="644", mkdir=True, backup=True):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        try:
            r = subprocess.run(["sysctl", "-n", key],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            cur = r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            cur = ""
        if cur != str(val):
            self.log("%s written but not active (current: %s)"
                     % (key, cur or "?"), "warning")
            return False
        self.log("✓ %s=%s" % (key, val), "success")
        return True

    def _sysctl_del(self, key, default):
        if self.dry_run:
            self.log("[DRY RUN] remove %s" % key, "warning")
            return True
        path = "/etc/sysctl.d/99-gaming-sysctl.conf"
        content = self.read_file(path) or ""
        rx = re.compile(r"^\s*%s\s*=" % re.escape(key))
        old = lines_in(content)
        out = [l for l in old if not rx.match(l)]
        if len(out) == len(old):
            self.log("%s not found in %s" % (key, path), "info")
        else:
            if not self.write_file(path, "\n".join(out) + "\n", backup=True):
                return False
        self.sudo_run(["sysctl", "-w", "%s=%s" % (key, default)],
                      ignore_error=True)
        self.log("✓ %s reverted to %s" % (key, default), "success")
        return True

    def apply_sysctl_cache(self, params=None):
        return self._sysctl_set("vm.vfs_cache_pressure", "50")

    def apply_sysctl_numa(self, params=None):
        return self._sysctl_set("kernel.numa_balancing", "0")

    def apply_reisub(self, params=None):
        path = "/etc/sysctl.d/99-sysrq.conf"
        content = "kernel.sysrq=244\n"
        if not self.write_file(path, content, chmod="644", mkdir=True):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        try:
            r = subprocess.run(["sysctl", "-n", "kernel.sysrq"],
                               capture_output=True, text=True,
                               timeout=TIMEOUT_QUICK)
            cur = r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            cur = ""
        if cur != "244":
            self.log("kernel.sysrq written but not active (current: %s)"
                     % (cur or "?"), "warning")
            return False
        self.log("✓ Magic SysRq (REISUB) enabled", "success")
        return True

    def apply_max_map_count(self, params=None):
        params = params or {}
        val = str(params.get("max_map_count_value",
                             MAX_MAP_COUNT_DEFAULT)).strip()
        if val not in MAX_MAP_COUNT_VALUES:
            self.log("Bad max_map_count value: %s" % val, "error")
            return False
        if self.dry_run:
            self.log("[DRY RUN] vm.max_map_count=%s" % val, "warning")
            return True
        path = "/etc/sysctl.d/99-gaming-mmap.conf"
        content = "vm.max_map_count=%s\n" % val
        if not self.write_file(path, content, chmod="644", mkdir=True):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        try:
            with open("/proc/sys/vm/max_map_count", "r") as f:
                cur = f.read().strip()
        except Exception:
            cur = ""
        if cur != val:
            self.log("max_map_count written but not active (current: %s)"
                     % (cur or "?"), "warning")
            return False
        self.log("✓ vm.max_map_count=%s" % val, "success")
        return True

    def rollback_max_map_count(self, params=None):
        self._rm("/etc/sysctl.d/99-gaming-mmap.conf")
        self.sudo_run(["sysctl", "-w", "vm.max_map_count=65530"],
                      ignore_error=True)
        self.log("✓ vm.max_map_count back to 65530", "success")
        return True

    def apply_ntsync(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] ntsync modules-load", "warning")
            return True
        if self.state.ntsync:
            self.log("ntsync already available", "info")
            return True
        if not self.write_file("/etc/modules-load.d/ntsync.conf",
                               "ntsync\n", chmod="644", mkdir=True):
            return False
        if not self.sudo_run(["modprobe", "ntsync"], ignore_error=True):
            self.log("ntsync module not loaded (needs kernel 6.14+)", "warning")
            return False
        if not os.path.exists("/dev/ntsync"):
            self.log("ntsync loaded but /dev/ntsync not present", "warning")
            return False
        self.log("✓ ntsync autoloaded", "success")
        return True

    def apply_tmpfs_tmp(self, params=None):
        params = params or {}
        size = str(params.get("tmpfs_size_value",
                              TMPFS_SIZE_DEFAULT)).strip() or TMPFS_SIZE_DEFAULT
        if not re.fullmatch(TMPFS_SIZE_REGEX, size):
            self.log("Bad tmpfs size: %s" % size, "error")
            return False
        if self.dry_run:
            self.log("[DRY RUN] /tmp tmpfs size=%s" % size, "warning")
            return True
        path = "/etc/fstab"
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error")
            return False
        rx = re.compile(r"^\s*tmpfs\s+/tmp\s+tmpfs\s")
        old_lines = lines_in(content)
        new_lines, replaced, changed = [], False, False
        for line in old_lines:
            if rx.match(line):
                new_line = ("tmpfs\t/tmp\ttmpfs\t"
                            "defaults,mode=1777,size=%s\t0 0" % size)
                if line.strip() != new_line:
                    changed = True
                new_lines.append(new_line)
                replaced = True
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.append("tmpfs\t/tmp\ttmpfs\t"
                             "defaults,mode=1777,size=%s\t0 0" % size)
            changed = True
        if not changed:
            self.log("/tmp tmpfs already configured with size %s" % size, "info")
            return True
        if not self.write_file(path, "\n".join(new_lines) + "\n", backup=True):
            return False
        if not self.verify_fstab():
            self.log("fstab verification failed — /tmp tmpfs may be unsafe",
                     "error")
            return False
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        self.log("✓ /tmp in tmpfs configured (needs reboot)", "success")
        return True

    def rollback_tmpfs_tmp(self, params=None):
        path = "/etc/fstab"
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error")
            return False
        rx = re.compile(r"^\s*tmpfs\s+/tmp\s+tmpfs\s")
        old = lines_in(content)
        new = [l for l in old if not rx.match(l)]
        if len(new) == len(old):
            self.log("/tmp tmpfs not found in fstab", "info")
            return True
        if not self.write_file(path, "\n".join(new) + "\n", backup=True):
            return False
        if not self.verify_fstab():
            self.log("fstab verification failed after rollback", "error")
            return False
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        self.log("✓ /tmp tmpfs removed (reboot to apply)", "success")
        return True

    def apply_ntfs3(self, params=None):
        if not getattr(self.state, "has_ntfs_partitions", False):
            self.log("No NTFS partitions found, skipping", "warning")
            return None
        if self.dry_run:
            self.log("[DRY RUN] ntfs3 unlock", "warning")
            return True
        path = "/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"
        if not self.path_exists(path):
            self.log("mint-blacklist-ntfs3.conf not found", "warning")
            return None
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        if not content.strip():
            self.log("File is empty, nothing to unlock", "info")
            return True
        if re.search(r"^\s*#\s*blacklist\s+ntfs3\s*$", content, re.M):
            self.log("ntfs3 already unlocked", "info")
            return True
        if re.search(r"^\s*blacklist\s+ntfs3\s*$", content, re.M):
            new = re.sub(r"^\s*blacklist\s+ntfs3\s*$",
                         "# blacklist ntfs3", content, flags=re.M)
            if self.write_file(path, new, backup=True):
                self.log("✓ ntfs3 unlocked", "success")
                return True
            return False
        self.log("blacklist ntfs3 not found", "warning")
        return None

    def rollback_ntfs3(self, params=None):
        path = "/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"
        content = self.read_file(path)
        if not content:
            self.log("File not found: %s" % path, "info")
            return True
        if re.search(r"^\s*blacklist\s+ntfs3\s*$", content, re.M):
            self.log("ntfs3 already blocked", "info")
            return True
        new = re.sub(r"^\s*#\s*blacklist\s+ntfs3\s*$", "blacklist ntfs3",
                     content, flags=re.M)
        if self.write_file(path, new, backup=True):
            self.log("✓ ntfs3 blocked again", "success")
            return True
        return False

    # ─── fstab ──────────────────────────────────────────────────────────

    def _device_identifiers(self, dev):
        idents = []
        try:
            res = subprocess.run(["lsblk", "-no", "UUID,LABEL,PARTUUID", dev],
                                 capture_output=True, text=True,
                                 timeout=TIMEOUT_QUICK)
            if res.returncode == 0:
                parts = res.stdout.strip().split(None, 2)
                if len(parts) >= 1 and parts[0]:
                    idents.append("UUID=%s" % parts[0])
                if len(parts) >= 2 and parts[1]:
                    idents.append("LABEL=%s" % parts[1])
                if len(parts) >= 3 and parts[2]:
                    idents.append("PARTUUID=%s" % parts[2])
        except Exception:
            pass
        return idents

    def _fstab_find(self, lines, mp, dev):
        idents = []
        if dev:
            idents = self._device_identifiers(dev)
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            f = s.split()
            if len(f) < 4:
                continue
            if f[1] == mp:
                return i, f
            if idents:
                first_lower = f[0].lower()
                for ident in idents:
                    if first_lower == ident.lower():
                        return i, f
        return None, None

    def _dev_of(self, mp):
        return next((it["dev"] for it in self.mount_items
                     if mp in it.get("mps", [])), None)

    def _fstype_of_mp(self, mp):
        for it in self.mount_items:
            if mp in it.get("mps", []):
                return it.get("fstype", "").lower()
        return ""

    def _mount_opts_edit(self, mp, add=True):
        path = "/etc/fstab"
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error")
            return False
        dev = self._dev_of(mp)
        lines = lines_in(content)
        idx, parts = self._fstab_find(lines, mp, dev)
        if idx is None:
            self.log("%s not found in fstab — skipped" % mp, "warning")
            return None
        opts = parts[3].split(",")
        if add:
            if "noatime" not in opts:
                opts.append("noatime")
            else:
                self.log("fstab %s already has noatime" % mp, "info")
                return True
        else:
            filtered = [o for o in opts if o not in ("noatime", "nodiratime")]
            if filtered == opts:
                self.log("fstab %s has no noatime" % mp, "info")
                return True
            opts = filtered
        parts[3] = ",".join(opts)
        lines[idx] = "\t".join(parts)
        if not self.write_file(path, "\n".join(lines) + "\n", backup=True):
            return False
        if not self.verify_fstab():
            self.log("fstab verification failed after editing %s" % mp, "error")
            return False
        if add:
            self.log("✓ fstab %s: +noatime" % mp, "success")
        else:
            self.log("✓ fstab %s: noatime removed" % mp, "success")
        return True

    def apply_mount_opts(self, mps):
        if self.dry_run:
            for mp in mps:
                self.log("[DRY RUN] fstab %s +noatime" % mp, "warning")
            return True
        res = [self._mount_opts_edit(mp, True) for mp in mps]
        if all(r is None for r in res):
            return None
        if any(r is False for r in res):
            return False
        return True

    def rollback_mount_opts(self, mps):
        if self.dry_run:
            for mp in mps:
                self.log("[DRY RUN] fstab %s -noatime" % mp, "warning")
            return True
        res = [self._mount_opts_edit(mp, False) for mp in mps]
        if all(r is None for r in res):
            return None
        if any(r is False for r in res):
            return False
        return True

    def _mount_commit_edit(self, mp, val, add=True):
        path = "/etc/fstab"
        fstype = self._fstype_of_mp(mp)
        if add and not fs_supports_commit(fstype):
            self.log("Skipped %s (%s): commit= is only valid for ext2/3/4"
                     % (mp, fstype or "unknown"), "warning")
            return None
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error")
            return False
        dev = self._dev_of(mp)
        lines = lines_in(content)
        idx, parts = self._fstab_find(lines, mp, dev)
        if idx is None:
            self.log("%s not found in fstab — skipped" % mp, "warning")
            return None
        opts = [o for o in parts[3].split(",") if not o.startswith("commit=")]
        if add:
            opts.append("commit=%s" % val)
        parts[3] = ",".join(opts)
        lines[idx] = "\t".join(parts)
        if not self.write_file(path, "\n".join(lines) + "\n", backup=True):
            return False
        if not self.verify_fstab():
            self.log("fstab verification failed after commit edit on %s" % mp,
                     "error")
            return False
        return True

    def apply_commit(self, params=None):
        params = params or {}
        val = str(params.get("commit_value", COMMIT_DEFAULT)).strip() or COMMIT_DEFAULT
        try:
            iv = int(val)
            if iv < COMMIT_MIN or iv > COMMIT_MAX:
                raise ValueError
        except ValueError:
            self.log("Bad commit value: %s (%d-%d)"
                     % (val, COMMIT_MIN, COMMIT_MAX), "error")
            return False
        val = str(iv)
        targets = list(self.commit_targets)
        if not targets:
            self.log("commit=: no ext2/3/4 partitions selected", "warning")
            return None
        if self.dry_run:
            for mp in targets:
                self.log("[DRY RUN] fstab %s commit=%s" % (mp, val), "warning")
            return None
        ok = True
        applied_any = False
        for mp in targets:
            fstype = self._fstype_of_mp(mp)
            if not fs_supports_commit(fstype):
                self.log("Skipped %s (%s): commit= unsupported here"
                         % (mp, fstype or "unknown"), "warning")
                continue
            r = self._mount_commit_edit(mp, val, True)
            if r is True:
                applied_any = True
            elif r is False:
                ok = False
        if not applied_any:
            self.log("commit=: all targets skipped", "warning")
            return None
        if not ok:
            return False
        self.log("✓ fstab commit=%s applied" % val, "success")
        return True

    def rollback_commit(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] fstab remove commit", "warning")
            return True
        targets = list(self.commit_targets)
        if not targets:
            return True
        res = [self._mount_commit_edit(mp, "", False) for mp in targets]
        if all(r is None for r in res):
            return None
        if any(r is False for r in res):
            return False
        self.log("✓ fstab commit removed", "success")
        return True

    def _commit_value_for(self, mp):
        try:
            with open("/etc/fstab", "r", encoding="utf-8",
                      errors="replace") as f:
                content = f.read()
        except Exception:
            return ""
        for line in lines_in(content):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            f2 = s.split()
            if len(f2) >= 4 and f2[1] == mp:
                for opt in f2[3].split(","):
                    if opt.startswith("commit="):
                        return opt
                return ""
        return ""

    def _commit_applied(self):
        try:
            with open("/etc/fstab", "r", encoding="utf-8",
                      errors="replace") as f:
                content = f.read()
        except Exception:
            return False
        candidates = self.commit_targets or [
            mp for m in self.mount_items
            if fs_supports_commit(m.get("fstype", ""))
            for mp in m["mps"]]
        if not candidates:
            return False
        for mp in candidates:
            fstype = self._fstype_of_mp(mp)
            if not fs_supports_commit(fstype):
                continue
            for line in lines_in(content):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                f2 = s.split()
                if len(f2) >= 4 and f2[1] == mp:
                    if any(o.startswith("commit=") for o in f2[3].split(",")):
                        return True
        return False

    def apply_steam_links(self, libs):
        src = os.path.join(self.state.user_home, ".steam", "steam",
                           "steamapps", "compatdata")
        try:
            os.makedirs(src, exist_ok=True)
        except Exception as e:
            self.log("Cannot create %s: %s" % (src, e), "error")
            return False
        for lib in libs:
            dst = os.path.join(lib, "compatdata")
            if os.path.realpath(lib) == os.path.realpath(os.path.dirname(src)):
                continue
            if self.dry_run:
                self.log("[DRY RUN] ln -s %s -> %s" % (src, dst), "warning")
                continue
            try:
                if os.path.islink(dst):
                    os.remove(dst)
                elif os.path.isdir(dst):
                    self.log("Skipped: %s exists as data directory" % dst,
                             "warning")
                    continue
                elif os.path.exists(dst):
                    self.log("Skipped: %s exists" % dst, "warning")
                    continue
                os.symlink(src, dst)
                self.log("✓ symlink created: %s" % dst, "success")
            except Exception as e:
                self.log("Symlink error %s: %s" % (dst, e), "error")
        return True

    def rollback_steam_links(self, libs):
        for lib in libs:
            dst = os.path.join(lib, "compatdata")
            if self.dry_run:
                self.log("[DRY RUN] rm %s" % dst, "warning")
                continue
            try:
                if os.path.islink(dst):
                    os.remove(dst)
                    self.log("✓ symlink removed: %s" % dst, "success")
                else:
                    self.log("Not a symlink, untouched: %s" % dst, "info")
            except Exception as e:
                self.log("Remove error %s: %s" % (dst, e), "error")
        return True

    def apply_aliases(self, params=None):
        bashrc = os.path.join(self.state.user_home, ".bashrc")
        if self.dry_run:
            self.log("[DRY RUN] add commands to .bashrc", "warning")
            return True
        if not self.path_exists(bashrc):
            self.log(".bashrc not found: %s" % bashrc, "error")
            return False
        content = self.read_file(bashrc)
        if content is None:
            self.log("Cannot read .bashrc", "error")
            return False
        sm = "# >>> system-tuneup commands >>>"
        em = "# <<< system-tuneup commands <<<"
        without, skip = [], False
        for line in lines_in(content):
            if line.strip() == sm:
                skip = True
                continue
            if line.strip() == em:
                skip = False
                continue
            if not skip:
                without.append(line)
        names = ["upd", "upgr", "spices", "update_all", "inst", "remove",
                 "search", "info", "clean", "space", "fix", "mem", "serv",
                 "update_time"]
        np_ = "|".join(names)
        alias_rx = re.compile(r"^\s*alias\s+(" + np_ + r")=")
        func_rx = re.compile(r"^\s*(" + np_ + r")\s*\(\)\s*\{")
        cleaned, skip_fn, warned = [], False, False
        for line in without:
            if alias_rx.match(line):
                if not warned:
                    self.log("Existing user aliases with same names found — "
                             "left untouched", "warning")
                    warned = True
                cleaned.append(line)
                continue
            if func_rx.match(line):
                if not warned:
                    self.log("Existing user functions with same names found — "
                             "left untouched", "warning")
                    warned = True
                cleaned.append(line)
                if "}" in line:
                    continue
                skip_fn = True
                continue
            if skip_fn:
                cleaned.append(line)
                if line.strip().startswith("}"):
                    skip_fn = False
                continue
            if "system-tuneup" in line and line.strip().startswith("#"):
                continue
            cleaned.append(line)
        spices, has_fp = self._spices(), self.state.has_flatpak
        block = [sm, "# system-tuneup commands", ""]
        block += ["upd() {", '    echo "APT update..."',
                  "    sudo apt update", "}", ""]
        block += ["upgr() {", '    echo "APT upgrade..."',
                  "    sudo apt full-upgrade"]
        if has_fp:
            block.append('    echo "Flatpak update..."')
            if spices:
                block.append("    flatpak update && "
                             "cinnamon-spice-updater --update-all")
            else:
                block.append("    flatpak update")
        block += ["}", ""]
        if spices:
            block += ["spices() {", '    echo "Cinnamon spices update..."',
                      "    cinnamon-spice-updater --update-all", "}", ""]
        block += ["update_all() {",
                  "    sudo apt update && sudo apt full-upgrade -y"]
        if has_fp:
            block.append("    flatpak update -y")
        if spices:
            block.append("    cinnamon-spice-updater --update-all")
        block += ['    echo "Done."', "}", ""]
        block += ["# Extra commands (system-tuneup)",
                  'inst() { sudo apt install "$@"; }',
                  'remove() { sudo apt purge --autoremove "$@"; }',
                  'search() { apt search "$@"; }',
                  'info() { apt show "$@"; }', ""]
        block += ["clean() {",
                  "    sudo apt autoremove -y && sudo apt autoclean && "
                  "sudo apt clean", "}", ""]
        block += ["space() {", "    df -h /", "}", ""]
        block += ["fix() {", "    sudo apt --fix-broken install -y",
                  "    sudo dpkg --configure -a", "}", ""]
        block += ["mem() {", "    sync && sudo sh -c "
                  "'echo 3 > /proc/sys/vm/drop_caches' && free -h", "}", ""]
        block += ["serv() {",
                  "    systemctl list-unit-files --type=service | less",
                  "}", ""]
        block += ["update_time() {",
                  "    systemctl list-timers --no-pager 2>/dev/null | "
                  'grep -E "NEXT|upgrade|update|apt" || echo "No timers"',
                  "}", ""]
        block.append(em)
        while cleaned and cleaned[-1].strip() == "":
            cleaned.pop()
        new = "\n".join(cleaned + [""] + block) + "\n"
        if new == content:
            self.log("Commands already added", "info")
            return True
        if not self.write_file(bashrc, new, backup=True):
            return False
        if self.state.user_name and self.state.user_name != "root":
            self.sudo_run(["chown",
                           "%s:%s" % (self.state.user_name,
                                      self.state.user_name),
                           bashrc], ignore_error=True)
        self.log("✓ commands added to .bashrc", "success")
        return True

    # ─── Автообновления ─────────────────────────────────────────────────

    def _mask_apt_daily(self):
        if self.dry_run:
            for u in self.APT_DAILY_UNITS:
                self.log("[DRY RUN] mask %s" % u, "warning")
            return True
        masked_any = False
        for u in self.APT_DAILY_UNITS:
            if not self.unit_exists(u):
                continue
            self.sudo_run(["systemctl", "disable", "--now", u],
                          ignore_error=True)
            if self.sudo_run(["systemctl", "mask", u], ignore_error=True):
                masked_any = True
        if masked_any:
            self.log("✓ apt-daily / unattended-upgrades masked", "success")
        return True

    def _unmask_apt_daily(self):
        if self.dry_run:
            for u in self.APT_DAILY_UNITS:
                self.log("[DRY RUN] unmask %s" % u, "warning")
            return True
        for u in self.APT_DAILY_UNITS:
            if not self.unit_exists(u):
                continue
            self.sudo_run(["systemctl", "unmask", u], ignore_error=True)
            self.sudo_run(["systemctl", "enable", u], ignore_error=True)
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        self.log("✓ apt-daily / unattended-upgrades unmasked and enabled",
                 "success")
        return True

    def apply_autoupdate(self, params=None):
        params = params or {}
        sched = params.get("update_schedule", "Отключено")
        table = {
            "Ежедневно": ("*-*-* 18:30:00", "daily 18:30"),
            "Еженедельно (суббота)": ("Sat 18:30:00", "weekly Sat"),
            "2 раза в месяц (1 и 15)": ("*-*-1,15 18:30:00", "1st & 15th"),
            "Ежемесячно (1 число)": ("*-*-1 18:30:00", "monthly 1st"),
            "Daily": ("*-*-* 18:30:00", "daily 18:30"),
            "Weekly (Saturday)": ("Sat 18:30:00", "weekly Sat"),
            "Twice a month (1 & 15)": ("*-*-1,15 18:30:00", "1st & 15th"),
            "Monthly (1st)": ("*-*-1 18:30:00", "monthly 1st"),
            "Disabled": (None, None), "Отключено": (None, None),
        }
        svc = "/etc/systemd/system/biweekly-upgrade.service"
        tmr = "/etc/systemd/system/biweekly-upgrade.timer"
        exists = self.path_exists(tmr) or self.path_exists(svc)
        if sched in ("Отключено", "Disabled"):
            if not exists:
                self.log("Auto-update timer not found", "info")
                self._unmask_apt_daily()
                return True
            if self.dry_run:
                self.log("[DRY RUN] remove timer", "warning")
                return True
            self.sudo_run(["systemctl", "disable", "--now",
                           "biweekly-upgrade.timer"], ignore_error=True)
            self.sudo_run(["rm", "-f", svc, tmr], ignore_error=True)
            self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
            self._unmask_apt_daily()
            self.log("Auto-update timer removed", "success")
            return True
        if sched not in table:
            self.log("Unknown schedule: %s" % sched, "error")
            return False
        onc, desc = table[sched]
        spices = self._spices()
        cmd = ("DEBIAN_FRONTEND=noninteractive apt-get update && "
               "DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y")
        if self.state.has_flatpak:
            cmd += " && flatpak update -y"
        if spices:
            cmd += " && cinnamon-spice-updater --update-all"
        svc_c = ("[Unit]\nDescription=System upgrade (%s)\n\n"
                 "[Service]\nType=oneshot\nExecStartPre=/bin/sleep 600\n"
                 "Environment=DEBIAN_FRONTEND=noninteractive\n"
                 "ExecStart=/usr/bin/bash -c \"%s\"\nUser=root\n"
                 % (desc, cmd))
        tmr_c = ("[Unit]\nDescription=System upgrade timer (%s)\n\n"
                 "[Timer]\nOnCalendar=%s\nPersistent=true\n\n"
                 "[Install]\nWantedBy=timers.target\n" % (desc, onc))
        ex_svc = self.read_file(svc) or ""
        ex_tmr = self.read_file(tmr) or ""
        if exists and ex_svc == svc_c and ex_tmr == tmr_c:
            self.log("Timer already configured: %s" % desc, "info")
            if (self.service_enabled("biweekly-upgrade.timer") != "enabled"
                    and not self.dry_run):
                self.sudo_run(["systemctl", "daemon-reload"],
                              ignore_error=True)
                self.sudo_run(["systemctl", "enable", "--now",
                               "biweekly-upgrade.timer"],
                              ignore_error=True)
            self._mask_apt_daily()
            return True
        if self.dry_run:
            self.log("[DRY RUN] create timer: %s" % desc, "warning")
            return True
        if not self.write_file(svc, svc_c, chmod="644", backup=True):
            return False
        if not self.write_file(tmr, tmr_c, chmod="644", backup=True):
            return False
        self._mask_apt_daily()
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        self.sudo_run(["systemctl", "enable", "--now",
                       "biweekly-upgrade.timer"],
                      ok_msg="✓ timer created: %s" % desc,
                      err_msg="Cannot enable timer")
        return True

    def rollback_autoupdate(self, params=None):
        ok = self.apply_autoupdate({"update_schedule": "Отключено"})
        self._unmask_apt_daily()
        return ok

    # ─── Удаление приложений ────────────────────────────────────────────

    def apps_purge(self, pkgs):
        if self.dry_run:
            self.log("[DRY RUN] apt purge " + " ".join(pkgs), "warning")
            return True, "?"
        freed = estimate_packages_size(pkgs)
        env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
        if not self.sudo_run(["apt-get", "purge", "-y"] + list(pkgs),
                             err_msg="apt purge failed",
                             timeout=SUDO_TIMEOUT_APT, env=env):
            return False, "?"
        self.sudo_run(["apt-get", "autoremove", "-y"],
                      ignore_error=True,
                      timeout=SUDO_TIMEOUT_APT, env=env)
        return True, freed

    # ─── Вспомогательные ────────────────────────────────────────────────

    def _rm(self, path):
        if self.dry_run:
            self.log("[DRY RUN] rm %s" % path, "warning")
            return True
        if not self.path_exists(path):
            self.log("File not found: %s" % path, "info")
            return True
        return self.sudo_run(["rm", "-f", path],
                             ok_msg="✓ removed %s" % path)

    def _remove_line(self, path, pattern):
        if self.dry_run:
            self.log("[DRY RUN] %s: remove %s" % (path, pattern), "warning")
            return True
        content = self.read_file(path)
        if not content:
            self.log("File not found: %s" % path, "info")
            return True
        rx = re.compile(pattern)
        old = lines_in(content)
        new = [l for l in old if not rx.match(l.strip())]
        if len(new) == len(old):
            self.log("Line not found in %s" % path, "info")
            return True
        return self.write_file(path, "\n".join(new) + "\n", backup=True)

    # ─── ROLLBACK ───────────────────────────────────────────────────────

    def rollback_journald(self, params=None):
        path = "/etc/systemd/journald.conf"
        safe = path.lstrip("/").replace("/", "_")
        pattern = os.path.join(self.backup_dir, safe + ".*.bak")
        candidates = sorted(glob.glob(pattern),
                            key=lambda p: os.path.getmtime(p),
                            reverse=True)
        if candidates:
            c = self.read_file(candidates[0])
            if c:
                self.write_file(path, c, backup=True)
                self.sudo_run(["systemctl", "restart", "systemd-journald"],
                              ignore_error=True)
                self.log("✓ journald restored from backup", "success")
                return True
        self._remove_line(path, r"^\s*Storage\s*=")
        self._remove_line(path, r"^\s*RuntimeMaxUse\s*=")
        self.sudo_run(["systemctl", "restart", "systemd-journald"],
                      ignore_error=True)
        self.log("✓ journald back to defaults", "success")
        return True

    def rollback_audit(self, params=None):
        return self._remove_grub_params(["audit=0"])

    def rollback_raid(self, params=None):
        return self._remove_grub_params(["raid=noautodetect"])

    def rollback_nmi_watchdog(self, params=None):
        return self._remove_grub_params(["nmi_watchdog=0"])

    def rollback_ppfeaturemask(self, params=None):
        return self._remove_grub_params(["amdgpu.ppfeaturemask=0xffffffff"])

    def rollback_nvidia_modeset(self, params=None):
        return self._remove_grub_params(["nvidia-drm.modeset=1"])

    def rollback_vrr(self, params=None):
        path = "/etc/X11/xorg.conf.d/20-amdgpu.conf"
        if not self.path_exists(path):
            self.log("VRR config not found, nothing to rollback", "info")
            return True
        safe = path.lstrip("/").replace("/", "_")
        pattern = os.path.join(self.backup_dir, safe + ".*.bak")
        candidates = sorted(glob.glob(pattern),
                            key=lambda p: os.path.getmtime(p),
                            reverse=True)
        if candidates:
            c = self.read_file(candidates[0])
            if c:
                if self.write_file(path, c, backup=True):
                    self.log("✓ VRR config restored from backup", "success")
                    return True
        content = self.read_file(path) or ""
        if re.search(r'Option\s+"VariableRefresh"', content, re.I):
            self._rm(path)
            self.log("✓ VRR config removed", "success")
        else:
            self.log("VRR config not ours, left untouched", "info")
        return True

    def rollback_radv(self, params=None):
        self._remove_line("/etc/environment", r"^\s*RADV_PERFTEST=.*")
        self.log("✓ RADV_PERFTEST removed", "success")
        return True

    def rollback_mesa(self, params=None):
        self._remove_line("/etc/environment",
                          r"^\s*MESA_SHADER_CACHE_MAX_SIZE=.*")
        self.log("✓ MESA cache removed", "success")
        return True

    def rollback_pipewire(self, params=None):
        path = os.path.join(self.state.user_home, ".config", "pipewire",
                            "pipewire.conf.d", "10-sound.conf")
        self.remove_user_file(path)
        self.log("✓ PipeWire config removed", "success")
        return True

    def rollback_bbr(self, params=None):
        self._rm("/etc/sysctl.d/99-bbr.conf")
        self.sudo_run(["sysctl", "-w",
                       "net.ipv4.tcp_congestion_control=cubic"],
                      ignore_error=True)
        self.sudo_run(["sysctl", "-w", "net.core.default_qdisc=pfifo_fast"],
                      ignore_error=True)
        self.log("✓ BBR and fq reverted", "success")
        return True

    def rollback_swap(self, params=None):
        self._rm("/etc/sysctl.d/99-gaming-swap.conf")
        self.log("✓ swappiness: file removed; live value reverts to stock "
                 "after reboot", "success")
        return True

    def rollback_zram(self, params=None):
        path = "/etc/systemd/zram-generator.conf"
        content = self.read_file(path) or ""
        if re.search(r"zram-size\s*=\s*ram-size", content):
            self._rm(path)
            self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
            self.log("✓ zram config removed", "success")
        else:
            self.log("zram config not ours, left untouched", "info")
        return True

    def rollback_zswap(self, params=None):
        return self._remove_grub_params(["zswap.enabled=1",
                                         "zswap.compressor=zstd",
                                         "zswap.zpool=z3fold"])

    def rollback_thp(self, params=None):
        return self._remove_grub_params(["transparent_hugepage=always",
                                         "transparent_hugepage=madvise",
                                         "transparent_hugepage=never"])

    def rollback_sysctl_cache(self, params=None):
        return self._sysctl_del("vm.vfs_cache_pressure", "100")

    def rollback_sysctl_numa(self, params=None):
        return self._sysctl_del("kernel.numa_balancing", "1")

    def rollback_reisub(self, params=None):
        self._rm("/etc/sysctl.d/99-sysrq.conf")
        self.sudo_run(["sysctl", "-w", "kernel.sysrq=176"], ignore_error=True)
        self.log("✓ kernel.sysrq back to 176", "success")
        return True

    def rollback_ntsync(self, params=None):
        self._rm("/etc/modules-load.d/ntsync.conf")
        self.log("✓ ntsync removed", "success")
        return True

    def rollback_aliases(self, params=None):
        bashrc = os.path.join(self.state.user_home, ".bashrc")
        content = self.read_file(bashrc)
        if not content:
            self.log(".bashrc not found", "info")
            return True
        sm = "# >>> system-tuneup commands >>>"
        em = "# <<< system-tuneup commands <<<"
        lines, skip = [], False
        for line in lines_in(content):
            if line.strip() == sm:
                skip = True
                continue
            if line.strip() == em:
                skip = False
                continue
            if not skip:
                lines.append(line)
        if len(lines) == len(lines_in(content)):
            self.log("Command block not found", "info")
            return True
        if not self.write_file(bashrc, "\n".join(lines) + "\n", backup=True):
            return False
        if self.state.user_name and self.state.user_name != "root":
            self.sudo_run(["chown",
                           "%s:%s" % (self.state.user_name,
                                      self.state.user_name),
                           bashrc], ignore_error=True)
        self.log("✓ commands removed from .bashrc", "success")
        return True

# ============================================================================
# БЛОК 13. СИГНАЛЫ
# ============================================================================

class Sig(QObject):
    log = pyqtSignal(str, str)
    statusbar = pyqtSignal(str)
    progress = pyqtSignal(int)
    running = pyqtSignal(bool)
    applied = pyqtSignal(dict)
    mount_applied = pyqtSignal(dict)
    steam_applied = pyqtSignal(dict)
    commit_applied = pyqtSignal(dict)
    schedule = pyqtSignal(str)
    services_rows = pyqtSignal(list)
    status_html = pyqtSignal(str)
    toast = pyqtSignal(str, str)
    spawn = pyqtSignal(object)
    ask_zfs_remove = pyqtSignal()
    result_summary = pyqtSignal(int, int, int)
    rebuild_tune = pyqtSignal()

class Task(QThread):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.fn()
        except Exception:
            traceback.print_exc()

# ============================================================================
# БЛОК 14. TOAST (всплывающее уведомление)
# ============================================================================

class Toast(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(22, 22)
        self.text_lbl = QLabel()
        self.text_lbl.setWordWrap(True)
        lay.addWidget(self.icon_lbl)
        lay.addWidget(self.text_lbl, 1)
        self._eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._anim = QPropertyAnimation(self._eff, b"opacity", self)
        self._anim.setDuration(240)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_anim)
        self.hide()

    def show_msg(self, text, kind, colors):
        self.text_lbl.setText(text)
        col = (colors["green"] if kind == "ok"
               else colors["red"] if kind == "err"
               else colors["yellow"])
        self.text_lbl.setStyleSheet("color: %s; font-weight: bold;" % col)
        self.icon_lbl.setPixmap(app_icon(
            "apply" if kind == "ok"
            else "rollback" if kind == "err" else "status",
            22, col).pixmap(22, 22))
        self.adjustSize()
        pw = self.parentWidget()
        if pw is not None:
            self.move(pw.width() - self.width() - 16, 60)
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(2600)

    def hide_anim(self):
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        try:
            self._anim.finished.disconnect(self._done)
        except Exception:
            pass
        self._anim.finished.connect(self._done)
        self._anim.start()

    def _done(self):
        if self._anim.currentValue() < 0.05:
            self.hide()

# ============================================================================
# БЛОК 15. BADGE (пилюля «применено/не применено» с анимацией)
# ============================================================================

class Badge(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("…")
        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(0.4)
        self.setGraphicsEffect(self._eff)
        self._anim = QPropertyAnimation(self._eff, b"opacity", self)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def set_state(self, text, fg, bg):
        self.setText(text)
        self.setStyleSheet(
            "background:%s; color:%s; border-radius:7px; padding:3px 9px; "
            "font-weight:bold;" % (bg, fg))
        self._anim.stop()
        self._anim.setStartValue(0.4)
        self._anim.setEndValue(1.0)
        self._anim.start()

# ============================================================================
# БЛОК 16. ГЛАВНОЕ ОКНО
# ============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sig = Sig()
        self.lang = detect_lang()
        self.theme = "light"
        self.is_running = False
        self.applied = {}
        self.mount_applied = {}
        self.steam_applied = {}
        self.commit_applied_per_mp = {}
        self.badges = {}
        self.mount_badges = {}
        self.steam_badges = {}
        self.commit_badges = {}
        self.option_widgets = {}
        self.disabled_reasons = {}
        self.opts_state = {k: False for k in OPTIONS_META}
        self.mount_state = {}
        self.steam_state = {}
        self.commit_state = {}
        self._tasks = []
        self._ram_cache = None
        self.sched_lbl = None
        self.thp_lbl = None
        self._zfs_button = None
        self._tune_filter = ""
        self._show_only_available = False
        self._apps_filter_text = ""
        self.apps_checked = set()
        self._installed_packages = None
        self._apps_inner_layout = None
        self._apps_status_lbl = None
        self._tune_inner_layout = None
        self._tune_scroll = None
        self._tune_filter_entry = None
        self._apps_scroll = None
        self._apps_filter_entry = None
        self._terminal = None
        self._progress = None
        self._status_lbl = None
        self._apply_btn = None
        self._rollback_btn = None
        self._selall_btn = None
        self._selnone_btn = None
        self._result_lbl = None
        self._toast = None
        self.sudo = SudoManager()
        self.sudo.prompt_password = self._ask_password
        self.sudo.show_error = lambda m: QMessageBox.warning(
            self, self.t("sudo_title"),
            self.t("sudo_wrong") + ("\n" + m if m else ""))
        self.state = SystemState()
        self.state.detect()
        dg = self.state.user_name if self.state.user_name != "root" else "sudo"
        self.corectrl_group = dg
        self.swap_value = "150" if self.state.swap_type == "zram" else "10"
        self.commit_value = "60"
        self.thp_value = "madvise"
        self.max_map_count_value = MAX_MAP_COUNT_DEFAULT
        self.tmpfs_size_value = TMPFS_SIZE_DEFAULT
        self.shutdown_timeout_value = SHUTDOWN_TIMEOUT_DEFAULT
        self.pipewire_preset_key = PIPEWIRE_PRESET_DEFAULT
        self.schedule_value = self._schedule_values()[2]
        self._build_mounts_and_steam()
        self._compute_disabled_reasons()
        # сигналы
        self.sig.log.connect(self._on_log)
        self.sig.statusbar.connect(self._on_statusbar)
        self.sig.progress.connect(self._on_progress)
        self.sig.running.connect(self._on_running)
        self.sig.applied.connect(self._on_applied)
        self.sig.mount_applied.connect(self._on_mount_applied)
        self.sig.steam_applied.connect(self._on_steam_applied)
        self.sig.commit_applied.connect(self._on_commit_applied)
        self.sig.schedule.connect(self._on_schedule)
        self.sig.services_rows.connect(self._on_services_rows)
        self.sig.status_html.connect(self._on_status_html)
        self.sig.toast.connect(self._on_toast)
        self.sig.spawn.connect(self._spawn_task)
        self.sig.ask_zfs_remove.connect(self._zfs_confirm)
        self.sig.result_summary.connect(self._show_result)
        self.sig.rebuild_tune.connect(self._rebuild_tune_list)
        self.build_ui()
        self.log("%s v%s запущен" % (APP_NAME, APP_VERSION), "success")
        self.log("GPU: %s %s" % (self.state.gpu, self.state.gpu_model), "info")
        QTimer.singleShot(200, lambda: self._spawn_task(self._services_work))
        QTimer.singleShot(400, lambda: self._spawn_task(self._applied_work))
        QTimer.singleShot(600, lambda: self._spawn_task(self._status_work))
        QTimer.singleShot(800, lambda: self._spawn_task(self._apps_load_installed))

    # ─── Инициализация данных ───────────────────────────────────────────

    def _build_mounts_and_steam(self):
        mounts, seen = [], set()
        for it in parse_mounts():
            if it["mp"] == "/boot/efi" or (it["fstype"] == "vfat"
                                           and it["mp"].startswith("/boot")):
                continue
            if it["dev"] in seen:
                for m in mounts:
                    if m["dev"] == it["dev"]:
                        m["mps"].append(it["mp"])
                continue
            seen.add(it["dev"])
            it["mps"] = [it["mp"]]
            mounts.append(it)
            self.mount_state[it["mp"]] = False
        self.mount_items = mounts
        for m in self.mount_items:
            if fs_supports_commit(m.get("fstype", "")):
                for mp in m["mps"]:
                    self.commit_state[mp] = False
        self.steam_items = []
        for lib in find_steam_libraries(self.state.user_home):
            if self._lib_on_ntfs(lib):
                self.steam_items.append(lib)
                self.steam_state[lib] = False

    def _compute_disabled_reasons(self):
        r = {}
        if self.state.has_raid:
            r["raid"] = self.t("reason_raid")
        if not getattr(self.state, "is_intel", False):
            r["itco_wdt"] = self.t("reason_itco_not_intel")
        elif not getattr(self.state, "has_itco_module", False):
            r["itco_wdt"] = self.t("reason_itco_no_module")
        elif not getattr(self.state, "nmi_watchdog_active", False):
            r["itco_wdt"] = self.t("reason_itco_watchdog_off")
        elif not getattr(self.state, "nmi_watchdog_in_grub", False):
            r["itco_wdt"] = self.t("reason_itco_grub_missing")
        if not getattr(self.state, "zfs_installed", False):
            r["zfs_services"] = self.t("reason_zfs_not_installed")
        if self.state.gpu not in ("AMD", "Unknown"):
            for k in ("corectrl", "ppfeaturemask", "vrr", "radv"):
                r[k] = self.t("reason_amd_only")
        if self.state.gpu not in ("NVIDIA", "Unknown"):
            r["nvidia_modeset"] = self.t("reason_nvidia_only")
        if not self.state.has_swap:
            r["swap"] = self.t("reason_no_swap")
            r["zswap"] = self.t("reason_no_swap")
        if not zram_generator_present():
            r["zram"] = self.t("reason_no_zram")
        if not os.path.exists("/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"):
            r["ntfs3"] = self.t("reason_mint_only")
        elif not getattr(self.state, "has_ntfs_partitions", False):
            r["ntfs3"] = self.t("reason_no_ntfs")
        if not getattr(self.state, "pipewire_active", False):
            r["pipewire"] = self.t("reason_pipewire_inactive")
        self.disabled_reasons = r

    def _lib_on_ntfs(self, lib):
        best, dev, fstype = "", "", ""
        for it in parse_mounts():
            mp = it["mp"]
            if (lib == mp or lib.startswith(mp.rstrip("/") + "/")
                    or mp == "/"):
                if len(mp) > len(best):
                    best, dev, fstype = mp, it["dev"], it["fstype"]
        if fstype in ("ntfs", "ntfs3", "fuseblk"):
            return True
        if fstype in ("auto", ""):
            fstype = self._fstype_of(dev)
        return fstype in ("ntfs", "ntfs3", "fuseblk")

    def _fstype_of(self, dev):
        known = {"ext2", "ext3", "ext4", "xfs", "btrfs", "f2fs",
                 "ntfs", "ntfs3", "vfat", "exfat", "fuseblk"}
        try:
            res = subprocess.run(["lsblk", "-no", "FSTYPE", dev],
                                 capture_output=True, text=True,
                                 timeout=5, env=self._host_env())
            out = [x.strip() for x in res.stdout.strip().splitlines()
                   if x.strip()]
            for ln in out:
                if ln in known:
                    return ln
            return out[0] if out else ""
        except Exception:
            return ""

    # ─── i18n ───────────────────────────────────────────────────────────

    def t(self, k):
        if k not in STR[self.lang]:
            return k
        return STR[self.lang][k]

    def om(self, k):
        return OPTIONS_META[k][self.lang]

    def colors(self):
        return THEMES[self.theme]

    def _host_env(self):
        return {k: v for k, v in os.environ.items()
                if k not in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONPATH",
                             "PYTHONHOME", "APPDIR", "APPIMAGE")}

    def _ask_password(self, attempt):
        text, ok = QInputDialog.getText(self, self.t("sudo_title"),
                                        self.t("sudo_prompt") % attempt,
                                        QLineEdit.Password)
        return text if ok else None

    def _schedule_values(self):
        if self.lang == "ru":
            return ("Отключено", "Ежедневно", "Еженедельно (суббота)",
                    "2 раза в месяц (1 и 15)", "Ежемесячно (1 число)")
        return ("Disabled", "Daily", "Weekly (Saturday)",
                "Twice a month (1 & 15)", "Monthly (1st)")

    def _pipewire_preset_label(self, key):
        p = PIPEWIRE_PRESETS[key]
        return "%s — %s" % (p["label_%s" % self.lang],
                            p["desc_%s" % self.lang])

    def _pipewire_preset_strings(self):
        result = []
        for key in ("default", "gaming", "recording"):
            result.append(self._pipewire_preset_label(key))
        return result

    # ─── Построение UI ──────────────────────────────────────────────────

    def build_ui(self):
        c = self.colors()
        self.setWindowTitle("%s v%s (%s)" % (APP_NAME, APP_VERSION, APP_BUILD_DATE))
        self.setWindowIcon(app_icon("logo", 64, c["accent"]))
        self.resize(1080, 820)
        self.setMinimumSize(880, 640)
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        # Шапка
        head = QHBoxLayout()
        head.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(app_icon("logo", 34, c["accent"]).pixmap(34, 34))
        head.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: %s;"
                            % c["accent"])
        head.addWidget(title)
        ver = QLabel("v%s (%s)" % (APP_VERSION, APP_BUILD_DATE))
        ver.setStyleSheet("color: %s;" % c["gray"])
        head.addWidget(ver)
        head.addStretch(1)
        self._about_btn = QPushButton(self.t("btn_about"))
        self._about_btn.clicked.connect(self.show_about)
        head.addWidget(self._about_btn)
        self._theme_btn = QPushButton(
            self.t("theme_dark") if self.theme == "light"
            else self.t("theme_light"))
        self._theme_btn.clicked.connect(self.toggle_theme)
        head.addWidget(self._theme_btn)
        self._lang_btn = QPushButton("EN" if self.lang == "ru" else "RU")
        self._lang_btn.setFixedWidth(46)
        self._lang_btn.clicked.connect(self.toggle_lang)
        head.addWidget(self._lang_btn)
        root.addLayout(head)

        # Вкладки
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._build_tune(c)
        self._build_serv(c)
        self._build_stat(c)
        self._build_apps(c)

        # Терминал
        tl = QLabel(self.t("lbl_terminal"))
        tl.setStyleSheet("color: %s;" % c["gray"])
        root.addWidget(tl)
        self._terminal = QTextEdit()
        self._terminal.setReadOnly(True)
        self._terminal.setMaximumHeight(150)
        self._terminal.setContextMenuPolicy(Qt.CustomContextMenu)
        self._terminal.customContextMenuRequested.connect(
            lambda p: self._menu_for(self._terminal, p))
        root.addWidget(self._terminal)

        # Статус-бар
        sb = QHBoxLayout()
        self._status_lbl = QLabel(self.t("ready"))
        self._status_lbl.setStyleSheet("color: %s;" % c["gray"])
        sb.addWidget(self._status_lbl)
        sb.addStretch(1)
        self._result_lbl = QLabel("")
        self._result_lbl.setStyleSheet("font-weight: bold; color: %s;"
                                       % c["gray"])
        sb.addWidget(self._result_lbl)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(200)
        self._progress.setFixedHeight(12)
        sb.addWidget(self._progress)
        self._dry_check = QCheckBox(self.t("lbl_dry"))
        self._dry_check.setStyleSheet("color: %s;" % c["yellow"])
        if "--dry-run" in sys.argv:
            self._dry_check.setChecked(True)
        sb.addWidget(self._dry_check)
        root.addLayout(sb)

        self._toast = Toast(central)

    # ─── Вкладка «Тюнинг» ───────────────────────────────────────────────

    def _build_tune(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, app_icon("gear", 40, c["accent"]),
                         self.t("tab_tune"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # Верхняя панель кнопок — как в Tkinter: слева в ряд
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self._apply_btn = QPushButton(self.t("btn_apply"))
        self._apply_btn.setObjectName("accent")
        self._apply_btn.clicked.connect(self.apply_selected)
        bar.addWidget(self._apply_btn)
        self._rollback_btn = QPushButton(self.t("btn_rollback"))
        self._rollback_btn.clicked.connect(self.rollback_selected)
        bar.addWidget(self._rollback_btn)
        self._selall_btn = QPushButton(self.t("btn_selall"))
        self._selall_btn.clicked.connect(self.select_all_options)
        bar.addWidget(self._selall_btn)
        self._selnone_btn = QPushButton(self.t("btn_selnone"))
        self._selnone_btn.clicked.connect(self.reset_options)
        bar.addWidget(self._selnone_btn)
        bar.addStretch(1)
        lay.addLayout(bar)

        # Панель поиска
        sbar = QHBoxLayout()
        sbar.setSpacing(6)
        sbar.addWidget(QLabel(self.t("lbl_search")))
        self._tune_filter_entry = QLineEdit()
        self._tune_filter_entry.textChanged.connect(self._on_tune_filter_changed)
        sbar.addWidget(self._tune_filter_entry, 1)
        clr = QPushButton(self.t("btn_search_clear"))
        clr.clicked.connect(lambda: self._tune_filter_entry.setText(""))
        sbar.addWidget(clr)
        self._avail_chk = QCheckBox(self.t("lbl_show_only_available"))
        self._avail_chk.toggled.connect(self._on_avail_toggled)
        sbar.addWidget(self._avail_chk)
        lay.addLayout(sbar)

        # Скролл-область твиков
        self._tune_scroll = QScrollArea()
        self._tune_scroll.setWidgetResizable(True)
        self._tune_scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner.setObjectName("optinner")
        self._tune_inner_layout = QVBoxLayout(inner)
        self._tune_inner_layout.setContentsMargins(4, 4, 4, 4)
        self._tune_inner_layout.setSpacing(2)
        self._tune_scroll.setWidget(inner)
        lay.addWidget(self._tune_scroll, 1)
        self._rebuild_tune_list()

    def _on_tune_filter_changed(self, text):
        self._tune_filter = text
        self._rebuild_tune_list()

    def _on_avail_toggled(self, val):
        self._show_only_available = val
        self._rebuild_tune_list()

    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _rebuild_tune_list(self):
        if self._tune_inner_layout is None:
            return
        c = self.colors()
        self._clear_layout(self._tune_inner_layout)
        self.badges = {}
        self.mount_badges = {}
        self.steam_badges = {}
        self.commit_badges = {}
        self.option_widgets = {}
        self.sched_lbl = None
        self.thp_lbl = None
        self._zfs_button = None

        cats = {}
        for k in OPTIONS_META:
            if k == "commit":
                continue
            cats.setdefault(self.om(k)[2], []).append(k)
        order = CAT_ORDER[self.lang]
        seq = [x for x in order if x in cats] + \
              [x for x in sorted(cats) if x not in order]
        query = (self._tune_filter or "").strip().lower()
        show_only_avail = self._show_only_available
        disk_cat = self.om("ntfs3")[2]
        any_shown = False

        for cat in seq:
            matches = []
            for k in cats[cat]:
                label, desc, _c, short = self.om(k)
                if show_only_avail and k in self.disabled_reasons:
                    continue
                if (not query or query in label.lower()
                        or query in desc.lower()
                        or query in short.lower()):
                    matches.append(k)
            show_disk_extras = (cat == disk_cat and not query)
            if not matches and not show_disk_extras:
                continue
            any_shown = True
            hdr = QLabel("─── %s ───" % cat)
            hdr.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;"
                              % c["yellow"])
            self._tune_inner_layout.addWidget(hdr)
            for k in matches:
                self._tune_inner_layout.addWidget(self._option_row(c, k))
            if show_disk_extras:
                self._build_disk_extras(c)

        if not any_shown:
            lbl = QLabel(self.t("search_no_results") % (self._tune_filter or ""))
            lbl.setStyleSheet("color: %s; font-style: italic;" % c["gray"])
            self._tune_inner_layout.addWidget(lbl)
        self._tune_inner_layout.addStretch(1)
        self._update_badges()

    def _option_row(self, c, key):
        label, desc, _cat, _short = self.om(key)
        disabled = key in self.disabled_reasons
        row = QFrame()
        row.setObjectName("optrow")
        vl = QVBoxLayout(row)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(2)

        top = QHBoxLayout()
        top.setSpacing(8)
        cb = QCheckBox(label)
        cb.setChecked(self.opts_state.get(key, False))
        cb.toggled.connect(lambda v, k=key: self.opts_state.__setitem__(k, v))
        if disabled:
            cb.setEnabled(False)
            cb.setChecked(False)
            self.opts_state[key] = False
        top.addWidget(cb)
        self.option_widgets[key] = cb
        if disabled:
            reason = QLabel("(%s)" % self.disabled_reasons[key])
            reason.setStyleSheet("color: %s; font-style: italic;" % c["gray"])
            top.addWidget(reason)

        # Особые контролы
        if key == "corectrl":
            top.addWidget(QLabel(self.t("lbl_group")))
            le = QLineEdit(self.corectrl_group)
            le.setFixedWidth(120)
            le.textChanged.connect(lambda v: setattr(self, "corectrl_group", v))
            if disabled:
                le.setEnabled(False)
            top.addWidget(le)
        elif key == "swap":
            top.addWidget(QLabel(self.t("lbl_value")))
            le = QLineEdit(self.swap_value)
            le.setFixedWidth(60)
            le.textChanged.connect(lambda v: setattr(self, "swap_value", v))
            if disabled:
                le.setEnabled(False)
            top.addWidget(le)
        elif key == "thp":
            top.addWidget(QLabel(self.t("lbl_value")))
            combo = QComboBox()
            combo.addItems(["always", "madvise", "never"])
            combo.setCurrentText(self.thp_value)
            combo.currentTextChanged.connect(lambda v: setattr(self, "thp_value", v))
            if disabled:
                combo.setEnabled(False)
            top.addWidget(combo)
            fmt = self.t("thp_cur")
            cur = self._thp_current() or "?"
            self.thp_lbl = QLabel(fmt % cur if "%" in fmt else fmt)
            self.thp_lbl.setStyleSheet("color: %s;" % c["gray"])
            top.addWidget(self.thp_lbl)
        elif key == "max_map_count":
            top.addWidget(QLabel(self.t("mmc_value_label")))
            combo = QComboBox()
            combo.addItems(MAX_MAP_COUNT_VALUES)
            combo.setCurrentText(self.max_map_count_value)
            combo.currentTextChanged.connect(
                lambda v: setattr(self, "max_map_count_value", v))
            if disabled:
                combo.setEnabled(False)
            top.addWidget(combo)
            cur = getattr(self.state, "current_max_map_count", "")
            if cur:
                lbl = QLabel(self.t("cur_value") % cur)
                lbl.setStyleSheet("color: %s;" % c["gray"])
                top.addWidget(lbl)
        elif key == "shutdown_timeout":
            top.addWidget(QLabel(self.t("lbl_value")))
            combo = QComboBox()
            combo.addItems(SHUTDOWN_TIMEOUT_VALUES)
            combo.setCurrentText(self.shutdown_timeout_value)
            combo.currentTextChanged.connect(
                lambda v: setattr(self, "shutdown_timeout_value", v))
            if disabled:
                combo.setEnabled(False)
            top.addWidget(combo)
            cur = self._shutdown_timeout_current()
            if cur and cur != "?":
                lbl = QLabel(self.t("cur_value") % cur)
                lbl.setStyleSheet("color: %s;" % c["gray"])
                top.addWidget(lbl)
        elif key == "tmpfs_tmp":
            top.addWidget(QLabel(self.t("tmpfs_size_label")))
            le = QLineEdit(self.tmpfs_size_value)
            le.setFixedWidth(80)
            le.textChanged.connect(lambda v: setattr(self, "tmpfs_size_value", v))
            if disabled:
                le.setEnabled(False)
            top.addWidget(le)
            if tmpfs_tmp_mounted() or fstab_has_tmp_tmpfs():
                lbl = QLabel(self.t("tmpfs_already"))
                lbl.setStyleSheet("color: %s;" % c["green"])
                top.addWidget(lbl)
        elif key == "autoupdate":
            top.addWidget(QLabel(self.t("lbl_schedule")))
            combo = QComboBox()
            combo.addItems(self._schedule_values())
            combo.setCurrentText(self.schedule_value)
            combo.currentTextChanged.connect(
                lambda v: setattr(self, "schedule_value", v))
            if disabled:
                combo.setEnabled(False)
            top.addWidget(combo)
            self.sched_lbl = QLabel()
            self.sched_lbl.setStyleSheet("color: %s;" % c["gray"])
            top.addWidget(self.sched_lbl)
        elif key == "pipewire":
            top.addWidget(QLabel(self.t("lbl_mode")))
            combo = QComboBox()
            combo.addItems(self._pipewire_preset_strings())
            combo.setCurrentText(self._pipewire_preset_label(
                self.pipewire_preset_key))
            def on_preset(text):
                for k2 in ("default", "gaming", "recording"):
                    if text == self._pipewire_preset_label(k2):
                        self.pipewire_preset_key = k2
                        return
            combo.currentTextChanged.connect(on_preset)
            if disabled:
                combo.setEnabled(False)
            top.addWidget(combo)

        # Текущее значение — справа
        cur_label = self._current_value_label(key)
        if cur_label:
            lbl = QLabel(cur_label)
            lbl.setStyleSheet("color: %s;" % c["gray"])
            top.addWidget(lbl)

        # Бейдж
        badge = Badge()
        top.addWidget(badge)
        self.badges[key] = badge

        # Кнопка «проверить» для corectrl
        if key == "corectrl":
            rb = QPushButton(self.t("btn_check_status"))
            rb.setObjectName("qbtn_small")
            rb.clicked.connect(self._check_corectrl_status)
            top.addWidget(rb)

        # Кнопки «файл» и «?»
        fb = QPushButton(self.t("btn_file"))
        fb.setObjectName("qbtn_small")
        fb.clicked.connect(lambda _c, k=key: self.open_option_file(k))
        top.addWidget(fb)
        qb = QPushButton(self.t("btn_q"))
        qb.setObjectName("qbtn")
        qb.setFixedSize(26, 26)
        qb.clicked.connect(lambda _c, k=key: self._show_option_help(k))
        top.addWidget(qb)
        top.addStretch(1)
        vl.addLayout(top)

        # Описание
        dl = QLabel(desc)
        dl.setWordWrap(True)
        dl.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
        vl.addWidget(dl)

        # ZFS: кнопка удаления пакетов
        if key == "zfs_services":
            zfs_removable = (self.state.zfs_installed
                             and not self.state.zfs_used)
            btn_text = (self.t("btn_remove_zfs") if zfs_removable
                        else self.t("btn_remove_zfs_unavailable"))
            self._zfs_button = QPushButton(btn_text)
            if zfs_removable:
                self._zfs_button.setStyleSheet("color: %s;" % c["red"])
                self._zfs_button.setEnabled(True)
            else:
                self._zfs_button.setStyleSheet("color: %s;" % c["gray"])
                self._zfs_button.setEnabled(False)
            self._zfs_button.clicked.connect(self._zfs_remove_packages)
            hl = QHBoxLayout()
            hl.setContentsMargins(24, 4, 0, 0)
            hl.addWidget(self._zfs_button)
            hl.addStretch(1)
            vl.addLayout(hl)
        return row

    def _current_value_label(self, key):
        try:
            if key == "sysctl_cache":
                return self.t("cur_value") % self._read_sysctl_int(
                    "/proc/sys/vm/vfs_cache_pressure", "?")
            if key == "nmi_watchdog":
                return (self.t("nmi_now_active")
                        if getattr(self.state, "nmi_watchdog_active", False)
                        else self.t("nmi_now_off"))
            if key == "swap":
                return self.t("cur_value") % self._swap_current()
            if key == "sysctl_numa":
                return self.t("cur_value") % self._numa_current()
            if key == "bbr":
                return self.t("cur_value") % self._bbr_current()
            if key == "journald":
                return self.t("cur_value") % self._journald_current()
            if key == "zswap":
                return self.t("cur_value") % self._zswap_current()
            if key == "zram":
                return self.t("cur_value") % self._zram_current()
            if key == "ntfs3":
                return self.t("cur_value") % self._ntfs3_current()
            if key == "ntsync":
                return self.t("cur_value") % self._ntsync_current()
        except Exception:
            pass
        return ""

    # ─── Диски: extras ──────────────────────────────────────────────────

    def _build_disk_extras(self, c):
        # mount options
        if self.mount_items:
            top = QWidget()
            hl = QHBoxLayout(top)
            hl.setContentsMargins(0, 8, 0, 2)
            h = QLabel("─── %s ───" % self.t("mount_title"))
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;"
                            % c["yellow"])
            hl.addWidget(h)
            fb = QPushButton(self.t("btn_file"))
            fb.setObjectName("qbtn_small")
            fb.clicked.connect(lambda _c: self._open_path("/etc/fstab"))
            hl.addWidget(fb)
            qb = QPushButton(self.t("btn_q"))
            qb.setObjectName("qbtn")
            qb.setFixedSize(26, 26)
            qb.clicked.connect(lambda _c: self._show_option_help("mount"))
            hl.addWidget(qb)
            hl.addStretch(1)
            self._tune_inner_layout.addWidget(top)
            d = QLabel(self.t("mount_desc"))
            d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            self._tune_inner_layout.addWidget(d)
            for m in self.mount_items:
                row = QFrame()
                row.setObjectName("optrow")
                hl = QHBoxLayout(row)
                hl.setContentsMargins(24, 4, 8, 4)
                key = m["mps"][0]
                cb = QCheckBox("%s (%s)" % (", ".join(m["mps"]),
                                            os.path.basename(m["dev"])))
                cb.setChecked(self.mount_state.get(key, False))
                cb.toggled.connect(
                    lambda v, k=key: self.mount_state.__setitem__(k, v))
                hl.addWidget(cb)
                info = self._disk_info(m["mps"][0])
                if info:
                    lbl = QLabel("%s, %s" % (m.get("fstype", ""),
                                             human_size(info[0] * 1024 ** 3)))
                    lbl.setStyleSheet("color: %s;" % c["gray"])
                    hl.addWidget(lbl)
                badge = Badge()
                hl.addWidget(badge)
                self.mount_badges[key] = badge
                hl.addStretch(1)
                self._tune_inner_layout.addWidget(row)

        # commit=
        top = QWidget()
        hl = QHBoxLayout(top)
        hl.setContentsMargins(0, 8, 0, 2)
        h = QLabel("─── %s ───" % self.t("commit_title"))
        h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;"
                        % c["yellow"])
        hl.addWidget(h)
        fb = QPushButton(self.t("btn_file"))
        fb.setObjectName("qbtn_small")
        fb.clicked.connect(lambda _c: self._open_path("/etc/fstab"))
        hl.addWidget(fb)
        qb = QPushButton(self.t("btn_q"))
        qb.setObjectName("qbtn")
        qb.setFixedSize(26, 26)
        qb.clicked.connect(lambda _c: self._show_option_help("commit"))
        hl.addWidget(qb)
        hl.addStretch(1)
        self._tune_inner_layout.addWidget(top)

        if self.commit_state:
            val_row = QHBoxLayout()
            val_row.setContentsMargins(8, 2, 8, 2)
            val_row.addWidget(QLabel(self.t("commit_value_label")))
            le = QLineEdit(self.commit_value)
            le.setFixedWidth(60)
            le.textChanged.connect(lambda v: setattr(self, "commit_value", v))
            val_row.addWidget(le)
            lbl = QLabel(self.t("commit_default_hint"))
            lbl.setStyleSheet("color: %s;" % c["gray"])
            val_row.addWidget(lbl)
            val_row.addStretch(1)
            self._tune_inner_layout.addLayout(val_row)
            d = QLabel(self.t("commit_desc"))
            d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            self._tune_inner_layout.addWidget(d)
            for m in self.mount_items:
                if not fs_supports_commit(m.get("fstype", "")):
                    continue
                for mp in m["mps"]:
                    row = QFrame()
                    row.setObjectName("optrow")
                    hl = QHBoxLayout(row)
                    hl.setContentsMargins(24, 4, 8, 4)
                    cb = QCheckBox("%s (%s) — %s" % (mp,
                                                     os.path.basename(m["dev"]),
                                                     m["fstype"]))
                    cb.setChecked(self.commit_state.get(mp, False))
                    cb.toggled.connect(
                        lambda v, k=mp: self.commit_state.__setitem__(k, v))
                    hl.addWidget(cb)
                    cur_val = self._commit_value_for_ui(mp) or \
                        self.t("commit_not_set")
                    lbl = QLabel(cur_val)
                    lbl.setStyleSheet("color: %s;" % c["gray"])
                    hl.addWidget(lbl)
                    badge = Badge()
                    hl.addWidget(badge)
                    self.commit_badges[mp] = badge
                    hl.addStretch(1)
                    self._tune_inner_layout.addWidget(row)
        else:
            d = QLabel(self.t("commit_none"))
            d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            self._tune_inner_layout.addWidget(d)

        # Steam
        if self.steam_items:
            top = QWidget()
            hl = QHBoxLayout(top)
            hl.setContentsMargins(0, 8, 0, 2)
            h = QLabel("─── %s ───" % self.t("steam_title"))
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;"
                            % c["yellow"])
            hl.addWidget(h)
            qb = QPushButton(self.t("btn_q"))
            qb.setObjectName("qbtn")
            qb.setFixedSize(26, 26)
            qb.clicked.connect(lambda _c: self._show_option_help("steam"))
            hl.addWidget(qb)
            hl.addStretch(1)
            self._tune_inner_layout.addWidget(top)
            d = QLabel(self.t("steam_desc"))
            d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            self._tune_inner_layout.addWidget(d)
            for lib in self.steam_items:
                row = QFrame()
                row.setObjectName("optrow")
                hl = QHBoxLayout(row)
                hl.setContentsMargins(24, 4, 8, 4)
                cb = QCheckBox(lib)
                cb.setChecked(self.steam_state.get(lib, False))
                cb.toggled.connect(
                    lambda v, k=lib: self.steam_state.__setitem__(k, v))
                hl.addWidget(cb)
                badge = Badge()
                hl.addWidget(badge)
                self.steam_badges[lib] = badge
                hl.addStretch(1)
                self._tune_inner_layout.addWidget(row)

    # ─── Вкладка «Службы» ───────────────────────────────────────────────

    def _build_serv(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, app_icon("services", 40, c["blue"]),
                         self.t("tab_serv"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        for txt, fn in ((self.t("btn_selall"), self.select_all_services),
                        (self.t("btn_selnone"), self.clear_services_selection),
                        (self.t("svc_off_sel"), self.disable_selected),
                        (self.t("svc_on_sel"), self.enable_selected)):
            b = QPushButton(txt)
            b.clicked.connect(fn)
            bar.addWidget(b)
        bar.addStretch(1)
        lay.addLayout(bar)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            self.t("svc_col_sel"), self.t("svc_name"),
            self.t("svc_state"), self.t("svc_run"),
            self.t("svc_desc"), self.t("svc_help")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 240)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(5, 34)
        hh.sectionClicked.connect(self._on_header_clicked)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.itemSelectionChanged.connect(self._serv_detail)
        lay.addWidget(self.table, 1)
        hint = QLabel(self.t("svc_hint"))
        hint.setStyleSheet("color: %s;" % c["gray"])
        lay.addWidget(hint)
        self.serv_detail = QTextEdit()
        self.serv_detail.setReadOnly(True)
        self.serv_detail.setMaximumHeight(80)
        self.serv_detail.setContextMenuPolicy(Qt.CustomContextMenu)
        self.serv_detail.customContextMenuRequested.connect(
            lambda p: self._menu_for(self.serv_detail, p))
        lay.addWidget(self.serv_detail)
        # сортировка
        self._svc_sort_col = None
        self._svc_sort_reverse = False

    def _on_header_clicked(self, idx):
        col_map = {1: "name", 2: "state", 3: "run", 4: "desc"}
        col = col_map.get(idx)
        if not col:
            return
        if self._svc_sort_col == col:
            self._svc_sort_reverse = not self._svc_sort_reverse
        else:
            self._svc_sort_col = col
            self._svc_sort_reverse = False
        self._render_services_rows()

    # ─── Вкладка «Статус» ───────────────────────────────────────────────

    def _build_stat(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, app_icon("status", 40, c["green"]),
                         self.t("tab_stat"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        b = QPushButton(self.t("stat_refresh"))
        b.clicked.connect(lambda: self._spawn_task(self._status_work))
        lay.addWidget(b, 0, Qt.AlignLeft)
        self.stat_view = QTextBrowser()
        self.stat_view.setOpenExternalLinks(True)
        self.stat_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.stat_view.customContextMenuRequested.connect(
            lambda p: self._menu_for(self.stat_view, p))
        lay.addWidget(self.stat_view, 1)

    # ─── Вкладка «Приложения» ───────────────────────────────────────────

    def _build_apps(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, app_icon("apps", 40, c["orange"]),
                         self.t("tab_apps"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self._apps_remove_btn = QPushButton(self.t("apps_remove"))
        self._apps_remove_btn.setObjectName("accent_warn")
        self._apps_remove_btn.clicked.connect(self._apps_remove_selected)
        bar.addWidget(self._apps_remove_btn)
        clr = QPushButton(self.t("apps_clear"))
        clr.clicked.connect(self._apps_clear)
        bar.addWidget(clr)
        rfr = QPushButton(self.t("apps_refresh"))
        rfr.clicked.connect(self._apps_refresh)
        bar.addWidget(rfr)
        bar.addStretch(1)
        lay.addLayout(bar)
        sbar = QHBoxLayout()
        sbar.addWidget(QLabel(self.t("apps_search")))
        self._apps_filter_entry = QLineEdit()
        self._apps_filter_entry.textChanged.connect(self._on_apps_filter_changed)
        sbar.addWidget(self._apps_filter_entry, 1)
        lay.addLayout(sbar)
        self._apps_scroll = QScrollArea()
        self._apps_scroll.setWidgetResizable(True)
        self._apps_scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner.setObjectName("optinner")
        self._apps_inner_layout = QVBoxLayout(inner)
        self._apps_inner_layout.setContentsMargins(4, 4, 4, 4)
        self._apps_inner_layout.setSpacing(2)
        self._apps_scroll.setWidget(inner)
        lay.addWidget(self._apps_scroll, 1)
        self._apps_status_lbl = QLabel(self.t("apps_selected_none"))
        self._apps_status_lbl.setStyleSheet("color: %s;" % c["gray"])
        lay.addWidget(self._apps_status_lbl)

    def _on_apps_filter_changed(self, text):
        self._apps_filter_text = text
        self._apps_render()

    # ========================================================================
    # ЛОГИКА
    # ========================================================================

    def _spawn_task(self, fn):
        self._tasks = [t for t in self._tasks if t.isRunning()]
        t = Task(fn)
        self._tasks.append(t)
        t.start()
        return t

    def log(self, msg, tag="normal"):
        self.sig.log.emit(msg, tag)

    def _on_log(self, msg, tag):
        c = self.colors()
        colors = {"normal": c["terminal_fg"], "success": c["green"],
                  "error": c["red"], "warning": c["yellow"],
                  "info": c["blue"], "highlight": c["orange"]}
        self._terminal.moveCursor(QTextCursor.End)
        for line in msg.split("\n"):
            esc = (line.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;"))
            self._terminal.insertHtml(
                "<span style='color:%s; white-space:pre;'>%s</span><br>"
                % (colors.get(tag, c["terminal_fg"]), esc))
        self._terminal.moveCursor(QTextCursor.End)

    def _on_statusbar(self, s):
        self._status_lbl.setText(s)

    def _on_progress(self, v):
        self._progress.setValue(v)

    def _on_running(self, r):
        self.is_running = r
        for b in (self._apply_btn, self._rollback_btn,
                  self._selall_btn, self._selnone_btn):
            if b is not None:
                b.setEnabled(not r)

    def _on_applied(self, d):
        self.applied = d
        self._update_badges()

    def _on_mount_applied(self, d):
        self.mount_applied = d
        self._update_badges()

    def _on_steam_applied(self, d):
        self.steam_applied = d
        self._update_badges()

    def _on_commit_applied(self, d):
        self.commit_applied_per_mp = d
        self._update_badges()

    def _on_schedule(self, s):
        if self.sched_lbl is not None:
            self.sched_lbl.setText(self.t("sched_cur") % s)

    def _on_toast(self, text, kind):
        if self._toast is not None and text:
            self._toast.show_msg(text, kind, self.colors())

    def _show_result(self, ok, skip, fail):
        if self._result_lbl is None:
            return
        c = self.colors()
        if fail == 0 and ok > 0:
            mark, col = "✓", c["green"]
        elif fail == 0 and ok == 0:
            mark, col = "•", c["gray"]
        elif fail < ok:
            mark, col = "⚠", c["yellow"]
        else:
            mark, col = "✗", c["red"]
        self._result_lbl.setText(
            "%s  %d ok / %d skip / %d fail" % (mark, ok, skip, fail))
        self._result_lbl.setStyleSheet("font-weight: bold; color: %s;" % col)
        QTimer.singleShot(5000, lambda: self._result_lbl.setText(""))

    # ─── Меню ───────────────────────────────────────────────────────────

    def _menu_for(self, w, pos):
        menu = QMenu(self)
        menu.addAction(self.t("menu_copy")).triggered.connect(
            lambda: self._copy_sel(w))
        menu.addAction(self.t("menu_copy_all")).triggered.connect(
            lambda: QApplication.clipboard().setText(w.toPlainText()))
        menu.addAction(self.t("menu_select_all")).triggered.connect(
            lambda: w.selectAll())
        menu.exec_(w.mapToGlobal(pos))

    def _copy_sel(self, w):
        cur = w.textCursor()
        if cur.hasSelection():
            QApplication.clipboard().setText(cur.selectedText())

    # ─── Справки ────────────────────────────────────────────────────────

    def _show_option_help(self, key):
        txt = OPTIONS_HELP.get(key, {}).get(self.lang, "")
        if not txt:
            self.log("No help for %s" % key, "info")
            return
        title = self.om(key)[0] if key in OPTIONS_META else \
            (self.t("mount_title") if key == "mount"
             else self.t("commit_title") if key == "commit"
             else self.t("steam_title"))
        html = ("<p style='font-size:14px;'>%s</p>"
                % txt.replace("&", "&amp;").replace("<", "&lt;")
                     .replace(">", "&gt;").replace("\n\n", "</p><p>")
                     .replace("\n", "<br>"))
        self._open_info_dialog(title, html)

    def _show_service_help(self, name):
        txt = SERVICES_HELP.get(name, {}).get(self.lang, "")
        if not txt:
            self.log("No help for %s" % name, "info")
            return
        html = ("<p style='font-size:14px;'>%s</p>"
                % txt.replace("&", "&amp;").replace("<", "&lt;")
                     .replace(">", "&gt;").replace("\n\n", "</p><p>")
                     .replace("\n", "<br>"))
        self._open_info_dialog(name, html)

    def _open_info_dialog(self, title, html):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setModal(True)
        dlg.resize(720, 560)
        vl = QVBoxLayout(dlg)
        te = QTextBrowser()
        te.setOpenExternalLinks(True)
        te.setContextMenuPolicy(Qt.CustomContextMenu)
        te.customContextMenuRequested.connect(lambda p, w=te: self._menu_for(w, p))
        te.setHtml(html)
        vl.addWidget(te)
        bb = QHBoxLayout()
        bb.addStretch(1)
        cb = QPushButton(self.t("btn_close"))
        cb.clicked.connect(dlg.close)
        bb.addWidget(cb)
        vl.addLayout(bb)
        dlg.exec_()

    def show_about(self):
        disclaimer_html = (self.t("about_disclaimer")
                           .replace("&", "&amp;").replace("<", "&lt;")
                           .replace(">", "&gt;").replace("\n", "<br>"))
        html = ('<div style="font-family: monospace;">'
                '<h2>%s v%s</h2>'
                '<p style="color:#888;">%s</p>'
                '<p>%s</p>'
                '<p><b>%s:</b> %s</p>'
                '<p><b>%s:</b> %s</p>'
                '<p><a href="%s">%s</a></p>'
                '<hr>'
                '<p style="font-size:12px;">%s</p>'
                '</div>'
                % (APP_NAME, APP_VERSION, APP_BUILD_DATE,
                   self.t("about_purpose"),
                   self.t("about_author"), self.t("about_author_name"),
                   self.t("about_license"), LICENSE_NAME,
                   GITHUB_URL, GITHUB_URL,
                   disclaimer_html))
        self._open_info_dialog(self.t("about_title"), html)

    def _open_path(self, path):
        ops = SystemOps(self.sudo, self.state, lambda m, t="normal": None, True)
        ops.mount_items = self.mount_items
        content = ops.read_file(path) or ""
        self._show_viewer(path, content)

    def open_option_file(self, key):
        cands = [p.format(home=self.state.user_home)
                 for p in OPTION_FILES.get(key, [])]
        if not cands:
            return
        target = next((p for p in cands if os.path.exists(p)), None)
        if target is None:
            if not self.sudo._cached():
                if not self.sudo.ensure():
                    return
            target = next(
                (p for p in cands
                 if subprocess.run(["sudo", "-n", "test", "-e", p],
                                   capture_output=True,
                                   timeout=5).returncode == 0),
                None)
        if target is None:
            QMessageBox.information(self, self.t("viewer"),
                                    self.t("msg_nofile") + "\n"
                                    + "\n".join(cands))
            return
        ops = SystemOps(self.sudo, self.state, lambda m, t="normal": None, True)
        ops.mount_items = self.mount_items
        content = ops.read_file(target) or ""
        self._show_viewer(target, content)

    def _show_viewer(self, path, content):
        dlg = QDialog(self)
        dlg.setWindowTitle("%s: %s" % (self.t("viewer"), path))
        dlg.resize(760, 520)
        vl = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(content)
        te.setStyleSheet("font-family: 'DejaVu Sans Mono', monospace;")
        te.setContextMenuPolicy(Qt.CustomContextMenu)
        te.customContextMenuRequested.connect(lambda p: self._menu_for(te, p))
        vl.addWidget(te)
        b = QPushButton(self.t("viewer_ext"))
        b.clicked.connect(lambda: self._open_ext(path))
        vl.addWidget(b, 0, Qt.AlignLeft)
        bb = QHBoxLayout()
        bb.addStretch(1)
        cb = QPushButton(self.t("btn_close"))
        cb.clicked.connect(dlg.close)
        bb.addWidget(cb)
        vl.addLayout(bb)
        dlg.exec_()

    def _open_ext(self, path):
        env = self._host_env()
        if os.geteuid() == 0 and self.state.user_name != "root":
            env["DISPLAY"] = os.environ.get("DISPLAY", ":0")
            env["XAUTHORITY"] = os.environ.get("XAUTHORITY") or \
                os.path.join(self.state.user_home, ".Xauthority")
        for cmd in (["xed", path], ["mousepad", path], ["gedit", path],
                    ["kate", path], ["pluma", path], ["xdg-open", path],
                    ["gio", "open", path]):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True, env=env)
                return
            except Exception:
                continue
        self.log("Cannot open external editor for %s" % path, "error")

    # ─── Выбор всех/ничего ──────────────────────────────────────────────

    def select_all_options(self):
        for k, v in self.opts_state.items():
            if k in self.disabled_reasons:
                continue
            w = self.option_widgets.get(k)
            if w is not None and w.isEnabled():
                v = True
                self.opts_state[k] = True
                w.setChecked(True)
        for k in self.mount_state:
            self.mount_state[k] = True
        for k in self.steam_state:
            self.steam_state[k] = True
        for k in self.commit_state:
            self.commit_state[k] = True
        self._rebuild_tune_list()

    def reset_options(self):
        for k in self.opts_state:
            self.opts_state[k] = False
        for k in self.mount_state:
            self.mount_state[k] = False
        for k in self.steam_state:
            self.steam_state[k] = False
        for k in self.commit_state:
            self.commit_state[k] = False
        self._rebuild_tune_list()

    def select_all_services(self):
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setText("[✓]")

    def clear_services_selection(self):
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setText("[ ]")
        self.table.clearSelection()

    def _on_cell_clicked(self, row, col):
        if col == 0:
            it = self.table.item(row, 0)
            it.setText("[ ]" if it.text() == "[✓]" else "[✓]")
        elif col == 5:
            name = self.table.item(row, 1).text()
            self._show_service_help(name)

    def _checked_service_names(self):
        names = []
        for row in range(self.table.rowCount()):
            it = self.table.item(row, 0)
            if it is not None and it.text() == "[✓]":
                names.append(self.table.item(row, 1).text())
        return names

    def _serv_detail(self):
        items = self.table.selectedItems()
        names = []
        for it in items:
            if it.column() == 1:
                names.append(it.text())
        parts = ["%s — %s" % (n, SERVICES_META.get(n, {}).get(self.lang, ""))
                 for n in names[:3]]
        self.serv_detail.setPlainText("\n".join(parts))

    # ─── apply / rollback ───────────────────────────────────────────────

    def apply_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        selected = [k for k, v in self.opts_state.items()
                    if v and k not in self.disabled_reasons]
        mount_sel = [mp for m in self.mount_items
                     if self.mount_state.get(m["mps"][0])
                     for mp in m["mps"]]
        steam_sel = [l for l in self.steam_items if self.steam_state.get(l)]
        commit_sel = [mp for mp, v in self.commit_state.items() if v]
        if (not selected and not mount_sel and not steam_sel
                and not commit_sel):
            QMessageBox.warning(self, APP_NAME, self.t("msg_noopt"))
            return
        params = {
            "corectrl_group": self.corectrl_group,
            "swap_value": self.swap_value,
            "update_schedule": self.schedule_value,
            "commit_value": self.commit_value,
            "thp_value": self.thp_value,
            "max_map_count_value": self.max_map_count_value,
            "tmpfs_size_value": self.tmpfs_size_value,
            "shutdown_timeout_value": self.shutdown_timeout_value,
            "pipewire_preset": self.pipewire_preset_key,
        }
        dry = self._dry_check.isChecked()
        if ("autoupdate" in selected and not dry
                and params["update_schedule"]
                not in ("Отключено", "Disabled")):
            QMessageBox.information(self, APP_NAME, self.t("autoupdate_warn"))
        if "shutdown_timeout" in selected and not dry:
            QMessageBox.information(self, APP_NAME,
                                    self.t("shutdown_timeout_warn"))
        needs_sudo = bool(mount_sel or commit_sel or steam_sel
                          or any(k != "pipewire" for k in selected))
        if not dry and needs_sudo and not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        self._ram_cache = None
        self.is_running = True
        self._on_running(True)
        self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        self._spawn_task(lambda: self._apply_work(selected, mount_sel,
                                                  steam_sel, commit_sel,
                                                  params, dry))

    def _apply_work(self, selected, mount_sel, steam_sel, commit_sel,
                    params, dry):
        ops = SystemOps(self.sudo, self.state, self.log, dry)
        ops.mount_items = self.mount_items
        ops.commit_targets = commit_sel
        total = (len(selected) + (1 if mount_sel else 0)
                 + (1 if steam_sel else 0) + (1 if commit_sel else 0))
        if total == 0:
            self.sig.running.emit(False)
            return
        done = 0
        ok_count = skip_count = fail_count = 0
        self.log("=" * 60, "highlight")
        self.log("APPLY START" if self.lang == "en" else "ЗАПУСК ТЮНИНГА",
                 "highlight")
        try:
            for k in selected:
                label = self.om(k)[0]
                self.log("→ %s" % label, "info")
                result = None
                try:
                    result = getattr(ops, "apply_%s" % k)(params)
                except Exception as e:
                    self.log("Error in %s: %s" % (k, e), "error")
                    result = False
                if result is False:
                    fail_count += 1
                elif result is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if mount_sel:
                self.log("→ %s" % self.t("mount_title"), "info")
                r = ops.apply_mount_opts(mount_sel)
                if r is False:
                    fail_count += 1
                elif r is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if commit_sel:
                self.log("→ %s" % self.t("commit_title"), "info")
                r = ops.apply_commit(params)
                if r is False:
                    fail_count += 1
                elif r is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if steam_sel:
                self.log("→ %s" % self.t("steam_title"), "info")
                r = ops.apply_steam_links(steam_sel)
                if r is False:
                    fail_count += 1
                elif r is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if not dry:
                ops.finalize_grub()
            self.sig.progress.emit(100)
            self.sig.statusbar.emit(self.t("done"))
            self.log("Done", "success")
            if fail_count > 0 and ok_count == 0:
                self.sig.toast.emit(self.t("done"), "err")
            else:
                self.sig.toast.emit(self.t("done"), "ok")
        except Exception as e:
            self.log("Critical error: %s" % e, "error")
            fail_count += 1
        finally:
            self._finish_run(ok_count, skip_count, fail_count)

    def rollback_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        selected = [k for k, v in self.opts_state.items()
                    if v and k not in self.disabled_reasons]
        mount_sel = [mp for m in self.mount_items
                     if self.mount_state.get(m["mps"][0])
                     for mp in m["mps"]]
        steam_sel = [l for l in self.steam_items if self.steam_state.get(l)]
        commit_sel = [mp for mp, v in self.commit_state.items() if v]
        if (not selected and not mount_sel and not steam_sel
                and not commit_sel):
            QMessageBox.warning(self, APP_NAME, self.t("msg_noopt"))
            return
        dry = self._dry_check.isChecked()
        needs_sudo = bool(mount_sel or commit_sel or steam_sel
                          or any(k != "pipewire" for k in selected))
        if not dry and needs_sudo and not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        self._ram_cache = None
        self.is_running = True
        self._on_running(True)
        self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        self._spawn_task(lambda: self._rollback_work(selected, mount_sel,
                                                     steam_sel, commit_sel,
                                                     dry))

    def _rollback_work(self, selected, mount_sel, steam_sel, commit_sel, dry):
        ops = SystemOps(self.sudo, self.state, self.log, dry)
        ops.mount_items = self.mount_items
        ops.commit_targets = commit_sel
        total = (len(selected) + (1 if mount_sel else 0)
                 + (1 if steam_sel else 0) + (1 if commit_sel else 0))
        if total == 0:
            self.sig.running.emit(False)
            return
        done = 0
        ok_count = skip_count = fail_count = 0
        self.log("=" * 60, "highlight")
        self.log("ROLLBACK START" if self.lang == "en" else "ЗАПУСК ОТКАТА",
                 "highlight")
        try:
            for k in selected:
                label = self.om(k)[0]
                self.log("→ %s" % label, "info")
                result = None
                try:
                    result = getattr(ops, "rollback_%s" % k)()
                except Exception as e:
                    self.log("Error in %s: %s" % (k, e), "error")
                    result = False
                if result is False:
                    fail_count += 1
                elif result is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if mount_sel:
                r = ops.rollback_mount_opts(mount_sel)
                if r is False:
                    fail_count += 1
                elif r is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if commit_sel:
                r = ops.rollback_commit({})
                if r is False:
                    fail_count += 1
                elif r is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if steam_sel:
                r = ops.rollback_steam_links(steam_sel)
                if r is False:
                    fail_count += 1
                elif r is None:
                    skip_count += 1
                else:
                    ok_count += 1
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if not dry:
                ops.finalize_grub()
            self.sig.progress.emit(100)
            self.sig.statusbar.emit(self.t("done"))
            self.log("Rollback done", "success")
            self.sig.toast.emit(self.t("done"), "ok")
        except Exception as e:
            self.log("Critical error: %s" % e, "error")
            fail_count += 1
        finally:
            self._finish_run(ok_count, skip_count, fail_count)

    def _finish_run(self, ok_count, skip_count, fail_count):
        self.sig.running.emit(False)
        self.sig.result_summary.emit(ok_count, skip_count, fail_count)
        try:
            self.state.detect()
        except Exception:
            pass
        self.sig.spawn.emit(self._applied_work)
        self.sig.spawn.emit(self._status_work)
        self.sig.spawn.emit(self._services_work)

    # ─── Службы: включить/отключить ─────────────────────────────────────

    def enable_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        names = self._checked_service_names()
        if not names:
            QMessageBox.information(self, APP_NAME, self.t("msg_sel"))
            return
        if not self._dry_check.isChecked() and not self.sudo.ensure():
            return
        self._spawn_task(lambda: self._enable_work(names))

    def _enable_work(self, names):
        ops = SystemOps(self.sudo, self.state, self.log,
                        self._dry_check.isChecked())
        for name in names:
            if ops.dry_run:
                ops.log("[DRY RUN] enable %s" % name, "warning")
                continue
            ok = ops.sudo_run(["systemctl", "unmask", name], ignore_error=True)
            ok2 = ops.sudo_run(["systemctl", "enable", "--now", name],
                               ignore_error=True)
            if ok or ok2:
                ops.log("✓ %s enabled" % name, "success")
            else:
                ops.log("Cannot enable %s" % name, "warning")
        self.sig.spawn.emit(self._services_work)
        self.sig.spawn.emit(self._status_work)

    def disable_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        names = self._checked_service_names()
        if not names:
            QMessageBox.information(self, APP_NAME, self.t("msg_sel"))
            return
        if not self._dry_check.isChecked() and not self.sudo.ensure():
            return
        self._spawn_task(lambda: self._disable_work(names))

    def _disable_work(self, names):
        ops = SystemOps(self.sudo, self.state, self.log,
                        self._dry_check.isChecked())
        for name in names:
            if ops.dry_run:
                ops.log("[DRY RUN] disable %s" % name, "warning")
                continue
            ok = ops.sudo_run(["systemctl", "disable", "--now", name],
                              ignore_error=True)
            if (name.startswith("avahi") or name.startswith("bluetooth")
                    or name.startswith("apport")):
                ok = ops.sudo_run(["systemctl", "mask", name],
                                  ignore_error=True) or ok
            if ok:
                ops.log("✓ %s disabled" % name, "success")
            else:
                ops.log("Cannot disable %s" % name, "warning")
        self.sig.spawn.emit(self._services_work)
        self.sig.spawn.emit(self._status_work)

    # ─── ZFS ────────────────────────────────────────────────────────────

    def _zfs_remove_packages(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        if self.state.zfs_used:
            QMessageBox.warning(self, APP_NAME,
                                "ZFS is in use, removal blocked."
                                if self.lang == "en"
                                else "ZFS используется, удаление заблокировано.")
            return
        if not self.state.zfs_installed:
            QMessageBox.information(self, APP_NAME,
                                    "ZFS packages not installed."
                                    if self.lang == "en"
                                    else "Пакеты ZFS не установлены.")
            return
        ans = QMessageBox.question(self, self.t("zfs_remove_title"),
                                   self.t("zfs_remove_body"),
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        if not self._dry_check.isChecked() and not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        self.is_running = True
        self._on_running(True)
        self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        self._spawn_task(self._zfs_remove_work)

    def _zfs_confirm(self):
        pass

    def _zfs_remove_work(self):
        ops = SystemOps(self.sudo, self.state, self.log,
                        self._dry_check.isChecked())
        try:
            ok = ops.apply_zfs_remove_packages()
            if ok:
                self.log("ZFS packages removed. Rolling back requires "
                         "'sudo apt install zfsutils-linux'.", "info")
                self.sig.toast.emit("ZFS removed", "ok")
        except Exception as e:
            self.log("Critical error: %s" % e, "error")
        finally:
            self.state.zfs_installed = zfs_packages_installed()
            self.state.zfs_used = zfs_in_use()
            self.sig.running.emit(False)
            self.sig.spawn.emit(self._applied_work)
            self.sig.spawn.emit(self._status_work)
            self.sig.spawn.emit(self._services_work)

    # ─── Вкладка «Приложения» ───────────────────────────────────────────

    def _apps_load_installed(self):
        try:
            from tweaker_packages import REMOVABLE_PACKAGES  # noqa
        except ImportError:
            self._installed_packages = set()
            self.sig.spawn.emit(self._apps_render)
            return
        self._installed_packages = installed_packages_set()
        self.sig.spawn.emit(self._apps_render)

    def _apps_refresh(self):
        self._installed_packages = None
        self._spawn_task(self._apps_load_installed)

    def _apps_clear(self):
        self.apps_checked.clear()
        self._apps_render()

    def _apps_toggle(self, pkg, checked):
        if checked:
            self.apps_checked.add(pkg)
        else:
            self.apps_checked.discard(pkg)
        self._apps_update_status()

    def _apps_render(self):
        if self._apps_inner_layout is None:
            return
        c = self.colors()
        self._clear_layout(self._apps_inner_layout)
        if not is_debian_based():
            lbl = QLabel(self.t("apps_unsupported"))
            lbl.setStyleSheet("color: %s;" % c["gray"])
            self._apps_inner_layout.addWidget(lbl)
            self._apps_inner_layout.addStretch(1)
            self._apps_update_status()
            return
        if not REMOVABLE_PACKAGES:
            lbl = QLabel(self.t("apps_no_list"))
            lbl.setStyleSheet("color: %s;" % c["gray"])
            self._apps_inner_layout.addWidget(lbl)
            self._apps_inner_layout.addStretch(1)
            self._apps_update_status()
            return
        if self._installed_packages is None:
            lbl = QLabel("…")
            lbl.setStyleSheet("color: %s;" % c["gray"])
            self._apps_inner_layout.addWidget(lbl)
            return
        query = (self._apps_filter_text or "").strip().lower()
        cats = {}
        for pkg, meta in REMOVABLE_PACKAGES.items():
            if pkg not in self._installed_packages:
                continue
            lang_meta = meta.get(self.lang) or meta.get("en")
            if not lang_meta:
                continue
            label, desc, cat, careful = lang_meta
            if (query and query not in pkg.lower()
                    and query not in label.lower()
                    and query not in desc.lower()):
                continue
            cats.setdefault(cat, []).append((pkg, label, desc, careful))
        if not cats:
            lbl = QLabel(self.t("apps_empty"))
            lbl.setStyleSheet("color: %s;" % c["gray"])
            self._apps_inner_layout.addWidget(lbl)
            self._apps_inner_layout.addStretch(1)
            self._apps_update_status()
            return
        order = APPS_CATEGORY_ORDER[self.lang]
        seq = [x for x in order if x in cats] + \
              [x for x in sorted(cats) if x not in order]
        for cat in seq:
            hdr = QLabel("─── %s ───" % cat)
            hdr.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;"
                              % c["yellow"])
            self._apps_inner_layout.addWidget(hdr)
            for pkg, label, desc, careful in sorted(cats[cat],
                                                     key=lambda x: x[1].lower()):
                row = QFrame()
                row.setObjectName("optrow")
                hl = QHBoxLayout(row)
                hl.setContentsMargins(8, 4, 8, 4)
                cb = QCheckBox("%-28s %s" % (pkg, desc))
                cb.setChecked(pkg in self.apps_checked)
                cb.toggled.connect(lambda v, p=pkg: self._apps_toggle(p, v))
                hl.addWidget(cb)
                if careful:
                    mark = QLabel(self.t("apps_careful_mark"))
                    mark.setStyleSheet("color: %s; font-weight: bold;"
                                       % c["orange"])
                    hl.addWidget(mark)
                hl.addStretch(1)
                self._apps_inner_layout.addWidget(row)
        self._apps_inner_layout.addStretch(1)
        self._apps_update_status()

    def _apps_update_status(self):
        if self._apps_status_lbl is None:
            return
        if not self.apps_checked:
            self._apps_status_lbl.setText(self.t("apps_selected_none"))
            return
        count = len(self.apps_checked)
        size = estimate_packages_size(list(self.apps_checked))
        self._apps_status_lbl.setText(
            self.t("apps_selected") % (count, size))

    def _apps_remove_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        pkgs = sorted(self.apps_checked)
        if not pkgs:
            QMessageBox.information(self, APP_NAME, self.t("msg_noopt"))
            return
        if not self._dry_check.isChecked() and not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        self._spawn_task(lambda: self._apps_dry_run_work(pkgs))

    def _apps_dry_run_work(self, pkgs):
        explicit, deps, system_hits, ok = apt_dry_run_purge(pkgs)
        if not ok:
            self.log("apt simulation failed — cannot confirm removal list",
                     "error")
        size = estimate_packages_size(explicit + deps)
        lines = [self.t("apps_confirm_will_remove"),
                 "  " + ", ".join(explicit)]
        if deps:
            lines += ["", self.t("apps_confirm_deps"),
                      "  " + ", ".join(deps)]
        lines += ["", "%s %s" % (self.t("apps_confirm_size"), size)]
        if system_hits:
            lines += ["", self.t("apps_confirm_system_warn"),
                      "  " + ", ".join(system_hits),
                      self.t("apps_confirm_system_hint")]
        lines += ["", self.t("apps_confirm_no_rollback")]
        body = "\n".join(lines)
        QTimer.singleShot(0, lambda: self._apps_show_confirm(body, pkgs))

    def _apps_show_confirm(self, body, pkgs):
        ans = QMessageBox.question(self, self.t("apps_confirm_title"), body,
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        self.is_running = True
        self._on_running(True)
        self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        self._spawn_task(lambda: self._apps_remove_work(pkgs))

    def _apps_remove_work(self, pkgs):
        ops = SystemOps(self.sudo, self.state, self.log,
                        self._dry_check.isChecked())
        try:
            ok, freed = ops.apps_purge(pkgs)
            if ok:
                if self._dry_check.isChecked():
                    self.log(self.t("apps_done_dry") % len(pkgs), "success")
                    self.sig.toast.emit(self.t("apps_done_dry") % len(pkgs),
                                        "ok")
                else:
                    self.log(self.t("apps_done") % (len(pkgs), freed),
                             "success")
                    self.sig.toast.emit(self.t("apps_done")
                                        % (len(pkgs), freed), "ok")
                    self.apps_checked.clear()
            else:
                self.log(self.t("apps_failed"), "error")
        except Exception as e:
            self.log("Critical error: %s" % e, "error")
        finally:
            self.sig.running.emit(False)
            if not self._dry_check.isChecked():
                self._installed_packages = installed_packages_set()
            self.sig.spawn.emit(self._apps_render)

    # ─── Детекты ────────────────────────────────────────────────────────

    def _applied_work(self):
        ops = SystemOps(self.sudo, self.state, lambda m, t="normal": None, True)
        ops.mount_items = self.mount_items
        ops.commit_targets = [mp for mp in self.commit_state]
        try:
            self.sig.applied.emit(self._detect_applied(ops))
            self.sig.mount_applied.emit(self._detect_mount())
            self.sig.steam_applied.emit(self._detect_steam())
            self.sig.schedule.emit(self._schedule_text())
            self.sig.commit_applied.emit(self._detect_commit_per_mp(ops))
        except Exception:
            traceback.print_exc()

    def _schedule_text(self):
        path = "/etc/systemd/system/biweekly-upgrade.timer"
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return self.t("sched_none")
        m = re.search(r"^\s*OnCalendar\s*=\s*(.+)$", content, re.M)
        if not m:
            return self.t("sched_none")
        cal = m.group(1).strip()
        names = {"*-*-* 18:30:00": ("Ежедневно", "Daily"),
                 "Sat 18:30:00": ("Еженедельно (суббота)",
                                  "Weekly (Saturday)"),
                 "*-*-1,15 18:30:00": ("2 раза в месяц (1 и 15)",
                                       "Twice a month (1 & 15)"),
                 "*-*-1 18:30:00": ("Ежемесячно (1 число)",
                                    "Monthly (1st)")}
        pair = names.get(cal)
        if pair:
            label = pair[0 if self.lang == "ru" else 1]
            m2 = re.search(r"(\d{2}:\d{2}(?::\d{2})?)", cal)
            if m2:
                t = m2.group(1)
                if len(t) == 8:
                    t = t[:5]
                label = "%s, %s" % (label, t)
            return label
        return cal

    def _check_corectrl_status(self):
        if self.is_running:
            return
        if not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        try:
            ops = SystemOps(self.sudo, self.state,
                            lambda m, t="normal": None, True)
            found = self._corectrl_found(ops)
            self.applied["corectrl"] = found
            self._update_badges()
            if found:
                self.log("CoreCtrl rule found", "success")
            else:
                self.log("CoreCtrl rule NOT found", "warning")
        except Exception as e:
            self.log("Check corectrl failed: %s" % e, "error")

    def _corectrl_found(self, ops):
        direct_paths = (
            "/etc/polkit-1/rules.d/90-corectrl.rules",
            "/usr/share/polkit-1/rules.d/90-corectrl.rules",
            "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla",
        )
        direct_decisive = True
        for p in direct_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    if "org.corectrl" in f.read():
                        return True
            except FileNotFoundError:
                continue
            except PermissionError:
                direct_decisive = False
            except Exception:
                direct_decisive = False
        sudo_decisive = True
        for p in direct_paths:
            try:
                r = subprocess.run(["sudo", "-n", "cat", p],
                                   capture_output=True, text=True,
                                   timeout=3)
                if r.returncode == 0:
                    if "org.corectrl" in r.stdout:
                        return True
                elif "No such file" in (r.stderr or ""):
                    continue
                else:
                    sudo_decisive = False
            except Exception:
                sudo_decisive = False
        if direct_decisive or sudo_decisive:
            return False
        return None

    def _max_map_count_applied(self, mmc_content):
        return bool(re.search(r"^vm\.max_map_count=\d+\s*$",
                              mmc_content, re.M))

    def _vrr_applied(self, ops):
        content = ops.read_file(
            "/etc/X11/xorg.conf.d/20-amdgpu.conf") or ""
        return bool(re.search(r'Option\s+"VariableRefresh"\s+"true"',
                              content, re.I))

    def _zram_applied(self, ops):
        if not zram_generator_present():
            return False
        content = ops.read_file("/etc/systemd/zram-generator.conf") or ""
        return bool(re.search(r"^\s*\[zram", content, re.M))

    def _grub_has_token(self, grub, token):
        for line in grub.splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX(?:_DEFAULT)?=(.*)$", line)
            if not m:
                continue
            raw = m.group(1).strip().strip('"').strip("'")
            if token in raw.split():
                return True
        return False

    def _grub_has_prefix(self, grub, prefix):
        for line in grub.splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX(?:_DEFAULT)?=(.*)$", line)
            if not m:
                continue
            raw = m.group(1).strip().strip('"').strip("'")
            if any(t.startswith(prefix) for t in raw.split()):
                return True
        return False

    def _detect_applied(self, ops):
        grub = ops.read_file("/etc/default/grub") or ""
        env = ops.read_file("/etc/environment") or ""
        j = ops.read_file("/etc/systemd/journald.conf") or ""
        swp = ops.read_file("/etc/sysctl.d/99-gaming-swap.conf") or ""
        sysc = ops.read_file("/etc/sysctl.d/99-gaming-sysctl.conf") or ""
        bashrc = ops.read_file(os.path.join(self.state.user_home,
                                            ".bashrc")) or ""
        mint = ops.read_file(
            "/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf") or ""
        itco = ops.read_file("/etc/modprobe.d/nmi-watchdog.conf") or ""
        mmc = ops.read_file("/etc/sysctl.d/99-gaming-mmap.conf") or ""

        def sv(p):
            try:
                r = subprocess.run(["sysctl", "-n", p],
                                   capture_output=True, text=True,
                                   timeout=3, env=self._host_env())
                return r.stdout.strip() if r.returncode == 0 else ""
            except Exception:
                return ""

        pw = os.path.join(self.state.user_home, ".config", "pipewire",
                          "pipewire.conf.d", "10-sound.conf")
        j_ok = (re.search(r"^\s*Storage\s*=\s*volatile\s*$", j, re.M)
                and re.search(r"^\s*RuntimeMaxUse\s*=\s*50M\s*$", j, re.M))
        thp_ok = self._grub_has_prefix(grub, "transparent_hugepage=")
        pipewire_preset = self._pipewire_preset_current()
        return {
            "journald": bool(j_ok),
            "audit": self._grub_has_token(grub, "audit=0"),
            "raid": self._grub_has_token(grub, "raid=noautodetect"),
            "nmi_watchdog": self._grub_has_token(grub, "nmi_watchdog=0"),
            "itco_wdt": "blacklist iTCO_wdt" in itco,
            "zfs_services": (zfs_units_masked()
                             if self.state.zfs_installed else False),
            "shutdown_timeout": self._shutdown_timeout_applied(),
            "corectrl": self._corectrl_found(ops),
            "ppfeaturemask": (self._grub_has_token(
                grub, "amdgpu.ppfeaturemask=0xffffffff")
                or "amdgpu.ppfeaturemask" in grub),
            "nvidia_modeset": self._grub_has_token(
                grub, "nvidia-drm.modeset=1"),
            "vrr": self._vrr_applied(ops),
            "radv": "RADV_PERFTEST=sam" in env,
            "mesa": "MESA_SHADER_CACHE_MAX_SIZE=4G" in env,
            "pipewire": bool(pipewire_preset),
            "bbr": sv("net.ipv4.tcp_congestion_control") == "bbr",
            "swap": bool(re.search(r"^\s*vm\.swappiness\s*=\s*\d+\s*$",
                                   swp, re.M)),
            "zram": self._zram_applied(ops),
            "zswap": (self._grub_has_token(grub, "zswap.enabled=1")
                      and self.state.has_swap),
            "thp": thp_ok,
            "sysctl_cache": bool(
                re.search(r"^vm\.vfs_cache_pressure=50$", sysc, re.M))
                or sv("vm.vfs_cache_pressure") == "50",
            "sysctl_numa": bool(
                re.search(r"^kernel\.numa_balancing=0$", sysc, re.M))
                or sv("kernel.numa_balancing") == "0",
            "reisub": (sv("kernel.sysrq") == "244"
                       or ops.path_exists("/etc/sysctl.d/99-sysrq.conf")),
            "ntsync": (self.state.ntsync
                       or ops.path_exists("/etc/modules-load.d/ntsync.conf")),
            "max_map_count": self._max_map_count_applied(mmc),
            "ntfs3": bool(re.search(r"^\s*#\s*blacklist\s+ntfs3\s*$",
                                    mint, re.M)),
            "commit": ops._commit_applied(),
            "tmpfs_tmp": tmpfs_tmp_mounted() or fstab_has_tmp_tmpfs(),
            "aliases": "system-tuneup" in bashrc,
            "autoupdate": ops.service_enabled(
                "biweekly-upgrade.timer") == "enabled",
        }

    def _detect_mount(self):
        try:
            with open("/etc/fstab", "r", encoding="utf-8",
                      errors="replace") as f:
                content = f.read()
        except Exception:
            content = ""
        res = {}
        for m in self.mount_items:
            oks = []
            for mp in m["mps"]:
                ok = False
                for line in lines_in(content):
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    f2 = s.split()
                    if len(f2) >= 4 and f2[1] == mp:
                        opts = f2[3].split(",")
                        ok = "noatime" in opts
                        break
                oks.append(ok)
            res[m["mps"][0]] = all(oks)
        return res

    def _detect_steam(self):
        return {lib: os.path.islink(os.path.join(lib, "compatdata"))
                for lib in self.steam_items}

    def _detect_commit_per_mp(self, ops):
        res = {}
        for mp in self.commit_state:
            val = ops._commit_value_for(mp)
            res[mp] = self._commit_is_effective(val)
        return res

    def _commit_is_effective(self, value):
        if not value:
            return False
        m = re.match(r"commit=(\d+)$", value)
        if not m:
            return False
        v = m.group(1)
        return v not in ("0", "5")

    def _commit_value_for_ui(self, mp):
        ops = SystemOps(self.sudo, self.state,
                        lambda m, t="normal": None, True)
        return ops._commit_value_for(mp)

    def _pipewire_preset_current(self):
        path = os.path.join(self.state.user_home, ".config", "pipewire",
                            "pipewire.conf.d", "10-sound.conf")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return None
        m_min = re.search(r"min-quantum\s*=\s*(\d+)", content)
        m_q = re.search(r"default\.clock\.quantum\s*=\s*(\d+)", content)
        m_max = re.search(r"max-quantum\s*=\s*(\d+)", content)
        if not (m_min and m_q and m_max):
            return "manual"
        cur = (int(m_min.group(1)), int(m_q.group(1)), int(m_max.group(1)))
        for key, p in PIPEWIRE_PRESETS.items():
            if (p["min"], p["quantum"], p["max"]) == cur:
                return key
        return "manual"

    def _shutdown_timeout_applied(self):
        content = self._read_text_file("/etc/systemd/system.conf")
        m = re.search(r"^\s*DefaultTimeoutStopSec\s*=\s*(\S+)", content, re.M)
        if not m:
            return False
        val = m.group(1).strip()
        if val == "90s":
            return False
        return val in SHUTDOWN_TIMEOUT_VALUES

    # ─── Вспомогательные чтения ─────────────────────────────────────────

    def _read_text_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    def _read_sysctl_int(self, path, default=""):
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except Exception:
            return default

    def _swap_current(self):
        return self._read_sysctl_int("/proc/sys/vm/swappiness", "?")

    def _numa_current(self):
        v = self._read_sysctl_int("/proc/sys/kernel/numa_balancing", "")
        if v == "1":
            return "включено" if self.lang == "ru" else "enabled"
        if v == "0":
            return "отключено" if self.lang == "ru" else "disabled"
        return v or "?"

    def _bbr_current(self):
        return self._read_sysctl_int(
            "/proc/sys/net/ipv4/tcp_congestion_control", "?")

    def _journald_current(self):
        content = self._read_text_file("/etc/systemd/journald.conf")
        m = re.search(r"^\s*Storage\s*=\s*(\w+)\s*$", content, re.M)
        if m:
            val = m.group(1).lower()
            if val == "volatile":
                return self.t("journald_volatile")
            if val == "persistent":
                return self.t("journald_persistent")
            if val == "none":
                return self.t("journald_none")
        if os.path.isdir("/var/log/journal"):
            return self.t("journald_persistent")
        if os.path.isdir("/run/log/journal"):
            return self.t("journald_volatile")
        return self.t("journald_auto")

    def _zswap_current(self):
        try:
            with open("/sys/module/zswap/parameters/enabled", "r") as f:
                en = f.read().strip().lower()
        except Exception:
            return "?"
        if en not in ("y", "1", "yes", "true"):
            return "отключён" if self.lang == "ru" else "off"
        comp = "?"
        try:
            with open("/sys/module/zswap/parameters/compressor", "r") as f:
                comp = f.read().strip()
        except Exception:
            pass
        return (("включён (%s)" % comp) if self.lang == "ru"
                else ("on (%s)" % comp))

    def _zram_current(self):
        try:
            with open("/proc/swaps", "r", encoding="utf-8",
                      errors="replace") as f:
                for line in f:
                    if "zram" in line:
                        return "активен" if self.lang == "ru" else "active"
        except Exception:
            pass
        return "не активен" if self.lang == "ru" else "inactive"

    def _ntfs3_current(self):
        path = "/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"
        if not os.path.exists(path):
            return "?"
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return "?"
        if re.search(r"^\s*blacklist\s+ntfs3\s*$", content, re.M):
            return "заблокирован" if self.lang == "ru" else "blocked"
        return "разблокирован" if self.lang == "ru" else "unblocked"

    def _ntsync_current(self):
        return (("доступен" if self.lang == "ru" else "available")
                if getattr(self.state, "ntsync", False)
                else ("недоступен" if self.lang == "ru" else "unavailable"))

    def _shutdown_timeout_current(self):
        try:
            res = subprocess.run(
                ["systemctl", "show", "-p", "DefaultTimeoutStopSec", "--value"],
                capture_output=True, text=True, timeout=5,
                env=self._host_env())
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        content = self._read_text_file("/etc/systemd/system.conf")
        m = re.search(r"^\s*DefaultTimeoutStopSec\s*=\s*(\S+)", content, re.M)
        if m:
            return m.group(1)
        return "?"

    def _thp_current(self):
        try:
            with open("/sys/kernel/mm/transparent_hugepage/enabled", "r",
                      encoding="utf-8", errors="replace") as f:
                m = re.search(r"\[(\w+)\]", f.read())
                return m.group(1) if m else ""
        except Exception:
            return ""

    def _disk_info(self, path):
        try:
            st = os.statvfs(path)
            total = st.f_blocks * st.f_frsize / 1024.0 ** 3
            free = st.f_bavail * st.f_frsize / 1024.0 ** 3
            return total, free
        except Exception:
            return None

    def _swap_size_gb(self):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8",
                      errors="replace") as f:
                for line in f:
                    if line.startswith("SwapTotal:"):
                        return int(line.split()[1]) / 1024.0 / 1024.0
        except Exception:
            pass
        return None

    # ─── Обновление бейджей ─────────────────────────────────────────────

    def _update_badges(self):
        c = self.colors()
        for k, b in self.badges.items():
            if b is None:
                continue
            if k == "pipewire":
                preset = self._pipewire_preset_current()
                if preset is None:
                    b.set_state(self.t("applied_no"), c["gray"], c["gray_bg"])
                elif preset == "manual":
                    b.set_state(self.t("applied_manual"), c["yellow"],
                                c["gray_bg"])
                else:
                    b.set_state(self.t("applied_yes"), c["green"],
                                c["green_bg"])
                continue
            if k == "corectrl":
                val = self.applied.get("corectrl", None)
                if val is True:
                    b.set_state(self.t("applied_yes"), c["green"],
                                c["green_bg"])
                elif val is False:
                    b.set_state(self.t("applied_no"), c["gray"],
                                c["gray_bg"])
                else:
                    b.set_state(self.t("applied_unknown"), c["yellow"],
                                c["gray_bg"])
                continue
            ok = self.applied.get(k, False)
            if ok is True:
                b.set_state(self.t("applied_yes"), c["green"], c["green_bg"])
            elif ok is False:
                b.set_state(self.t("applied_no"), c["gray"], c["gray_bg"])
            else:
                b.set_state(self.t("applied_unknown"), c["yellow"],
                            c["gray_bg"])
        for k, b in self.mount_badges.items():
            if b is None:
                continue
            ok = self.mount_applied.get(k, False)
            if ok:
                b.set_state(self.t("applied_yes"), c["green"], c["green_bg"])
            else:
                b.set_state(self.t("applied_no"), c["gray"], c["gray_bg"])
        for k, b in self.steam_badges.items():
            if b is None:
                continue
            ok = self.steam_applied.get(k, False)
            if ok:
                b.set_state(self.t("applied_yes"), c["green"], c["green_bg"])
            else:
                b.set_state(self.t("applied_no"), c["gray"], c["gray_bg"])
        for k, b in self.commit_badges.items():
            if b is None:
                continue
            ok = self.commit_applied_per_mp.get(k, False)
            if ok:
                b.set_state(self.t("applied_yes"), c["green"], c["green_bg"])
            else:
                b.set_state(self.t("applied_no"), c["gray"], c["gray_bg"])
        if self.thp_lbl is not None:
            fmt = self.t("thp_cur")
            cur = self._thp_current() or "?"
            self.thp_lbl.setText(fmt % cur if "%" in fmt else fmt)

    # ─── Службы: рендер ─────────────────────────────────────────────────

    def _services_work(self):
        ops = SystemOps(self.sudo, self.state, lambda m, t="normal": None,
                        self._dry_check.isChecked())
        rows = []
        for n in SERVICES_ORDER:
            if not ops.unit_exists(n):
                continue
            desc = SERVICES_META[n][self.lang]
            en = ops.service_enabled(n)
            ac = ops.service_active(n)
            if en == "masked":
                st, tag = self.t("svc_masked"), "err"
            elif en == "disabled":
                st, tag = self.t("svc_off"), "muted"
            elif ac == "active":
                st, tag = self.t("svc_on"), "ok"
            else:
                st, tag = self.t("svc_onoff"), "warn"
            run = (self.t("run_yes") if ac == "active"
                   else self.t("run_no"))
            rows.append((n, st, run, desc, "?", tag))
        self.sig.services_rows.emit(rows)

    def _on_services_rows(self, rows):
        c = self.colors()
        self._svc_rows = rows
        self._render_services_rows()

    def _sort_key_for(self, row, col):
        name, st, run, desc, q, tag = row
        if col == "name":
            return name.lower()
        if col == "state":
            order = {"err": 0, "muted": 1, "ok": 2, "warn": 3}
            return order.get(tag, 9)
        if col == "run":
            return 0 if run in ("running", "работает") else 1
        if col == "desc":
            return desc.lower()
        return name.lower()

    def _render_services_rows(self):
        c = self.colors()
        rows = list(getattr(self, "_svc_rows", []))
        if self._svc_sort_col:
            rows.sort(key=lambda r: self._sort_key_for(r, self._svc_sort_col),
                      reverse=self._svc_sort_reverse)
        self.table.setRowCount(0)
        for n, st, run, desc, q, tag in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = ["[ ]", n, st, run, desc, q]
            for ci, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if ci == 0:
                    it.setTextAlignment(Qt.AlignCenter)
                if ci == 5:
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setForeground(QColor(c["blue"]))
                elif tag == "err":
                    it.setForeground(QColor(c["red"]))
                elif tag == "warn":
                    it.setForeground(QColor(c["yellow"]))
                elif tag == "ok":
                    it.setForeground(QColor(c["green"]))
                elif tag == "muted":
                    it.setForeground(QColor(c["gray"]))
                self.table.setItem(row, ci, it)

    # ─── Статус ─────────────────────────────────────────────────────────

    def _status_work(self):
        try:
            self._status_inner()
        except Exception:
            traceback.print_exc()

    def _status_inner(self):
        ops = SystemOps(self.sudo, self.state, lambda m, t="normal": None, True)
        ops.mount_items = self.mount_items
        ops.commit_targets = list(self.commit_state.keys())
        A = self._detect_applied(ops)
        self.sig.applied.emit(A)
        c = self.colors()

        def sv(p):
            try:
                r = subprocess.run(["sysctl", "-n", p], capture_output=True,
                                   text=True, timeout=3, env=self._host_env())
                return r.stdout.strip() if r.returncode == 0 else "n/a"
            except Exception:
                return "n/a"

        def esc(s):
            return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;"))

        def table(title, headers, rows_html):
            bc = c["border"]
            h = ("<table border='1' cellspacing='0' cellpadding='4' "
                 "width='100%' style='border-collapse:collapse; "
                 "border:1px solid %s;'>" % bc)
            h += ("<tr><th colspan='%d' style='background:%s; color:%s; "
                  "text-align:left;'>%s</th></tr>"
                  % (len(headers), c["tab"], c["fg"], esc(title)))
            h += "<tr>" + "".join(
                "<td style='background:%s; color:%s; border:1px solid %s;'>"
                "<b>%s</b></td>" % (c["panel"], c["gray"], bc, esc(x))
                for x in headers) + "</tr>"
            h += "".join(rows_html)
            h += "</table><br>"
            return h

        P = []
        name = ""
        try:
            with open("/etc/os-release", "r", encoding="utf-8",
                      errors="replace") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        name = line.split("=", 1)[1].strip().strip('"')
                        break
        except Exception:
            pass
        bits = 64 if sys.maxsize > 2 ** 32 else 32
        gpu = self.state.gpu
        if self.state.gpu_model:
            gpu += " " + self.state.gpu_model
        drv, drv_ver = self._gpu_driver()
        mesa = self._mesa_version() if drv != "nvidia" else ""
        drv_s = ""
        if drv or mesa:
            pp = []
            if drv:
                pp.append(drv + ((" " + drv_ver) if drv_ver else ""))
            if mesa:
                pp.append("Mesa %s" % mesa)
            drv_s = ", ".join(pp)
        ram = ram_total_gb()
        ram_s = ""
        if ram is not None:
            extra = self._ram_details()
            ram_s = "%.1f %s" % (ram, self.t("gb"))
            if extra:
                ram_s += ", %s" % extra
        if self.state.has_swap:
            tn = {"file": self.t("swap_file"),
                  "partition": self.t("swap_part"), "zram": "zram"}
            sw_s = tn.get(self.state.swap_type, self.state.swap_type)
            sz = self._swap_size_gb()
            if sz:
                sw_s += ", %.1f %s" % (sz, self.t("gb"))
        else:
            sw_s = self.t("no_swap")
        sw_px = self.screen().size().width() if self.screen() else 0
        sh_px = self.screen().size().height() if self.screen() else 0
        hw = [(self.t("os_lbl"), "%s (%d-bit)" % (name or "Linux", bits)),
              (self.t("cpu_lbl"), cpu_model()),
              (self.t("gpu_lbl"), gpu),
              (self.t("driver_lbl"), drv_s or "n/a"),
              (self.t("screen_lbl"), "%dx%d" % (sw_px, sh_px)),
              (self.t("ram_lbl"), ram_s),
              (self.t("swap_lbl"), sw_s),
              (self.t("kernel_lbl"), os.uname().release),
              (self.t("de_lbl"), desktop_name()),
              (self.t("user_lbl"), self.state.user_name),
              (self.t("home_lbl"), self.state.user_home)]
        hw_rows = ["<tr><td style='color:%s;'><b>%s</b></td>"
                   "<td style='color:%s;'>%s</td></tr>"
                   % (c["gray"], esc(k), c["fg"], esc(v)) for k, v in hw]
        P.append(table(self.t("st_hw"), ["", ""], hw_rows))

        seen = {}
        for it in parse_mounts():
            if it["mp"] == "/boot/efi" or (it["fstype"] == "vfat"
                                           and it["mp"].startswith("/boot")):
                continue
            seen.setdefault(it["dev"], {"mps": [], "fstype": it["fstype"]})
            seen[it["dev"]]["mps"].append(it["mp"])
        part_rows = []
        for dev, info in seen.items():
            d = self._disk_info(info["mps"][0])
            if not d:
                continue
            total, free = d
            part_rows.append(
                "<tr><td style='color:%s;'><b>%s</b> (%s)</td>"
                "<td style='color:%s;'>%s</td>"
                "<td style='color:%s;'>%.1f %s</td>"
                "<td style='color:%s;'>%.1f %s</td></tr>"
                % (c["fg"], esc(", ".join(info["mps"])),
                   esc(os.path.basename(dev)), c["gray"], esc(info["fstype"]),
                   c["fg"], total, self.t("gb"),
                   c["fg"], free, self.t("gb")))
        P.append(table(self.t("st_parts"),
                       [self.t("part_mount"), self.t("part_fs"),
                        self.t("part_total"), self.t("part_free")], part_rows))

        tw_rows = []
        for k in OPTIONS_META:
            label, _d, _c, short = self.om(k)
            ok = A.get(k, False)
            cc = c["green"] if ok else c["red"]
            tw_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'>%s</td></tr>"
                % (c["fg"], esc(label), cc,
                   self.t("yes") if ok else self.t("no"),
                   c["gray"], esc(short)))
        for mp in self.commit_state:
            val = self._commit_value_for_ui(mp) or self.t("commit_not_set")
            ok = self._commit_is_effective(
                val if val != self.t("commit_not_set") else "")
            cc = c["green"] if ok else c["red"]
            tw_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'>%s %s</td></tr>"
                % (c["fg"], esc(self.t("commit_title")), cc,
                   self.t("yes") if ok else self.t("no"),
                   c["gray"], esc(mp), esc(val)))
        for m in self.mount_items:
            ok = self.mount_applied.get(m["mps"][0], False)
            cc = c["green"] if ok else c["red"]
            tw_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'>%s</td></tr>"
                % (c["fg"], esc(self.t("mount_short")), cc,
                   self.t("yes") if ok else self.t("no"),
                   c["gray"], esc(", ".join(m["mps"]))))
        for lib in self.steam_items:
            ok = self.steam_applied.get(lib, False)
            cc = c["green"] if ok else c["red"]
            tw_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'>%s</td></tr>"
                % (c["fg"], esc(self.t("steam_short")), cc,
                   self.t("yes") if ok else self.t("no"),
                   c["gray"], esc(lib)))
        P.append(table(self.t("st_tweaks"),
                       [self.t("tw_name"), self.t("yes"), ""], tw_rows))

        sv_rows = []
        for n in SERVICES_ORDER:
            if not ops.unit_exists(n):
                continue
            en = ops.service_enabled(n)
            ac = ops.service_active(n)
            if en == "masked":
                cc, w = c["red"], self.t("svc_masked")
            elif en == "disabled":
                cc, w = c["gray"], self.t("svc_off")
            elif ac == "active":
                cc, w = c["green"], self.t("svc_on")
            else:
                cc, w = c["yellow"], self.t("svc_onoff")
            sv_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'>%s</td></tr>"
                % (c["fg"], esc(n), cc, esc(w), c["gray"],
                   esc(SERVICES_META[n][self.lang])))
        P.append(table(self.t("st_services"),
                       [self.t("svc_name"), self.t("svc_state"),
                        self.t("svc_desc")], sv_rows))

        vals = {p: sv(p) for p in ("vm.swappiness", "vm.vfs_cache_pressure",
                                   "kernel.numa_balancing",
                                   "net.ipv4.tcp_congestion_control")}
        kn_rows = []
        kern = [("vm.swappiness", self.t("kern_sw"), A.get("swap", False)),
                ("vm.vfs_cache_pressure", self.t("kern_vfs"),
                 A.get("sysctl_cache", False)),
                ("kernel.numa_balancing", self.t("kern_numa"),
                 A.get("sysctl_numa", False)),
                ("net.ipv4.tcp_congestion_control", self.t("kern_bbr"),
                 A.get("bbr", False))]
        for p, dsc, ok in kern:
            cc = c["green"] if ok else c["red"]
            kn_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'>%s</td>"
                "<td style='color:%s;'><b>%s</b></td></tr>"
                % (c["fg"], esc(p), c["fg"], esc(vals[p]), c["gray"],
                   esc(dsc), cc, self.t("yes") if ok else self.t("no")))
        raw = self._thp_current() or "n/a"
        thp_ok = A.get("thp", False)
        kn_rows.append(
            "<tr><td style='color:%s;'><b>%s</b></td>"
            "<td style='color:%s;'><b>%s</b></td>"
            "<td style='color:%s;'>%s</td>"
            "<td style='color:%s;'><b>%s</b></td></tr>"
            % (c["fg"], "transparent_hugepage", c["fg"], esc(raw),
               c["gray"], esc(self.t("kern_thp")),
               c["green"] if thp_ok else c["red"],
               self.t("yes") if thp_ok else self.t("no")))
        timer = ops.service_enabled("biweekly-upgrade.timer")
        tcc = c["green"] if timer == "enabled" else c["gray"]
        kn_rows.append(
            "<tr><td style='color:%s;'><b>%s</b></td>"
            "<td style='color:%s;'><b>%s</b></td>"
            "<td colspan='2'></td></tr>"
            % (c["fg"], esc(self.t("st_timer")), tcc,
               esc(self._fmt_state(timer))))
        P.append(table(self.t("st_kernel"),
                       [self.t("kn_hdr_param"), self.t("kn_hdr_val"),
                        self.t("kn_hdr_desc"), self.t("kn_hdr_status")],
                       kn_rows))
        self.sig.status_html.emit("".join(P))

    def _on_status_html(self, html):
        self.stat_view.setHtml(html)

    def _fmt_state(self, value):
        mapping = {
            "enabled": self.t("st_enabled"),
            "disabled": self.t("st_disabled"),
            "masked": self.t("st_masked"),
            "not-found": self.t("st_notfound"),
            "active": self.t("run_yes"),
            "inactive": self.t("run_no"),
        }
        return mapping.get(value, value)

    def _gpu_driver(self):
        name = ""
        try:
            res = subprocess.run(["lspci", "-k"], capture_output=True,
                                 text=True, timeout=5, env=self._host_env())
            lines = res.stdout.splitlines()
            for i, ln in enumerate(lines):
                if ("VGA compatible controller" in ln
                        or "3D controller" in ln):
                    for j in range(i + 1, min(i + 4, len(lines))):
                        m = re.search(r"Kernel driver in use:\s*(\S+)",
                                      lines[j])
                        if m:
                            name = m.group(1)
                            break
                    break
        except Exception:
            pass
        ver = ""
        if name == "nvidia":
            try:
                res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=driver_version",
                     "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=5,
                    env=self._host_env())
                if res.returncode == 0 and res.stdout.strip():
                    ver = res.stdout.strip().splitlines()[0]
            except Exception:
                pass
        if not ver and name:
            try:
                res = subprocess.run(["modinfo", "-F", "version", name],
                                     capture_output=True, text=True,
                                     timeout=5, env=self._host_env())
                ver = res.stdout.strip()
            except Exception:
                pass
        return name, ver

    def _mesa_version(self):
        try:
            res = subprocess.run(["glxinfo"], capture_output=True, text=True,
                                 timeout=5, env=self._host_env())
            if res.returncode == 0:
                m = re.search(r"Mesa\s+([0-9][0-9a-zA-Z.\-+]*)", res.stdout)
                if m:
                    return m.group(1)
        except Exception:
            pass
        for pkg in ("libglx-mesa0", "libgl1-mesa-dri", "libgl1-mesa-glx"):
            try:
                res = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Version}", pkg],
                    capture_output=True, text=True, timeout=5,
                    env=self._host_env())
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                continue
        return ""

    def _ram_details(self):
        if self._ram_cache is not None:
            return self._ram_cache
        try:
            res = subprocess.run(["sudo", "-n", "dmidecode", "-t", "17"],
                                 capture_output=True, text=True,
                                 timeout=5, env=self._host_env())
            if res.returncode != 0:
                self._ram_cache = ""
                return ""
            typ, speed = "", ""
            for ln in res.stdout.splitlines():
                s = ln.strip()
                if not typ and s.startswith("Type:"):
                    v = s.split(":", 1)[1].strip()
                    if v and v != "Unknown":
                        typ = v
                if not speed and s.startswith("Configured Memory Speed:"):
                    v = s.split(":", 1)[1].strip()
                    if v and v != "Unknown":
                        speed = v.replace("MT/s", "MHz").strip()
                if typ and speed:
                    break
            self._ram_cache = ", ".join([x for x in (typ, speed) if x])
            return self._ram_cache
        except Exception:
            self._ram_cache = ""
            return ""

    # ─── Темы / язык ────────────────────────────────────────────────────

    def toggle_theme(self):
        if self.is_running:
            return
        self.theme = "dark" if self.theme == "light" else "light"
        self._apply_theme()
        if self._theme_btn is not None:
            self._theme_btn.setText(
                self.t("theme_dark") if self.theme == "light"
                else self.t("theme_light"))
        self._update_badges()
        QTimer.singleShot(30, self._restyle_all)

    def _apply_theme(self):
        c = self.colors()
        qss = self._qss_template()
        for k, v in c.items():
            qss = qss.replace("{" + k + "}", v)
        self.setStyleSheet(qss)

    def _restyle_all(self):
        self._rebuild_tune_list()
        # Apps перерендер
        if self._installed_packages is not None:
            self._apps_render()

    def toggle_lang(self):
        if self.is_running:
            return
        current = self.schedule_value
        ru_vals = ("Отключено", "Ежедневно", "Еженедельно (суббота)",
                   "2 раза в месяц (1 и 15)", "Ежемесячно (1 число)")
        en_vals = ("Disabled", "Daily", "Weekly (Saturday)",
                   "Twice a month (1 & 15)", "Monthly (1st)")
        self.lang = "en" if self.lang == "ru" else "ru"
        if self.lang == "ru":
            self.schedule_value = dict(zip(en_vals, ru_vals)).get(current,
                                                                  current)
        else:
            self.schedule_value = dict(zip(ru_vals, en_vals)).get(current,
                                                                  current)
        self._rebuild_ui()

    def _rebuild_ui(self):
        c = self.colors()
        # сохранить состояние
        saved_opts = dict(self.opts_state)
        saved_mounts = dict(self.mount_state)
        saved_steam = dict(self.steam_state)
        saved_commit = dict(self.commit_state)
        saved_apps = set(self.apps_checked)
        hist = self._terminal.toPlainText() if self._terminal else ""
        # пересобрать
        old = self.centralWidget()
        if old is not None:
            old.hide()
            old.setParent(None)
            old.deleteLater()
        self.badges = {}
        self.mount_badges = {}
        self.steam_badges = {}
        self.commit_badges = {}
        self.option_widgets = {}
        self.sched_lbl = None
        self.thp_lbl = None
        self._zfs_button = None
        self.opts_state = {k: saved_opts.get(k, False) for k in OPTIONS_META}
        self.mount_state = {k: saved_mounts.get(k, False)
                            for k in self.mount_state}
        self.steam_state = {k: saved_steam.get(k, False)
                            for k in self.steam_state}
        self.commit_state = {k: saved_commit.get(k, False)
                             for k in self.commit_state}
        self.apps_checked = saved_apps
        try:
            self.state.zfs_installed = zfs_packages_installed()
            self.state.zfs_used = zfs_in_use()
            self.state.pipewire_active = pipewire_active()
            self.state.nmi_watchdog_active = nmi_watchdog_active()
            self.state.nmi_watchdog_in_grub = nmi_watchdog_in_grub()
            with open("/proc/sys/vm/max_map_count", "r") as f:
                self.state.current_max_map_count = f.read().strip()
        except Exception:
            pass
        self._compute_disabled_reasons()
        self.build_ui()
        self._apply_theme()
        if hist:
            self._terminal.setPlainText(hist)
            self._terminal.moveCursor(QTextCursor.End)
        self._update_badges()
        self._spawn_task(self._services_work)
        self._spawn_task(self._applied_work)
        self._spawn_task(self._status_work)
        if self._installed_packages is not None:
            self._apps_render()

    def _qss_template(self):
        return """
QMainWindow, QWidget#central { background: {bg}; }
QScrollArea { background: {panel}; border: none; }
QScrollArea > QWidget > QWidget { background: {panel}; }
QWidget#optinner { background: {panel}; }
QTabWidget::pane { border: 1px solid {border}; border-radius: 10px;
                   background: {panel}; }
QTabBar::tab { background: {tab}; color: {fg}; padding: 9px 22px;
               border-top-left-radius: 10px; border-top-right-radius: 10px;
               margin-right: 3px; }
QTabBar::tab:selected { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                       stop:0 {accent}, stop:1 {accent2});
                       color: {accent_fg}; font-weight: bold; }
QTabBar::tab:hover:!selected { background: {tab_hover}; }
QPushButton { background: {button}; color: {fg}; border: none;
              border-radius: 9px; padding: 8px 14px; }
QPushButton:hover { background: {button_hover}; }
QPushButton:disabled { background: {button_dis}; color: {fg_dis}; }
QPushButton#accent { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                     stop:0 {accent}, stop:1 {accent2});
                     color: {accent_fg}; font-weight: bold; }
QPushButton#accent:hover { background: {accent2}; }
QPushButton#accent_warn { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                         stop:0 {orange}, stop:1 {red});
                         color: {accent_fg}; font-weight: bold; }
QPushButton#accent_warn:hover { background: {red}; }
QPushButton#qbtn { background: {button}; color: {blue}; font-weight: bold;
                   border-radius: 12px; padding: 2px 8px; }
QPushButton#qbtn:hover { background: {accent}; color: {accent_fg}; }
QPushButton#qbtn_small { background: {button}; color: {blue};
                         border-radius: 6px; padding: 3px 8px;
                         font-size: 11px; }
QPushButton#qbtn_small:hover { background: {accent}; color: {accent_fg}; }
QCheckBox { color: {fg}; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px;
                       border: 2px solid {scroll}; background: {panel}; }
QCheckBox::indicator:checked { background: {accent}; border-color: {accent}; }
QCheckBox:disabled { color: {fg_dis}; }
QLineEdit, QComboBox { background: {entry}; color: {fg};
                       border: 1px solid {border}; border-radius: 7px;
                       padding: 4px 8px; }
QComboBox::drop-down { border: none; width: 22px; }
QTableWidget { background: {panel}; color: {fg};
               gridline-color: {border}; border: 1px solid {border};
               border-radius: 10px; }
QTableWidget::item:selected { background: {sel}; }
QHeaderView::section { background: {tab}; color: {fg}; padding: 7px;
                       border: none; border-right: 1px solid {border}; }
QTextEdit, QTextBrowser { background: {terminal}; color: {terminal_fg};
                          border: 1px solid {border}; border-radius: 10px; }
QProgressBar { background: {gray_bg}; border: none; border-radius: 6px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                     stop:0 {accent}, stop:1 {accent2});
                     border-radius: 6px; }
QScrollBar:vertical { background: {panel}; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: {scroll}; border-radius: 5px;
                              min-height: 24px; }
QScrollBar::handle:vertical:hover { background: {accent}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: {panel}; height: 10px;
                        border-radius: 5px; }
QScrollBar::handle:horizontal { background: {scroll}; border-radius: 5px;
                                min-width: 24px; }
QFrame#optrow { background: transparent; border-radius: 10px; }
QFrame#optrow:hover { background: {row_hover}; }
QFrame#toast { background: {panel}; border: 1px solid {border};
               border-radius: 12px; }
QMenu { background: {panel}; color: {fg}; border: 1px solid {border};
        border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 18px; border-radius: 6px; }
QMenu::item:selected { background: {row_hover}; }
QToolTip { background: {panel}; color: {fg}; border: 1px solid {border}; }
"""

    def closeEvent(self, e):
        if self.is_running:
            r = QMessageBox.question(self, APP_NAME, self.t("msg_close"))
            if r != QMessageBox.Yes:
                e.ignore()
                return
        release_lock()
        e.accept()

# ============================================================================
# БЛОК 17. ТОЧКА ВХОДА
# ============================================================================

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("%s v%s (%s)\npython3 linux_tweaker.py [--dry-run]"
              % (APP_NAME, APP_VERSION, APP_BUILD_DATE))
        sys.exit(0)
    if not acquire_lock():
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None, APP_NAME,
            "Linux Tweaker is already running." if detect_lang() == "en"
            else "Linux Tweaker уже запущен.")
        sys.exit(1)
    if os.geteuid() == 0:
        print("WARNING: Linux Tweaker should be run as a normal user, "
              "not as root. Sudo will be requested when needed.",
              file=sys.stderr)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    try:
        sys.exit(app.exec_())
    finally:
        release_lock()

if __name__ == "__main__":
    main()
