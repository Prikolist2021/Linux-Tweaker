#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Tweaker v0.08
Графическая оболочка тюнинга Linux Mint / Ubuntu / Debian на PyQt6.
RU/EN, светлая/тёмная тема, детект применённых настроек,
откат, бэкапы, mount-опции, симлинки compatdata для Steam.
Диалоги справки: модальные, перетаскиваемые, без крашей.
"""
import sys, os, re, subprocess, time, shutil, glob, pwd, grp, threading, traceback
from PyQt6.QtCore import (Qt, QObject, QThread, pyqtSignal, QTimer,
                          QPropertyAnimation, QEasingCurve, QRect, QRectF)
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QPen, QBrush,
                         QPainterPath, QLinearGradient, QTransform, QTextCursor)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QCheckBox, QLineEdit, QComboBox, QTextEdit,
                             QTableWidget, QTableWidgetItem, QAbstractItemView,
                             QHeaderView, QScrollArea, QFrame, QInputDialog,
                             QMessageBox, QFileDialog, QMenu, QDialog,
                             QGraphicsOpacityEffect)

APP_NAME = "Linux Tweaker"
APP_VERSION = "0.08"
GITHUB_URL = "https://github.com/Prikolist2021/Linux-Tweaker"

THEMES = {
    "light": {"bg": "#f5f5f5", "panel": "#ffffff", "fg": "#1e1e1e", "gray": "#616161",
              "border": "#d0d0d0", "tab": "#e4e4e4", "tab_hover": "#d8d8d8",
              "accent": "#2e9e83", "accent2": "#268a72", "accent_fg": "#ffffff",
              "button": "#e4e4e4", "button_hover": "#d8d8d8", "button_dis": "#ececec",
              "fg_dis": "#9a9a9a", "entry": "#ffffff", "terminal": "#ffffff",
              "terminal_fg": "#1e1e1e", "sel": "#cde4f7", "scroll": "#b0b0b0",
              "row_hover": "#ececec", "green": "#2e7d32", "green_bg": "#e2f0e3",
              "gray_bg": "#e8e8e8", "red": "#c62828", "yellow": "#b26a00",
              "blue": "#1565c0", "orange": "#e65100"},
    "dark": {"bg": "#1e1e1e", "panel": "#252526", "fg": "#d4d4d4", "gray": "#9a9a9a",
             "border": "#3c3c3c", "tab": "#2d2d30", "tab_hover": "#38383d",
             "accent": "#4ec9b0", "accent2": "#3aa794", "accent_fg": "#10201c",
             "button": "#3a3d41", "button_hover": "#46494e", "button_dis": "#2d2d30",
             "fg_dis": "#6a6a6a", "entry": "#333333", "terminal": "#0c0c0c",
             "terminal_fg": "#d4d4d4", "sel": "#094771", "scroll": "#5a5a5a",
             "row_hover": "#2a2d2e", "green": "#4ec9b0", "green_bg": "#17352f",
             "gray_bg": "#2f2f2f", "red": "#f44747", "yellow": "#d7ba7d",
             "blue": "#569cd6", "orange": "#ce9178"},
}

OPTIONS_META = {
    "rsyslog": {
        "ru": ("Отключить rsyslog", "Система постоянно пишет подробные журналы на диск. На домашнем ПК это лишняя нагрузка: отключение экономит ресурс SSD и слегка ускоряет работу. Краткие журналы при этом остаются в памяти (см. следующий пункт).", "Логи системы", "запись подробных журналов rsyslog на диск"),
        "en": ("Disable rsyslog", "The system constantly writes detailed logs to disk. On a home PC this is unnecessary wear: disabling saves SSD life and slightly speeds things up. Short logs remain in RAM (see next item).", "System logs", "detailed rsyslog logging to disk")},
    "journald": {
        "ru": ("Логи в ОЗУ (journald)", "Переносит журналы systemd в оперативную память и ограничивает их 50 МБ. Диски не изнашиваются, старые логи не накапливаются годами.", "Логи системы", "хранение журналов systemd в ОЗУ (50 МБ)"),
        "en": ("Logs in RAM (journald)", "Moves systemd journals to RAM and caps them at 50 MB. No disk wear, old logs do not pile up for years.", "System logs", "systemd journals stored in RAM (50 MB)")},
    "audit": {
        "ru": ("audit=0 (GRUB)", "Отключает встроенный аудит ядра: система перестаёт протоколировать каждый системный вызов. Меньше накладных расходов — чуть быстрее загрузка и работа.", "Ядро и загрузка", "аудит ядра (audit=0)"),
        "en": ("audit=0 (GRUB)", "Disables kernel auditing: the kernel stops logging every syscall. Less overhead — slightly faster boot and runtime.", "Kernel & boot", "kernel auditing (audit=0)")},
    "raid": {
        "ru": ("raid=noautodetect (GRUB)", "Если у вас нет RAID-массива, при каждой загрузке система тратит время на его поиск. Параметр отключает этот поиск — загрузка быстрее.", "Ядро и загрузка", "поиск RAID при загрузке"),
        "en": ("raid=noautodetect (GRUB)", "If you have no RAID array, the system wastes boot time probing for one. This option skips the probe — faster boot.", "Kernel & boot", "RAID probing at boot")},
    "nmi_watchdog": {
        "ru": ("nmi_watchdog=0 (GRUB)", "Отключает NMI-watchdog ядра — периодические немаскируемые прерывания для отладки. Дома не нужны и дают микро-фризы в играх.", "Ядро и загрузка", "nmi_watchdog=0"),
        "en": ("nmi_watchdog=0 (GRUB)", "Disables the kernel NMI watchdog — periodic non-maskable debugging interrupts. Unneeded at home and can cause micro-stutters in games.", "Kernel & boot", "nmi_watchdog=0")},
    "corectrl": {
        "ru": ("CoreCtrl (Polkit)", "Правило Polkit для программы CoreCtrl: позволяет управлять частотами и вентиляторами видеокарты AMD без ввода пароля. В поле указывается группа пользователей, которым это разрешено (по умолчанию — ваша).", "Видеокарта и графика", "polkit-правило для CoreCtrl"),
        "en": ("CoreCtrl (Polkit)", "Polkit rule for CoreCtrl: allows controlling AMD GPU clocks and fans without a password. The field sets the user group allowed to do so (defaults to yours).", "GPU & graphics", "Polkit rule for CoreCtrl")},
    "ppfeaturemask": {
        "ru": ("amdgpu.ppfeaturemask", "Разблокирует скрытые возможности управления питанием AMD GPU (нужно на старых ядрах). Открывает CoreCtrl полный контроль над частотами.", "Видеокарта и графика", "разблокировка управления питанием AMD"),
        "en": ("amdgpu.ppfeaturemask", "Unlocks hidden AMD GPU power-management features (needed on older kernels). Gives CoreCtrl full clock control.", "GPU & graphics", "AMD power management unlock")},
    "nvidia_modeset": {
        "ru": ("nvidia-drm.modeset=1 (GRUB)", "Включает KMS для драйвера NVIDIA: нужно для Wayland, плавного переключения режимов и корректного композитинга.", "Видеокарта и графика", "nvidia-drm.modeset=1"),
        "en": ("nvidia-drm.modeset=1 (GRUB)", "Enables KMS for the NVIDIA driver: needed for Wayland, smooth mode switching and correct compositing.", "GPU & graphics", "nvidia-drm.modeset=1")},
    "vrr": {
        "ru": ("VRR/FreeSync", "Включает переменную частоту обновления (FreeSync) для AMD: картинка в играх без разрывов при плавающем FPS. Работает в X11 с драйвером amdgpu.", "Видеокарта и графика", "VRR/FreeSync (X11, amdgpu)"),
        "en": ("VRR/FreeSync", "Enables variable refresh rate (FreeSync) on AMD: tear-free gaming at fluctuating FPS. Works in X11 with the amdgpu driver.", "GPU & graphics", "VRR/FreeSync (X11, amdgpu)")},
    "radv": {
        "ru": ("RADV_PERFTEST=sam", "Включает в драйвере RADV оптимизацию SAM / Resizable BAR: процессор получает доступ ко всей видеопамяти сразу — небольшой прирост FPS в играх.", "Видеокарта и графика", "SAM / Resizable BAR в RADV"),
        "en": ("RADV_PERFTEST=sam", "Enables SAM / Resizable BAR optimization in the RADV driver: the CPU accesses all VRAM at once — a small FPS gain in games.", "GPU & graphics", "SAM / Resizable BAR in RADV")},
    "mesa": {
        "ru": ("MESA_SHADER_CACHE=4G", "Увеличивает кэш скомпилированных шейдеров до 4 ГБ. Игры и GL-приложения реже перекомпилируют шейдеры — меньше подтормаживаний в первые минуты игры.", "Видеокарта и графика", "кэш шейдеров MESA 4 ГБ"),
        "en": ("MESA_SHADER_CACHE=4G", "Raises the compiled shader cache to 4 GB. Games and GL apps recompile shaders less often — fewer hitches in the first minutes of play.", "GPU & graphics", "MESA shader cache 4 GB")},
    "pipewire": {
        "ru": ("PipeWire (звук)", "Увеличивает буферы (кванты) звукового сервера PipeWire. Убирает треск, щелчки и прерывистый звук в наушниках и колонках.", "Звук", "увеличенные буферы PipeWire"),
        "en": ("PipeWire (sound)", "Increases PipeWire sound-server quanta. Removes crackling, pops and stuttering audio in headphones and speakers.", "Sound", "increased PipeWire quanta")},
    "bbr": {
        "ru": ("TCP BBR", "Включает алгоритм управления перегрузками BBR + fq: выше реальная скорость и ниже задержки на нестабильных каналах.", "Сеть", "TCP BBR + fq"),
        "en": ("TCP BBR", "Enables BBR congestion control + fq: higher real throughput and lower latency on unstable links.", "Network", "TCP BBR + fq")},
    "swap": {
        "ru": ("Тюнинг swap", "Настраивает vm.swappiness — насколько охотно система сбрасывает память в swap. Для сжатого zram выгодно 150, для диска/SSD — 10: меньше лишних обращений к диску.", "Память и swap", "настройка vm.swappiness"),
        "en": ("Swap tuning", "Sets vm.swappiness — how eagerly memory is pushed to swap. 150 suits compressed zram, 10 suits disk/SSD: fewer pointless disk accesses.", "Memory & swap", "vm.swappiness tuning")},
    "zram": {
        "ru": ("zram-swap", "Создаёт сжатый swap в оперативке (zram) через zram-generator: быстрее дискового swap, экономит SSD. Требует пакет zram-generator.", "Память и swap", "zram-swap"),
        "en": ("zram-swap", "Creates compressed swap in RAM (zram) via zram-generator: faster than disk swap, saves SSD. Requires zram-generator package.", "Memory & swap", "zram-swap")},
    "zswap": {
        "ru": ("zswap (GRUB)", "Включает zswap — сжатый кэш перед дисковым swap: меньше обращений к диску, быстрее отклик при нехватке памяти. Совместим с обычным swap и гибернацией.", "Память и swap", "zswap"),
        "en": ("zswap (GRUB)", "Enables zswap — a compressed cache in front of disk swap: fewer disk accesses, faster response under memory pressure. Works with normal swap and hibernation.", "Memory & swap", "zswap")},
    "thp": {
        "ru": ("Transparent HugePages", "Режим прозрачных огромных страниц: always (максимум), madvise (только по запросу приложений, рекомендуется для игр/БД), never (отключено).", "Память и swap", "transparent_hugepage"),
        "en": ("Transparent HugePages", "Transparent huge pages mode: always (max), madvise (only on app request, recommended for games/DB), never (off).", "Memory & swap", "transparent_hugepage")},
    "sysctl_cache": {
        "ru": ("Кэш VFS (sysctl)", "vfs_cache_pressure=50: система дольше держит кэш каталогов и файлов в памяти, меньше повторных чтений с диска. Ускоряет работу с файлами.", "Ядро и загрузка", "vfs_cache_pressure=50"),
        "en": ("VFS cache (sysctl)", "vfs_cache_pressure=50: the system keeps directory/file cache in RAM longer, fewer disk re-reads. Speeds up file operations.", "Kernel & boot", "vfs_cache_pressure=50")},
    "sysctl_numa": {
        "ru": ("Миграция NUMA (sysctl)", "kernel.numa_balancing=0: отключает автоматическую миграцию страниц памяти между ядрами CPU. Уменьшает задержки в играх и чувствительных к latency задачах.", "Ядро и загрузка", "numa_balancing=0"),
        "en": ("NUMA migration (sysctl)", "kernel.numa_balancing=0: disables automatic memory page migration between CPU cores. Reduces stalls in games and latency-sensitive tasks.", "Kernel & boot", "numa_balancing=0")},
    "reisub": {
        "ru": ("REISUB (Magic SysRq)", "Включает аварийные клавиши SysRq (маска 244): при зависании удерживайте Alt+PrtSc и по порядку нажимайте R E I S U B для безопасного завершения процессов, синхронизации и перезагрузки без жёсткого сброса питания.", "Ядро и загрузка", "kernel.sysrq=244"),
        "en": ("REISUB (Magic SysRq)", "Enables SysRq emergency keys (mask 244): on a freeze hold Alt+PrtSc and press R E I S U B in order to safely terminate processes, sync and reboot without a hard reset.", "Kernel & boot", "kernel.sysrq=244")},
    "ntsync": {
        "ru": ("ntsync (модуль ядра)", "Включает модуль ntsync — новый ускоритель синхронизации для Wine/Proton. Заметный прирост FPS в части игр. Требуется ядро 6.14+ или с патчем ntsync.", "Игры и совместимость", "модуль ядра ntsync"),
        "en": ("ntsync (kernel module)", "Enables the ntsync module — a new synchronization accelerator for Wine/Proton. Noticeable FPS gain in some games. Needs kernel 6.14+ or a patched one.", "Gaming & compatibility", "ntsync kernel module")},
    "ntfs3": {
        "ru": ("ntfs3 драйвер", "Включает быстрый встроенный драйвер ntfs3 для NTFS-дисков вместо медленного ntfs-3g. Linux Mint по умолчанию его блокирует — опция снимает блокировку.", "Диски и файловые системы", "быстрый драйвер ntfs3"),
        "en": ("ntfs3 driver", "Enables the fast in-kernel ntfs3 driver for NTFS disks instead of slow ntfs-3g. Linux Mint blocks it by default — this option lifts the block.", "Drives & filesystems", "fast ntfs3 driver")},
    "commit": {
        "ru": ("commit=NN (fstab)", "Увеличивает интервал сброса метаданных ext4 на диск (по умолчанию 60 с): меньше мелких записей. Значение задаётся самим.", "Диски и файловые системы", "commit=NN"),
        "en": ("commit=NN (fstab)", "Increases ext4 metadata commit interval (default 60 s): fewer small writes. Value is editable.", "Drives & filesystems", "commit=NN")},
    "aliases": {
        "ru": ("Команды в .bashrc", "Добавляет удобные команды терминала: upd, upgr, update_all (обновление всей системы), clean (очистка), space (место на диске), mem (очистка памяти) и другие.", "Удобство", "команды upd/upgr/clean в .bashrc"),
        "en": ("Commands in .bashrc", "Adds handy shell commands: upd, upgr, update_all (full system update), clean, space (disk free), mem (memory clean) and more.", "Convenience", "upd/upgr/clean commands in .bashrc")},
    "autoupdate": {
        "ru": ("Автообновления", "Создаёт systemd-таймер, который по выбранному расписанию сам обновляет APT-пакеты и Flatpak без вашего участия. ВНИМАНИЕ: отключите встроенное автообновление Mint (mintupdate), иначе обновления будут выполняться дважды.", "Обновления", "systemd-таймер автообновлений"),
        "en": ("Auto-updates", "Creates a systemd timer that updates APT packages and Flatpak on the chosen schedule without you. NOTE: disable the built-in Mint auto-update (mintupdate), otherwise updates will run twice.", "Updates", "systemd auto-update timer")},
}

CAT_ORDER = {
    "ru": ["Видеокарта и графика", "Ядро и загрузка", "Логи системы", "Звук", "Сеть",
           "Память и swap", "Диски и файловые системы", "Игры и совместимость",
           "Удобство", "Обновления"],
    "en": ["GPU & graphics", "Kernel & boot", "System logs", "Sound", "Network",
           "Memory & swap", "Drives & filesystems", "Gaming & compatibility",
           "Convenience", "Updates"],
}

OPTIONS_HELP = {
    "rsyslog": {"ru": "rsyslog — служба, которая записывает системные журналы в файлы на диске (/var/log). На домашнем ПК эти файлы почти не нужны, но постоянно нагружают диск. Отключение безопасно: важные сообщения по-прежнему видны через journalctl.", "en": "rsyslog writes system logs to files on disk (/var/log). On a home PC these files are rarely needed but constantly load the disk. Disabling is safe: important messages remain visible via journalctl."},
    "journald": {"ru": "journald — современный журнал systemd. Перенос его в ОЗУ (Storage=volatile) значит, что журналы не пишутся на диск вовсе и исчезают после перезагрузки. Это снижает износ SSD. Ограничение 50 МБ не даёт журналам съесть память.", "en": "journald is the modern systemd log. Moving it to RAM (Storage=volatile) means logs are never written to disk and vanish after reboot, reducing SSD wear. The 50 MB cap prevents logs from eating memory."},
    "audit": {"ru": "audit — подсистема ядра для записи каждого системного вызова (нужна в корпоративных средах для безопасности). Дома она только создаёт накладные расходы. Отключение (audit=0) слегка ускоряет систему и убирает лишние записи.", "en": "audit is a kernel subsystem logging every syscall (needed in corporate security environments). At home it only adds overhead. Disabling (audit=0) slightly speeds up the system and removes noise."},
    "raid": {"ru": "При загрузке ядро ищет RAID-массивы. Если у вас их нет, поиск тратит время впустую. raid=noautodetect отключает поиск и ускоряет загрузку. НЕ включайте, если используете RAID!", "en": "At boot the kernel probes for RAID arrays. If you have none, the probe wastes time. raid=noautodetect skips it and speeds up boot. DO NOT enable if you use RAID!"},
    "nmi_watchdog": {"ru": "NMI-watchdog — механизм ядра для отладки зависаний через немаскируемые прерывания. На домашнем ПК он не нужен, а его периодические прерывания дают микро-фризы. Отключение (nmi_watchdog=0) убирает их.", "en": "The NMI watchdog is a kernel debugging facility using non-maskable interrupts. Unneeded at home; its periodic interrupts cause micro-stutters. Disabling (nmi_watchdog=0) removes them."},
    "corectrl": {"ru": "CoreCtrl — программа для тонкой настройки AMD GPU (частоты, вентиляторы, лимиты). По умолчанию её действия требуют пароль администратора. Это правило Polkit разрешает вашей группе пользователей управлять GPU без пароля.", "en": "CoreCtrl is a tool for fine-tuning AMD GPU (clocks, fans, limits). By default its actions require the admin password. This Polkit rule lets your user group control the GPU without a password."},
    "ppfeaturemask": {"ru": "Драйвер amdgpu на старых ядрах блокирует часть функций управления питанием. Параметр amdgpu.ppfeaturemask=0xffffffff снимает блокировку, и CoreCtrl получает полный контроль над частотами.", "en": "On older kernels the amdgpu driver blocks some power-management features. amdgpu.ppfeaturemask=0xffffffff lifts the block so CoreCtrl gets full clock control."},
    "nvidia_modeset": {"ru": "nvidia-drm.modeset=1 включает kernel modesetting для проприетарного драйвера NVIDIA: необходимо для Wayland, плавного переключения видеорежимов и корректной работы композитора.", "en": "nvidia-drm.modeset=1 enables kernel modesetting for the proprietary NVIDIA driver: required for Wayland, smooth mode switching and correct compositing."},
    "vrr": {"ru": "VRR (FreeSync) позволяет монитору обновляться синхронно с кадрами игры, убирая разрывы картинки. Работает только в X11 с драйвером amdgpu и на мониторе с поддержкой FreeSync.", "en": "VRR (FreeSync) lets the monitor refresh in sync with game frames, removing tearing. Works only in X11 with the amdgpu driver and a FreeSync-capable monitor."},
    "radv": {"ru": "SAM / Resizable BAR даёт процессору доступ ко всей видеопамяти сразу, а не кусками. Это даёт небольшой прирост FPS в играх. Параметр включает оптимизацию в открытом драйвере RADV.", "en": "SAM / Resizable BAR gives the CPU access to all VRAM at once instead of chunks, giving a small FPS gain. This option enables the optimization in the open RADV driver."},
    "mesa": {"ru": "MESA кэширует скомпилированные шейдеры игр. По умолчанию кэш мал, и игры часто перекомпилируют шейдеры, вызывая подтормаживания. Увеличение кэша до 4 ГБ уменьшает эти паузы.", "en": "MESA caches compiled game shaders. The default cache is small so games recompile shaders often, causing hitches. Raising the cache to 4 GB reduces these pauses."},
    "pipewire": {"ru": "PipeWire — звуковой сервер. Малые буферы дают низкую задержку, но на некоторых системах вызывают треск и щелчки. Увеличение буферов (квантов) убирает артефакты ценой чуть большей задержки (незаметно на практике).", "en": "PipeWire is the sound server. Small buffers give low latency but on some systems cause crackling. Increasing the quanta removes artifacts at the cost of slightly higher latency (imperceptible in practice)."},
    "bbr": {"ru": "BBR — современный алгоритм управления перегрузками TCP от Google. Вместе с очередью fq даёт более высокую реальную пропускную способность и меньшие задержки, особенно на нестабильных каналах.", "en": "BBR is Google's modern TCP congestion control. Together with the fq queue it gives higher real throughput and lower latency, especially on unstable links."},
    "swap": {"ru": "vm.swappiness управляет тем, как охотно система вытесняет память в swap. Высокое значение (150) выгодно для сжатого zram (память), низкое (10) — для диска/SSD, чтобы не дёргать диск лишний раз.", "en": "vm.swappiness controls how eagerly memory is pushed to swap. A high value (150) suits compressed zram (memory); a low value (10) suits disk/SSD to avoid needless disk access."},
    "zram": {"ru": "zram создаёт сжатое блочное устройство в оперативной памяти и использует его как swap. Это быстрее дискового swap и экономит ресурс SSD. Требует установленный zram-generator; активируется после перезагрузки.", "en": "zram creates a compressed block device in RAM and uses it as swap. Faster than disk swap and saves SSD wear. Requires zram-generator; activates after reboot."},
    "zswap": {"ru": "zswap — сжатый кэш в памяти ПЕРЕД дисковым swap: страницы сначала сжимаются в RAM и только при переполнении уходят на диск. Меньше обращений к диску, совместим с обычным swap и гибернацией.", "en": "zswap is a compressed cache in RAM in front of disk swap: pages compress in RAM first and only go to disk on overflow. Fewer disk accesses, works with normal swap and hibernation."},
    "thp": {"ru": "Transparent HugePages — прозрачные огромные страницы памяти. always — всегда (может давать задержки), madvise — только по запросу приложений (рекомендуется для игр/БД), never — отключено. Значение передаётся через GRUB.", "en": "Transparent HugePages. always — always on (can cause stalls), madvise — only on app request (recommended for games/DB), never — off. The value is passed via GRUB."},
    "sysctl_cache": {"ru": "vfs_cache_pressure говорит ядру, как агрессивно освобождать кэш каталогов и файлов. Значение 50 (вместо 100) значит, что кэш держится дольше и файлы открываются быстрее, особенно при частой работе с множеством файлов.", "en": "vfs_cache_pressure tells the kernel how aggressively to free directory/file cache. Value 50 (instead of 100) keeps the cache longer so files open faster, especially with many files."},
    "sysctl_numa": {"ru": "kernel.numa_balancing автоматически переносит страницы памяти между ядрами CPU (полезно на серверах с NUMA). На домашних ПК это чаще вредит: миграция вызывает паузы. Отключение (0) убирает эти паузы.", "en": "kernel.numa_balancing automatically migrates memory pages between CPU cores (useful on NUMA servers). On home PCs it usually hurts: migration causes stalls. Disabling (0) removes those stalls."},
    "reisub": {"ru": "kernel.sysrq=244 разрешает аварийные функции ядра Magic SysRq, из которых состоит последовательность REISUB: R (вернуть клавиатуру из-под X), E/I (корректно завершить/убить процессы), S (синхронизация дисков), U (remount read-only), B (перезагрузка). Маска 244 = сумма этих битов (4+16+32+64+128) без опасных отладочных функций. При зависании удерживайте Alt+PrtSc и нажимайте клавиши по порядку с интервалом 1–2 с.", "en": "kernel.sysrq=244 enables the Magic SysRq emergency functions that make up REISUB: R (unraw keyboard), E/I (terminate/kill processes), S (sync disks), U (remount read-only), B (reboot). Mask 244 = sum of these bits (4+16+32+64+128) without dangerous debug functions. On a freeze hold Alt+PrtSc and press the keys in order 1–2 s apart."},
    "ntsync": {"ru": "ntsync — новый модуль ядра, ускоряющий синхронизацию потоков в Wine/Proton. Игры под Windows используют много примитивов синхронизации; ntsync делает их быстрее, давая прирост FPS. Требует ядро 6.14+ или патченное.", "en": "ntsync is a new kernel module speeding up thread synchronization in Wine/Proton. Windows games use many sync primitives; ntsync makes them faster, giving FPS gains. Needs kernel 6.14+ or a patched one."},
    "ntfs3": {"ru": "ntfs3 — современный встроенный драйвер NTFS (быстрый). Mint блокирует его и использует медленный ntfs-3g. Опция снимает блокировку, и NTFS-диски работают заметно быстрее.", "en": "ntfs3 is the modern in-kernel NTFS driver (fast). Mint blocks it and uses slow ntfs-3g. This option lifts the block so NTFS disks work noticeably faster."},
    "commit": {"ru": "commit=NN задаёт интервал (в секундах), с которым ext4 сбрасывает метаданные на диск. Больше значение — меньше мелких записей и меньше износа SSD, но чуть выше риск потери последних метаданных при сбое питания. По умолчанию 60.", "en": "commit=NN sets the interval (seconds) at which ext4 flushes metadata to disk. Higher value — fewer small writes and less SSD wear, but slightly higher risk of losing last metadata on power loss. Default 60."},
    "aliases": {"ru": "Добавляет в ваш .bashrc готовые функции: upd (обновить списки), upgr (обновить пакеты), update_all (полное обновление), clean (очистка), space (место на диске), mem (очистка памяти) и др. Это экономит время на рутинных операциях.", "en": "Adds ready functions to your .bashrc: upd (update lists), upgr (upgrade packages), update_all (full update), clean (cleanup), space (disk free), mem (memory clean) etc. Saves time on routine operations."},
    "autoupdate": {"ru": "Создаёт systemd-таймер, который по расписанию обновляет систему и Flatpak. ВАЖНО: отключите встроенное автообновление Mint (mintupdate / автоматизацию), иначе обновления будут запускаться дважды и конфликтовать.", "en": "Creates a systemd timer that updates the system and Flatpak on schedule. IMPORTANT: disable the built-in Mint auto-update (mintupdate automation), otherwise updates will run twice and conflict."},
    "mount": {"ru": "Опция монтирования noatime отключает обновление времени последнего доступа к файлам и каталогам (nodiratime — её историческое подмножество, отдельно не требуется). Это убирает лишние операции записи при каждом чтении, снижая износ SSD и ускоряя чтение. Вступает в силу после перезагрузки.", "en": "The noatime mount option disables updating last-access times for files and directories (nodiratime is its historical subset and is not needed separately). This removes extra write operations on every read, reducing SSD wear and speeding up reads. Takes effect after reboot."},
    "steam": {"ru": "Игры Steam под Proton хранят данные (префиксы) в ~/.steam/steam/steamapps/compatdata. Если библиотека Steam лежит на другом диске (NTFS), игра не находит эти данные. Симлинк compatdata в библиотеке указывает на домашнюю папку, и игры работают корректно.", "en": "Steam Proton games store data (prefixes) in ~/.steam/steam/steamapps/compatdata. If a Steam library is on another disk (NTFS), games cannot find this data. A compatdata symlink in the library points to the home folder so games work correctly."},
}

SERVICES_META = {
    "avahi-daemon.service": {"ru": "Сетевое обнаружение устройств (принтеры, ТВ, Chromecast). На домашнем ПК без сетевой печати почти не нужно.", "en": "Network device discovery (printers, TVs, Chromecast). Rarely needed on a home PC without network printing."},
    "avahi-daemon.socket": {"ru": "Сокет-активатор Avahi: будит службу при обращении из сети. Отключается вместе со службой.", "en": "Avahi socket activator: wakes the service on network requests. Disabled together with the service."},
    "cups-browsed.service": {"ru": "Автоматический поиск сетевых принтеров. Если у вас нет сетевого принтера — служба простаивает зря.", "en": "Automatic network printer discovery. Useless if you have no network printer."},
    "cups.service": {"ru": "Сервер печати CUPS. Если принтера/сканера нет — служба не нужна.", "en": "CUPS print server. If you have no printer/scanner — unneeded."},
    "cups.socket": {"ru": "Сокет CUPS: активирует службу печати при обращении. Отключается вместе с cups.service.", "en": "CUPS socket: activates printing on demand. Disabled together with cups.service."},
    "ModemManager.service": {"ru": "Управление USB-модемами (3G/4G). Без модема не нужен; иногда мешает serial-устройствам и Arduino.", "en": "USB modem (3G/4G) management. Useless without a modem; can interfere with serial devices and Arduino."},
    "openvpn.service": {"ru": "Встроенный VPN-сервер. Если не поднимаете собственный VPN — не нужен.", "en": "Built-in VPN server. Useless unless you run your own VPN."},
    "lvm2-monitor.service": {"ru": "Мониторинг LVM-томов. При обычной установке без LVM не нужен.", "en": "LVM volume monitoring. Useless on a plain install without LVM."},
    "switcheroo-control.service": {"ru": "Переключение встроенной и дискретной графики на ноутбуках. На настольном ПК не нужен.", "en": "Switching integrated/discrete graphics on laptops. Useless on a desktop."},
    "touchegg.service": {"ru": "Распознавание мультитач-жестов тачпада. На настольном ПК без тачскрина не нужен.", "en": "Multitouch gesture recognition. Useless on a desktop without a touchscreen."},
    "zfs-zed.service": {"ru": "Мониторинг ZFS-пулов (дисковые массивы ZFS). Без ZFS не нужен.", "en": "ZFS pool monitoring. Useless without ZFS."},
    "kerneloops.service": {"ru": "Отправка разработчикам отчётов о сбоях ядра. На домашнем ПК не нужна.", "en": "Sends kernel crash reports to developers. Unneeded on a home PC."},
}
SERVICES_ORDER = list(SERVICES_META.keys())

SERVICES_HELP = {
    "avahi-daemon.service": {"ru": "Avahi (mDNS/DNS-SD) позволяет устройствам в локальной сети находить друг друга без настройки: принтеры, колонки, ТВ. Если у вас нет сетевых принтеров и вы не пользуетесь Chromecast/AirPlay, служба не нужна и только периодически рассылает пакеты по сети. Отключение безопасно.", "en": "Avahi (mDNS/DNS-SD) lets local devices discover each other without setup: printers, speakers, TVs. If you have no network printers and don't use Chromecast/AirPlay, the service is unneeded and only periodically broadcasts on the network. Safe to disable."},
    "avahi-daemon.socket": {"ru": "Сокет активирует avahi-daemon при первом обращении из сети. Отключайте вместе со службой, чтобы avahi не «проснулась» сама.", "en": "The socket activates avahi-daemon on first network request. Disable together with the service so avahi cannot wake up on its own."},
    "cups-browsed.service": {"ru": "Часть системы печати CUPS: ищет сетевые принтеры и добавляет их автоматически. Если принтера нет или он подключён по USB, служба не нужна.", "en": "Part of the CUPS printing system: discovers network printers and adds them automatically. If you have no printer or it is USB-connected, the service is unneeded."},
    "cups.service": {"ru": "CUPS обслуживает печать и сканирование. Если печатающих устройств нет, служба только висит фоном. Отключение безопасно; при необходимости печать можно включить обратно.", "en": "CUPS handles printing/scanning. With no printing devices the service just idles. Safe to disable; printing can be re-enabled later."},
    "cups.socket": {"ru": "Сокет активирует cups.service при первом обращении к печати. Отключайте вместе с cups.service, чтобы печать не «проснулась» сама.", "en": "The socket activates cups.service on first print access. Disable together with cups.service so printing cannot wake up on its own."},
    "ModemManager.service": {"ru": "Управляет мобильными модемами (3G/4G). На ПК без модема служба не нужна; более того, она может мешать устройствам, которые определяются как serial-порты (Arduino, некоторые преобразователи).", "en": "Manages mobile modems (3G/4G). On a PC without a modem the service is unneeded; moreover it can interfere with devices that appear as serial ports (Arduino, some converters)."},
    "openvpn.service": {"ru": "Сервер OpenVPN для входящих VPN-подключений. Если вы не настроили собственный VPN-сервер, служба не активна и не нужна.", "en": "OpenVPN server for incoming VPN connections. If you have not set up your own VPN server, the service is inactive and unneeded."},
    "lvm2-monitor.service": {"ru": "Следит за томами LVM (логические диски). При обычной установке Mint/Ubuntu без LVM служба не нужна.", "en": "Monitors LVM volumes (logical disks). On a standard Mint/Ubuntu install without LVM the service is unneeded."},
    "switcheroo-control.service": {"ru": "Переключает встроенную и дискретную графику на гибридных ноутбуках. На настольном ПК с одной видеокартой не нужна.", "en": "Switches integrated and discrete graphics on hybrid laptops. On a desktop with a single GPU it is unneeded."},
    "touchegg.service": {"ru": "Распознаёт мультитач-жесты на тачпадах и тачскринах. На настольном ПК без сенсорного ввода не нужна.", "en": "Recognizes multitouch gestures on touchpads and touchscreens. On a desktop without touch input it is unneeded."},
    "zfs-zed.service": {"ru": "Демон ZFS (ZED) следит за состоянием ZFS-пулов и шлёт уведомления о проблемах дисков. Без ZFS не нужна.", "en": "The ZFS daemon (ZED) monitors ZFS pool health and sends notifications on disk issues. Without ZFS it is unneeded."},
    "kerneloops.service": {"ru": "Собирает и отправляет разработчикам отчёты о сбоях ядра. На домашнем ПК это лишь фоновая нагрузка и исходящий трафик.", "en": "Collects and sends kernel crash reports to developers. On a home PC this is only background load and outgoing traffic."},
}

OPTION_FILES = {
    "rsyslog": ["/etc/systemd/system/rsyslog.service",
                "/lib/systemd/system/rsyslog.service"],
    "journald": ["/etc/systemd/journald.conf"],
    "audit": ["/etc/default/grub"],
    "raid": ["/etc/default/grub"],
    "nmi_watchdog": ["/etc/default/grub"],
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
    "ntfs3": ["/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"],
    "commit": ["/etc/fstab"],
    "aliases": ["{home}/.bashrc"],
    "autoupdate": ["/etc/systemd/system/biweekly-upgrade.timer",
                   "/etc/systemd/system/biweekly-upgrade.service"],
}

STR = {
    "ru": {
        "tab_tune": "Тюнинг", "tab_serv": "Службы", "tab_stat": "Статус",
        "btn_apply": "Применить выбранное", "btn_rollback": "Откатить выбранное",
        "btn_selall": "Выбрать все", "btn_selnone": "Снять выделение",
        "btn_export": "Экспорт", "btn_about": "О твикере",
        "theme_dark": "Тёмная тема", "theme_light": "Светлая тема",
        "lbl_dry": "Сухой прогон", "lbl_terminal": "Терминальный вывод:",
        "lbl_group": "Группа:", "lbl_value": "Значение:", "lbl_schedule": "Расписание:",
        "ready": "Готово", "running": "Выполнение...", "done": "Готово",
        "applied_yes": "✓ применено", "applied_no": "не применено",
        "btn_file": "файл", "btn_q": "?",
        "menu_copy": "Копировать", "menu_copy_all": "Копировать всё",
        "menu_select_all": "Выделить всё",
        "svc_name": "Служба", "svc_state": "Состояние", "svc_run": "Запуск",
        "svc_desc": "Описание", "svc_help": "?",
        "svc_hint": "Выберите строку, чтобы увидеть описание; «?» — подробности.",
        "svc_on": "работает", "svc_onoff": "не запущена", "svc_off": "остановлена",
        "svc_masked": "заблокирована", "svc_na": "нет в системе",
        "run_yes": "работает", "run_no": "остановлена",
        "svc_on_sel": "Включить выбранные", "svc_off_sel": "Отключить выбранные",
        "stat_refresh": "Обновить статус",
        "st_hw": "ИНФОРМАЦИЯ О СИСТЕМЕ", "st_parts": "РАЗДЕЛЫ СИСТЕМЫ",
        "st_tweaks": "ТВИКИ", "st_services": "СЛУЖБЫ", "st_kernel": "ПАРАМЕТРЫ ЯДРА",
        "st_timer": "Таймер автообновлений",
        "part_mount": "Раздел", "part_fs": "ФС", "part_total": "Всего",
        "part_free": "Свободно",
        "os_lbl": "ОС", "gpu_lbl": "Видеокарта", "screen_lbl": "Разрешение экрана",
        "swap_lbl": "Файл подкачки", "kernel_lbl": "Ядро", "de_lbl": "Оболочка",
        "ram_lbl": "ОЗУ", "cpu_lbl": "Процессор", "disk_lbl": "Диск",
        "driver_lbl": "Драйвер видеокарты",
        "user_lbl": "Пользователь", "home_lbl": "Домашняя папка",
        "hz": "Гц", "ram_hint": "(тип и частота — после ввода sudo)",
        "w_yes": "да", "w_no": "нет", "no_swap": "отсутствует",
        "gb": "ГБ", "free_w": "свободно", "swap_file": "файл", "swap_part": "раздел",
        "yes": "ПРИМЕНЕНО", "no": "НЕ ПРИМЕНЕНО",
        "sched_cur": "Текущее: %s", "sched_none": "не настроено",
        "mount_title": "Диски: параметры монтирования",
        "mount_desc": "Добавит опцию noatime в /etc/fstab (меньше служебных обращений к диску, полезно для SSD и NTFS; noatime покрывает и каталоги). Вступает в силу после перезагрузки.",
        "steam_title": "Steam: симлинки compatdata",
        "steam_desc": "Создаст ссылку compatdata на ~/.steam/steam/steamapps/compatdata для библиотек Steam на NTFS-разделах, чтобы игры видели данные Proton/Wine из домашней папки.",
        "mount_short": "параметры монтирования", "steam_short": "симлинк compatdata",
        "kern_sw": "насколько охотно система выгружает память в swap (меньше значение — реже)",
        "kern_vfs": "кэш файлов в памяти",
        "kern_numa": "миграция памяти между ядрами",
        "tw_name": "Твик", "kn_param": "Параметр", "kn_val": "Значение",
        "sudo_title": "sudo", "sudo_prompt": "Пароль sudo (попытка %d из 3):",
        "sudo_wrong": "Неверный пароль или нет прав sudo.",
        "autoupdate_warn": "Включено автообновление по расписанию. Отключите встроенное автообновление Mint (mintupdate), иначе обновления будут выполняться дважды.",
        "viewer": "Просмотр файла", "viewer_ext": "Открыть во внешнем редакторе",
        "about_title": "О твикере",
        "about_purpose": "Графическая оболочка тюнинга для Linux Mint / Ubuntu / Debian и других systemd-дистрибутивов: твики производительности, логов, дисков, сети и игр с откатом и бэкапами.",
        "about_author": "Автор", "about_author_name": "Дмитрий Свистунов",
        "about_ver": "Версия",
        "msg_run": "Скрипт уже запущен. Дождитесь завершения.",
        "msg_noopt": "Отметьте хотя бы одну опцию.",
        "msg_sel": "Сначала выберите строки в таблице.",
        "msg_nofile": "Файл ещё не существует. Пути, где опция вносит изменения:",
        "msg_close": "Прервать выполнение и закрыть?",
    },
    "en": {
        "tab_tune": "Tuning", "tab_serv": "Services", "tab_stat": "Status",
        "btn_apply": "Apply selected", "btn_rollback": "Rollback selected",
        "btn_selall": "Select all", "btn_selnone": "Deselect",
        "btn_export": "Export", "btn_about": "About",
        "theme_dark": "Dark theme", "theme_light": "Light theme",
        "lbl_dry": "Dry run", "lbl_terminal": "Terminal output:",
        "lbl_group": "Group:", "lbl_value": "Value:", "lbl_schedule": "Schedule:",
        "ready": "Ready", "running": "Running...", "done": "Done",
        "applied_yes": "✓ applied", "applied_no": "not applied",
        "btn_file": "file", "btn_q": "?",
        "menu_copy": "Copy", "menu_copy_all": "Copy all",
        "menu_select_all": "Select all",
        "svc_name": "Service", "svc_state": "State", "svc_run": "Running",
        "svc_desc": "Description", "svc_help": "?",
        "svc_hint": "Select a row to see the description; “?” opens details.",
        "svc_on": "running", "svc_onoff": "not running", "svc_off": "stopped",
        "svc_masked": "blocked", "svc_na": "not installed",
        "run_yes": "running", "run_no": "stopped",
        "svc_on_sel": "Enable selected", "svc_off_sel": "Disable selected",
        "stat_refresh": "Refresh status",
        "st_hw": "SYSTEM INFORMATION", "st_parts": "SYSTEM PARTITIONS",
        "st_tweaks": "TWEAKS", "st_services": "SERVICES", "st_kernel": "KERNEL PARAMETERS",
        "st_timer": "Auto-update timer",
        "part_mount": "Partition", "part_fs": "FS", "part_total": "Total",
        "part_free": "Free",
        "os_lbl": "OS", "gpu_lbl": "GPU", "screen_lbl": "Screen resolution",
        "swap_lbl": "Swap", "kernel_lbl": "Kernel", "de_lbl": "Desktop",
        "ram_lbl": "RAM", "cpu_lbl": "CPU", "disk_lbl": "Disk",
        "driver_lbl": "GPU driver",
        "user_lbl": "User", "home_lbl": "Home folder",
        "hz": "Hz", "ram_hint": "(type & speed after sudo)",
        "w_yes": "yes", "w_no": "no", "no_swap": "none",
        "gb": "GB", "free_w": "free", "swap_file": "file", "swap_part": "partition",
        "yes": "APPLIED", "no": "NOT APPLIED",
        "sched_cur": "Current: %s", "sched_none": "not configured",
        "mount_title": "Disks: mount options",
        "mount_desc": "Adds the noatime option to /etc/fstab entries (less disk wear; noatime already covers directories). Takes effect after reboot.",
        "steam_title": "Steam: compatdata symlinks",
        "steam_desc": "Creates a compatdata symlink to ~/.steam/steam/steamapps/compatdata for Steam libraries on NTFS partitions so games can see Proton/Wine data from the home folder.",
        "mount_short": "mount options", "steam_short": "compatdata symlink",
        "kern_sw": "how eagerly the system moves memory to swap (lower = less often)",
        "kern_vfs": "file cache in RAM",
        "kern_numa": "memory migration between cores",
        "tw_name": "Tweak", "kn_param": "Parameter", "kn_val": "Value",
        "sudo_title": "sudo", "sudo_prompt": "sudo password (attempt %d of 3):",
        "sudo_wrong": "Wrong password or no sudo rights.",
        "autoupdate_warn": "Scheduled auto-update enabled. Disable the built-in Mint auto-update (mintupdate), otherwise updates will run twice.",
        "viewer": "File viewer", "viewer_ext": "Open in external editor",
        "about_title": "About",
        "about_purpose": "A graphical tuning shell for Linux Mint / Ubuntu / Debian and other systemd distributions: performance, logs, disk, network and gaming tweaks with rollback and backups.",
        "about_author": "Author", "about_author_name": "Dmitry Svistunov",
        "about_ver": "Version",
        "msg_run": "A job is already running. Wait for it to finish.",
        "msg_noopt": "Tick at least one option.",
        "msg_sel": "Select table rows first.",
        "msg_nofile": "This file appears after applying the option. Paths the option modifies:",
        "msg_close": "Interrupt the job and close?",
    },
}


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
                if fstype not in ("ext2", "ext3", "ext4", "xfs", "btrfs",
                                  "f2fs", "ntfs", "ntfs3", "vfat", "exfat",
                                  "fuseblk"):
                    continue
                if "rw" not in opts.split(","):
                    continue
                items.append({"dev": dev, "mp": mp, "fstype": fstype})
    except Exception:
        pass
    return items


def find_steam_libraries(user_home):
    libs = []
    vdf = os.path.join(user_home, ".steam", "steam", "steamapps",
                       "libraryfolders.vdf")
    if os.path.isfile(vdf):
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


def lines_in(content):
    return content.splitlines()


def _gear_path(cx, cy, r):
    path = QPainterPath()
    for i in range(8):
        tr = QTransform().translate(cx, cy).rotate(i * 45.0).translate(-cx, -cy)
        rect = QRectF(cx - r * 0.16, cy - r, r * 0.32, r * 0.42)
        path.addRect(tr.mapRect(rect))
    ring = QPainterPath()
    ring.addEllipse(QRectF(cx - r * 0.66, cy - r * 0.66, r * 1.32, r * 1.32))
    hole = QPainterPath()
    hole.addEllipse(QRectF(cx - r * 0.28, cy - r * 0.28, r * 0.56, r * 0.56))
    return path + (ring - hole)


def make_icon(kind, size=48, accent="#4ec9b0", fg="#d4d4d4"):
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = size / 2.0
    r = size * 0.36
    pen = QPen(QColor(fg), size * 0.09)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    if kind == "logo":
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor(accent))
        grad.setColorAt(1, QColor("#3aa794"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(2, 2, size - 4, size - 4, size * 0.24, size * 0.24)
        p.setBrush(QColor("#ffffff"))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(_gear_path(c, c, r * 0.86), QBrush(QColor("#ffffff")))
    elif kind == "gear":
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(_gear_path(c, c, r), QBrush(QColor(accent)))
    elif kind == "services":
        p.setPen(pen)
        for i, y in enumerate((0.3, 0.5, 0.7)):
            p.drawLine(int(size * 0.2), int(size * y), int(size * 0.8), int(size * y))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(accent))
            p.drawEllipse(int(size * (0.35 + 0.15 * i)) - 4, int(size * y) - 4, 8, 8)
            p.setPen(pen)
    elif kind == "status":
        p.setPen(QPen(QColor(accent), size * 0.1))
        path = QPainterPath()
        path.moveTo(size * 0.15, size * 0.6)
        path.lineTo(size * 0.35, size * 0.6)
        path.lineTo(size * 0.5, size * 0.3)
        path.lineTo(size * 0.65, size * 0.75)
        path.lineTo(size * 0.85, size * 0.5)
        p.drawPath(path)
    elif kind == "apply":
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(accent))
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
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(accent))
        p.drawEllipse(int(size * 0.62), int(size * 0.12), int(size * 0.2), int(size * 0.2))
    elif kind == "file":
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(accent))
        p.drawRoundedRect(int(size * 0.25), int(size * 0.15),
                          int(size * 0.5), int(size * 0.7), 4, 4)
        p.setPen(QPen(QColor("#ffffff"), size * 0.06))
        for y in (0.35, 0.5, 0.65):
            p.drawLine(int(size * 0.35), int(size * y), int(size * 0.65), int(size * y))
    elif kind == "export":
        p.setPen(QPen(QColor(accent), size * 0.1))
        p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.6))
        path = QPainterPath()
        path.moveTo(size * 0.32, size * 0.45)
        path.lineTo(size * 0.5, size * 0.65)
        path.lineTo(size * 0.68, size * 0.45)
        p.drawPath(path)
        p.drawLine(int(size * 0.25), int(size * 0.78), int(size * 0.75), int(size * 0.78))
    elif kind == "help":
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(accent))
        p.drawEllipse(4, 4, size - 8, size - 8)
        p.setPen(QPen(QColor("#ffffff"), size * 0.11))
        p.drawArc(int(size * 0.32), int(size * 0.24), int(size * 0.36), int(size * 0.36),
                  20 * 16, 200 * 16)
        p.drawLine(int(size * 0.5), int(size * 0.5), int(size * 0.5), int(size * 0.62))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(size * 0.46), int(size * 0.68), int(size * 0.09), int(size * 0.09))
    elif kind == "close":
        p.setPen(QPen(QColor(accent), max(2, int(size * 0.14))))
        p.drawLine(int(size * 0.26), int(size * 0.26), int(size * 0.74), int(size * 0.74))
        p.drawLine(int(size * 0.74), int(size * 0.26), int(size * 0.26), int(size * 0.74))
    elif kind == "selall":
        p.setPen(QPen(QColor(accent), max(2, int(size * 0.1))))
        p.drawRect(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6))
        p.drawLine(int(size * 0.32), int(size * 0.5), int(size * 0.45), int(size * 0.62))
        p.drawLine(int(size * 0.45), int(size * 0.62), int(size * 0.7), int(size * 0.36))
    elif kind == "selnone":
        p.setPen(QPen(QColor(accent), max(2, int(size * 0.1))))
        p.drawRect(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6))
    elif kind == "on":
        p.setPen(QPen(QColor(accent), max(2, int(size * 0.12))))
        p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.5))
        p.drawArc(int(size * 0.28), int(size * 0.34), int(size * 0.44), int(size * 0.44),
                  30 * 16, 300 * 16)
    elif kind == "off":
        p.setPen(QPen(QColor(accent), max(2, int(size * 0.12))))
        p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.5))
        p.drawRect(int(size * 0.3), int(size * 0.5), int(size * 0.4), int(size * 0.28))
    p.end()
    return px


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
            self._keepalive = False
            self.authenticated = False
        threading.Thread(target=loop, daemon=True).start()


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
            res = subprocess.run(["lsblk", "-n", "-o", "TYPE"], capture_output=True,
                                 text=True, timeout=5)
            if "raid" in res.stdout:
                self.has_raid = True
        except Exception:
            pass
        try:
            res = subprocess.run(["swapon", "--show=TYPE", "--noheadings"],
                                 capture_output=True, text=True, timeout=5)
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
        try:
            for pw in pwd.getpwall():
                if pw.pw_uid >= 1000 and pw.pw_name not in ("nobody", "nfsnobody"):
                    return pw.pw_name
        except Exception:
            pass
        return "root"


class SystemOps:
    def __init__(self, sudo, state, log, dry_run):
        self.sudo = sudo
        self.state = state
        self.log = log
        self.dry_run = dry_run
        self.grub_changed = False
        self.mount_items = []
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
            if self.state.user_name and self.state.user_name != "root":
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
            self.log("[DRY RUN] " + " ".join(args), "warning")
            return True
        try:
            res = self.sudo.run(args, input=input)
        except PermissionError as e:
            self.log(str(e), "error")
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
            self.log("[DRY RUN] write: %s" % path, "warning")
            return True
        if mkdir:
            d = os.path.dirname(path)
            if d:
                self.sudo_run(["mkdir", "-p", d], ignore_error=True)
        if backup:
            self.backup_file(path)
        try:
            res = self.sudo.run(["tee", path], input=content.encode())
        except PermissionError as e:
            self.log(str(e), "error")
            return False
        except Exception as e:
            self.log("Write error %s: %s" % (path, e), "error")
            return False
        if res.returncode != 0:
            self.log("Cannot write %s" % path, "error")
            return False
        if chmod:
            self.sudo_run(["chmod", chmod, path], ignore_error=True)
        if owner:
            self.sudo_run(["chown", owner, path], ignore_error=True)
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
        if not self.state.cinnamon:
            return False
        if shutil.which("cinnamon-spice-updater"):
            return True
        return os.path.exists("/usr/bin/cinnamon-spice-updater")

    def add_grub_params(self, params):
        if self.dry_run:
            self.log("[DRY RUN] GRUB add: " + " ".join(params), "warning")
            return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        lines, found, changed = [], False, False
        for line in lines_in(content):
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                found = True
                raw = m.group(1).strip().strip('"').strip("'")
                parts = [p for p in raw.split() if p]
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
            self.log("GRUB already has params", "info")
            return True
        self.backup_file(path)
        if self.write_file(path, "\n".join(new_lines) + "\n", backup=False):
            self.grub_changed = True
            self.log("GRUB: params added", "success")
            return True
        return False

    def _grub_set_param(self, token):
        if self.dry_run:
            self.log("[DRY RUN] GRUB set: %s" % token, "warning")
            return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error")
            return False
        key = token.split("=")[0]
        lines, changed = [], False
        for line in lines_in(content):
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                raw = m.group(1).strip().strip('"').strip("'")
                parts = [p for p in raw.split() if p and not p.startswith(key + "=")]
                if token not in parts:
                    parts.append(token)
                newl = 'GRUB_CMDLINE_LINUX_DEFAULT="' + " ".join(parts) + '"'
                if newl != line.strip():
                    changed = True
                lines.append(newl)
            else:
                lines.append(line)
        if not changed:
            self.log("GRUB already has %s" % token, "info")
            return True
        self.backup_file(path)
        if self.write_file(path, "\n".join(lines) + "\n", backup=False):
            self.grub_changed = True
            self.log("GRUB: %s set" % token, "success")
            return True
        return False

    def finalize_grub(self):
        if not self.grub_changed:
            return
        if self.dry_run:
            self.log("[DRY RUN] update-grub", "warning")
            return
        ug = shutil.which("update-grub")
        if not ug and os.path.exists("/usr/sbin/update-grub"):
            ug = "/usr/sbin/update-grub"
        gm = shutil.which("grub-mkconfig")
        if not gm and os.path.exists("/usr/sbin/grub-mkconfig"):
            gm = "/usr/sbin/grub-mkconfig"
        if ug:
            self.sudo_run([ug], ok_msg="GRUB updated", err_msg="update-grub failed")
        elif gm:
            self.sudo_run([gm, "-o", "/boot/grub/grub.cfg"],
                          ok_msg="GRUB updated", err_msg="grub-mkconfig failed")
        else:
            self.log("update-grub / grub-mkconfig not found", "warning")
        self.grub_changed = False

    def apply_rsyslog(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] disable + mask rsyslog", "warning"); return True
        if self.service_enabled("rsyslog.service") in ("disabled", "masked", "not-found"):
            self.log("rsyslog already disabled", "info"); return True
        ok1 = self.sudo_run(["systemctl", "disable", "--now", "rsyslog"], ignore_error=True)
        ok2 = self.sudo_run(["systemctl", "mask", "rsyslog"], ignore_error=True)
        if ok1 or ok2:
            self.log("✓ rsyslog disabled", "success"); return True
        self.log("Cannot disable rsyslog", "error"); return False

    def apply_journald(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] journald volatile 50M", "warning"); return True
        path = "/etc/systemd/journald.conf"
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error"); return False
        if (re.search(r"^\s*Storage\s*=\s*volatile\s*$", content, re.M)
                and re.search(r"^\s*RuntimeMaxUse\s*=\s*50M\s*$", content, re.M)):
            self.log("journald already configured", "info"); return True
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
        self.backup_file(path)
        if not self.write_file(path, "\n".join(out) + "\n", backup=False):
            return False
        self.sudo_run(["systemctl", "restart", "systemd-journald"], ignore_error=True)
        self.sudo_run(["journalctl", "--vacuum-size=200M", "--vacuum-time=1months"],
                      ignore_error=True)
        self.log("✓ journald → volatile (50M)", "success"); return True

    def apply_audit(self, params=None):
        return self.add_grub_params(["audit=0"])

    def apply_raid(self, params=None):
        if self.state.has_raid:
            self.log("RAID detected, skipping", "warning"); return True
        return self.add_grub_params(["raid=noautodetect"])

    def apply_nmi_watchdog(self, params=None):
        return self.add_grub_params(["nmi_watchdog=0"])

    def _polkit_is_new(self):
        try:
            res = subprocess.run(["pkaction", "--version"],
                                 capture_output=True, text=True, timeout=5)
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
            self.log("[DRY RUN] CoreCtrl polkit rule for %s" % group, "warning")
            return True
        try:
            grp.getgrnam(group)
        except KeyError:
            self.log("Group not found: %s" % group, "error"); return False
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
            content = ("[User permissions]\nIdentity=unix-group:" + group + "\n"
                       "Action=org.corectrl.*\nResultActive=yes\n")
            path = "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"
        if self.write_file(path, content, chmod="644", mkdir=True):
            self.log("✓ CoreCtrl configured for %s (%s)"
                     % (group, os.path.basename(path)), "success")
            return True
        return False

    def apply_ppfeaturemask(self, params=None):
        return self.add_grub_params(["amdgpu.ppfeaturemask=0xffffffff"])

    def apply_nvidia_modeset(self, params=None):
        return self.add_grub_params(["nvidia-drm.modeset=1"])

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

    def apply_radv(self, params=None):
        return self.ensure_line("/etc/environment", "RADV_PERFTEST=sam",
                                r"^\s*RADV_PERFTEST=.*")

    def apply_mesa(self, params=None):
        return self.ensure_line("/etc/environment", "MESA_SHADER_CACHE_MAX_SIZE=4G",
                                r"^\s*MESA_SHADER_CACHE_MAX_SIZE=.*")

    def apply_pipewire(self, params=None):
        d = os.path.join(self.state.user_home, ".config", "pipewire", "pipewire.conf.d")
        path = os.path.join(d, "10-sound.conf")
        if self.dry_run:
            self.log("[DRY RUN] PipeWire config: %s" % path, "warning"); return True
        content = ("context.properties = {\n    default.clock.min-quantum = 512\n"
                   "    default.clock.quantum = 4096\n"
                   "    default.clock.max-quantum = 8192\n}\n")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            self.log("Cannot create %s: %s" % (d, e), "error")
            return False
        if not self.write_file(path, content, chmod="644"):
            return False
        if self.state.user_name and self.state.user_name != "root":
            self.sudo_run(["chown", "-R",
                           "%s:%s" % (self.state.user_name, self.state.user_name),
                           os.path.join(self.state.user_home, ".config", "pipewire")],
                          ignore_error=True)
        self.log("✓ PipeWire configured", "success"); return True

    def apply_bbr(self, params=None):
        path = "/etc/sysctl.d/99-bbr.conf"
        content = "net.core.default_qdisc=fq\nnet.ipv4.tcp_congestion_control=bbr\n"
        if not self.write_file(path, content, chmod="644", mkdir=True):
            return False
        self.write_file("/etc/modules-load.d/bbr.conf", "tcp_bbr\n",
                        chmod="644", mkdir=True)
        self.sudo_run(["modprobe", "tcp_bbr"], ignore_error=True)
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        self.log("✓ TCP BBR enabled", "success"); return True

    def apply_swap(self, params=None):
        params = params or {}
        if not self.state.has_swap:
            self.log("No swap found, skipping", "warning"); return True
        val = params.get("swap_value", "").strip()
        if not val:
            val = "150" if self.state.swap_type == "zram" else "10"
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

    def apply_zram(self, params=None):
        gen = "/usr/lib/systemd/system-generators/zram-generator"
        if not os.path.exists(gen):
            self.log("zram-generator not installed", "warning"); return False
        path = "/etc/systemd/zram-generator.conf"
        content = "[zram0]\nzram-size = ram-size / 2\ncompression-algorithm = zstd\n"
        if self.write_file(path, content, chmod="644", mkdir=True):
            self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
            self.log("✓ zram configured (reboot to activate)", "success"); return True
        return False

    def apply_zswap(self, params=None):
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
            self.log("[DRY RUN] %s=%s" % (key, val), "warning"); return True
        path = "/etc/sysctl.d/99-gaming-sysctl.conf"
        content = self.read_file(path) or ""
        rx = re.compile(r"^\s*%s\s*=" % re.escape(key))
        out, replaced = [], False
        for l in lines_in(content):
            if rx.match(l):
                out.append("%s=%s" % (key, val)); replaced = True
            else:
                out.append(l)
        if not replaced:
            out.append("%s=%s" % (key, val))
        self.backup_file(path)
        if not self.write_file(path, "\n".join(out) + "\n", chmod="644",
                               mkdir=True, backup=False):
            return False
        self.sudo_run(["sysctl", "-p", path], ignore_error=True)
        self.log("✓ %s=%s" % (key, val), "success"); return True

    def _sysctl_del(self, key, default):
        if self.dry_run:
            self.log("[DRY RUN] remove %s" % key, "warning"); return True
        path = "/etc/sysctl.d/99-gaming-sysctl.conf"
        content = self.read_file(path) or ""
        rx = re.compile(r"^\s*%s\s*=" % re.escape(key))
        old = lines_in(content)
        out = [l for l in old if not rx.match(l)]
        if len(out) == len(old):
            self.log("%s not found in %s" % (key, path), "info")
        else:
            self.backup_file(path)
            self.write_file(path, "\n".join(out) + "\n", backup=False)
        self.sudo_run(["sysctl", "-w", "%s=%s" % (key, default)], ignore_error=True)
        self.log("✓ %s reverted to %s" % (key, default), "success"); return True

    def apply_sysctl_cache(self, params=None):
        return self._sysctl_set("vm.vfs_cache_pressure", "50")

    def apply_sysctl_numa(self, params=None):
        return self._sysctl_set("kernel.numa_balancing", "0")

    def apply_reisub(self, params=None):
        path = "/etc/sysctl.d/99-sysrq.conf"
        content = "kernel.sysrq = 244\n"
        if self.write_file(path, content, chmod="644", mkdir=True):
            self.sudo_run(["sysctl", "-p", path], ignore_error=True)
            self.log("✓ Magic SysRq (REISUB) enabled (kernel.sysrq=244)", "success")
            return True
        return False

    def apply_ntsync(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] ntsync modules-load", "warning"); return True
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
        if not self.path_exists(path):
            self.log("mint-blacklist-ntfs3.conf not found", "warning")
            return True
        content = self.read_file(path)
        if content is None:
            self.log("Cannot read %s" % path, "error"); return False
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

    def _uuid_of(self, dev):
        try:
            res = subprocess.run(["lsblk", "-no", "UUID", dev],
                                 capture_output=True, text=True, timeout=5)
            return res.stdout.strip() if res.returncode == 0 else ""
        except Exception:
            return ""

    def _fstab_find(self, lines, mp, uuid):
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            f = s.split()
            if len(f) < 4:
                continue
            if f[1] == mp:
                return i, f
            if uuid and f[0].lower() == ("uuid=%s" % uuid).lower():
                return i, f
        return None, None

    def _mount_opts_edit(self, mp, add=True):
        path = "/etc/fstab"
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error"); return False
        dev = next((it["dev"] for it in self.mount_items if mp in it["mps"]), None)
        uuid = self._uuid_of(dev) if dev else ""
        lines = lines_in(content)
        idx, parts = self._fstab_find(lines, mp, uuid)
        if idx is None:
            self.log("%s not found in fstab — skipped" % mp, "warning")
            return False
        opts = [o for o in parts[3].split(",") if not o.startswith("commit=")]
        if add:
            if "noatime" not in opts:
                opts.append("noatime")
        else:
            opts = [o for o in opts if o not in ("noatime", "nodiratime")]
        parts[3] = ",".join(opts)
        lines[idx] = "\t".join(parts)
        self.backup_file(path)
        if not self.write_file(path, "\n".join(lines) + "\n", backup=False):
            return False
        if add:
            self.log("✓ fstab %s: +noatime (after reboot)" % mp, "success")
        else:
            self.log("✓ fstab %s: noatime removed (after reboot)" % mp, "success")
        return True

    def _mount_commit_edit(self, mp, val, add=True):
        path = "/etc/fstab"
        content = self.read_file(path)
        if not content:
            self.log("Cannot read /etc/fstab", "error"); return False
        dev = next((it["dev"] for it in self.mount_items if mp in it["mps"]), None)
        uuid = self._uuid_of(dev) if dev else ""
        lines = lines_in(content)
        idx, parts = self._fstab_find(lines, mp, uuid)
        if idx is None:
            self.log("%s not found in fstab — skipped" % mp, "warning")
            return False
        opts = [o for o in parts[3].split(",") if not o.startswith("commit=")]
        if add:
            opts.append("commit=%s" % val)
        parts[3] = ",".join(opts)
        lines[idx] = "\t".join(parts)
        self.backup_file(path)
        return self.write_file(path, "\n".join(lines) + "\n", backup=False)

    def apply_mount_opts(self, mps):
        if self.dry_run:
            for mp in mps:
                self.log("[DRY RUN] fstab %s +noatime" % mp, "warning")
            return True
        ok = True
        for mp in mps:
            ok = self._mount_opts_edit(mp, True) and ok
        return ok

    def rollback_mount_opts(self, mps):
        if self.dry_run:
            for mp in mps:
                self.log("[DRY RUN] fstab %s -noatime" % mp, "warning")
            return True
        ok = True
        for mp in mps:
            ok = self._mount_opts_edit(mp, False) and ok
        return ok

    def apply_commit(self, params=None):
        params = params or {}
        val = str(params.get("commit_value", "60")).strip() or "60"
        try:
            iv = int(val)
            if iv < 1 or iv > 3600:
                raise ValueError
        except ValueError:
            self.log("Bad commit value: %s (1-3600)" % val, "error")
            return False
        val = str(iv)
        if self.dry_run:
            self.log("[DRY RUN] fstab commit=%s" % val, "warning"); return True
        ok = True
        for m in self.mount_items:
            for mp in m["mps"]:
                ok = self._mount_commit_edit(mp, val, True) and ok
        if ok:
            self.log("✓ fstab commit=%s (after reboot)" % val, "success")
        return ok

    def rollback_commit(self, params=None):
        if self.dry_run:
            self.log("[DRY RUN] fstab remove commit", "warning"); return True
        ok = True
        for m in self.mount_items:
            for mp in m["mps"]:
                ok = self._mount_commit_edit(mp, "", False) and ok
        if ok:
            self.log("✓ fstab commit removed (after reboot)", "success")
        return ok

    def _commit_applied(self):
        try:
            with open("/etc/fstab", "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return False
        if not self.mount_items:
            return False
        for m in self.mount_items:
            found = False
            for line in lines_in(content):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                f2 = s.split()
                if len(f2) >= 4 and f2[1] in m["mps"]:
                    if any(o.startswith("commit=") for o in f2[3].split(",")):
                        found = True
                        break
            if not found:
                return False
        return True

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
                    self.log("Skipped: %s exists as data directory" % dst, "warning")
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
            self.log("[DRY RUN] add commands to .bashrc", "warning"); return True
        if not self.path_exists(bashrc):
            self.log(".bashrc not found: %s" % bashrc, "error"); return False
        content = self.read_file(bashrc)
        if content is None:
            self.log("Cannot read .bashrc", "error"); return False
        sm = "# >>> system-tuneup commands >>>"
        em = "# <<< system-tuneup commands <<<"
        without, skip = [], False
        for line in lines_in(content):
            if line.strip() == sm:
                skip = True; continue
            if line.strip() == em:
                skip = False; continue
            if not skip:
                without.append(line)
        names = ["upd", "upgr", "spices", "update_all", "inst", "remove", "search",
                 "info", "clean", "space", "fix", "mem", "serv", "update_time"]
        np_ = "|".join(names)
        alias_rx = re.compile(r"^\s*alias\s+(" + np_ + r")=")
        func_rx = re.compile(r"^\s*(" + np_ + r")\s*\(\)\s*\{")
        cleaned, skip_fn = [], False
        for line in without:
            if alias_rx.match(line):
                continue
            if func_rx.match(line):
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
            block.append('    echo "Flatpak update..."')
            if spices:
                block.append("    flatpak update && cinnamon-spice-updater --update-all")
            else:
                block.append("    flatpak update")
        block += ["}", ""]
        if spices:
            block += ["spices() {", '    echo "Cinnamon spices update..."',
                      "    cinnamon-spice-updater --update-all", "}", ""]
        block += ["update_all() {", "    sudo apt update && sudo apt full-upgrade -y"]
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
        block += ["clean() {", "    sudo apt autoremove -y && sudo apt autoclean && sudo apt clean", "}", ""]
        block += ["space() {", "    df -h /", "}", ""]
        block += ["fix() {", "    sudo apt --fix-broken install -y && sudo dpkg --configure -a", "}", ""]
        block += ["mem() {", "    sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' && free -h", "}", ""]
        block += ["serv() {", "    systemctl list-unit-files --type=service | less", "}", ""]
        block += ["update_time() {",
                  "    systemctl list-timers --no-pager 2>/dev/null | "
                  'grep -E "NEXT|upgrade|update|apt" || echo "No timers"', "}", ""]
        block.append(em)
        while cleaned and cleaned[-1].strip() == "":
            cleaned.pop()
        new = "\n".join(cleaned + [""] + block) + "\n"
        if new == content:
            self.log("Commands already added", "info"); return True
        self.backup_file(bashrc)
        if not self.write_file(bashrc, new, backup=False):
            return False
        if self.state.user_name and self.state.user_name != "root":
            self.sudo_run(["chown", "%s:%s" % (self.state.user_name, self.state.user_name),
                           bashrc], ignore_error=True)
        self.log("✓ commands added to .bashrc", "success"); return True

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
                self.log("Auto-update timer not found", "info"); return True
            if self.dry_run:
                self.log("[DRY RUN] remove timer", "warning"); return True
            self.sudo_run(["systemctl", "disable", "--now", "biweekly-upgrade.timer"],
                          ignore_error=True)
            self.sudo_run(["rm", "-f", svc, tmr], ignore_error=True)
            self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
            self.log("Auto-update timer removed", "success"); return True
        if sched not in table:
            self.log("Unknown schedule: %s" % sched, "error"); return False
        onc, desc = table[sched]
        spices = self._spices()
        cmd = "apt update && apt full-upgrade -y"
        if self.state.has_flatpak:
            cmd += " && flatpak update -y"
        if spices:
            cmd += " && cinnamon-spice-updater --update-all"
        svc_c = ("[Unit]\nDescription=System upgrade (%s)\n\n[Service]\nType=oneshot\n"
                 "ExecStartPre=/bin/sleep 600\nExecStart=/usr/bin/bash -c \"%s\"\n"
                 "User=root\n" % (desc, cmd))
        tmr_c = ("[Unit]\nDescription=System upgrade timer (%s)\n\n[Timer]\n"
                 "OnCalendar=%s\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n"
                 % (desc, onc))
        ex_svc = self.read_file(svc) or ""
        ex_tmr = self.read_file(tmr) or ""
        if exists and ex_svc == svc_c and ex_tmr == tmr_c:
            self.log("Timer already configured: %s" % desc, "info")
            if self.service_enabled("biweekly-upgrade.timer") != "enabled" and not self.dry_run:
                self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
                self.sudo_run(["systemctl", "enable", "--now", "biweekly-upgrade.timer"],
                              ignore_error=True)
            return True
        if self.dry_run:
            self.log("[DRY RUN] create timer: %s" % desc, "warning"); return True
        if self.service_enabled("mintupdate-automation-upgrade.timer") == "enabled":
            self.log("Disabling mintupdate-automation-upgrade.timer", "info")
            self.sudo_run(["systemctl", "disable", "--now",
                           "mintupdate-automation-upgrade.timer"], ignore_error=True)
        if not self.write_file(svc, svc_c, chmod="644"):
            return False
        if not self.write_file(tmr, tmr_c, chmod="644"):
            return False
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        self.sudo_run(["systemctl", "enable", "--now", "biweekly-upgrade.timer"],
                      ok_msg="✓ timer created: %s" % desc,
                      err_msg="Cannot enable timer")
        return True

    def _rm(self, path):
        if self.dry_run:
            self.log("[DRY RUN] rm %s" % path, "warning"); return True
        if not self.path_exists(path):
            self.log("File not found: %s" % path, "info"); return True
        return self.sudo_run(["rm", "-f", path], ok_msg="✓ removed %s" % path)

    def _remove_line(self, path, pattern):
        if self.dry_run:
            self.log("[DRY RUN] %s: remove %s" % (path, pattern), "warning")
            return True
        content = self.read_file(path)
        if not content:
            self.log("File not found: %s" % path, "info"); return True
        rx = re.compile(pattern)
        old = lines_in(content)
        new = [l for l in old if not rx.match(l.strip())]
        if len(new) == len(old):
            self.log("Line not found in %s" % path, "info"); return True
        self.backup_file(path)
        return self.write_file(path, "\n".join(new) + "\n", backup=False)

    def _remove_grub_params(self, params):
        if self.dry_run:
            self.log("[DRY RUN] GRUB remove: " + " ".join(params), "warning")
            return True
        path = "/etc/default/grub"
        content = self.read_file(path)
        if not content:
            self.log("GRUB not found", "warning"); return False
        new_lines, changed = [], False
        for line in lines_in(content):
            m = re.match(r"^\s*GRUB_CMDLINE_LINUX_DEFAULT=(.*)$", line)
            if m:
                raw = m.group(1).strip().strip('"').strip("'")
                parts = [p for p in raw.split() if p and p not in params]
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
            self.log("[DRY RUN] unmask + enable rsyslog", "warning"); return True
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
        self.log("✓ journald back to defaults", "success")
        return True

    def rollback_audit(self, params=None):
        return self._remove_grub_params(["audit=0"])

    def rollback_raid(self, params=None):
        return self._remove_grub_params(["raid=noautodetect"])

    def rollback_nmi_watchdog(self, params=None):
        return self._remove_grub_params(["nmi_watchdog=0"])

    def rollback_corectrl(self, params=None):
        self._rm("/etc/polkit-1/rules.d/90-corectrl.rules")
        self._rm("/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla")
        self.log("✓ CoreCtrl rule removed", "success"); return True

    def rollback_ppfeaturemask(self, params=None):
        return self._remove_grub_params(["amdgpu.ppfeaturemask=0xffffffff"])

    def rollback_nvidia_modeset(self, params=None):
        return self._remove_grub_params(["nvidia-drm.modeset=1"])

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

    def rollback_bbr(self, params=None):
        self._rm("/etc/sysctl.d/99-bbr.conf")
        self._rm("/etc/modules-load.d/bbr.conf")
        self.sudo_run(["sysctl", "-w", "net.ipv4.tcp_congestion_control=cubic"],
                      ignore_error=True)
        return True

    def rollback_swap(self, params=None):
        self._rm("/etc/sysctl.d/99-gaming-swap.conf")
        self.sudo_run(["sysctl", "-w", "vm.swappiness=60"], ignore_error=True)
        self.log("✓ swappiness back to 60", "success"); return True

    def rollback_zram(self, params=None):
        self._rm("/etc/systemd/zram-generator.conf")
        self.sudo_run(["systemctl", "daemon-reload"], ignore_error=True)
        return True

    def rollback_zswap(self, params=None):
        return self._remove_grub_params(["zswap.enabled=1", "zswap.compressor=zstd",
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
        for line in lines_in(content):
            if line.strip() == sm:
                skip = True; continue
            if line.strip() == em:
                skip = False; continue
            if not skip:
                lines.append(line)
        if len(lines) == len(lines_in(content)):
            self.log("Command block not found", "info"); return True
        self.backup_file(bashrc)
        if self.write_file(bashrc, "\n".join(lines) + "\n", backup=False):
            self.log("✓ commands removed from .bashrc", "success"); return True
        return False

    def rollback_autoupdate(self, params=None):
        return self.apply_autoupdate({"update_schedule": "Отключено"})


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
    spawn = pyqtSignal(object)


class Task(QThread):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.fn()
        except Exception:
            traceback.print_exc()


class StripeProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._off = 0
        self.theme_colors = THEMES["light"]
        self.setMinimumHeight(14)
        self.setMaximumHeight(14)
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(50)

    def set_value(self, v):
        self._value = max(0, min(100, v))
        self.update()

    def _tick(self):
        if 0 < self._value < 100 and self.isVisible():
            self._off = (self._off + 2) % 28
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        th = self.theme_colors
        p.setBrush(QColor(th["panel"]))
        p.drawRoundedRect(self.rect(), 7, 7)
        w = int(self.width() * self._value / 100.0)
        if w > 2:
            g = QLinearGradient(0, 0, self.width(), 0)
            g.setColorAt(0, QColor(th["accent"]))
            g.setColorAt(1, QColor(th["accent2"]))
            p.setBrush(g)
            p.drawRoundedRect(QRect(0, 0, w, self.height()), 7, 7)
            p.setClipRect(0, 0, w, self.height())
            p.setBrush(QColor(255, 255, 255, 45))
            h = self.height()
            for x in range(-28, self.width() + 28, 28):
                path = QPainterPath()
                path.moveTo(x + self._off, h)
                path.lineTo(x + self._off + 9, h)
                path.lineTo(x + self._off + 21, 0)
                path.lineTo(x + self._off + 12, 0)
                path.closeSubpath()
                p.drawPath(path)
        p.end()


class LogoWidget(QWidget):
    def __init__(self, size=34, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0.0
        self._size = size
        self.theme_accent = "#2e9e83"
        t = QTimer(self)
        t.timeout.connect(self._spin)
        t.start(45)

    def _spin(self):
        self._angle = (self._angle + 1.2) % 360
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self._size / 2, self._size / 2)
        p.rotate(self._angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(_gear_path(0, 0, self._size * 0.42),
                   QBrush(QColor(self.theme_accent)))
        p.end()


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
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
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


class DraggableDialog(QDialog):
    """Модальный frameless-диалог, который можно перетаскивать за фон/шапку."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


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
        self.badges = {}
        self.mount_badges = {}
        self.steam_badges = {}
        self.option_widgets = {}
        self.opts_state = {k: False for k in OPTIONS_META}
        self.mount_state = {}
        self.steam_state = {}
        self._tasks = []
        self._ram_cache = None
        self._info_dlg = None
        self.sched_lbl = None
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
        self.schedule_value = self._schedule_values()[2]
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
        self.steam_items = []
        for lib in find_steam_libraries(self.state.user_home):
            if self._lib_on_ntfs(lib):
                self.steam_items.append(lib)
                self.steam_state[lib] = False
        scr = QApplication.primaryScreen()
        geo = scr.geometry()
        self.screen_w, self.screen_h = geo.width(), geo.height()
        self.refresh_rate = scr.refreshRate()
        avail = scr.availableGeometry()
        self.avail_w, self.avail_h = avail.width(), avail.height()
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
        self.sig.spawn.connect(self._spawn_task)
        self.build_ui()
        self.log("%s v%s запущен" % (APP_NAME, APP_VERSION), "success")
        self.log("GPU: %s %s" % (self.state.gpu, self.state.gpu_model), "info")
        QTimer.singleShot(300, lambda: self._spawn_task(self._services_work))
        QTimer.singleShot(600, lambda: self._spawn_task(self._applied_work))
        QTimer.singleShot(900, lambda: self._spawn_task(self._status_work))

    def t(self, k):
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
            fstype = self._fstype_of(dev)
        return fstype in ("ntfs", "ntfs3", "fuseblk")

    def _fstype_of(self, dev):
        try:
            res = subprocess.run(["lsblk", "-no", "FSTYPE", dev], capture_output=True,
                                 text=True, timeout=5, env=self._host_env())
            out = res.stdout.strip().splitlines()
            return out[0] if out else ""
        except Exception:
            return ""

    def _gpu_driver(self):
        name = ""
        try:
            res = subprocess.run(["lspci", "-k"], capture_output=True, text=True,
                                 timeout=5, env=self._host_env())
            lines = res.stdout.splitlines()
            for i, ln in enumerate(lines):
                if "VGA compatible controller" in ln or "3D controller" in ln:
                    for j in range(i + 1, min(i + 4, len(lines))):
                        m = re.search(r"Kernel driver in use:\s*(\S+)", lines[j])
                        if m:
                            name = m.group(1)
                            break
                    break
        except Exception:
            pass
        ver = ""
        if name == "nvidia":
            try:
                res = subprocess.run(["nvidia-smi", "--query-gpu=driver_version",
                                      "--format=csv,noheader"],
                                     capture_output=True, text=True,
                                     timeout=5, env=self._host_env())
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
                res = subprocess.run(["dpkg-query", "-W", "-f=${Version}", pkg],
                                     capture_output=True, text=True,
                                     timeout=5, env=self._host_env())
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
            return ""

    def _disk_info(self, path):
        try:
            st = os.statvfs(path)
            total = st.f_blocks * st.f_frsize / 1024.0 ** 3
            free = st.f_bavail * st.f_frsize / 1024.0 ** 3
            return total, free
        except Exception:
            return None

    def _spawn_task(self, fn):
        self._tasks = [t for t in self._tasks if t.isRunning()]
        t = Task(fn)
        self._tasks.append(t)
        t.start()
        return t

    def log(self, msg, tag="normal"):
        self.sig.log.emit(msg, tag)

    def build_ui(self):
        c = self.colors()
        qss = QSS
        for _k, _v in c.items():
            qss = qss.replace("{" + _k + "}", _v)
        self.setStyleSheet(qss)
        self.setWindowTitle("%s v%s" % (APP_NAME, APP_VERSION))
        self.setWindowIcon(QIcon(make_icon("logo", 64, c["accent"])))
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.logo = LogoWidget(34)
        self.logo.theme_accent = c["accent"]
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
        self.theme_btn = QPushButton()
        self.theme_btn.clicked.connect(self.toggle_theme)
        head.addWidget(self.theme_btn)
        root.addLayout(head)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._build_tune(c)
        self._build_serv(c)
        self._build_stat(c)
        bar = QHBoxLayout()
        bar.setSpacing(8)
        bar.addStretch(1)
        ab = QPushButton(self.t("btn_about"))
        ab.setIcon(QIcon(make_icon("help", 36, c["yellow"])))
        ab.clicked.connect(self.show_about)
        bar.addWidget(ab)
        ex = QPushButton(self.t("btn_export"))
        ex.setIcon(QIcon(make_icon("export", 36, c["blue"])))
        ex.clicked.connect(self.export_config)
        bar.addWidget(ex)
        root.addLayout(bar)
        tl = QLabel(self.t("lbl_terminal"))
        tl.setStyleSheet("color: %s;" % c["gray"])
        root.addWidget(tl)
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumHeight(150)
        self.terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.terminal.customContextMenuRequested.connect(
            lambda p: self._menu_for(self.terminal, p))
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
        self.toast_w = Toast(central)
        self.theme_btn.setText(self.t("theme_dark") if self.theme == "light"
                               else self.t("theme_light"))
        self.apply_hardware_restrictions()
        self.resize(min(1080, self.avail_w - 40), min(820, self.avail_h - 40))

    def _build_tune(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, QIcon(make_icon("gear", 40, c["accent"])),
                         self.t("tab_tune"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        bar = QHBoxLayout()
        bar.setSpacing(8)
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
        sa.setIcon(QIcon(make_icon("selall", 30, c["blue"])))
        sa.clicked.connect(self.select_all_options)
        bar.addWidget(sa)
        sn = QPushButton(self.t("btn_selnone"))
        sn.setIcon(QIcon(make_icon("selnone", 30, c["gray"])))
        sn.clicked.connect(self.reset_options)
        bar.addWidget(sn)
        bar.addStretch(1)
        lay.addLayout(bar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("optinner")
        vl = QVBoxLayout(inner)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.setSpacing(2)
        cats = {}
        for k in OPTIONS_META:
            cats.setdefault(self.om(k)[2], []).append(k)
        order = CAT_ORDER[self.lang]
        seq = [x for x in order if x in cats] + \
              [x for x in sorted(cats) if x not in order]
        disk_cat = self.om("ntfs3")[2]
        for cat in seq:
            h = QLabel("─── %s ───" % cat)
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;" % c["yellow"])
            vl.addWidget(h)
            vl.addSpacing(2)
            for k in cats[cat]:
                vl.addWidget(self._option_row(c, k))
            if cat == disk_cat:
                self._disk_extras(vl, c)
        vl.addStretch(1)
        scroll.setWidget(inner)
        lay.addWidget(scroll)

    def _option_row(self, c, key):
        label, desc, _cat, _short = self.om(key)
        row = QFrame()
        row.setObjectName("optrow")
        vl = QVBoxLayout(row)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(2)
        top = QHBoxLayout()
        top.setSpacing(8)
        cb = QCheckBox(label)
        cb.setChecked(self.opts_state[key])
        cb.toggled.connect(lambda v, k=key: self.opts_state.__setitem__(k, v))
        top.addWidget(cb)
        self.option_widgets[key] = cb
        if key == "corectrl":
            top.addWidget(QLabel(self.t("lbl_group")))
            le = QLineEdit(self.corectrl_group)
            le.setFixedWidth(120)
            le.textChanged.connect(lambda v: setattr(self, "corectrl_group", v))
            top.addWidget(le)
        elif key == "swap":
            top.addWidget(QLabel(self.t("lbl_value")))
            le = QLineEdit(self.swap_value)
            le.setFixedWidth(60)
            le.textChanged.connect(lambda v: setattr(self, "swap_value", v))
            top.addWidget(le)
        elif key == "commit":
            top.addWidget(QLabel(self.t("lbl_value")))
            le = QLineEdit(self.commit_value)
            le.setFixedWidth(60)
            le.textChanged.connect(lambda v: setattr(self, "commit_value", v))
            top.addWidget(le)
        elif key == "thp":
            top.addWidget(QLabel(self.t("lbl_value")))
            combo = QComboBox()
            combo.addItems(["always", "madvise", "never"])
            combo.setCurrentText(self.thp_value)
            combo.currentTextChanged.connect(lambda v: setattr(self, "thp_value", v))
            top.addWidget(combo)
        elif key == "autoupdate":
            top.addWidget(QLabel(self.t("lbl_schedule")))
            combo = QComboBox()
            combo.addItems(self._schedule_values())
            combo.setCurrentText(self.schedule_value)
            combo.currentTextChanged.connect(lambda v: setattr(self, "schedule_value", v))
            top.addWidget(combo)
            self.sched_lbl = QLabel()
            self.sched_lbl.setStyleSheet("color: %s;" % c["gray"])
            top.addWidget(self.sched_lbl)
        badge = QLabel("…")
        top.addWidget(badge)
        self.badges[key] = badge
        fb = QPushButton(self.t("btn_file"))
        fb.setIcon(QIcon(make_icon("file", 30, c["blue"])))
        fb.setFixedHeight(26)
        fb.clicked.connect(lambda _c, k=key: self.open_option_file(k))
        top.addWidget(fb)
        qb = QPushButton(self.t("btn_q"))
        qb.setObjectName("qbtn")
        qb.setFixedSize(26, 26)
        qb.clicked.connect(lambda _c, k=key: self._show_option_help(k))
        top.addWidget(qb)
        top.addStretch(1)
        vl.addLayout(top)
        dl = QLabel(desc)
        dl.setWordWrap(True)
        dl.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
        vl.addWidget(dl)
        return row

    def _disk_extras(self, vl, c):
        if self.mount_items:
            vl.addSpacing(6)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: %s;" % c["border"])
            vl.addWidget(sep)
            hh = QHBoxLayout()
            h = QLabel("─── %s ───" % self.t("mount_title"))
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;" % c["yellow"])
            hh.addWidget(h)
            fb = QPushButton(self.t("btn_file"))
            fb.setIcon(QIcon(make_icon("file", 30, c["blue"])))
            fb.setFixedHeight(24)
            fb.clicked.connect(lambda _c: self._open_path("/etc/fstab"))
            hh.addWidget(fb)
            qb = QPushButton(self.t("btn_q"))
            qb.setObjectName("qbtn")
            qb.setFixedSize(26, 26)
            qb.clicked.connect(lambda _c: self._show_option_help("mount"))
            hh.addWidget(qb)
            hh.addStretch(1)
            vl.addLayout(hh)
            d = QLabel(self.t("mount_desc"))
            d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            vl.addWidget(d)
            for m in self.mount_items:
                row = QFrame()
                row.setObjectName("optrow")
                hl = QHBoxLayout(row)
                hl.setContentsMargins(8, 4, 8, 4)
                cb = QCheckBox("%s (%s)" % (", ".join(m["mps"]), m["dev"]))
                cb.setChecked(self.mount_state.get(m["mps"][0], False))
                cb.toggled.connect(lambda v, k=m["mps"][0]: self.mount_state.__setitem__(k, v))
                hl.addWidget(cb)
                badge = QLabel("…")
                hl.addWidget(badge)
                self.mount_badges[m["mps"][0]] = badge
                hl.addStretch(1)
                vl.addWidget(row)
        if self.steam_items:
            vl.addSpacing(6)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: %s;" % c["border"])
            vl.addWidget(sep)
            hh = QHBoxLayout()
            h = QLabel("─── %s ───" % self.t("steam_title"))
            h.setStyleSheet("color: %s; font-weight: bold; font-size: 13px;" % c["yellow"])
            hh.addWidget(h)
            qb = QPushButton(self.t("btn_q"))
            qb.setObjectName("qbtn")
            qb.setFixedSize(26, 26)
            qb.clicked.connect(lambda _c: self._show_option_help("steam"))
            hh.addWidget(qb)
            hh.addStretch(1)
            vl.addLayout(hh)
            d = QLabel(self.t("steam_desc"))
            d.setWordWrap(True)
            d.setStyleSheet("color: %s; font-size: 12px;" % c["gray"])
            vl.addWidget(d)
            for lib in self.steam_items:
                row = QFrame()
                row.setObjectName("optrow")
                hl = QHBoxLayout(row)
                hl.setContentsMargins(8, 4, 8, 4)
                cb = QCheckBox(lib)
                cb.setChecked(self.steam_state.get(lib, False))
                cb.toggled.connect(lambda v, k=lib: self.steam_state.__setitem__(k, v))
                hl.addWidget(cb)
                badge = QLabel("…")
                hl.addWidget(badge)
                self.steam_badges[lib] = badge
                hl.addStretch(1)
                vl.addWidget(row)

    def _build_serv(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, QIcon(make_icon("services", 40, c["blue"])),
                         self.t("tab_serv"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        btns = QHBoxLayout()
        btns.setSpacing(8)
        for txt, fn, ik, ic in ((self.t("btn_selall"), self.select_all_services, "selall", c["blue"]),
                                (self.t("btn_selnone"), self.clear_services_selection, "selnone", c["gray"]),
                                (self.t("svc_off_sel"), self.disable_selected, "off", c["orange"]),
                                (self.t("svc_on_sel"), self.enable_selected, "on", c["green"])):
            b = QPushButton(txt)
            b.setIcon(QIcon(make_icon(ik, 30, ic)))
            b.clicked.connect(fn)
            btns.addWidget(b)
        btns.addStretch(1)
        lay.addLayout(btns)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([self.t("svc_name"), self.t("svc_state"),
                                              self.t("svc_run"), self.t("svc_desc"),
                                              self.t("svc_help")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(4, 34)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.itemSelectionChanged.connect(self._serv_detail)
        lay.addWidget(self.table, 1)
        hint = QLabel(self.t("svc_hint"))
        hint.setStyleSheet("color: %s;" % c["gray"])
        lay.addWidget(hint)
        self.serv_detail = QTextEdit()
        self.serv_detail.setReadOnly(True)
        self.serv_detail.setMaximumHeight(80)
        self.serv_detail.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.serv_detail.customContextMenuRequested.connect(
            lambda p: self._menu_for(self.serv_detail, p))
        lay.addWidget(self.serv_detail)

    def _build_stat(self, c):
        tab = QWidget()
        self.tabs.addTab(tab, QIcon(make_icon("status", 40, c["green"])),
                         self.t("tab_stat"))
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        b = QPushButton(self.t("stat_refresh"))
        b.setIcon(QIcon(make_icon("status", 32, c["green"])))
        b.clicked.connect(lambda: self._spawn_task(self._status_work))
        lay.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        self.stat_view = QTextEdit()
        self.stat_view.setReadOnly(True)
        self.stat_view.setStyleSheet("font-size: 15px;")
        self.stat_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stat_view.customContextMenuRequested.connect(
            lambda p: self._menu_for(self.stat_view, p))
        lay.addWidget(self.stat_view, 1)

    def _menu_for(self, w, pos):
        menu = QMenu(self)
        a1 = menu.addAction(self.t("menu_copy"))
        a1.triggered.connect(lambda: self._copy_sel(w))
        a2 = menu.addAction(self.t("menu_copy_all"))
        a2.triggered.connect(lambda: QApplication.clipboard().setText(w.toPlainText()))
        a3 = menu.addAction(self.t("menu_select_all"))
        a3.triggered.connect(lambda: w.selectAll())
        menu.exec(w.mapToGlobal(pos))

    def _copy_sel(self, w):
        cur = w.textCursor()
        if cur.hasSelection():
            QApplication.clipboard().setText(cur.selectedText())

    def _show_option_help(self, key):
        txt = OPTIONS_HELP.get(key, {}).get(self.lang, "")
        if not txt:
            return
        title = self.om(key)[0] if key in OPTIONS_META else \
            (self.t("mount_title") if key == "mount" else self.t("steam_title"))
        self._open_info_dialog(title, "<p style='font-size:14px;'>%s</p>" % txt)

    def _show_service_help(self, name):
        txt = SERVICES_HELP.get(name, {}).get(self.lang, "")
        if not txt:
            return
        self._open_info_dialog(name, "<p style='font-size:14px;'>%s</p>" % txt)

    def _open_info_dialog(self, title, html):
        c = self.colors()
        dlg = DraggableDialog(self)
        dlg.setObjectName("infodlg")
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        dlg.setModal(True)
        self._info_dlg = dlg
        dlg.resize(min(720, self.screen_w - 60), min(560, self.screen_h - 80))
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(14, 14, 14, 14)
        hd = QHBoxLayout()
        tl = QLabel(title)
        tl.setStyleSheet("font-size: 16px; font-weight: bold; color: %s;" % c["accent"])
        hd.addWidget(tl)
        hd.addStretch(1)
        cb = QPushButton()
        cb.setIcon(QIcon(make_icon("close", 22, c["red"])))
        cb.setFixedSize(28, 28)
        cb.clicked.connect(dlg.close)
        hd.addWidget(cb)
        vl.addLayout(hd)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setOpenExternalLinks(True)
        te.setHtml(html)
        vl.addWidget(te)
        dlg.exec()
        self._info_dlg = None

    def show_about(self):
        c = self.colors()
        dlg = DraggableDialog(self)
        dlg.setObjectName("infodlg")
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        dlg.setModal(True)
        self._info_dlg = dlg
        dlg.resize(min(640, self.screen_w - 60), min(420, self.screen_h - 80))
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(18, 18, 18, 18)
        hd = QHBoxLayout()
        tl = QLabel(self.t("about_title"))
        tl.setStyleSheet("font-size: 18px; font-weight: bold; color: %s;" % c["accent"])
        hd.addWidget(tl)
        hd.addStretch(1)
        cb = QPushButton()
        cb.setIcon(QIcon(make_icon("close", 22, c["red"])))
        cb.setFixedSize(28, 28)
        cb.clicked.connect(dlg.close)
        hd.addWidget(cb)
        vl.addLayout(hd)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setOpenExternalLinks(True)
        html = ('<div style="font-family: monospace;">'
                '<h2 style="color:%s;">%s v%s</h2>'
                '<p>%s</p>'
                '<p><b>%s:</b> %s</p>'
                '<p><b>%s:</b> %s</p>'
                '<p><a href="%s">%s</a></p></div>'
                % (c["accent"], APP_NAME, APP_VERSION,
                   self.t("about_purpose"),
                   self.t("about_author"), self.t("about_author_name"),
                   self.t("about_ver"), APP_VERSION,
                   GITHUB_URL, GITHUB_URL))
        te.setHtml(html)
        vl.addWidget(te)
        dlg.exec()
        self._info_dlg = None

    def _open_path(self, path):
        ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
        ops.mount_items = self.mount_items
        content = ops.read_file(path) or ""
        self._show_viewer(path, content)

    def _show_viewer(self, path, content):
        dlg = DraggableDialog(self)
        dlg.setWindowTitle("%s: %s" % (self.t("viewer"), path))
        dlg.resize(min(760, self.screen_w - 40), min(520, self.screen_h - 60))
        vl = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(content)
        te.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        te.customContextMenuRequested.connect(lambda p: self._menu_for(te, p))
        vl.addWidget(te)
        b = QPushButton(self.t("viewer_ext"))
        b.clicked.connect(lambda: self._open_ext(path))
        vl.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        dlg.exec()

    def _open_ext(self, path):
        for cmd in (["xed", path], ["mousepad", path], ["gedit", path],
                    ["kate", path], ["pluma", path],
                    ["xdg-open", path], ["gio", "open", path]):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True, env=self._host_env())
                return
            except Exception:
                continue
        self.log("Cannot open external editor for %s" % path, "error")

    def open_option_file(self, key):
        cands = [p.format(home=self.state.user_home) for p in OPTION_FILES.get(key, [])]
        target = next((p for p in cands if os.path.exists(p)), None)
        if target is None and cands:
            if not self.sudo._cached():
                if not self.sudo.ensure():
                    return
            target = next((p for p in cands
                           if subprocess.run(["sudo", "-n", "test", "-e", p],
                                             capture_output=True).returncode == 0),
                          None)
        if target is None:
            if not cands:
                return
            QMessageBox.information(self, self.t("viewer"),
                                    self.t("msg_nofile") + "\n" + "\n".join(cands))
            return
        ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
        ops.mount_items = self.mount_items
        content = ops.read_file(target) or ""
        self._show_viewer(target, content)

    def select_all_options(self):
        for k in self.opts_state:
            w = self.option_widgets.get(k)
            if w is not None and w.isEnabled():
                self.opts_state[k] = True
        for k in self.mount_state:
            self.mount_state[k] = True
        for k in self.steam_state:
            self.steam_state[k] = True
        self._rebuild()

    def reset_options(self):
        for k in self.opts_state:
            self.opts_state[k] = False
        for k in self.mount_state:
            self.mount_state[k] = False
        for k in self.steam_state:
            self.steam_state[k] = False
        self._rebuild()

    def select_all_services(self):
        self.table.selectAll()

    def clear_services_selection(self):
        self.table.clearSelection()

    def _on_cell_clicked(self, row, col):
        if col == 4:
            name = self.table.item(row, 0).text()
            self._show_service_help(name)
            self.table.clearSelection()

    def _serv_detail(self):
        items = self.table.selectedItems()
        names = []
        for it in items:
            if it.column() == 0:
                names.append(it.text())
        parts = ["%s — %s" % (n, SERVICES_META.get(n, {}).get(self.lang, ""))
                 for n in names[:3]]
        self.serv_detail.setPlainText("\n".join(parts))

    def apply_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        selected = [k for k, v in self.opts_state.items() if v]
        mount_sel = [mp for m in self.mount_items if self.mount_state.get(m["mps"][0])
                     for mp in m["mps"]]
        steam_sel = [l for l in self.steam_items if self.steam_state.get(l)]
        if not selected and not mount_sel and not steam_sel:
            QMessageBox.warning(self, APP_NAME, self.t("msg_noopt"))
            return
        params = {"corectrl_group": self.corectrl_group,
                  "swap_value": self.swap_value,
                  "update_schedule": self.schedule_value,
                  "commit_value": self.commit_value,
                  "thp_value": self.thp_value}
        dry = self.dry_check.isChecked()
        if ("autoupdate" in selected and not dry and
                params["update_schedule"] not in ("Отключено", "Disabled")):
            QMessageBox.information(self, APP_NAME, self.t("autoupdate_warn"))
        if not dry and not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        self._ram_cache = None
        self.is_running = True
        self.apply_btn.setEnabled(False)
        self.sig.running.emit(True)
        self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        t = self._spawn_task(lambda: self._apply_work(selected, mount_sel, steam_sel,
                                                      params, dry))
        t.finished.connect(lambda: self.sig.running.emit(False))

    def _apply_work(self, selected, mount_sel, steam_sel, params, dry):
        ops = SystemOps(self.sudo, self.state, self.log, dry)
        ops.mount_items = self.mount_items
        total = len(selected) + (1 if mount_sel else 0) + (1 if steam_sel else 0)
        if total == 0:
            return
        done = 0
        self.log("=" * 60, "highlight")
        self.log("APPLY START" if self.lang == "en" else "ЗАПУСК ТЮНИНГА", "highlight")
        try:
            for k in selected:
                label = self.om(k)[0]
                self.log("→ %s" % label, "info")
                try:
                    getattr(ops, "apply_%s" % k)(params)
                except Exception as e:
                    self.log("Error in %s: %s" % (k, e), "error")
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if mount_sel:
                self.log("→ %s" % self.t("mount_title"), "info")
                ops.apply_mount_opts(mount_sel)
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if steam_sel:
                self.log("→ %s" % self.t("steam_title"), "info")
                ops.apply_steam_links(steam_sel)
                done += 1
                self.sig.progress.emit(int(done / total * 90))
            if not dry:
                ops.finalize_grub()
            self.sig.progress.emit(100)
            self.sig.statusbar.emit(self.t("done"))
            self.log("Done", "success")
            self.sig.toast.emit(self.t("done"), "ok")
            self.sig.spawn.emit(self._applied_work)
            self.sig.spawn.emit(self._status_work)
            self.sig.spawn.emit(self._services_work)
        except Exception as e:
            self.log("Critical error: %s" % e, "error")
            self.sig.statusbar.emit(self.t("done"))

    def rollback_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        selected = [k for k, v in self.opts_state.items() if v]
        mount_sel = [mp for m in self.mount_items if self.mount_state.get(m["mps"][0])
                     for mp in m["mps"]]
        steam_sel = [l for l in self.steam_items if self.steam_state.get(l)]
        if not selected and not mount_sel and not steam_sel:
            QMessageBox.warning(self, APP_NAME, self.t("msg_noopt"))
            return
        dry = self.dry_check.isChecked()
        if not dry and not self.sudo.ensure():
            self.log("sudo failed", "error")
            return
        self._ram_cache = None
        self.is_running = True
        self.apply_btn.setEnabled(False)
        self.sig.running.emit(True)
        self.sig.progress.emit(0)
        self.sig.statusbar.emit(self.t("running"))
        t = self._spawn_task(lambda: self._rollback_work(selected, mount_sel,
                                                         steam_sel, dry))
        t.finished.connect(lambda: self.sig.running.emit(False))

    def _rollback_work(self, selected, mount_sel, steam_sel, dry):
        ops = SystemOps(self.sudo, self.state, self.log, dry)
        ops.mount_items = self.mount_items
        total = len(selected) + (1 if mount_sel else 0) + (1 if steam_sel else 0)
        if total == 0:
            return
        done = 0
        self.log("=" * 60, "highlight")
        self.log("ROLLBACK START" if self.lang == "en" else "ЗАПУСК ОТКАТА", "highlight")
        try:
            for k in selected:
                label = self.om(k)[0]
                self.log("→ %s" % label, "info")
                try:
                    getattr(ops, "rollback_%s" % k)()
                except Exception as e:
                    self.log("Error in %s: %s" % (k, e), "error")
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
            self.sig.statusbar.emit(self.t("done"))
            self.log("Rollback done", "success")
            self.sig.toast.emit(self.t("done"), "ok")
            self.sig.spawn.emit(self._applied_work)
            self.sig.spawn.emit(self._status_work)
            self.sig.spawn.emit(self._services_work)
        except Exception as e:
            self.log("Critical error: %s" % e, "error")
            self.sig.statusbar.emit(self.t("done"))

    def enable_selected(self):
        if self.is_running:
            QMessageBox.information(self, APP_NAME, self.t("msg_run"))
            return
        names = [self.table.item(i, 0).text()
                 for i in range(self.table.rowCount())
                 if self.table.item(i, 0).isSelected()]
        if not names:
            QMessageBox.information(self, APP_NAME, self.t("msg_sel"))
            return
        if not self.sudo.ensure():
            return
        self._spawn_task(lambda: self._enable_work(names))

    def _enable_work(self, names):
        ops = SystemOps(self.sudo, self.state, self.log, self.dry_check.isChecked())
        for name in names:
            if ops.dry_run:
                ops.log("[DRY RUN] enable %s" % name, "warning")
                continue
            ok = ops.sudo_run(["systemctl", "unmask", name], ignore_error=True)
            ok2 = ops.sudo_run(["systemctl", "enable", name], ignore_error=True)
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
        names = [self.table.item(i, 0).text()
                 for i in range(self.table.rowCount())
                 if self.table.item(i, 0).isSelected()]
        if not names:
            QMessageBox.information(self, APP_NAME, self.t("msg_sel"))
            return
        if not self.sudo.ensure():
            return
        self._spawn_task(lambda: self._disable_work(names))

    def _disable_work(self, names):
        ops = SystemOps(self.sudo, self.state, self.log, self.dry_check.isChecked())
        for name in names:
            if ops.dry_run:
                ops.log("[DRY RUN] disable %s" % name, "warning")
                continue
            ok = ops.sudo_run(["systemctl", "disable", "--now", name], ignore_error=True)
            if name.startswith("avahi"):
                ok = ops.sudo_run(["systemctl", "mask", name], ignore_error=True) or ok
            if ok:
                ops.log("✓ %s disabled" % name, "success")
            else:
                ops.log("Cannot disable %s" % name, "warning")
        self.sig.spawn.emit(self._services_work)
        self.sig.spawn.emit(self._status_work)

    def _applied_work(self):
        ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
        ops.mount_items = self.mount_items
        self.sig.applied.emit(self._detect_applied(ops))
        self.sig.mount_applied.emit(self._detect_mount())
        self.sig.steam_applied.emit(self._detect_steam())
        self.sig.schedule.emit(self._schedule_text())

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
                 "*-*-1,15 18:30:00": ("2 раза в месяц (1 и 15)", "Twice a month (1 & 15)"),
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
                  "/usr/share/polkit-1/rules.d/90-corectrl.rules",
                  "/etc/polkit-1/localauthority/50-local.d/90-corectrl.pkla"):
            c = ops.read_file(p)
            if c and "org.corectrl" in c:
                return True
        try:
            res = subprocess.run(["pkcheck", "--action-id",
                                  "org.corectrl.helper.init", "--process",
                                  str(os.getpid())], capture_output=True,
                                 timeout=5, env=self._host_env())
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
        m_sw = re.search(r"^\s*vm\.swappiness\s*=\s*(\d+)\s*$", swp, re.M)
        cur = sv("vm.swappiness")
        pw = os.path.join(self.state.user_home, ".config", "pipewire",
                          "pipewire.conf.d", "10-sound.conf")
        return {
            "rsyslog": ops.service_enabled("rsyslog.service") in ("disabled", "masked"),
            "journald": bool(re.search(r"^\s*Storage\s*=\s*volatile\s*$", j, re.M)),
            "audit": "audit=0" in grub,
            "raid": "raid=noautodetect" in grub,
            "nmi_watchdog": "nmi_watchdog=0" in grub,
            "corectrl": self._corectrl_found(ops),
            "ppfeaturemask": "amdgpu.ppfeaturemask" in grub,
            "nvidia_modeset": "nvidia-drm.modeset=1" in grub,
            "vrr": ops.path_exists("/etc/X11/xorg.conf.d/20-amdgpu.conf"),
            "radv": "RADV_PERFTEST=sam" in env,
            "mesa": "MESA_SHADER_CACHE_MAX_SIZE=4G" in env,
            "pipewire": ops.path_exists(pw),
            "bbr": sv("net.ipv4.tcp_congestion_control") == "bbr"
                     or ops.path_exists("/etc/sysctl.d/99-bbr.conf"),
            "swap": (m_sw and m_sw.group(1) in ("10", "150")) or cur in ("10", "150"),
            "zram": ops.path_exists("/etc/systemd/zram-generator.conf"),
            "zswap": "zswap.enabled=1" in grub,
            "thp": bool(re.search(r"transparent_hugepage=\w+", grub)),
            "sysctl_cache": bool(re.search(r"^vm\.vfs_cache_pressure=50$", sysc, re.M))
                            or sv("vm.vfs_cache_pressure") == "50",
            "sysctl_numa": bool(re.search(r"^kernel\.numa_balancing=0$", sysc, re.M))
                            or sv("kernel.numa_balancing") == "0",
            "reisub": sv("kernel.sysrq") == "244"
                            or ops.path_exists("/etc/sysctl.d/99-sysrq.conf"),
            "ntsync": self.state.ntsync or ops.path_exists("/etc/modules-load.d/ntsync.conf"),
            "ntfs3": bool(re.search(r"^\s*#\s*blacklist\s+ntfs3\s*$", mint, re.M)),
            "commit": ops._commit_applied(),
            "aliases": "system-tuneup" in bashrc,
            "autoupdate": ops.service_enabled("biweekly-upgrade.timer") == "enabled",
        }

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

    def _services_work(self):
        ops = SystemOps(self.sudo, self.state, lambda m, t: None,
                        self.dry_check.isChecked())
        rows = []
        for n in SERVICES_ORDER:
            if not ops.unit_exists(n):
                continue
            desc = SERVICES_META[n][self.lang]
            en = ops.service_enabled(n)
            ac = ops.service_active(n)
            if en == "masked":
                st, col = self.t("svc_masked"), "red"
            elif en == "disabled":
                st, col = self.t("svc_off"), "gray"
            elif ac == "active":
                st, col = self.t("svc_on"), "green"
            else:
                st, col = self.t("svc_onoff"), "yellow"
            run = self.t("run_yes") if ac == "active" else self.t("run_no")
            rows.append((n, st, run, desc, "?", col))
        self.sig.services_rows.emit(rows)

    def _status_work(self):
        fallback = dict(self.applied)
        try:
            ops = SystemOps(self.sudo, self.state, lambda m, t: None, True)
            ops.mount_items = self.mount_items
            try:
                A = self._detect_applied(ops)
                self.sig.applied.emit(A)
            except Exception:
                A = fallback

            def sv(p):
                try:
                    r = subprocess.run(["sysctl", "-n", p], capture_output=True,
                                       text=True, timeout=3)
                    return r.stdout.strip() if r.returncode == 0 else "n/a"
                except Exception:
                    return "n/a"
            vals = {p: sv(p) for p in ("vm.swappiness", "vm.vfs_cache_pressure",
                                      "kernel.numa_balancing",
                                      "net.ipv4.tcp_congestion_control")}
            c = self.colors()

            def col(k):
                return c[k]

            def esc(s):
                return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;"))

            def table(title, headers, rows_html):
                bc = col("border")
                h = ("<table border='1' cellspacing='0' cellpadding='4' width='100%%' "
                     "style='border-collapse:collapse; border:1px solid %s;'>" % bc)
                h += ("<tr><th colspan='%d' style='background:%s; color:%s; "
                      "text-align:left; border:1px solid %s;'>%s</th></tr>"
                      % (len(headers), col("tab"), col("fg"), bc, esc(title)))
                h += "<tr>" + "".join(
                    "<td style='background:%s; color:%s; border:1px solid %s;'><b>%s</b></td>"
                    % (col("panel"), col("gray"), bc, esc(x)) for x in headers) + "</tr>"
                h += "".join(rows_html)
                h += "</table><br>"
                return h

            P = []
            name = ""
            try:
                with open("/etc/os-release", "r", encoding="utf-8", errors="replace") as f:
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
                else:
                    ram_s += " " + self.t("ram_hint")
            if self.state.has_swap:
                tn = {"file": self.t("swap_file"), "partition": self.t("swap_part"),
                      "zram": "zram"}
                sw_s = tn.get(self.state.swap_type, self.state.swap_type)
                sz = self._swap_size_gb()
                if sz:
                    sw_s += ", %.1f %s" % (sz, self.t("gb"))
            else:
                sw_s = self.t("no_swap")
            rate = self.refresh_rate
            scr_s = "%dx%d" % (self.screen_w, self.screen_h)
            if rate and rate > 0:
                scr_s += ", %.0f %s" % (rate, self.t("hz"))
            hw = [(self.t("os_lbl"), "%s (%d-bit)" % (name or "Linux", bits)),
                  (self.t("cpu_lbl"), cpu_model()),
                  (self.t("gpu_lbl"), gpu),
                  (self.t("driver_lbl"), drv_s or "n/a"),
                  (self.t("screen_lbl"), scr_s),
                  (self.t("ram_lbl"), ram_s),
                  (self.t("swap_lbl"), sw_s),
                  (self.t("kernel_lbl"), os.uname().release),
                  (self.t("de_lbl"), desktop_name()),
                  ("RAID", self.t("w_yes") if self.state.has_raid else self.t("w_no")),
                  ("ntsync", self.t("w_yes") if self.state.ntsync else self.t("w_no")),
                  (self.t("user_lbl"), self.state.user_name),
                  (self.t("home_lbl"), self.state.user_home)]
            hw_rows = ["<tr><td style='color:%s;'><b>%s</b></td><td style='color:%s;'>%s</td></tr>"
                       % (col("gray"), esc(k), col("fg"), esc(v)) for k, v in hw]
            P.append(table(self.t("st_hw"), [self.t("st_hw"), ""], hw_rows))
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
                    % (col("fg"), esc(", ".join(info["mps"])), esc(os.path.basename(dev)),
                       col("gray"), esc(info["fstype"]),
                       col("fg"), total, self.t("gb"),
                       col("fg"), free, self.t("gb")))
            P.append(table(self.t("st_parts"),
                           [self.t("part_mount"), self.t("part_fs"),
                            self.t("part_total"), self.t("part_free")], part_rows))
            tw_rows = []
            for k in OPTIONS_META:
                label, _d, _c, short = self.om(k)
                ok = A.get(k, False)
                cc = col("green") if ok else col("red")
                tw_rows.append(
                    "<tr><td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'>%s</td></tr>"
                    % (col("fg"), esc(label), cc,
                       self.t("yes") if ok else self.t("no"), col("gray"), esc(short)))
            for m in self.mount_items:
                ok = self.mount_applied.get(m["mps"][0], False)
                cc = col("green") if ok else col("red")
                tw_rows.append(
                    "<tr><td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'>%s</td></tr>"
                    % (col("fg"), esc(self.t("mount_short")), cc,
                       self.t("yes") if ok else self.t("no"), col("gray"),
                       esc(", ".join(m["mps"]))))
            for lib in self.steam_items:
                ok = self.steam_applied.get(lib, False)
                cc = col("green") if ok else col("red")
                tw_rows.append(
                    "<tr><td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'>%s</td></tr>"
                    % (col("fg"), esc(self.t("steam_short")), cc,
                       self.t("yes") if ok else self.t("no"), col("gray"), esc(lib)))
            P.append(table(self.t("st_tweaks"),
                           [self.t("tw_name"), self.t("yes"), ""], tw_rows))
            sv_rows = []
            for n in SERVICES_ORDER:
                if not ops.unit_exists(n):
                    continue
                en = ops.service_enabled(n)
                ac = ops.service_active(n)
                if en == "masked":
                    cc, w = col("red"), self.t("svc_masked")
                elif en == "disabled":
                    cc, w = col("gray"), self.t("svc_off")
                elif ac == "active":
                    cc, w = col("green"), self.t("svc_on")
                else:
                    cc, w = col("yellow"), self.t("svc_onoff")
                sv_rows.append(
                    "<tr><td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'>%s</td></tr>"
                    % (col("fg"), esc(n), cc, esc(w), col("gray"),
                       esc(SERVICES_META[n][self.lang])))
            P.append(table(self.t("st_services"),
                           [self.t("svc_name"), self.t("svc_state"), self.t("svc_desc")],
                           sv_rows))
            kn_rows = []
            kern = [("vm.swappiness", self.t("kern_sw"), A.get("swap", False)),
                    ("vm.vfs_cache_pressure", self.t("kern_vfs"), A.get("sysctl_cache", False)),
                    ("kernel.numa_balancing", self.t("kern_numa"), A.get("sysctl_numa", False)),
                    ("net.ipv4.tcp_congestion_control", "BBR", A.get("bbr", False))]
            for p, dsc, ok in kern:
                cc = col("green") if ok else col("red")
                kn_rows.append(
                    "<tr><td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'><b>%s</b></td>"
                    "<td style='color:%s;'>%s</td>"
                    "<td style='color:%s;'><b>%s</b></td></tr>"
                    % (col("fg"), esc(p), col("fg"), esc(vals[p]), col("gray"), esc(dsc),
                       cc, self.t("yes") if ok else self.t("no")))
            timer = ops.service_enabled("biweekly-upgrade.timer")
            tcc = col("green") if timer == "enabled" else col("gray")
            kn_rows.append(
                "<tr><td style='color:%s;'><b>%s</b></td>"
                "<td style='color:%s;'><b>%s</b></td>"
                "<td colspan='2'></td></tr>"
                % (col("fg"), esc(self.t("st_timer")), tcc, esc(self._fmt_state(timer))))
            P.append(table(self.t("st_kernel"),
                           [self.t("kn_param"), self.t("kn_val"), "", ""], kn_rows))
            self.sig.status_html.emit("".join(P))
        except Exception as e:
            traceback.print_exc()
            try:
                c = self.colors()
                self.sig.status_html.emit(
                    "<p style='color:%s;'>Status error: %s</p>" % (c["red"], e))
            except Exception:
                pass

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

    def _swap_size_gb(self):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith("SwapTotal:"):
                        return int(line.split()[1]) / 1024.0 / 1024.0
        except Exception:
            pass
        return None

    def _update_badges(self):
        c = self.colors()

        def pill(lbl, ok):
            lbl.setObjectName("badge_yes" if ok else "badge_no")
            lbl.setText(self.t("applied_yes") if ok else self.t("applied_no"))
            lbl.setStyleSheet(
                "background:%s; color:%s; border-radius:7px; padding:3px 9px; font-weight:bold;"
                % (c["green_bg"] if ok else c["gray_bg"],
                   c["green"] if ok else c["gray"]))
        for k, b in self.badges.items():
            pill(b, self.applied.get(k, False))
        for k, b in self.mount_badges.items():
            pill(b, self.mount_applied.get(k, False))
        for k, b in self.steam_badges.items():
            pill(b, self.steam_applied.get(k, False))

    def _on_log(self, msg, tag):
        c = self.colors()
        colors = {"normal": c["terminal_fg"], "success": c["green"], "error": c["red"],
                  "warning": c["yellow"], "info": c["blue"], "highlight": c["orange"]}
        esc = (msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertHtml("<span style='color:%s;'>%s</span>"
                                 % (colors.get(tag, c["terminal_fg"]), esc))
        self.terminal.insertPlainText("\n")
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def _on_statusbar(self, s):
        self.status_lbl.setText(s)

    def _on_progress(self, v):
        self.progress.set_value(v)

    def _on_running(self, r):
        self.is_running = r
        self.apply_btn.setEnabled(not r)

    def _on_applied(self, d):
        self.applied = d
        self._update_badges()

    def _on_mount_applied(self, d):
        self.mount_applied = d
        self._update_badges()

    def _on_steam_applied(self, d):
        self.steam_applied = d
        self._update_badges()

    def _on_schedule(self, s):
        if self.sched_lbl is not None:
            self.sched_lbl.setText(self.t("sched_cur") % s)

    def _on_services_rows(self, rows):
        c = self.colors()
        self.table.setRowCount(0)
        for r in rows:
            n, st, run, desc, q, col = r
            row = self.table.rowCount()
            self.table.insertRow(row)
            for ci, val in enumerate((n, st, run, desc, q)):
                it = QTableWidgetItem(val)
                it.setForeground(QColor(c[col]))
                if ci == 4:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    it.setForeground(QColor(c["blue"]))
                self.table.setItem(row, ci, it)
            self.table.item(row, 0).setToolTip(n)

    def _on_status_html(self, html):
        self.stat_view.setHtml(html)

    def _on_toast(self, text, kind):
        self.toast_w.show_msg(text, kind, self.colors())

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._rebuild()

    def toggle_lang(self):
        current = self.schedule_value
        ru_vals = ("Отключено", "Ежедневно", "Еженедельно (суббота)",
                   "2 раза в месяц (1 и 15)", "Ежемесячно (1 число)")
        en_vals = ("Disabled", "Daily", "Weekly (Saturday)",
                   "Twice a month (1 & 15)", "Monthly (1st)")
        self.lang = "en" if self.lang == "ru" else "ru"
        if self.lang == "ru":
            self.schedule_value = dict(zip(en_vals, ru_vals)).get(current, current)
        else:
            self.schedule_value = dict(zip(ru_vals, en_vals)).get(current, current)
        self._rebuild()

    def _rebuild(self):
        hist = self.terminal.toPlainText() if hasattr(self, "terminal") else ""
        self.badges = {}
        self.mount_badges = {}
        self.steam_badges = {}
        self.option_widgets = {}
        self.sched_lbl = None
        old = self.centralWidget()
        if old is not None:
            old.hide()
            old.setParent(None)
            old.deleteLater()
        self.build_ui()
        if hist:
            self.terminal.setPlainText(hist)
            self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self._update_badges()
        self._spawn_task(self._services_work)
        self._spawn_task(self._status_work)
        self._spawn_task(self._applied_work)

    def apply_hardware_restrictions(self):
        if self.state.gpu not in ("AMD", "Unknown"):
            for k in ("corectrl", "ppfeaturemask", "vrr", "radv"):
                w = self.option_widgets.get(k)
                if w is not None:
                    w.setEnabled(False)
                self.opts_state[k] = False
        if self.state.gpu not in ("NVIDIA", "Unknown"):
            w = self.option_widgets.get("nvidia_modeset")
            if w is not None:
                w.setEnabled(False)
            self.opts_state["nvidia_modeset"] = False
        if self.state.has_raid:
            w = self.option_widgets.get("raid")
            if w is not None:
                w.setEnabled(False)
            self.opts_state["raid"] = False
        if not self.state.has_swap:
            w = self.option_widgets.get("swap")
            if w is not None:
                w.setEnabled(False)
            self.opts_state["swap"] = False
        if not os.path.exists("/usr/lib/modprobe.d/mint-blacklist-ntfs3.conf"):
            w = self.option_widgets.get("ntfs3")
            if w is not None:
                w.setEnabled(False)
            self.opts_state["ntfs3"] = False

    def export_config(self):
        selected = [k for k, v in self.opts_state.items() if v]
        if not selected:
            QMessageBox.information(self, APP_NAME, self.t("msg_noopt"))
            return
        path, _ = QFileDialog.getSaveFileName(self, self.t("btn_export"),
                                              os.path.expanduser("~/tweaker-config.txt"),
                                              "Text files (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("%s v%s\n%s\ndry_run=%s\n\n" % (APP_NAME, APP_VERSION,
                                                       time.strftime("%Y-%m-%d %H:%M:%S"),
                                                       self.dry_check.isChecked()))
                for k in selected:
                    f.write("%s: %s\n" % (k, self.om(k)[0]))
                f.write("\n[parameters]\ncorectrl_group=%s\nswap_value=%s\n"
                        "commit_value=%s\nthp_value=%s\nupdate_schedule=%s\n"
                        % (self.corectrl_group, self.swap_value, self.commit_value,
                           self.thp_value, self.schedule_value))
            self.log("Config saved: %s" % path, "success")
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))

    def closeEvent(self, e):
        if self.is_running:
            r = QMessageBox.question(self, APP_NAME, self.t("msg_close"))
            if r != QMessageBox.StandardButton.Yes:
                e.ignore()
                return
        e.accept()


QSS = """
QMainWindow, QWidget#central { background: {bg}; }
QScrollArea { background: {panel}; border: none; }
QScrollArea > QWidget > QWidget { background: {panel}; }
QWidget#optinner { background: {panel}; }
QTabWidget::pane { border: 1px solid {border}; border-radius: 10px; background: {panel}; }
QTabBar::tab { background: {tab}; color: {fg}; padding: 9px 22px; border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 3px; }
QTabBar::tab:selected { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {accent}, stop:1 {accent2}); color: {accent_fg}; font-weight: bold; }
QTabBar::tab:hover:!selected { background: {tab_hover}; }
QPushButton { background: {button}; color: {fg}; border: none; border-radius: 9px; padding: 8px 14px; }
QPushButton:hover { background: {button_hover}; }
QPushButton:disabled { background: {button_dis}; color: {fg_dis}; }
QPushButton#accent { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {accent}, stop:1 {accent2}); color: {accent_fg}; font-weight: bold; }
QPushButton#accent:hover { background: {accent2}; }
QPushButton#qbtn { background: {button}; color: {blue}; font-weight: bold; border-radius: 12px; padding: 2px 8px; }
QCheckBox { color: {fg}; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 2px solid {scroll}; background: {panel}; }
QCheckBox::indicator:checked { background: {accent}; border-color: {accent}; }
QCheckBox:disabled { color: {fg_dis}; }
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
QToolTip { background: {panel}; color: {fg}; border: 1px solid {border}; }
QDialog#infodlg { background: {panel}; border: 2px solid {accent}; border-radius: 12px; }
"""


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("%s v%s\npython3 linux_tweaker.py [--dry-run]" % (APP_NAME, APP_VERSION))
        sys.exit(0)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
