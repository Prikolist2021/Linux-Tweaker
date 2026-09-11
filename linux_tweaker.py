#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Tweaker v0.01
Графическая оболочка тюнинга Linux Mint / Ubuntu / Debian на PyQt6.
RU/EN, темы, анимации, детект применённых настроек, откат, бэкапы,
mount-опции noatime/nodiratime, симлинки compatdata для Steam.
"""
import sys, os, re, subprocess, time, shutil, glob, pwd, grp, traceback
from PyQt6.QtCore import (Qt, QObject, QThread, pyqtSignal, QTimer,
                          QPropertyAnimation, QEasingCurve, QRect, QSize)
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QPen, QBrush,
                         QPainterPath, QLinearGradient)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QCheckBox, QLineEdit, QComboBox, QTextEdit,
                             QTableWidget, QTableWidgetItem, QAbstractItemView,
                             QHeaderView, QScrollArea, QFrame, QInputDialog,
                             QMessageBox, QFileDialog, QMenu, QDialog,
                             QGraphicsOpacityEffect)

APP_NAME = "Linux Tweaker"
APP_VERSION = "0.01"

# ─── данные ──────────────────────────────────────────────────────────────
OPTIONS_META = {
    "rsyslog": {"ru": ("Отключить rsyslog", "Система постоянно пишет подробные журналы на диск. На домашнем ПК это лишняя нагрузка: отключение экономит ресурс SSD и слегка ускоряет работу.", "Логи системы", "запись журналов rsyslog на диск"),
                "en": ("Disable rsyslog", "The system constantly writes detailed logs to disk; disabling saves SSD life and speeds things up.", "System logs", "detailed rsyslog logging")},
    "journald": {"ru": ("Логи в ОЗУ (journald)", "Переносит журналы systemd в оперативную память и ограничивает их 50 МБ. Диски не изнашиваются.", "Логи системы", "журналы systemd в ОЗУ"),
                 "en": ("Logs in RAM (journald)", "Moves systemd journals to RAM capped at 50 MB; no disk wear.", "System logs", "journald in RAM")},
    "audit": {"ru": ("audit=0 (GRUB)", "Отключает аудит ядра: меньше накладных расходов, чуть быстрее загрузка.", "Ядро и загрузка", "аудит ядра (audit=0)"),
              "en": ("audit=0 (GRUB)", "Disables kernel auditing: less overhead, faster boot.", "Kernel & boot", "kernel audit (audit=0)")},
    "raid": {"ru": ("raid=noautodetect (GRUB)", "Если нет RAID — система не тратит время на его поиск при загрузке.", "Ядро и загрузка", "поиск RAID при загрузке"),
             "en": ("raid=noautodetect (GRUB)", "Skips RAID probing at boot when you have no RAID array.", "Kernel & boot", "RAID probing at boot")},
    "corectrl": {"ru": ("CoreCtrl (Polkit)", "Правило Polkit для CoreCtrl: управление частотами и вентиляторами AMD без пароля. Группа по умолчанию — ваша.", "Видеокарта и графика", "polkit-правило CoreCtrl"),
                 "en": ("CoreCtrl (Polkit)", "Polkit rule for CoreCtrl: AMD clocks/fans control without password; group defaults to yours.", "GPU & graphics", "CoreCtrl polkit rule")},
    "ppfeaturemask": {"ru": ("amdgpu.ppfeaturemask", "Разблокирует управление питанием AMD GPU (для старых ядер).", "Видеокарта и графика", "управление питанием AMD"),
                      "en": ("amdgpu.ppfeaturemask", "Unlocks AMD GPU power management (older kernels).", "GPU & graphics", "AMD power management")},
    "vrr": {"ru": ("VRR/FreeSync", "Переменная частота обновления для AMD: картинка без разрывов (X11, amdgpu).", "Видеокарта и графика", "VRR/FreeSync (X11)"),
            "en": ("VRR/FreeSync", "Variable refresh rate on AMD: tear-free gaming (X11, amdgpu).", "GPU & graphics", "VRR/FreeSync (X11)")},
    "radv": {"ru": ("RADV_PERFTEST=sam", "SAM / Resizable BAR в RADV: небольшой прирост FPS.", "Видеокарта и графика", "SAM / ReBAR в RADV"),
             "en": ("RADV_PERFTEST=sam", "SAM / Resizable BAR in RADV: small FPS gain.", "GPU & graphics", "SAM / ReBAR in RADV")},
    "mesa": {"ru": ("MESA_SHADER_CACHE=4G", "Кэш шейдеров 4 ГБ: меньше подтормаживаний в играх.", "Видеокарта и графика", "кэш шейдеров 4 ГБ"),
             "en": ("MESA_SHADER_CACHE=4G", "4 GB shader cache: fewer in-game hitches.", "GPU & graphics", "4 GB shader cache")},
    "pipewire": {"ru": ("PipeWire (звук)", "Увеличивает буферы PipeWire: убирает треск и щелчки звука.", "Звук", "буферы PipeWire"),
                 "en": ("PipeWire (sound)", "Increases PipeWire quanta: removes audio crackling.", "Sound", "PipeWire quanta")},
    "swap": {"ru": ("Тюнинг swap", "vm.swappiness: 150 для zram, 10 для диска — меньше лишних обращений к диску.", "Память и swap", "vm.swappiness"),
             "en": ("Swap tuning", "vm.swappiness: 150 for zram, 10 for disk — less disk traffic.", "Memory & swap", "vm.swappiness")},
    "sysctl": {"ru": ("Тюнинг sysctl", "vfs_cache_pressure=50 (кэш дольше в памяти) и numa_balancing=0 (лучше играм).", "Ядро и загрузка", "sysctl-тюнинг"),
               "en": ("sysctl tuning", "vfs_cache_pressure=50 and numa_balancing=0 (better for games).", "Kernel & boot", "sysctl tuning")},
    "ntsync": {"ru": ("ntsync (модуль ядра)", "Ускоритель синхронизации Wine/Proton: прирост FPS (ядро 6.14+).", "Игры и совместимость", "модуль ntsync"),
               "en": ("ntsync (kernel module)", "Wine/Proton sync accelerator: FPS gain (kernel 6.14+).", "Gaming & compatibility", "ntsync module")},
    "ntfs3": {"ru": ("ntfs3 драйвер", "Быстрый встроенный драйвер NTFS вместо ntfs-3g (Mint блокирует по умолчанию).", "Диски и файловые системы", "драйвер ntfs3"),
              "en": ("ntfs3 driver", "Fast in-kernel NTFS driver instead of ntfs-3g (Mint blocks it).", "Drives & filesystems", "ntfs3 driver")},
    "aliases": {"ru": ("Команды в .bashrc", "Команды upd, upgr, update_all, clean, space, mem и другие.", "Удобство", "команды в .bashrc"),
                "en": ("Commands in .bashrc", "Adds upd, upgr, update_all, clean, space, mem commands.", "Convenience", ".bashrc commands")},
    "autoupdate": {"ru": ("Автообновления", "systemd-таймер автообновления APT и Flatpak по расписанию.", "Обновления", "таймер автообновлений"),
                   "en": ("Auto-updates", "systemd timer updating APT and Flatpak on schedule.", "Updates", "auto-update timer")},
}
CAT_ORDER = {"ru": ["Видеокарта и графика", "Ядро и загрузка", "Логи системы", "Звук",
                    "Память и swap", "Диски и файловые системы", "Игры и совместимость",
                    "Удобство", "Обновления"],
             "en": ["GPU & graphics", "Kernel & boot", "System logs", "Sound",
                    "Memory & swap", "Drives & filesystems", "Gaming & compatibility",
                    "Convenience", "Updates"]}
SERVICES_META = {
    "avahi-daemon.service": {"ru": "Сетевое обнаружение устройств (принтеры, ТВ). Дома обычно не нужно.", "en": "Network device discovery; rarely needed at home."},
    "avahi-daemon.socket": {"ru": "Сокет-активатор Avahi; отключается вместе со службой.", "en": "Avahi socket activator; disabled with the service."},
    "cups-browsed.service": {"ru": "Поиск сетевых принтеров; без сетевого принтера не нужен.", "en": "Network printer discovery; useless without one."},
    "ModemManager.service": {"ru": "Управление USB-модемами; без модема не нужен.", "en": "USB modem management; useless without a modem."},
    "openvpn.service": {"ru": "Встроенный VPN-сервер; не нужен, если не поднимаете VPN.", "en": "Built-in VPN server; useless unless you run one."},
    "lvm2-monitor.service": {"ru": "Мониторинг LVM; без LVM не нужен.", "en": "LVM monitoring; useless without LVM."},
    "switcheroo-control.service": {"ru": "Переключение графики на ноутбуках; на ПК не нужен.", "en": "GPU switching on laptops; useless on desktops."},
    "touchegg.service": {"ru": "Жесты тачпада; на ПК без тачскрина не нужен.", "en": "Touchpad gestures; useless without a touchscreen."},
    "zfs-zed.service": {"ru": "Мониторинг ZFS; без ZFS не нужен.", "en": "ZFS monitoring; useless without ZFS."},
    "kerneloops.service": {"ru": "Отчёты о сбоях ядра разработчикам; дома не нужны.", "en": "Kernel crash reports; unneeded at home."},
}
SERVICES_ORDER = list(SERVICES_META.keys())
OPTION_FILES = {
    "rsyslog": ["/etc/systemd/system/rsyslog.service", "/lib/systemd/system/rsyslog.service"],
    "journald": ["/etc/systemd/journald.conf"],
    "audit": ["/etc/default/grub"], "raid": ["/etc/default/grub"],
    "corectrl": ["/etc/polkit-1/rules.d/90-corectrl.rules",
                 "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"],
    "ppfeaturemask": ["/etc/default/grub"],
    "vrr": ["/etc/X11/xorg.conf.d/20-amdgpu.conf"],
    "radv": ["/etc/environment"], "mesa": ["/etc/environment"],
    "pipewire": ["{home}/.config/pipewire/pipewire.conf.d/10-sound.conf"],
    "swap": ["/etc/sysctl.d/99-gaming-swap.conf"],
    "sysctl": ["/etc/sysctl.d/99-gaming-sysctl.conf"],
    "ntsync": ["/etc/modules-load.d/ntsync.conf"],
    "ntfs3": ["/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"],
    "aliases": ["{home}/.bashrc"],
    "autoupdate": ["/etc/systemd/system/biweekly-upgrade.timer",
                   "/etc/systemd/system/biweekly-upgrade.service"],
}
STR = {
 "ru": {"tab_tune": "Тюнинг", "tab_serv": "Службы", "tab_stat": "Статус",
        "btn_apply": "Применить выбранное", "btn_rollback": "Откатить выбранное",
        "btn_selall": "Выбрать все", "btn_selnone": "Снять выделение",
        "btn_export": "Экспорт", "btn_about": "О твикере",
        "theme_dark": "Тёмная тема", "theme_light": "Светлая тема",
        "lbl_dry": "Сухой прогон", "lbl_terminal": "Терминальный вывод:",
        "lbl_group": "Группа:", "lbl_value": "Значение:", "lbl_schedule": "Расписание:",
        "ready": "Готово", "running": "Выполнение...", "done": "Готово",
        "applied_yes": "✓ применено", "applied_no": "не применено",
        "btn_file": "файл", "copy": "Копировать", "copy_all": "Копировать всё",
        "sel_all_txt": "Выделить всё",
        "svc_name": "Служба", "svc_state": "Состояние", "svc_run": "Запуск",
        "svc_desc": "Описание", "svc_hint": "Выберите строку, чтобы увидеть описание.",
        "svc_on": "работает", "svc_onoff": "не запущена", "svc_off": "остановлена",
        "svc_masked": "заблокирована", "svc_na": "нет в системе",
        "run_yes": "работает", "run_no": "остановлена",
        "svc_on_sel": "Включить выбранные", "svc_off_sel": "Отключить выбранные",
        "stat_refresh": "Обновить статус",
        "st_hw": "ИНФОРМАЦИЯ О СИСТЕМЕ", "st_tweaks": "ТВИКИ",
        "st_services": "СЛУЖБЫ", "st_kernel": "ПАРАМЕТРЫ ЯДРА",
        "st_timer": "Таймер автообновлений",
        "os_lbl": "ОС", "gpu_lbl": "Видеокарта", "screen_lbl": "Разрешение экрана",
        "swap_lbl": "Файл подкачки", "kernel_lbl": "Ядро", "de_lbl": "Оболочка",
        "ram_lbl": "ОЗУ", "disk_lbl": "Диск", "driver_lbl": "Драйвер видеокарты",
        "user_lbl": "Пользователь", "home_lbl": "Домашняя папка",
        "yes_w": "да", "no_w": "нет", "no_swap": "отсутствует",
        "gb": "ГБ", "free_w": "свободно", "swap_file": "файл", "swap_part": "раздел",
        "yes": "ПРИМЕНЕНО", "no": "НЕ ПРИМЕНЕНО",
        "sched_cur": "Текущее: %s", "sched_none": "не настроено",
        "mount_title": "Диски: параметры монтирования",
        "mount_desc": "Добавит noatime,nodiratime в /etc/fstab (меньше обращений к диску). Вступает в силу после перезагрузки.",
        "steam_title": "Steam: симлинки compatdata",
        "steam_desc": "Создаст ссылку compatdata на ~/.steam/steam/steamapps/compatdata для библиотек на NTFS.",
        "mount_short": "параметры монтирования", "steam_short": "симлинк compatdata",
        "kern_sw": "охота сбрасывать память в swap", "kern_vfs": "кэш файлов в памяти",
        "kern_numa": "миграция памяти между ядрами",
        "msg_run": "Скрипт уже запущен. Дождитесь завершения.",
        "msg_noopt": "Отметьте хотя бы одну опцию.",
        "msg_sel": "Сначала выберите строки в таблице.",
        "msg_nofile": "Файл ещё не существует. Пути опции:",
        "viewer": "Просмотр файла", "viewer_ext": "Открыть во внешнем редакторе",
        "about_title": "О твикере",
        "about_purpose": "Графическая оболочка для безопасного тюнинга Linux Mint / Ubuntu / Debian: твики производительности, логов, дисков и игр с откатом и бэкапами.",
        "about_author": "Автор", "about_author_name": "Дмитрий Свистунов",
        "about_ver": "Версия",
        "help_body": "КАК ПОЛЬЗОВАТЬСЯ\n1. Отметьте опции на вкладке «Тюнинг»; зелёная метка «✓ применено» значит настройка уже активна.\n2. Нажмите «Применить выбранное» и введите пароль sudo.\n3. «Сухой прогон» показывает команды без применения.\n\nОТКАТ\nОтметьте опции и нажмите «Откатить выбранное»; бэкапы файлов хранятся в ~/system-tuneup-backups.\n\nСЛУЖБЫ\nВыделите строки таблицы и включите/отключите их кнопками.\n\nСТАТУС\nЗелёным — применённые твики, красным — нет.",
        "toast_ok": "Успех", "toast_err": "Ошибка", "toast_info": "Внимание"},
 "en": {"tab_tune": "Tuning", "tab_serv": "Services", "tab_stat": "Status",
        "btn_apply": "Apply selected", "btn_rollback": "Rollback selected",
        "btn_selall": "Select all", "btn_selnone": "Deselect",
        "btn_export": "Export", "btn_about": "About",
        "theme_dark": "Dark theme", "theme_light": "Light theme",
        "lbl_dry": "Dry run", "lbl_terminal": "Terminal output:",
        "lbl_group": "Group:", "lbl_value": "Value:", "lbl_schedule": "Schedule:",
        "ready": "Ready", "running": "Running...", "done": "Done",
        "applied_yes": "✓ applied", "applied_no": "not applied",
        "btn_file": "file", "copy": "Copy", "copy_all": "Copy all",
        "sel_all_txt": "Select all",
        "svc_name": "Service", "svc_state": "State", "svc_run": "Running",
        "svc_desc": "Description", "svc_hint": "Select a row to see the description.",
        "svc_on": "running", "svc_onoff": "not running", "svc_off": "stopped",
        "svc_masked": "blocked", "svc_na": "not installed",
        "run_yes": "running", "run_no": "stopped",
        "svc_on_sel": "Enable selected", "svc_off_sel": "Disable selected",
        "stat_refresh": "Refresh status",
        "st_hw": "SYSTEM INFORMATION", "st_tweaks": "TWEAKS",
        "st_services": "SERVICES", "st_kernel": "KERNEL PARAMETERS",
        "st_timer": "Auto-update timer",
        "os_lbl": "OS", "gpu_lbl": "GPU", "screen_lbl": "Screen resolution",
        "swap_lbl": "Swap", "kernel_lbl": "Kernel", "de_lbl": "Desktop",
        "ram_lbl": "RAM", "disk_lbl": "Disk", "driver_lbl": "GPU driver",
        "user_lbl": "User", "home_lbl": "Home folder",
        "yes_w": "yes", "no_w": "no", "no_swap": "none",
        "gb": "GB", "free_w": "free", "swap_file": "file", "swap_part": "partition",
        "yes": "APPLIED", "no": "NOT APPLIED",
        "sched_cur": "Current: %s", "sched_none": "not configured",
        "mount_title": "Disks: mount options",
        "mount_desc": "Adds noatime,nodiratime to /etc/fstab (less disk wear). Takes effect after reboot.",
        "steam_title": "Steam: compatdata symlinks",
        "steam_desc": "Creates compatdata symlink to ~/.steam/steam/steamapps/compatdata for NTFS libraries.",
        "mount_short": "mount options", "steam_short": "compatdata symlink",
        "kern_sw": "eagerness to swap memory", "kern_vfs": "file cache in RAM",
        "kern_numa": "memory migration between cores",
        "msg_run": "A job is already running. Wait for it.",
        "msg_noopt": "Tick at least one option.",
        "msg_sel": "Select table rows first.",
        "msg_nofile": "File does not exist yet. Option paths:",
        "viewer": "File viewer", "viewer_ext": "Open in external editor",
        "about_title": "About",
        "about_purpose": "A graphical shell for safe tuning of Linux Mint / Ubuntu / Debian with rollback and backups.",
        "about_author": "Author", "about_author_name": "Dmitry Svistunov",
        "about_ver": "Version",
        "help_body": "HOW TO USE\n1. Tick options on the Tuning tab; a green \"✓ applied\" mark means the setting is already active.\n2. Press \"Apply selected\" and enter your sudo password.\n3. \"Dry run\" shows commands without applying.\n\nROLLBACK\nTick options and press \"Rollback selected\"; file backups live in ~/system-tuneup-backups.\n\nSERVICES\nSelect table rows and enable/disable them with the buttons.\n\nSTATUS\nGreen means applied tweaks, red means not applied.",
        "toast_ok": "Success", "toast_err": "Error", "toast_info": "Notice"},
}

THEMES = {
 "dark": {"bg": "#1e1e1e", "panel": "#252526", "fg": "#d4d4d4", "gray": "#9a9a9a",
          "border": "#3c3c3c", "tab": "#2d2d30", "tab_hover": "#38383d",
          "accent": "#4ec9b0", "accent2": "#3aa794", "accent_fg": "#10201c",
          "button": "#3a3d41", "button_hover": "#46494e", "button_dis": "#2d2d30",
          "fg_dis": "#6a6a6a", "entry": "#333333", "terminal": "#0c0c0c",
          "terminal_fg": "#d4d4d4", "sel": "#094771", "scroll": "#5a5a5a",
          "row_hover": "#2a2d2e", "green": "#4ec9b0", "green_bg": "#17352f",
          "gray_bg": "#2f2f2f", "red": "#f44747", "yellow": "#d7ba7d",
          "blue": "#569cd6", "orange": "#ce9178"},
 "light": {"bg": "#f5f5f5", "panel": "#ffffff", "fg": "#1e1e1e", "gray": "#616161",
           "border": "#d0d0d0", "tab": "#e4e4e4", "tab_hover": "#d8d8d8",
           "accent": "#2e9e83", "accent2": "#268a72", "accent_fg": "#ffffff",
           "button": "#e4e4e4", "button_hover": "#d8d8d8", "button_dis": "#ececec",
           "fg_dis": "#9a9a9a", "entry": "#ffffff", "terminal": "#ffffff",
           "terminal_fg": "#1e1e1e", "sel": "#cde4f7", "scroll": "#b0b0b0",
           "row_hover": "#ececec", "green": "#2e7d32", "green_bg": "#e2f0e3",
           "gray_bg": "#e8e8e8", "red": "#c62828", "yellow": "#b26a00",
           "blue": "#1565c0", "orange": "#e65100"},
}

QSS = """
QMainWindow, QWidget#central { background: {bg}; }
QTabWidget::pane { border: 1px solid {border}; border-radius: 10px; background: {panel}; }
QTabBar::tab { background: {tab}; color: {fg}; padding: 9px 22px;
  border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 3px; }
QTabBar::tab:selected { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {accent}, stop:1 {accent2}); color: {accent_fg}; font-weight: bold; }
QTabBar::tab:hover:!selected { background: {tab_hover}; }
QPushButton { background: {button}; color: {fg}; border: none; border-radius: 9px; padding: 8px 14px; }
QPushButton:hover { background: {button_hover}; }
QPushButton:disabled { background: {button_dis}; color: {fg_dis}; }
QPushButton#accent { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {accent}, stop:1 {accent2}); color: {accent_fg}; font-weight: bold; }
QPushButton#accent:hover { background: {accent2}; }
QCheckBox { color: {fg}; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 2px solid {scroll}; background: {panel}; }
QCheckBox::indicator:checked { background: {accent}; border-color: {accent}; }
QLineEdit, QComboBox { background: {entry}; color: {fg}; border: 1px solid {border}; border-radius: 7px; padding: 4px 8px; }
QComboBox::drop-down { border: none; width: 22px; }
QTableWidget { background: {panel}; color: {fg}; gridline-color: {border}; border: 1px solid {border}; border-radius: 10px; }
QTableWidget::item:selected { background: {sel}; }
QHeaderView::section { background: {tab}; color: {fg}; padding: 7px; border: none; border-right: 1px solid {border}; }
QTextEdit { background: {terminal}; color: {terminal_fg}; border: 1px solid {border}; border-radius: 10px; }
QScrollBar:vertical { background: {panel}; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: {scroll}; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: {panel}; height: 10px; border-radius: 5px; }
QScrollBar::handle:horizontal { background: {scroll}; border-radius: 5px; min-width: 24px; }
QFrame#optrow { background: transparent; border-radius: 10px; }
QFrame#optrow:hover { background: {row_hover}; }
QLabel#badge_yes { background: {green_bg}; color: {green}; border-radius: 7px; padding: 3px 9px; font-weight: bold; }
QLabel#badge_no { background: {gray_bg}; color: {gray}; border-radius: 7px; padding: 3px 9px; }
QFrame#toast { background: {panel}; border: 1px solid {border}; border-radius: 12px; }
QMenu { background: {panel}; color: {fg}; border: 1px solid {border}; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 18px; border-radius: 6px; }
QMenu::item:selected { background: {row_hover}; }
"""

# ─── утилиты ─────────────────────────────────────────────────────────────
def decode_bytes(v):
    return v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)

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
    for key, name in [("cinnamon", "Cinnamon"), ("xfce", "XFCE"), ("mate", "MATE"),
                      ("plasma", "KDE Plasma"), ("kde", "KDE Plasma"), ("gnome", "GNOME"),
                      ("lxqt", "LXQt"), ("lxde", "LXDE"), ("openbox", "Openbox"),
                      ("budgie", "Budgie"), ("pantheon", "Pantheon")]:
        if key in d:
            return name
    return os.environ.get("XDG_CURRENT_DESKTOP", "") or "?"

def detect_lang():
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val:
            return "ru" if val.lower().startswith("ru") else "en"
    return "en"

def parse_mounts():
    items = []
    try:
        with open("/proc/mounts", "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                dev, mp, fstype, opts = parts[0], parts[1], parts[2], parts[3]
                if not dev.startswith("/dev/"):
                    continue
                if fstype not in ("ext2", "ext3", "ext4", "xfs", "btrfs", "f2fs",
                                  "ntfs", "ntfs3", "vfat", "exfat", "fuseblk"):
                    continue
                if "rw" not in opts.split(","):
                    continue
                items.append({"dev": dev, "mp": mp, "fstype": fstype})
    except Exception:
        pass
    return items

def find_steam_libraries(user_home):
    libs = []
    vdf = os.path.join(user_home, ".steam", "steam", "steamapps", "libraryfolders.vdf")
    if os.path.isfile(vdf):
        try:
            with open(vdf, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = re.search(r'"path"\s+"([^"]+)"', line)
                    if m:
                        sa = os.path.join(m.group(1).replace("\\\\", "/"), "steamapps")
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

# ─── иконки (рисуются кодом) ─────────────────────────────────────────────
def _gear_path(cx, cy, r):
    path = QPainterPath()
    teeth = 8
    for i in range(teeth):
        import math
        a = math.radians(i * 360.0 / teeth)
        rect = QRect(cx - r * 0.16, cy - r * 1.0, r * 0.32, r * 0.42)
        from PyQt6.QtGui import QTransform
        tr = QTransform().translate(cx, cy).rotate(i * 360.0 / teeth).translate(-cx, -cy)
        path.addRect(tr.mapRect(rect))
    ring = QPainterPath(); ring.addEllipse(cx - r * 0.66, cy - r * 0.66, r * 1.32, r * 1.32)
    hole = QPainterPath(); hole.addEllipse(cx - r * 0.28, cy - r * 0.28, r * 0.56, r * 0.56)
    return path + (ring - hole)

def make_icon(kind, size=48, accent="#4ec9b0", fg="#d4d4d4"):
    px = QPixmap(size, size); px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = size / 2.0; r = size * 0.36
    pen = QPen(QColor(fg), size * 0.09); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    if kind == "logo":
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor(accent)); grad.setColorAt(1, QColor("#3aa794"))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(grad)
        p.drawRoundedRect(2, 2, size - 4, size - 4, size * 0.24, size * 0.24)
        p.setBrush(QColor("#ffffff")); p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(_gear_path(c, c, r * 0.86), QBrush(QColor("#ffffff")))
    elif kind == "gear":
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(_gear_path(c, c, r), QBrush(QColor(accent)))
    elif kind == "services":
        p.setPen(pen)
        for i, y in enumerate((0.3, 0.5, 0.7)):
            p.drawLine(int(size * 0.2), int(size * y), int(size * 0.8), int(size * y))
            dx = 0.35 + 0.15 * i
            p.setBrush(QColor(accent)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(size * dx) - 4, int(size * y) - 4, 8, 8)
            p.setPen(pen)
    elif kind == "status":
        p.setPen(QPen(QColor(accent), size * 0.1)); 
        path = QPainterPath()
        path.moveTo(size * 0.15, size * 0.6)
        path.lineTo(size * 0.35, size * 0.6)
        path.lineTo(size * 0.5, size * 0.3)
        path.lineTo(size * 0.65, size * 0.75)
        path.lineTo(size * 0.85, size * 0.5)
        p.drawPath(path)
    elif kind == "apply":
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(accent))
        p.drawEllipse(4, 4, size - 8, size - 8)
        p.setPen(QPen(QColor("#ffffff"), size * 0.12))
        path = QPainterPath()
        path.moveTo(size * 0.28, size * 0.52)
        path.lineTo(size * 0.45, size * 0.68)
        path.lineTo(size * 0.74, size * 0.34)
        p.drawPath(path)
    elif kind == "rollback":
        p.setPen(QPen(QColor(accent), size * 0.11))
        p.drawArc(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6),
                  40 * 16, 260 * 16)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(accent))
        p.drawEllipse(int(size * 0.62), int(size * 0.12), int(size * 0.2), int(size * 0.2))
    elif kind == "file":
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(accent))
        p.drawRoundedRect(int(size * 0.25), int(size * 0.15),
                          int(size * 0.5), int(size * 0.7), 4, 4)
        p.setPen(QPen(QColor("#ffffff"), size * 0.06))
        for y in (0.35, 0.5, 0.65):
            p.drawLine(int(size * 0.35), int(size * y), int(size * 0.65), int(size * y))
    elif kind == "disk":
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(accent))
        p.drawEllipse(int(size * 0.2), int(size * 0.18), int(size * 0.6), int(size * 0.24))
        p.drawRect(int(size * 0.2), int(size * 0.3), int(size * 0.6), int(size * 0.4))
        p.drawEllipse(int(size * 0.2), int(size * 0.46), int(size * 0.6), int(size * 0.24))
    elif kind == "steam":
        p.setPen(QPen(QColor(accent), size * 0.1))
        p.drawEllipse(int(size * 0.18), int(size * 0.42), int(size * 0.28), int(size * 0.28))
        p.drawEllipse(int(size * 0.54), int(size * 0.3), int(size * 0.28), int(size * 0.28))
        p.drawLine(int(size * 0.4), int(size * 0.52), int(size * 0.6), int(size * 0.46))
    elif kind == "help":
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(accent))
        p.drawEllipse(4, 4, size - 8, size - 8)
        p.setPen(QPen(QColor("#ffffff"), size * 0.11))
        p.drawArc(int(size * 0.32), int(size * 0.24), int(size * 0.36), int(size * 0.36),
                  20 * 16, 200 * 16)
        p.drawLine(int(size * 0.5), int(size * 0.5), int(size * 0.5), int(size * 0.62))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(size * 0.46), int(size * 0.68), int(size * 0.09), int(size * 0.09))
    elif kind == "export":
        p.setPen(QPen(QColor(accent), size * 0.1))
        p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.6))
        path = QPainterPath()
        path.moveTo(size * 0.32, size * 0.45); path.lineTo(size * 0.5, size * 0.65)
        path.lineTo(size * 0.68, size * 0.45); p.drawPath(path)
        p.drawLine(int(size * 0.25), int(size * 0.78), int(size * 0.75), int(size * 0.78))
    p.end()
    return px

# ─── sudo / система / операции (без UI) ──────────────────────────────────
class SudoManager:
    def __init__(self):
        self.prompt_password = None
        self.show_error = None
        self.authenticated = False
        self._keepalive = False
    def _cached(self):
        try:
            return subprocess.run(["sudo", "-n", "true"], capture_output=True,
                                  timeout=3).returncode == 0
        except Exception:
            return False
    def authenticate(self):
        if self._cached():
            self.authenticated = True; self._start_keepalive(); return True
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
                    self.authenticated = True; self._start_keepalive(); return True
                if self.show_error:
                    self.show_error("Wrong password or no sudo rights.")
            except Exception as e:
                if self.show_error:
                    self.show_error("sudo failed: %s" % e)
        return False
    def ensure(self):
        if self._cached():
            self.authenticated = True; self._start_keepalive(); return True
        return self.authenticate()
    def run(self, args, input=None):
        if not self._cached():
            raise PermissionError("Sudo session expired. Press Apply again.")
        return subprocess.run(["sudo", "-n"] + list(args), input=input,
                              capture_output=True, timeout=180)
    def _start_keepalive(self):
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
            self._keepalive = False; self.authenticated = False
        threading.Thread(target=loop, daemon=True).start()

class SystemState:
    def __init__(self):
        self.gpu = "Unknown"; self.gpu_model = ""; self.has_raid = False
        self.has_swap = False; self.swap_type = ""; self.ntsync = False
        self.cinnamon = False; self.has_flatpak = False
        self.user_name = "root"; self.user_home = "/root"
    def detect(self):
        try:
            self.user_name = self._real_user()
        except Exception:
            pass
        try:
            self.user_home = pwd.getpwnam(self.user_name).pw_dir
        except Exception:
            self.user_home = os.path.expanduser("~")
        try:
            res = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
            for raw in res.stdout.splitlines():
                line = raw.lower()
                if "vga" in line or "3d controller" in line or "display controller" in line:
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
                with open("/proc/mdstat", "r", encoding="utf-8", errors="replace") as f:
                    if re.search(r"^md\d+", f.read(), re.M):
                        self.has_raid = True
        except Exception:
            pass
        try:
            res = subprocess.run(["swapon", "--show=TYPE", "--noheadings"],
                                 capture_output=True, text=True, timeout=5)
            out = res.stdout.strip()
            if out:
                self.has_swap = True
                self.swap_type = ("zram" if "zram" in out else
                                  "partition" if "partition" in out else "file")
        except Exception:
            pass
        self.ntsync = os.path.exists("/dev/ntsync")
        d = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        s = os.environ.get("DESKTOP_SESSION", "").lower()
        self.cinnamon = "cinnamon" in d or s == "cinnamon"
        self.has_flatpak = bool(shutil.which("flatpak"))
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
        return "root"

class SystemOps:
    def __init__(self, sudo, state, log, dry_run):
        self.sudo = sudo; self.state = state; self.log = log
        self.dry_run = dry_run; self.grub_changed = False
        self.backup_dir = os.path.join(state.user_home, "system-tuneup-backups")
    def backup_file(self, path):
        if self.dry_run:
            return
        try:
            if not self.path_exists(path):
                return
            content = self.read_file(path)
            if content is None:
                return
            os.makedirs(self.backup_dir, exist_ok=True)
            safe = path.lstrip("/").replace("/", "_")
            bp = os.path.join(self.backup_dir, safe + ".bak")
            with open(bp, "w", encoding="utf-8") as f:
                f.write(content)
            if self.state.user_name != "root":
                try:
                    pw = pwd.getpwnam(self.state.user_name)
                    os.chown(bp, pw.pw_uid, pw.pw_gid)
                except Exception:
                    pass
            self.log("[BACKUP] %s" % os.path.basename(bp), "info")
        except Exception as e:
            self.log("[WARN] backup %s: %s" % (path, e), "warning")
    def sudo_run(self, args, input=None, ok_msg=None, err_msg=None, ignore_error=False):
        if self.dry_run:
            self.log("[DRY RUN] " + " ".join(args), "warning"); return True
        try:
            res = self.sudo.run(args, input=input)
        except PermissionError as e:
            self.log(str(e), "error"); return False
        except Exception as e:
            self.log("Command error: %s" % e, "error"); return False
        if res.returncode == 0:
            if ok_msg:
                self.log(ok_msg, "success")
            return True
        if not ignore_error:
            err = decode_bytes(res.stderr).strip()
            msg = err_msg or "Command failed: " + " ".join(args)
            self.log("[ERR] %s\n   %s" % (msg, err) if err else "[ERR] %s" % msg, "error")
        return False
    def path_exists(self, path):
        if os.path.exists(path):
            return True
        try:
            return subprocess.run(["sudo", "-n", "test", "-e", path],
                                  capture_output=True, timeout=3).returncode == 0
        except Exception:
            return False
    def read_file(self, path):
        if not self.path_exists(path):
            return ""
        try:
            res = subprocess.run(["sudo", "-n", "cat", path], capture_output=True, timeout=5)
            if res.returncode == 0:
                return decode_bytes(res.stdout)
        except Exception:
            pass
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return None
    def write_file(self, path, content, chmod="644", owner=None, mkdir=False, backup=True):
        if self.dry_run:
            self.log("[DRY RUN] write: %s" % path, "warning"); return True
        if mkdir:
            d = os.path.dirname(path)
            if d:
                self.sudo_run(["mkdir", "-p", d], ignore_error=True)
        if backup:
            self.backup_file(path)
        try:
            res = self.sudo.run(["tee", path], input=content.encode())
        except PermissionError as e:
            self.log(str(e), "error"); return False
        except Exception as e:
            self.log("Write error %s: %s" % (path, e), "error"); return False
        if res.returncode != 0:
            self.log("Cannot write %s" % path, "error"); return False
        if chmod:
            self.sudo_run(["chmod", chmod, path], ignore_error=True)
        if owner:
            self.sudo_run(["chown", owner, path], ignore_error=True)
        return True
    def ensure_line(self, path, line, pattern, chmod="644", mkdir=False):
        if self.dry_run:
            self.log("[DRY RUN] %s: %s" % (path, line), "warning"); return True
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error"); return False
        rx = re.compile(pattern)
        new_lines, replaced, changed = [], False, False
        for old in content.splitlines():
            if rx.match(old.strip()):
                if not replaced:
                    changed = changed or old != line
                    new_lines.append(line); replaced = True
                else:
                    changed = True
            else:
                new_lines.append(old)
        if not replaced:
            new_lines.append(line); changed = True
        if not changed:
            self.log("Already configured: %s" % path, "info"); return True
        self.backup_file(path)
        return self.write_file(path, "\n".join(new_lines) + "\n",
                               chmod=chmod, mkdir=mkdir, backup=False)
    def unit_exists(self, name):
        try:
            res = subprocess.run(["systemctl", "list-unit-files", name,
                                  "--no-legend", "--no-pager"],
                                 capture_output=True, timeout=5)
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
                                 capture_output=True, timeout=5)
            return decode_bytes(res.stdout).strip() or "unknown"
        except Exception:
            return "unknown"
    def service_active(self, name):
        try:
            res = subprocess.run(["systemctl", "is-active", name],
                                 capture_output=True, timeout=5)
            return decode_bytes(res.stdout).strip() or "unknown"
        except Exception:
            return "unknown"
    def _spices(self):
        return (self.state.cinnamon and
                (bool(shutil.which("cinnamon-spice-updater")) or
                 os.path.exists("/usr/bin/cinnamon-spice-updater")))
    def add_grub_params(self, params):
        if self.dry_run:
            self.log("[DRY RUN] GRUB add: " + " ".join(params), "warning"); return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if not content:
            self.log("%s not found" % path, "warning"); return False
        new_lines, found, changed = [], False, False
        for line in content.splitlines():
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                found = True
                raw = m.group(1).strip().strip('"').strip("'")
                parts = [x for x in raw.split() if x]
                orig = parts.copy()
                parts += [x for x in params if x not in parts]
                if parts != orig:
                    new_lines.append('GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(parts) + '"')
                    changed = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        if not found:
            new_lines.append('GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(params) + '"')
            changed = True
        if not changed:
            self.log("GRUB already has params", "info"); return True
        self.backup_file(path)
        if self.write_file(path, "\n".join(new_lines) + "\n", backup=False):
            self.grub_changed = True
            self.log("GRUB: params added", "success"); return True
        return False
    def finalize_grub(self):
        if not self.grub_changed:
            return
        if self.dry_run:
            self.log("[DRY RUN] update-grub", "warning"); return
        ug = shutil.which("update-grub") or ("/usr/sbin/update-grub"
             if os.path.exists("/usr/sbin/update-grub") else None)
        gm = shutil.which("grub-mkconfig") or ("/usr/sbin/grub-mkconfig"
             if os.path.exists("/usr/sbin/grub-mkconfig") else None)
        if ug:
            self.sudo_run([ug], ok_msg="GRUB updated", err_msg="update-grub failed")
        elif gm:
            self.sudo_run([gm, "-o", "/boot/grub/grub.cfg"],
                          ok_msg="GRUB updated", err_msg="grub-mkconfig failed")
        else:
            self.log("update-grub not found", "warning")
        self.grub_changed = False
    # ── apply_* ──
    def apply_rsyslog(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] disable+mask rsyslog", "warning"); return True
        if self.service_enabled("rsyslog.service") in ("disabled", "masked", "not-found"):
            self.log("rsyslog already disabled", "info"); return True
        ok = self.sudo_run(["systemctl", "disable", "--now", "rsyslog"], ignore_error=True)
        ok = self.sudo_run(["systemctl", "mask", "rsyslog"], ignore_error=True) or ok
        if ok:
            self.log("✓ rsyslog disabled", "success"); return True
        self.log("Cannot disable rsyslog", "error"); return False
    def apply_journald(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] journald volatile", "warning"); return True
        path = "/etc/systemd/journald.conf"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error"); return False
        if (re.search(r"^\s*Storage\s*=\s*volatile\s*$", content, re.M) and
                re.search(r"^\s*RuntimeMaxUse\s*=\s*50M\s*$", content, re.M)):
            self.log("journald already configured", "info"); return True
        new_lines = []
        for line in content.splitlines():
            if re.match(r"^\s*(Storage|RuntimeMaxUse)\s*=", line):
                new_lines.append(line if line.lstrip().startswith("#") else "# " + line)
            else:
                new_lines.append(line)
        new_lines += ["Storage=volatile", "RuntimeMaxUse=50M"]
        self.backup_file(path)
        if not self.write_file(path, "\n".join(new_lines) + "\n", backup=False):
            return False
        self.sudo_run(["systemctl", "restart", "systemd-journald"], ignore_error=True)
        self.log("✓ journald → volatile (50M)", "success"); return True
    def apply_audit(self, params=None):
        return self.add_grub_params(["audit=0"])
    def apply_raid(self, params=None):
        if self.state.has_raid:
            self.log("RAID detected, skipping", "warning"); return True
        return self.add_grub_params(["raid=noautodetect"])
    def _polkit_new(self):
        try:
            res = subprocess.run(["pkaction", "--version"], capture_output=True,
                                 text=True, timeout=5)
            m = re.search(r"(\d+)\.(\d+)", (res.stdout or "") + (res.stderr or ""))
            if m:
                return int(m.group(1)) > 0 or int(m.group(2)) >= 106
        except Exception:
            pass
        return os.path.isdir("/etc/polkit-1/rules.d")
    def apply_corectrl(self, params=None):
        params = params or {}
        group = params.get("corectrl_group", "").strip() or self.state.user_name
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", group):
            self.log("Bad group name: %s" % group, "error"); return False
        if self.dry_run:
            self.log("[DRY RUN] CoreCtrl rule for %s" % group, "warning"); return True
        try:
            grp.getgrnam(group)
        except KeyError:
            self.log("Group not found: %s" % group, "error"); return False
        if self._polkit_new():
            content = ('polkit.addRule(function(action, subject) {\n'
                       '    if ((action.id == "org.corectrl.helper.init" ||\n'
                       '         action.id == "org.corectrl.helperkiller.init") &&\n'
                       '        subject.local == true && subject.active == true &&\n'
                       '        subject.isInGroup("' + group + '")) {\n'
                       '        return polkit.Result.YES;\n    }\n});\n')
            path = "/etc/polkit-1/rules.d/90-corectrl.rules"
        else:
            content = ("[User permissions]\nIdentity=unix-group:" + group +
                       "\nAction=org.corectrl.*\nResultActive=yes\n")
            path = "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"
        if self.write_file(path, content, chmod="644", mkdir=True):
            self.log("✓ CoreCtrl configured for %s" % group, "success"); return True
        return False
    def apply_ppfeaturemask(self, params=None):
        return self.add_grub_params(["amdgpu.ppfeaturemask=0xffffffff"])
    def apply_vrr(self, params=None):
        if self.state.gpu not in ("AMD", "Unknown"):
            self.log("VRR is AMD-only", "warning"); return True
        if self.dry_run:
            self.log("[DRY RUN] VRR config", "warning"); return True
        content = ('Section "Device"\n    Identifier "AMD"\n    Driver "amdgpu"\n'
                   '    Option "VariableRefresh" "true"\nEndSection\n')
        if self.write_file("/etc/X11/xorg.conf.d/20-amdgpu.conf", content,
                           chmod="644", mkdir=True):
            self.log("✓ VRR/FreeSync enabled", "success"); return True
        return False
    def apply_pipewire(self, params=None):
        d = os.path.join(self.state.user_home, ".config", "pipewire", "pipewire.conf.d")
        path = os.path.join(d, "10-sound.conf")
        if self.dry_run:
            self.log("[DRY RUN] PipeWire config", "warning"); return True
        content = ("context.properties = {\n    default.clock.min-quantum = 512\n"
                   "    default.clock.quantum = 4096\n"
                   "    default.clock.max-quantum = 8192\n}\n")
        if not self.sudo_run(["mkdir", "-p", d], ignore_error=True):
            return False
        if not self.write_file(path, content, chmod="644"):
            return False
        if self.state.user_name != "root":
            self.sudo_run(["chown", "-R", "%s:%s" % (self.state.user_name,
                           self.state.user_name),
                           os.path.join(self.state.user_home, ".config", "pipewire")],
                          ignore_error=True)
        self.log("✓ PipeWire configured", "success"); return True
    def apply_mesa(self, params=None):
        return self.ensure_line("/etc/environment", "MESA_SHADER_CACHE_MAX_SIZE=4G",
                                r"^\s*MESA_SHADER_CACHE_MAX_SIZE=.*")
    def apply_radv(self, params=None):
        return self.ensure_line("/etc/environment", "RADV_PERFTEST=sam",
                                r"^\s*RADV_PERFTEST=.*")
    def apply_swap(self, params=None):
        params = params or {}
        if not self.state.has_swap:
            self.log("No swap found, skipping", "warning"); return True
        val = params.get("swap_value", "").strip() or \
            ("150" if self.state.swap_type == "zram" else "10")
        try:
            iv = int(val)
            if iv < 0 or iv > 200:
                raise ValueError
        except ValueError:
            self.log("Bad swappiness: %s (0-200)" % val, "error"); return False
        if self.dry_run:
            self.log("[DRY RUN] swappiness=%d" % iv, "warning"); return True
        path = "/etc/sysctl.d/99-gaming-swap.conf"
        ex = self.read_file(path)
        if ex and re.search(r"^vm\.swappiness=%d$" % iv, ex, re.M):
            self.log("swappiness already %d" % iv, "info"); return True
        if not self.write_file(path, "vm.swappiness=%d\n" % iv, chmod="644", mkdir=True):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        self.log("✓ swappiness=%d" % iv, "success"); return True
    def apply_sysctl(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] sysctl tuning", "warning"); return True
        path = "/etc/sysctl.d/99-gaming-sysctl.conf"
        ex = self.read_file(path)
        if ex and re.search(r"^vm\.vfs_cache_pressure=50$", ex, re.M) and \
                re.search(r"^kernel\.numa_balancing=0$", ex, re.M):
            self.log("sysctl already tuned", "info"); return True
        self.backup_file(path)
        if not self.write_file(path, "vm.vfs_cache_pressure=50\nkernel.numa_balancing=0\n",
                               chmod="644", mkdir=True, backup=False):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        self.log("✓ sysctl tuned", "success"); return True
    def apply_ntsync(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] ntsync", "warning"); return True
        if self.state.ntsync:
            self.log("ntsync already available", "info"); return True
        if not self.write_file("/etc/modules-load.d/ntsync.conf", "ntsync\n",
                               chmod="644", mkdir=True):
            return False
        self.sudo_run(["modprobe", "ntsync"], ignore_error=True)
        self.log("✓ ntsync autoloaded", "success"); return True
    def apply_ntfs3(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] ntfs3 unlock", "warning"); return True
        path = "/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"
        content = self.read_file(path)
        if not content:
            self.log("mint-blacklist-ntfs3.conf not found", "warning"); return True
        if re.search(r"^\s*#\s*blacklist\s+ntfs3\s*$", content, re.M):
            self.log("ntfs3 already unlocked", "info"); return True
        if re.search(r"^\s*blacklist\s+ntfs3\s*$", content, re.M):
            new = re.sub(r"^\s*blacklist\s+ntfs3\s*$", "# blacklist ntfs3",
                         content, flags=re.M)
            self.backup_file(path)
            if self.write_file(path, new, backup=False):
                self.log("✓ ntfs3 unlocked", "success"); return True
            return False
        self.log("blacklist ntfs3 not found", "warning"); return True
    def apply_aliases(self, params=None):
        bashrc = os.path.join(self.state.user_home, ".bashrc")
        if self.dry_run:
            self.log("[DRY RUN] add commands to .bashrc", "warning"); return True
        content = self.read_file(bashrc)
        if not content:
            self.log(".bashrc not found", "error"); return False
        sm = "# >>> system-tuneup commands >>>"
        em = "# <<< system-tuneup commands <<<"
        lines, skip = [], False
        for line in content.splitlines():
            if line.strip() == sm:
                skip = True; continue
            if line.strip() == em:
                skip = False; continue
            if not skip:
                lines.append(line)
        names = ["upd", "upgr", "spices", "update_all", "inst", "remove", "search",
                 "info", "clean", "space", "fix", "mem", "serv", "update_time"]
        np = "|".join(names)
        arx = re.compile(r"^\s*alias\s+(" + np + r")=")
        frx = re.compile(r"^\s*(" + np + r")\s*\(\)\s*\{")
        cleaned, skip_fn = [], False
        for line in lines:
            if arx.match(line):
                continue
            if frx.match(line):
                if "}" in line:
                    continue
                skip_fn = True; continue
            if skip_fn:
                if line.strip().startswith("}"):
                    skip_fn = False
                continue
            if "system-tuneup" in line and line.strip().startswith("#"):
                continue
            cleaned.append(line)
        spices, has_fp = self._spices(), self.state.has_flatpak
        block = [sm, "# system-tuneup commands", ""]
        block += ["upd() {", '    echo "APT update..."', "    sudo apt update", "}", ""]
        block += ["upgr() {", '    echo "APT upgrade..."', "    sudo apt full-upgrade"]
        if has_fp:
            block.append("    flatpak update")
        block += ["}", ""]
        if spices:
            block += ["spices() {", "    cinnamon-spice-updater --update-all", "}", ""]
        block += ["update_all() {", "    sudo apt update && sudo apt full-upgrade -y"]
        if has_fp:
            block.append("    flatpak update -y")
        if spices:
            block.append("    cinnamon-spice-updater --update-all")
        block += ['    echo "Done."', "}", ""]
        block += ['inst() { sudo apt install "$@"; }',
                  'remove() { sudo apt purge --autoremove "$@"; }',
                  'search() { apt search "$@"; }', 'info() { apt show "$@"; }', ""]
        block += ["clean() {", "    sudo apt autoremove -y && sudo apt autoclean && sudo apt clean", "}", ""]
        block += ["space() {", "    df -h /", "}", ""]
        block += ["fix() {", "    sudo apt --fix-broken install -y && sudo dpkg --configure -a", "}", ""]
        block += ["mem() {", "    sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' && free -h", "}", ""]
        block += ["serv() {", "    systemctl list-unit-files --type=service | less", "}", ""]
        block.append(em)
        while cleaned and cleaned[-1].strip() == "":
            cleaned.pop()
        new = "\n".join(cleaned + [""] + block) + "\n"
        if new == content:
            self.log("Commands already added", "info"); return True
        self.backup_file(bashrc)
        if not self.write_file(bashrc, new, backup=False):
            return False
        if self.state.user_name != "root":
            self.sudo_run(["chown", "%s:%s" % (self.state.user_name,
                           self.state.user_name), bashrc], ignore_error=True)
        self.log("✓ commands added to .bashrc", "success"); return True
    def apply_autoupdate(self, params=None):
        params = params or {}
        sched = params.get("update_schedule", "Отключено")
        table = {"Ежедневно": ("*-*-* 18:30:00", "daily 18:30"),
                 "Еженедельно (суббота)": ("Sat 18:30:00", "weekly Sat"),
                 "2 раза в месяц (1 и 15)": ("*-*-1,15 18:30:00", "1st & 15th"),
                 "Ежемесячно (1 число)": ("*-*-1 18:30:00", "monthly 1st"),
                 "Daily": ("*-*-* 18:30:00", "daily 18:30"),
                 "Weekly (Saturday)": ("Sat 18:30:00", "weekly Sat"),
                 "Twice a month (1 & 15)": ("*-*-1,15 18:30:00", "1st & 15th"),
                 "Monthly (1st)": ("*-*-1 18:30:00", "monthly 1st"),
                 "Disabled": (None, None), "Отключено": (None, None)}
        svc = "/etc/systemd/system/biweekly-upgrade.service"
        tmr = "/etc/systemd/system/biweekly-upgrade.timer"
        exists = self.path_exists(tmr) or self.path_exists(svc)
        if sched in ("Отключено", "Disabled"):
            if not exists:
                self.log("Timer not found", "info"); return True
            if self.dry_run:
                self.log("[DRY RUN] remove timer", "warning"); return True
            self.sudo_run(["systemctl", "disable", "--now",
                           "biweekly-upgrade.timer"], ignore_error=True)
            self.sudo_run(["rm", "-f", svc, tmr], ignore_error=True)
            self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
            self.log("✓ timer removed", "success"); return True
        if sched not in table:
            self.log("Unknown schedule: %s" % sched, "error"); return False
        onc, desc = table[sched]
        cmd = "apt update && apt full-upgrade -y"
        if self.state.has_flatpak:
            cmd += " && flatpak update -y"
        if self._spices():
            cmd += " && cinnamon-spice-updater --update-all"
        svc_c = ("[Unit]\nDescription=System upgrade (%s)\n\n[Service]\nType=oneshot\n"
                 "ExecStartPre=/bin/sleep 600\nExecStart=/usr/bin/bash -c \"%s\"\n"
                 "User=root\n" % (desc, cmd))
        tmr_c = ("[Unit]\nDescription=System upgrade timer (%s)\n\n[Timer]\n"
                 "OnCalendar=%s\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n"
                 % (desc, onc))
        if exists and self.read_file(svc) == svc_c and self.read_file(tmr) == tmr_c:
            self.log("Timer already configured: %s" % desc, "info")
            if self.service_enabled("biweekly-upgrade.timer") != "enabled" and not self.dry_run:
                self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
                self.sudo_run(["systemctl", "enable", "--now",
                               "biweekly-upgrade.timer"], ignore_error=True)
            return True
        if self.dry_run:
            self.log("[DRY RUN] create timer: %s" % desc, "warning"); return True
        self.sudo_run(["systemctl", "disable", "--now",
                       "mintupdate-automation-upgrade.timer"], ignore_error=True)
        if not self.write_file(svc, svc_c, chmod="644"):
            return False
        if not self.write_file(tmr, tmr_c, chmod="644"):
            return False
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        self.sudo_run(["systemctl", "enable", "--now", "biweekly-upgrade.timer"],
                      ok_msg="✓ timer created: %s" % desc, err_msg="timer enable failed")
        return True
    # ── fstab / steam ──
    def _uuid_of(self, dev):
        try:
            res = subprocess.run(["lsblk", "-no", "UUID", dev], capture_output=True,
                                 text=True, timeout=5)
            return res.stdout.strip() if res.returncode == 0 else ""
        except Exception:
            return ""
    def _mount_opts_edit(self, mp, add=True):
        path = "/etc/fstab"
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error"); return False
        dev = next((it["dev"] for it in parse_mounts() if it["mp"] == mp), None)
        uuid = self._uuid_of(dev) if dev else ""
        lines = content.splitlines()
        idx, parts = None, None
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            f = s.split()
            if len(f) < 4:
                continue
            if f[1] == mp or (uuid and f[0].lower() == ("uuid=%s" % uuid).lower()):
                idx, parts = i, f
                break
        if idx is None:
            self.log("%s not found in fstab — skipped" % mp, "warning"); return False
        opts = parts[3].split(",")
        target = ["noatime", "nodiratime"]
        new_opts = opts + [o for o in target if o not in opts] if add else \
            [o for o in opts if o not in target]
        if new_opts == opts:
            self.log("Already configured: %s" % mp, "info"); return True
        parts[3] = ",".join(new_opts)
        lines[idx] = "\t".join(parts)
        self.backup_file(path)
        if not self.write_file(path, "\n".join(lines) + "\n", backup=False):
            return False
        self.log("✓ fstab %s: noatime,nodiratime %s" %
                 (mp, "added (after reboot)" if add else "removed (after reboot)"),
                 "success")
        return True
    def apply_mount_opts(self, mps):
        if self.dry_run:
            for mp in mps:
                self.log("[DRY RUN] fstab %s +noatime,nodiratime" % mp, "warning")
            return True
        for mp in mps:
            self._mount_opts_edit(mp, True)
        return True
    def rollback_mount_opts(self, mps):
        if self.dry_run:
            for mp in mps:
                self.log("[DRY RUN] fstab %s -noatime,nodiratime" % mp, "warning")
            return True
        for mp in mps:
            self._mount_opts_edit(mp, False)
        return True
    def apply_steam_links(self, libs):
        src = os.path.join(self.state.user_home, ".steam", "steam", "steamapps",
                           "compatdata")
        try:
            os.makedirs(src, exist_ok=True)
        except Exception as e:
            self.log("Cannot create %s: %s" % (src, e), "error"); return False
        for lib in libs:
            dst = os.path.join(lib, "compatdata")
            if os.path.realpath(lib) == os.path.realpath(os.path.dirname(src)):
                continue
            if self.dry_run:
                self.log("[DRY RUN] ln -s %s -> %s" % (src, dst), "warning"); continue
            try:
                if os.path.islink(dst):
                    os.remove(dst)
                elif os.path.isdir(dst):
                    self.log("Skipped: %s exists as data directory" % dst, "warning")
                    continue
                elif os.path.exists(dst):
                    self.log("Skipped: %s exists" % dst, "warning"); continue
                os.symlink(src, dst)
                self.log("✓ symlink created: %s" % dst, "success")
            except Exception as e:
                self.log("Symlink error %s: %s" % (dst, e), "error")
        return True
    def rollback_steam_links(self, libs):
        for lib in libs:
            dst = os.path.join(lib, "compatdata")
            if self.dry_run:
                self.log("[DRY RUN] rm %s" % dst, "warning"); continue
            try:
                if os.path.islink(dst):
                    os.remove(dst); self.log("✓ symlink removed: %s" % dst, "success")
                else:
                    self.log("Not a symlink, untouched: %s" % dst, "info")
            except Exception as e:
                self.log("Remove error %s: %s" % (dst, e), "error")
        return True
    # ── rollback ─
    def _rm(self, path):
        if self.dry_run:
            self.log("[DRY RUN] rm %s" % path, "warning"); return True
        if not self.path_exists(path):
            self.log("File not found: %s" % path, "info"); return True
        return self.sudo_run(["rm", "-f", path], ok_msg="✓ removed %s" % path)
    def _remove_line(self, path, pattern):
        if self.dry_run:
            self.log("[DRY RUN] %s: remove %s" % (path, pattern), "warning"); return True
        content = self.read_file(path)
        if not content:
            self.log("File not found: %s" % path, "info"); return True
        rx = re.compile(pattern)
        old = content.splitlines()
        new = [l for l in old if not rx.match(l.strip())]
        if len(new) == len(old):
            self.log("Line not found in %s" % path, "info"); return True
        self.backup_file(path)
        return self.write_file(path, "\n".join(new) + "\n", backup=False)
    def _remove_grub(self, params):
        if self.dry_run:
            self.log("[DRY RUN] GRUB remove: " + " ".join(params), "warning"); return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if not content:
            self.log("GRUB not found", "warning"); return False
        new_lines, changed = [], False
        for line in content.splitlines():
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                raw = m.group(1).strip().strip('"').strip("'")
                parts = [x for x in raw.split() if x and x not in params]
                new_lines.append('GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(parts) + '"')
                changed = True
            else:
                new_lines.append(line)
        if not changed:
            self.log("GRUB params not found", "info"); return True
        self.backup_file(path)
        if self.write_file(path, "\n".join(new_lines) + "\n", backup=False):
            self.grub_changed = True
            self.log("✓ GRUB params removed", "success"); return True
        return False
    def rollback_rsyslog(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] unmask+enable rsyslog", "warning"); return True
        self.sudo_run(["systemctl", "unmask", "rsyslog"], ignore_error=True)
        self.sudo_run(["systemctl", "enable", "--now", "rsyslog"],
                      ok_msg="✓ rsyslog re-enabled", ignore_error=True)
        return True
    def rollback_journald(self, params=None):
        path = "/etc/systemd/journald.conf"
        bak = os.path.join(self.backup_dir, "etc_systemd_journald.conf.bak")
        if self.path_exists(bak):
            c = self.read_file(bak)
            if c:
                self.write_file(path, c, backup=False)
                self.sudo_run(["systemctl", "restart", "systemd-journald"],
                              ignore_error=True)
                self.log("✓ journald restored from backup", "success"); return True
        self._remove_line(path, r"^\s*Storage\s*=")
        self._remove_line(path, r"^\s*RuntimeMaxUse\s*=")
        self.sudo_run(["systemctl", "restart", "systemd-journald"], ignore_error=True)
        self.log("✓ journald back to defaults", "success"); return True
    def rollback_audit(self, params=None):
        return self._remove_grub(["audit=0"])
    def rollback_raid(self, params=None):
        return self._remove_grub(["raid=noautodetect"])
    def rollback_ppfeaturemask(self, params=None):
        return self._remove_grub(["amdgpu.ppfeaturemask=0xffffffff"])
    def rollback_corectrl(self, params=None):
        self._rm("/etc/polkit-1/rules.d/90-corectrl.rules")
        self._rm("/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla")
        self.log("✓ CoreCtrl rule removed", "success"); return True
    def rollback_vrr(self, params=None):
        self._rm("/etc/X11/xorg.conf.d/20-amdgpu.conf")
        self.log("✓ VRR config removed", "success"); return True
    def rollback_radv(self, params=None):
        self._remove_line("/etc/environment", r"^\s*RADV_PERFTEST=.*")
        self.log("✓ RADV_PERFTEST removed", "success"); return True
    def rollback_mesa(self, params=None):
        self._remove_line("/etc/environment", r"^\s*MESA_SHADER_CACHE_MAX_SIZE=.*")
        self.log("✓ MESA cache removed", "success"); return True
    def rollback_pipewire(self, params=None):
        self._rm(os.path.join(self.state.user_home, ".config", "pipewire",
                              "pipewire.conf.d", "10-sound.conf"))
        self.log("✓ PipeWire config removed", "success"); return True
    def rollback_swap(self, params=None):
        self._rm("/etc/sysctl.d/99-gaming-swap.conf")
        self.sudo_run(["sysctl", "-w", "vm.swappiness=60"], ignore_error=True)
        self.log("✓ swappiness back to 60", "success"); return True
    def rollback_sysctl(self, params=None):
        self._rm("/etc/sysctl.d/99-gaming-sysctl.conf")
        self.sudo_run(["sysctl", "-w", "vm.vfs_cache_pressure=100"], ignore_error=True)
        self.sudo_run(["sysctl", "-w", "kernel.numa_balancing=1"], ignore_error=True)
        self.log("✓ sysctl back to defaults", "success"); return True
    def rollback_ntsync(self, params=None):
        self._rm("/etc/modules-load.d/ntsync.conf")
        self.log("✓ ntsync removed", "success"); return True
    def rollback_ntfs3(self, params=None):
        path = "/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"
        content = self.read_file(path)
        if not content:
            self.log("File not found: %s" % path, "info"); return True
        if re.search(r"^\s*blacklist\s+ntfs3\s*$", content, re.M):
            self.log("ntfs3 already blocked", "info"); return True
        new = re.sub(r"^\s*#\s*blacklist\s+ntfs3\s*$", "blacklist ntfs3",
                     content, flags=re.M)
        self.backup_file(path)
        if self.write_file(path, new, backup=False):
            self.log("✓ ntfs3 blocked again", "success"); return True
        return False
    def rollback_aliases(self, params=None):
        bashrc = os.path.join(self.state.user_home, ".bashrc")
        content = self.read_file(bashrc)
        if not content:
            self.log(".bashrc not found", "info"); return True
        sm = "# >>> system-tuneup commands >>>"
        em = "# <<< system-tuneup commands <<<"
        lines, skip = [], False
        for line in content.splitlines():
            if line.strip() == sm:
                skip = True; continue
            if line.strip() == em:
                skip = False; continue
            if not skip:
                lines.append(line)
        if len(lines) == len(content.splitlines()):
            self.log("Command block not found", "info"); return True
        self.backup_file(bashrc)
        if self.write_file(bashrc, "\n".join(lines) + "\n", backup=False):
            self.log("✓ commands removed from .bashrc", "success"); return True
        return False
    def rollback_autoupdate(self, params=None):
        return self.apply_autoupdate({"update_schedule": "Отключено"})

# ─── сигналы и потоки ────────────────────────────────────────────────────
class Sig(QObject):
    log = pyqtSignal(str, str)
    statusbar = pyqtSignal(str)
    progress = pyqtSignal(int)
    running = pyqtSignal(bool)
    applied = pyqtSignal(dict)
    mount_applied = pyqtSignal(dict)
    steam_applied = pyqtSignal(dict)
    schedule = pyqtSignal(str)
    services_rows = pyqtSignal(list)
    status_html = pyqtSignal(str)
    toast = pyqtSignal(str, str)

class Task(QThread):
    def __init__(self, fn):
        super().__init__(); self.fn = fn
    def run(self):
        try:
            self.fn()
        except Exception:
            traceback.print_exc()

# ─── виджеты с анимацией ─────────────────────────────────────────────────
class StripeProgress(QWidget):
    """Прогресс-бар с бегущими диагональными полосками."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0; self._off = 0
        self.setMinimumHeight(14); self.setMaximumHeight(14)
        t = QTimer(self); t.timeout.connect(self._tick); t.start(50)
    def set_value(self, v):
        self._value = max(0, min(100, v)); self.update()
    def _tick(self):
        if 0 < self._value < 100:
            self._off = (self._off + 2) % 28
            self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        th = self.theme_colors
        p.setBrush(QColor(th["panel"])); p.drawRoundedRect(self.rect(), 7, 7)
        w = int(self.width() * self._value / 100.0)
        if w > 2:
            g = QLinearGradient(0, 0, self.width(), 0)
            g.setColorAt(0, QColor(th["accent"])); g.setColorAt(1, QColor(th["accent2"]))
            p.setBrush(g); p.drawRoundedRect(QRect(0, 0, w, self.height()), 7, 7)
            p.setClipRect(0, 0, w, self.height())
            p.setBrush(QColor(255, 255, 255, 45))
            h = self.height()
            for x in range(-28, self.width() + 28, 28):
                path = QPainterPath()
                path.moveTo(x + self._off, h); path.lineTo(x + self._off + 9, h)
                path.lineTo(x + self._off + 9 + 12, 0); path.lineTo(x + self._off + 12, 0)
                path.closeSubpath(); p.drawPath(path)
        p.end()

class LogoWidget(QWidget):
    """Медленно вращающаяся шестерёнка-логотип."""
    def __init__(self, size=34, parent=None):
        super().__init__(parent); self.setFixedSize(size, size)
        self._angle = 0.0; self._size = size
        t = QTimer(self); t.timeout.connect(self._spin); t.start(45)
    def _spin(self):
        self._angle = (self._angle + 1.2) % 360; self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self._size / 2, self._size / 2); p.rotate(self._angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(_gear_path(0, 0, self._size * 0.42),
                   QBrush(QColor(self.theme_accent)))
        p.end()

class Toast(QFrame):
    """Всплывающее уведомление справа сверху с fade+slide."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        lay = QHBoxLayout(self); lay.setContentsMargins(16, 12, 16, 12)
        self.icon_lbl = QLabel(); self.icon_lbl.setFixedSize(22, 22)
        self.text_lbl = QLabel(); self.text_lbl.setWordWrap(True)
        lay.addWidget(self.icon_lbl); lay.addWidget(self.text_lbl, 1)
        self._eff = QGraphicsOpacityEffect(self); self.setGraphicsEffect(self._eff)
        self._anim = QPropertyAnimation(self._eff, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._timer = QTimer(self); self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_anim)
        self.hide()
    def show_msg(self, text, kind, colors):
        self.text_lbl.setText(text)
        col = colors["green"] if kind == "ok" else colors["red"] if kind == "err" \
            else colors["yellow"]
        self.text_lbl.setStyleSheet("color: %s; font-weight: bold;" % col)
        self.icon_lbl.setPixmap(make_icon(
            "apply" if kind == "ok" else "rollback" if kind == "err" else "help",
            22, col, col))
        self.adjustSize()
        pw = self.parentWidget()
        self.move(pw.width() - self.width() - 16, 60)
        self.show(); self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0); self._anim.setEndValue(1.0); self._anim.start()
        self._timer.start(2600)
    def hide_anim(self):
        self._anim.stop()
        self._anim.setStartValue(1.0); self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._done, Qt.ConnectionType.UniqueConnection)
        self._anim.start()
    def _done(self):
        if self._anim.currentValue() < 0.05:
            self.hide()

# ─── главное окно ────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sig = Sig()
        self.lang = detect_lang()
        self.theme = "dark"
        self.is_running = False
        self.opts_state = {k: False for k in OPTIONS_META}
        self.mount_state = {}; self.steam_state = {}
        self.applied = {}; self.mount_applied = {}; self.steam_applied = {}
        self.badges = {}; self.mount_badges = {}; self.steam_badges = {}
        self._anims = []
        self.sudo = SudoManager()
        self.sudo.prompt_password = self._ask_password
        self.sudo.show_error = lambda m: QMessageBox.warning(self, "sudo", m)
        self.state = SystemState(); self.state.detect()
        self.corectrl_group = (self.state.user_name if self.state.user_name != "root"
                               else "sudo")
        self.swap_value = "150" if self.state.swap_type == "zram" else "10"
        self.schedule_value = self._schedule_values()[2]
        mounts = []; seen = set()
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
        self.mount_items = mounts
        for m in mounts:
            self.mount_state[m["mps"][0]] = False
        self.steam_items = []
        for lib in find_steam_libraries(self.state.user_home):
            if self._lib_on_ntfs(lib):
                self.steam_items.append(lib)
                self.steam_state[lib] = False
        screens = QApplication.primaryScreen().availableGeometry()
        self.screen_w, self.screen_h = screens.width(), screens.height()
        self.sig.log.connect(self._on_log)
        self.sig.statusbar.connect(self._on_statusbar)
        self.sig.progress.connect(self._on_progress)
        self.sig.running.connect(self._on_running)
        self.sig.applied.connect(self._on_applied)
        self.sig.mount_applied.connect(self._on_mount_applied)
        self.sig.steam_applied.connect(self._on_steam_applied)
        self.sig.schedule.connect(self._on_schedule)
        self.sig.services_rows.connect(self._on_services_rows)
        self.sig.status_html.connect(self._on_status_html)
        self.sig.toast.connect(self._on_toast)
        self.build_ui()
        self.log("%s v%s запущен" % (APP_NAME, APP_VERSION), "success")
        self.log("GPU: %s %s" % (self.state.gpu, self.state.gpu_model), "info")
        QTimer.singleShot(300, self.refresh_services)
        QTimer.singleShot(600, self.refresh_applied)
        QTimer.singleShot(900, self.refresh_status)

    # ─── helpers ───
    def t(self, k):
        return STR[self.lang][k]
    def om(self, k):
        return OPTIONS_META[k][self.lang]
    def colors(self):
        return THEMES[self.theme]
    def _ask_password(self, attempt):
        text, ok = QInputDialog.getText(self, "sudo",
                                        "Password (attempt %d/3):" % attempt,
                                        QLineEdit.EchoMode.Password)
        return text if ok else None
    def _schedule_values(self):
        if self.lang == "ru":
            return ("Отключено", "Ежедневно", "Еженедельно (суббота)",
                    "2 раза в месяц (1 и 15)", "Ежемесячно (1 число)")
        return ("Disabled", "Daily", "Weekly (Saturday)",
                "Twice a month (1 & 15)", "Monthly (1st)")
    def _lib_on_ntfs(self, lib):
        best, dev, fstype = "", "", ""
        for it in parse_mounts():
            mp = it["mp"]
            if lib == mp or lib.startswith(mp.rstrip("/") + "/") or mp == "/":
                if len(mp) > len(best):
                    best, dev, fstype = mp, it["dev"], it["fstype"]
        if fstype in ("ntfs", "ntfs3", "fuseblk"):
            return True
        if fstype in ("auto", ""):
            try:
                res = subprocess.run(["lsblk", "-no", "FSTYPE", dev],
                                     capture_output=True, text=True, timeout=5)
                fstype = res.stdout.strip().splitlines()[0] if res.stdout.strip() else ""
            except Exception:
                fstype = ""
        return fstype in ("ntfs", "ntfs3", "fuseblk")
    def log(self, msg, tag="normal"):
        self.sig.log.emit(msg, tag)
    def toast(self, text, kind="ok"):
        self.sig.toast.emit(text, kind)

    # ─── UI build ───
    def build_ui(self):
        c = self.colors()
        self.setStyleSheet(QSS.format(**c))
        self.setWindowTitle("%s v%s" % (APP_NAME, APP_VERSION))
        self.setWindowIcon(QIcon(make_icon("logo", 64)))
        central = QWidget(); central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)
        # header
        head = QHBoxLayout(); head.setSpacing(10)
        self.logo = LogoWidget(34); self.logo.theme_accent = c["accent"]
        head.addWidget(self.logo)
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: %s;" % c["accent"])
        head.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setStyleSheet("color: %s;" % c["gray"])
        head.addWidget(ver)
        head.addStretch(1)
        self.dry_check = QCheckBox(self.t("lbl_dry"))
        self.dry_check.setStyleSheet("font-weight: bold; color: %s;" % c["yellow"])
        head.addWidget(self.dry_check)
        self.lang_btn = QPushButton("EN" if self.lang == "ru" else "RU")
        self.lang_btn.setFixedWidth(46)
        self.lang_btn.clicked.connect(self.toggle_lang)
        head.addWidget(self.lang_btn)
        self.theme_btn = QPushButton(self.t("theme_light") if self.theme == "dark"
                                     else self.t("theme_dark"))
        self.theme_btn.clicked.connect(self.toggle_theme)
        head.addWidget(self.theme_btn)
        root.addLayout(head)
        # tabs
        self.tabs = QTabWidget()
        self.tabs.setTabIcon(0, QIcon())
        root.addWidget(self.tabs, 1)
        self.tab_tune = QWidget(); self.tab_serv = QWidget(); self.tab_stat = QWidget()
        self.tabs.addTab(self.tab_tune, QIcon(make_icon("gear", 40, c["accent"])),
                         self.t("tab_tune"))
        self.tabs.addTab(self.tab_serv, QIcon(make_icon("services", 40, c["blue"])),
                         self.t("tab_serv"))
        self.tabs.addTab(self.tab_stat, QIcon(make_icon("status", 40, c["green"])),
                         self.t("tab_stat"))
        self.tabs.currentChanged.connect(self._fade_tab)
        self._build_tune(); self._build_serv(); self._build_stat()
        # bottom bar
        bar = QHBoxLayout(); bar.setSpacing(8)
        self.apply_btn = QPushButton(self.t("btn_apply"))
        self.apply_btn.setObjectName("accent")
        self.apply_btn.setIcon(QIcon(make_icon("apply", 36, c["accent"], c["accent_fg"])))
        self.apply_btn.clicked.connect(self.apply_selected)
        bar.addWidget(self.apply_btn)
        rb = QPushButton(self.t("btn_rollback"))
        rb.setIcon(QIcon(make_icon("rollback", 36, c["orange"])))
        rb.clicked.connect(self.rollback_selected)
        bar.addWidget(rb)
        sa = QPushButton(self.t("btn_selall"))
        sa.clicked.connect(self.select_all_options)
        bar.addWidget(sa)
        sn = QPushButton(self.t("btn_selnone"))
        sn.clicked.connect(self.reset_options)
        bar.addWidget(sn)
        bar.addStretch(1)
        ex = QPushButton(self.t("btn_export"))
        ex.setIcon(QIcon(make_icon("export", 36, c["blue"])))
        ex.clicked.connect(self.export_config)
        bar.addWidget(ex)
        ab = QPushButton(self.t("btn_about"))
        ab.setIcon(QIcon(make_icon("help", 36, c["yellow"])))
        ab.clicked.connect(self.show_about)
        bar.addWidget(ab)
        root.addLayout(bar)
        # terminal + status
        tl = QLabel(self.t("lbl_terminal"))
        tl.setStyleSheet("color: %s;" % c["gray"])
        root.addWidget(tl)
        self.terminal = QTextEdit(); self.terminal.setReadOnly(True)
        self.terminal.setMaximumHeight(150)
        self.terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.terminal.customContextMenuRequested.connect(self._copy_menu)
        root.addWidget(self.terminal)
        sb = QHBoxLayout()
        self.status_lbl = QLabel(self.t("ready"))
        self.status_lbl.setStyleSheet("color: %s;" % c["gray"])
        sb.addWidget(self.status_lbl)
        sb.addStretch(1)
        self.progress = StripeProgress()
        self.progress.theme_colors = c
        self.progress.setFixedWidth(220)
        sb.addWidget(self.progress)
        root.addLayout(sb)
        # toast
        self.toast_w = Toast(central)
        self.resize(min(1080, self.screen_w - 40), min(820, self.screen_h - 40))

    def _fade_tab(self, idx):
        w = self.tabs.widget(idx)
        eff = QGraphicsOpacityEffect(w); w.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(180); anim.setStartValue(0.25); anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: w.setGraphicsEffect(None))
        self._anims.append(anim); anim.start()

    def _build_tune(self):
        lay = QVBoxLayout(self.tab_tune); lay.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); vl = QVBoxLayout(inner)
        vl.setContentsMargins(4, 4, 4, 4); vl.setSpacing(2)
        cats = {}
        for k in OPTIONS_META:
            cats.setdefault(self.om(k)[2], []).append(k)
        order = CAT_ORDER[self.lang]
        seq = [x for x in order if x in cats] + \
              [x for x in sorted(cats) if x not in order]
        c = self.colors()
        for cat in seq:
            h = QLabel("─── %s ───" % cat)
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;" % c["yellow"])
            vl.addWidget(h); vl.addSpacing(2)
            for k in cats[cat]:
                vl.addWidget(self._option_row(k))
            if cat == self.om("ntfs3")[2]:
                self._disk_extras(vl, c)
        vl.addStretch(1)
        scroll.setWidget(inner); lay.addWidget(scroll)

    def _option_row(self, key):
        c = self.colors()
        row = QFrame(); row.setObjectName("optrow")
        vl = QVBoxLayout(row); vl.setContentsMargins(8, 6, 8, 6); vl.setSpacing(2)
        top = QHBoxLayout(); top.setSpacing(8)
        label, desc, _cat, _short = self.om(key)
        cb = QCheckBox(label)
        cb.setChecked(self.opts_state[key])
        cb.toggled.connect(lambda v, k=key: self.opts_state.__setitem__(k, v))
        top.addWidget(cb)
        if key == "corectrl":
            top.addWidget(QLabel(self.t("lbl_group")))
            le = QLineEdit(self.corectrl_group); le.setFixedWidth(120)
            le.textChanged.connect(lambda v: setattr(self, "corectrl_group", v))
            top.addWidget(le)
        elif key == "swap":
            top.addWidget(QLabel(self.t("lbl_value")))
            le = QLineEdit(self.swap_value); le.setFixedWidth(60)
            le.textChanged.connect(lambda v: setattr(self, "swap_value", v))
            top.addWidget(le)
        elif key == "autoupdate":
            top.addWidget(QLabel(self.t("lbl_schedule")))
            combo = QComboBox(); combo.addItems(self._schedule_values())
            combo.setCurrentText(self.schedule_value)
            combo.currentTextChanged.connect(lambda v: setattr(self, "schedule_value", v))
            top.addWidget(combo)
            self.sched_lbl = QLabel()
            self.sched_lbl.setStyleSheet("color: %s;" % c["gray"])
            top.addWidget(self.sched_lbl)
        badge = QLabel()
        badge.setObjectName("badge_no"); badge.setText(self.t("applied_no"))
        top.addWidget(badge)
        self.badges[key] = badge
        fb = QPushButton(self.t("btn_file"))
        fb.setIcon(QIcon(make_icon("file", 30, c["blue"])))
        fb.setFixedHeight(26)
        fb.clicked.connect(lambda _c, k=key: self.open_option_file(k))
        top.addWidget(fb)
        top.addStretch(1)
        vl.addLayout(top)
        dl = QLabel(desc); dl.setWordWrap(True)
        dl.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
        vl.addWidget(dl)
        return row

    def _disk_extras(self, vl, c):
        if self.mount_items:
            vl.addSpacing(6)
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: %s;" % c["border"]); vl.addWidget(sep)
            h = QLabel("─── %s ───" % self.t("mount_title"))
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;" % c["yellow"])
            vl.addWidget(h)
            d = QLabel(self.t("mount_desc")); d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            vl.addWidget(d)
            for m in self.mount_items:
                key = m["mps"][0]
                row = QFrame(); row.setObjectName("optrow")
                hl = QHBoxLayout(row); hl.setContentsMargins(8, 4, 8, 4)
                cb = QCheckBox("%s (%s)" % (", ".join(m["mps"]), m["dev"]))
                cb.setChecked(self.mount_state.get(key, False))
                cb.toggled.connect(lambda v, k=key: self.mount_state.__setitem__(k, v))
                hl.addWidget(cb)
                badge = QLabel(self.t("applied_no")); badge.setObjectName("badge_no")
                hl.addWidget(badge); self.mount_badges[key] = badge
                hl.addStretch(1)
                vl.addWidget(row)
        if self.steam_items:
            vl.addSpacing(6)
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: %s;" % c["border"]); vl.addWidget(sep)
            h = QLabel("─── %s ───" % self.t("steam_title"))
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;" % c["yellow"])
            vl.addWidget(h)
            d = QLabel(self.t("steam_desc")); d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            vl.addWidget(d)
            for lib in self.steam_items:
                row = QFrame(); row.setObjectName("optrow")
                hl = QHBoxLayout(row); hl.setContentsMargins(8, 4, 8, 4)
                cb = QCheckBox(lib)
                cb.setChecked(self.steam_state.get(lib, False))
                cb.toggled.connect(lambda v, k=lib: self.steam_state.__setitem__(k, v))
                hl.addWidget(cb)
                badge = QLabel(self.t("applied_no")); badge.setObjectName("badge_no")
                hl.addWidget(badge); self.steam_badges[lib] = badge
                hl.addStretch(1)
                vl.addWidget(row)

    def _build_serv(self):
        lay = QVBoxLayout(self.tab_serv); lay.setContentsMargins(8, 8, 8, 8)
        btns = QHBoxLayout(); btns.setSpacing(8)
        c = self.colors()
        for txt, fn, ic in ((self.t("btn_selall"), self.select_all_services, "select"),
                            (self.t("btn_selnone"), self.clear_services_selection, "clear"),
                            (self.t("svc_off_sel"), self.disable_selected, "rollback"),
                            (self.t("svc_on_sel"), self.enable_selected, "apply")):
            b = QPushButton(txt)
            b.setIcon(QIcon(make_icon("apply" if ic == "apply" else
                            "rollback" if ic == "rollback" else "services",
                            32, c["accent"] if ic == "apply" else
                            c["orange"] if ic == "rollback" else c["blue"])))
            b.clicked.connect(fn); btns.addWidget(b)
        btns.addStretch(1)
        lay.addLayout(btns)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([self.t("svc_name"), self.t("svc_state"),
                                              self.t("svc_run"), self.t("svc_desc")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._serv_detail)
        lay.addWidget(self.table, 1)
        self.serv_hint = QLabel(self.t("svc_hint"))
        self.serv_hint.setStyleSheet("color: %s;" % c["gray"])
        lay.addWidget(self.serv_hint)
        self.serv_detail = QTextEdit(); self.serv_detail.setReadOnly(True)
        self.serv_detail.setMaximumHeight(80)
        self.serv_detail.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.serv_detail.customContextMenuRequested.connect(self._copy_menu)
        lay.addWidget(self.serv_detail)

    def _build_stat(self):
        lay = QVBoxLayout(self.tab_stat); lay.setContentsMargins(8, 8, 8, 8)
        b = QPushButton(self.t("stat_refresh"))
        b.setIcon(QIcon(make_icon("status", 32, self.colors()["green"])))
        b.clicked.connect(self.refresh_status)
        lay.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        self.stat_view = QTextEdit(); self.stat_view.setReadOnly(True)
        self.stat_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stat_view.customContextMenuRequested.connect(self._copy_menu)
        lay.addWidget(self.stat_view, 1)

    # ─── actions ───
    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._rebuild()
    def toggle_lang(self):
        ru = ("Отключено", "Ежедневно", "Еженедельно (суббота)",
              "2 раза в месяц (1 и 15)", "Ежемесячно (1 число)")
        en = ("Disabled", "Daily", "Weekly (Saturday)",
              "Twice a month (1 & 15)", "Monthly (1st)")
        cur = self.schedule_value
        self.lang = "en" if self.lang == "ru" else "ru"
        self.schedule_value = (dict(zip(en, ru)) if self.lang == "ru"
                               else dict(zip(ru, en))).get(cur, cur)
        self._rebuild()
    def _rebuild(self):
        self.badges = {}; self.mount_badges = {}; self.steam_badges = {}
        old = self.centralWidget()
        self.build_ui()
        if old is not None:
            old.deleteLater()
        self._update_badges()
        self.refresh_services(); self.refresh_status(); self.refresh_applied()
    def _copy_menu(self, pos):
        w = self.sender()
        menu = QMenu(self)
        a1 = menu.addAction(self.t("copy"))
        a1.triggered.connect(lambda: self._copy_sel(w))
        a2 = menu.addAction(self.t("copy_all"))
        a2.triggered.connect(lambda: QApplication.clipboard().setText(
            w.toPlainText()))
        a3 = menu.addAction(self.t("sel_all_txt"))
        a3.triggered.connect(lambda: w.selectAll())
        menu.exec(w.mapToGlobal(pos))
    def _copy_sel(self, w):
        cur = w.textCursor()
        if cur.hasSelection():
            QApplication.clipboard().setText(cur.selectedText())
    def open_option_file(self, key):
        cands = [p.format(home=self.state.user_home) for p in OPTION_FILES.get(key, [])]
        target = next((p for p in cands if os.path.exists(p)), None)
        if target is None and cands:
            if not self.sudo._cached():
                if not self.sudo.ensure():
                    return
            target = next((p for p in cands if self.sudo.run and os.path.exists(p)
                           or subprocess.run(["sudo", "-n", "test", "-e", p],
                                             capture_output=True).returncode == 0), None)
        if target is None:
            QMessageBox.information(self, self.t("viewer"),
                                    self.t("msg_nofile") + "\n" + "\n".join(cands))
            return
        ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
        content = ops.read_file(target) or ""
        dlg = QDialog(self)
        dlg.setWindowTitle("%s: %s" % (self.t("viewer"), target))
        dlg.resize(720, 520)
        vl = QVBoxLayout(dlg)
        te = QTextEdit(); te.setReadOnly(True); te.setPlainText(content)
        te.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        te.customContextMenuRequested.connect(
            lambda p, w=te: self._copy_menu_te(w, p))
        vl.addWidget(te)
        b = QPushButton(self.t("viewer_ext"))
        b.clicked.connect(lambda: self._open_ext(target))
        vl.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        dlg.exec()
    def _copy_menu_te(self, w, pos):
        self._copy_menu(pos) if False else None
        menu = QMenu(self)
        a1 = menu.addAction(self.t("copy"))
        a1.triggered.connect(lambda: self._copy_sel(w))
        a2 = menu.addAction(self.t("copy_all"))
        a2.triggered.connect(lambda: QApplication.clipboard().setText(w.toPlainText()))
        menu.exec(w.mapToGlobal(pos))
    def _open_ext(self, path):
        env = {k: v for k, v in os.environ.items()
               if k not in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONPATH",
                            "PYTHONHOME", "APPDIR", "APPIMAGE")}
        for cmd in (["xdg-open", path], ["gio", "open", path], ["xed", path],
                    ["gedit", path], ["mousepad", path], ["kate", path]):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True, env=env)
                return
            except Exception:
                continue
        self.log("Cannot open external editor for %s" % path, "error")
    def select_all_options(self):
        for k in self.opts_state:
            self.opts_state[k] = True
        for k in self.mount_state:
            self.mount_state[k] = True
        for k in self.steam_state:
            self.steam_state[k] = True
        self._rebuild_checks()
    def reset_options(self):
        for k in self.opts_state:
            self.opts_state[k] = False
        for k in self.mount_state:
            self.mount_state[k] = False
        for k in self.steam_state:
            self.steam_state[k] = False
        self._rebuild_checks()
    def _rebuild_checks(self):
        self._rebuild()
    def select_all_services(self):
        self.table.selectAll()
    def clear_services_selection(self):
        self.table.clearSelection()
    def _serv_detail(self):
        items = self.table.selectedItems()
        names = []
        for it in items:
            if it.column() == 0:
                names.append(it.text())
        parts = ["%s — %s" % (n, SERVICES_META.get(n, {}).get(self.lang, ""))
                 for n in names[:3]]
        self.serv_detail.setPlainText("\n\n".join(parts))
    def apply_selected(self):
        if self.is_running:
            QMessageBox.information(self, self.t("running"), self.t("msg_run")); return
        selected = [k for k, v in self.opts_state.items() if v]
        mount_sel = [mp for m in self.mount_items if self.mount_state.get(m["mps"][0])
                     for mp in m["mps"]]
        steam_sel = [l for l in self.steam_items if self.steam_state.get(l)]
        if not selected and not mount_sel and not steam_sel:
            QMessageBox.warning(self, APP_NAME, self.t("msg_noopt")); return
        params = {"corectrl_group": self.corectrl_group,
                  "swap_value": self.swap_value,
                  "update_schedule": self.schedule_value}
        dry = self.dry_check.isChecked()
        if not dry and not self.sudo.ensure():
            self.log("sudo failed", "error"); return
        self.is_running = True
        self.apply_btn.setEnabled(False)
        self.sig.running.emit(True); self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        def work():
            ops = SystemOps(self.sudo, self.state,
                            lambda m, t: self.sig.log.emit(m, t), dry)
            total = len(selected) + (1 if mount_sel else 0) + (1 if steam_sel else 0)
            done = 0
            self.sig.log.emit("=" * 60, "highlight")
            self.sig.log.emit("ЗАПУСК ТЮНИНГА" if self.lang == "ru" else "APPLY START",
                              "highlight")
            for k in selected:
                self.sig.log.emit("→ %s" % self.om(k)[0], "info")
                try:
                    getattr(ops, "apply_%s" % k)(params)
                except Exception as e:
                    self.sig.log.emit("Error in %s: %s" % (k, e), "error")
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if mount_sel:
                ops.apply_mount_opts(mount_sel)
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if steam_sel:
                ops.apply_steam_links(steam_sel)
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if not dry:
                ops.finalize_grub()
            self.sig.progress.emit(100)
            self.sig.statusbar.emit(self.t("done"))
            self.sig.log.emit("Done", "success")
            self.sig.toast.emit(self.t("done"), "ok")
            self.refresh_applied(); self.refresh_status(); self.refresh_services()
        t = Task(work); t.finished.connect(lambda: self.sig.running.emit(False))
        self._task = t; t.start()
    def rollback_selected(self):
        if self.is_running:
            QMessageBox.information(self, self.t("running"), self.t("msg_run")); return
        selected = [k for k, v in self.opts_state.items() if v]
        mount_sel = [mp for m in self.mount_items if self.mount_state.get(m["mps"][0])
                     for mp in m["mps"]]
        steam_sel = [l for l in self.steam_items if self.steam_state.get(l)]
        if not selected and not mount_sel and not steam_sel:
            QMessageBox.warning(self, APP_NAME, self.t("msg_noopt")); return
        dry = self.dry_check.isChecked()
        if not dry and not self.sudo.ensure():
            self.log("sudo failed", "error"); return
        self.is_running = True
        self.apply_btn.setEnabled(False)
        self.sig.running.emit(True); self.sig.progress.emit(0)
        def work():
            ops = SystemOps(self.sudo, self.state,
                            lambda m, t: self.sig.log.emit(m, t), dry)
            total = len(selected) + (1 if mount_sel else 0) + (1 if steam_sel else 0)
            done = 0
            self.sig.log.emit("ЗАПУСК ОТКАТА" if self.lang == "ru" else "ROLLBACK START",
                              "highlight")
            for k in selected:
                self.sig.log.emit("→ %s" % self.om(k)[0], "info")
                try:
                    getattr(ops, "rollback_%s" % k)()
                except Exception as e:
                    self.sig.log.emit("Error in %s: %s" % (k, e), "error")
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if mount_sel:
                ops.rollback_mount_opts(mount_sel)
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if steam_sel:
                ops.rollback_steam_links(steam_sel)
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if not dry:
                ops.finalize_grub()
            self.sig.progress.emit(100)
            self.sig.log.emit("Rollback done", "success")
            self.sig.toast.emit(self.t("done"), "ok")
            self.refresh_applied(); self.refresh_status(); self.refresh_services()
        t = Task(work); t.finished.connect(lambda: self.sig.running.emit(False))
        self._task = t; t.start()
    def enable_selected(self):
        if self.is_running:
            QMessageBox.information(self, self.t("running"), self.t("msg_run")); return
        names = [self.table.item(i, 0).text()
                 for i in range(self.table.rowCount())
                 if self.table.item(i, 0).isSelected()]
        if not names:
            QMessageBox.information(self, APP_NAME, self.t("msg_sel")); return
        if not self.sudo.ensure():
            return
        def work():
            ops = SystemOps(self.sudo, self.state,
                            lambda m, t: self.sig.log.emit(m, t),
                            self.dry_check.isChecked())
            for n in names:
                ops.sudo_run(["systemctl", "unmask", n], ignore_error=True)
                ok = ops.sudo_run(["systemctl", "enable", n], ignore_error=True)
                ops.log("✓ %s enabled" % n if ok else "Cannot enable %s" % n,
                        "success" if ok else "warning")
            self.refresh_services()
        self._task = Task(work); self._task.start()
    def disable_selected(self):
        if self.is_running:
            QMessageBox.information(self, self.t("running"), self.t("msg_run")); return
        names = [self.table.item(i, 0).text()
                 for i in range(self.table.rowCount())
                 if self.table.item(i, 0).isSelected()]
        if not names:
            QMessageBox.information(self, APP_NAME, self.t("msg_sel")); return
        if not self.sudo.ensure():
            return
        def work():
            ops = SystemOps(self.sudo, self.state,
                            lambda m, t: self.sig.log.emit(m, t),
                            self.dry_check.isChecked())
            for n in names:
                ok = ops.sudo_run(["systemctl", "disable", "--now", n],
                                  ignore_error=True)
                if n.startswith("avahi"):
                    ok = ops.sudo_run(["systemctl", "mask", n],
                                      ignore_error=True) or ok
                ops.log("✓ %s disabled" % n if ok else "Cannot disable %s" % n,
                        "success" if ok else "warning")
            self.refresh_services()
        self._task = Task(work); self._task.start()
    def export_config(self):
        selected = [k for k, v in self.opts_state.items() if v]
        if not selected:
            QMessageBox.information(self, APP_NAME, self.t("msg_noopt")); return
        path, _ = QFileDialog.getSaveFileName(self, self.t("btn_export"),
                                              os.path.expanduser("~/tweaker-config.txt"),
                                              "Text files (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("%s v%s\n%s\n\n" % (APP_NAME, APP_VERSION,
                                            time.strftime("%Y-%m-%d %H:%M:%S")))
                for k in selected:
                    f.write("%s: %s\n" % (k, self.om(k)[0]))
            self.log("Config saved: %s" % path, "success")
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
    def show_about(self):
        c = self.colors()
        dlg = QDialog(self); dlg.setWindowTitle(self.t("about_title"))
        dlg.resize(680, 560)
        vl = QVBoxLayout(dlg)
        te = QTextEdit(); te.setReadOnly(True)
        html = ('<div style="font-family: monospace;">'
                '<h2 style="color:%s;">%s</h2>'
                '<p><b>%s:</b> %s</p>'
                '<p>%s</p>'
                '<hr>'
                '<p style="color:%s; font-size:15px;"><b>%s:</b> %s</p>'
                '<hr><pre style="color:%s;">%s</pre></div>'
                % (c["accent"], APP_NAME + " v" + APP_VERSION,
                   self.t("about_ver"), APP_VERSION,
                   self.t("about_purpose"),
                   c["yellow"], self.t("about_author"), self.t("about_author_name"),
                   c["fg"], self.t("help_body")))
        te.setHtml(html)
        vl.addWidget(te)
        dlg.exec()

    # ─── refresh / detect ───
    def refresh_applied(self):
        def work():
            ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
            self.sig.applied.emit(self._detect_applied(ops))
            self.sig.mount_applied.emit(self._detect_mount())
            self.sig.steam_applied.emit(self._detect_steam())
            self.sig.schedule.emit(self._schedule_text())
        self._task = Task(work); self._task.start()
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
                 "Sat 18:30:00": ("Еженедельно (суббота)", "Weekly (Saturday)"),
                 "*-*-1,15 18:30:00": ("2 раза в месяц (1 и 15)", "Twice a month"),
                 "*-*-1 18:30:00": ("Ежемесячно (1 число)", "Monthly (1st)")}
        pair = names.get(cal)
        return pair[0 if self.lang == "ru" else 1] if pair else cal
    def _corectrl_found(self, ops):
        for d in ("/etc/polkit-1/rules.d", "/usr/share/polkit-1/rules.d",
                  "/etc/polkit-1/localauthority/50-local.d"):
            try:
                names = os.listdir(d)
            except Exception:
                names = []
            for fn in names:
                if "corectrl" in fn.lower():
                    return True
                try:
                    with open(os.path.join(d, fn), "r",
                              encoding="utf-8", errors="replace") as f:
                        if "org.corectrl" in f.read():
                            return True
                except Exception:
                    continue
        for p in ("/etc/polkit-1/rules.d/90-corectrl.rules",
                  "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"):
            c = ops.read_file(p)
            if c and "org.corectrl" in c:
                return True
        try:
            res = subprocess.run(["pkcheck", "--action-id",
                                  "org.corectrl.helper.init", "--process",
                                  str(os.getpid())], capture_output=True, timeout=5)
            if res.returncode == 0:
                return True
        except Exception:
            pass
        return False
    def _detect_applied(self, ops):
        grub = ops.read_file("/etc/default/grub") or ""
        env = ops.read_file("/etc/environment") or ""
        j = ops.read_file("/etc/systemd/journald.conf") or ""
        swp = ops.read_file("/etc/sysctl.d/99-gaming-swap.conf") or ""
        sysc = ops.read_file("/etc/sysctl.d/99-gaming-sysctl.conf") or ""
        bashrc = ops.read_file(os.path.join(self.state.user_home, ".bashrc")) or ""
        mint = ops.read_file("/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf") or ""
        def sv(p):
            try:
                r = subprocess.run(["sysctl", "-n", p], capture_output=True,
                                   text=True, timeout=3)
                return r.stdout.strip() if r.returncode == 0 else ""
            except Exception:
                return ""
        pw = os.path.join(self.state.user_home, ".config", "pipewire",
                          "pipewire.conf.d", "10-sound.conf")
        return {"rsyslog": ops.service_enabled("rsyslog.service") in ("disabled", "masked"),
                "journald": bool(re.search(r"^\s*Storage\s*=\s*volatile\s*$", j, re.M)),
                "audit": "audit=0" in grub, "raid": "raid=noautodetect" in grub,
                "corectrl": self._corectrl_found(ops),
                "ppfeaturemask": "amdgpu.ppfeaturemask" in grub,
                "vrr": ops.path_exists("/etc/X11/xorg.conf.d/20-amdgpu.conf"),
                "radv": "RADV_PERFTEST=sam" in env, "pipewire": ops.path_exists(pw),
                "mesa": "MESA_SHADER_CACHE_MAX_SIZE=4G" in env,
                "swap": bool(swp) or "vm.swappiness" in sysc or sv("vm.swappiness") not in ("", "60"),
                "sysctl": bool(sysc) or (sv("vm.vfs_cache_pressure") == "50" and
                                         sv("kernel.numa_balancing") == "0"),
                "ntsync": self.state.ntsync or ops.path_exists("/etc/modules-load.d/ntsync.conf"),
                "ntfs3": bool(re.search(r"^\s*#\s*blacklist\s+ntfs3\s*$", mint, re.M)),
                "aliases": "system-tuneup" in bashrc,
                "autoupdate": ops.service_enabled("biweekly-upgrade.timer") == "enabled"}
    def _detect_mount(self):
        try:
            with open("/etc/fstab", "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            content = ""
        res = {}
        for m in self.mount_items:
            oks = []
            for mp in m["mps"]:
                ok = False
                for line in content.splitlines():
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    f = s.split()
                    if len(f) >= 4 and f[1] == mp:
                        opts = f[3].split(",")
                        ok = "noatime" in opts and "nodiratime" in opts
                        break
                oks.append(ok)
            res[m["mps"][0]] = all(oks)
        return res
    def _detect_steam(self):
        return {lib: os.path.islink(os.path.join(lib, "compatdata"))
                for lib in self.steam_items}
    def refresh_services(self):
        def work():
            ops = SystemOps(self.sudo, self.state, lambda m, t: None,
                            self.dry_check.isChecked())
            rows = []
            for n in SERVICES_ORDER:
                desc = SERVICES_META[n][self.lang]
                if not ops.unit_exists(n):
                    rows.append((n, self.t("svc_na"), self.t("svc_na"), desc, "gray"))
                    continue
                en = ops.service_enabled(n); ac = ops.service_active(n)
                if en == "masked":
                    st, tag, col = self.t("svc_masked"), "masked", "red"
                elif en == "disabled":
                    st, tag, col = self.t("svc_off"), "off", "gray"
                elif ac == "active":
                    st, tag, col = self.t("svc_on"), "on", "green"
                else:
                    st, tag, col = self.t("svc_onoff"), "onoff", "yellow"
                run = self.t("run_yes") if ac == "active" else self.t("run_no")
                rows.append((n, st, run, desc, col))
            self.sig.services_rows.emit(rows)
        self._task = Task(work); self._task.start()
    def refresh_status(self):
        def work():
            ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
            try:
                A = self._detect_applied(ops)
                self.sig.applied.emit(A)
            except Exception:
                A = self.applied
            c = self.colors()
            def col(k):
                return c[k]
            rows = []
            rows.append(("<h3 style='color:%s;'>%s</h3>" % (col("blue"), self.t("st_hw")), ""))
            name = ""
            try:
                with open("/etc/os-release", "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            name = line.split("=", 1)[1].strip().strip('"'); break
            except Exception:
                pass
            bits = 64 if sys.maxsize > 2 ** 32 else 32
            gpu = self.state.gpu + (" " + self.state.gpu_model if self.state.gpu_model else "")
            ram = ram_total_gb()
            ram_s = "%.1f %s" % (ram, self.t("gb")) if ram else "?"
            rows.append(("%s: %s (%d-bit)" % (self.t("os_lbl"), name or "Linux", bits), "info"))
            rows.append(("%s: %s" % (self.t("gpu_lbl"), gpu), "info"))
            rows.append(("%s: %s" % (self.t("ram_lbl"), ram_s), "info"))
            rows.append(("%s: %dx%d" % (self.t("screen_lbl"), self.screen_w,
                                        self.screen_h), "info"))
            swap_s = (self.state.swap_type if self.state.has_swap
                      else self.t("no_swap"))
            rows.append(("%s: %s" % (self.t("swap_lbl"), swap_s), "info"))
            rows.append(("%s: %s" % (self.t("kernel_lbl"), os.uname().release), "info"))
            rows.append(("%s: %s" % (self.t("de_lbl"), desktop_name()), "info"))
            rows.append(("%s: %s<br>%s: %s" % (self.t("user_lbl"), self.state.user_name,
                                               self.t("home_lbl"), self.state.user_home),
                         "info"))
            rows.append(("<h3 style='color:%s;'>%s</h3>" % (col("blue"),
                        self.t("st_tweaks")), ""))
            for k in OPTIONS_META:
                ok = A.get(k, False)
                cc = col("green") if ok else col("red")
                mm = self.t("yes") if ok else self.t("no")
                rows.append(("<span style='color:%s;'><b>%s</b></span>&nbsp; %s — %s"
                             % (cc, mm, self.om(k)[0], self.om(k)[3]), ""))
            for m in self.mount_items:
                ok = self.mount_applied.get(m["mps"][0], False)
                cc = col("green") if ok else col("red")
                rows.append(("<span style='color:%s;'><b>%s</b></span>&nbsp; %s — %s"
                             % (cc, self.t("yes") if ok else self.t("no"),
                                self.t("mount_short"), ", ".join(m["mps"])), ""))
            for lib in self.steam_items:
                ok = self.steam_applied.get(lib, False)
                cc = col("green") if ok else col("red")
                rows.append(("<span style='color:%s;'><b>%s</b></span>&nbsp; %s — %s"
                             % (cc, self.t("yes") if ok else self.t("no"),
                                self.t("steam_short"), lib), ""))
            rows.append(("<h3 style='color:%s;'>%s</h3>" % (col("blue"),
                        self.t("st_services")), ""))
            for n in SERVICES_ORDER:
                en = ops.service_enabled(n); ac = ops.service_active(n)
                if en == "masked":
                    cc, w = col("red"), self.t("svc_masked")
                elif en == "disabled":
                    cc, w = col("gray"), self.t("svc_off")
                elif en == "not-found":
                    cc, w = col("gray"), self.t("svc_na")
                elif ac == "active":
                    cc, w = col("green"), self.t("svc_on")
                else:
                    cc, w = col("yellow"), self.t("svc_onoff")
                rows.append(("<span style='color:%s;'>%s</span> — %s — %s"
                             % (cc, n, w, SERVICES_META[n][self.lang]), ""))
            rows.append(("<h3 style='color:%s;'>%s</h3>" % (col("blue"),
                        self.t("st_kernel")), ""))
            kern = [("vm.swappiness", self.t("kern_sw"), A.get("swap", False)),
                    ("vm.vfs_cache_pressure", self.t("kern_vfs"), A.get("sysctl", False)),
                    ("kernel.numa_balancing", self.t("kern_numa"), A.get("sysctl", False))]
            for p, dsc, ok in kern:
                try:
                    r = subprocess.run(["sysctl", "-n", p], capture_output=True,
                                       text=True, timeout=3)
                    val = r.stdout.strip() if r.returncode == 0 else "n/a"
                except Exception:
                    val = "n/a"
                cc = col("green") if ok else col("red")
                rows.append(("%s = <b>%s</b> — %s &nbsp;<span style='color:%s;'>[%s]</span>"
                             % (p, val, dsc, cc, self.t("yes") if ok else self.t("no")), ""))
            timer = ops.service_enabled("biweekly-upgrade.timer")
            cc = col("green") if timer == "enabled" else col("gray")
            rows.append(("%s: <span style='color:%s;'>%s</span>"
                         % (self.t("st_timer"), cc, timer), ""))
            html = "".join(("<p style='margin:2px 0;'>%s</p>" % r[0]) for r in rows)
            self.sig.status_html.emit(html)
    # ─── slot handlers ───
    def _on_log(self, msg, tag):
        c = self.colors()
        colors = {"normal": c["terminal_fg"], "success": c["green"], "error": c["red"],
                  "warning": c["yellow"], "info": c["blue"], "highlight": c["orange"]}
        self.terminal.append("<span style='color:%s;'>%s</span>"
                             % (colors.get(tag, c["terminal_fg"]),
                                msg.replace("&", "&amp;").replace("<", "&lt;")))
    def _on_statusbar(self, s):
        self.status_lbl.setText(s)
    def _on_progress(self, v):
        self.progress.set_value(v)
    def _on_running(self, r):
        self.is_running = r
        self.apply_btn.setEnabled(not r)
    def _on_applied(self, d):
        self.applied = d; self._update_badges()
    def _on_mount_applied(self, d):
        self.mount_applied = d; self._update_badges()
    def _on_steam_applied(self, d):
        self.steam_applied = d; self._update_badges()
    def _on_schedule(self, s):
        if hasattr(self, "sched_lbl"):
            self.sched_lbl.setText(self.t("sched_cur") % s)
    def _update_badges(self):
        for k, b in self.badges.items():
            ok = self.applied.get(k, False)
            b.setObjectName("badge_yes" if ok else "badge_no")
            b.setText(self.t("applied_yes") if ok else self.t("applied_no"))
            b.style().unpolish(b); b.style().polish(b)
        for k, b in self.mount_badges.items():
            ok = self.mount_applied.get(k, False)
            b.setObjectName("badge_yes" if ok else "badge_no")
            b.setText(self.t("applied_yes") if ok else self.t("applied_no"))
            b.style().unpolish(b); b.style().polish(b)
        for k, b in self.steam_badges.items():
            ok = self.steam_applied.get(k, False)
            b.setObjectName("badge_yes" if ok else "badge_no")
            b.setText(self.t("applied_yes") if ok else self.t("applied_no"))
            b.style().unpolish(b); b.style().polish(b)
    def _on_services_rows(self, rows):
        c = self.colors()
        self.table.setRowCount(0)
        for n, st, run, desc, col in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for ci, val in enumerate((n, st, run, desc)):
                it = QTableWidgetItem(val)
                it.setForeground(QColor(c[col]))
                self.table.setItem(r, ci, it)
    def _on_status_html(self, html):
        self.stat_view.setHtml(html)
    def _on_toast(self, text, kind):
        self.toast_w.show_msg(text, kind, self.colors())
    def closeEvent(self, e):
        if self.is_running:
            r = QMessageBox.question(self, APP_NAME, self.t("msg_run"))
            if r != QMessageBox.StandardButton.Yes:
                e.ignore(); return
        e.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
