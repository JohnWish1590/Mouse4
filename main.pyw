"""
Mouse4 V107 - 混合 DPI 逐屏抓取跨屏截图
核心：物理像素模式 + 逐屏抓取拼接(消除混合 DPI 下单次 BitBlt 的接缝白条)
重写工具栏定位逻辑(下方放不下/落进空隙带时自动翻到上方)
"""

import sys
import os
import ctypes
import ctypes.wintypes
import datetime
import threading
import time
import webbrowser
import math
import subprocess
import json
import atexit
import winreg
import traceback
from pathlib import Path
from io import BytesIO

# GUI 库
from PyQt6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QMessageBox, QStyle, QPushButton, QFrame, QLineEdit, QComboBox, 
                             QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import (Qt, QRect, QPoint, pyqtSignal, QObject, 
                          QPropertyAnimation, QEasingCurve, QTimer, QSize, QPointF, QByteArray, QRectF)
from PyQt6.QtGui import (QPainter, QColor, QPen, QImage, QAction, 
                         QFont, QIcon, QBrush, QPixmap, QCursor, QPainterPath, QPolygonF)
from PyQt6.QtSvg import QSvgRenderer
import mss
# 图像处理库
from PIL import Image
import win32clipboard
import win32api

# 【微创修复 1】: 仅将 pynput 提前到全局加载，锁定内存，解决睡眠唤醒后的 ImportError
from pynput import mouse as pynput_mouse

# ================= 0. Win32 API 原型声明 =================
# 显式设置 argtypes/restype, 防止 64 位 HANDLE 被 ctypes 默认 c_int 截断
kernel32 = ctypes.windll.kernel32
kernel32.CreateMutexW.restype = ctypes.wintypes.HANDLE
kernel32.CreateMutexW.argtypes = [ctypes.wintypes.LPVOID, ctypes.wintypes.BOOL, ctypes.wintypes.LPCWSTR]
kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
kernel32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
kernel32.WaitForSingleObject.restype = ctypes.wintypes.DWORD
kernel32.WaitForSingleObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD]
kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]

# ================= 0.5 PyInstaller onefile 环境重置 =================
# onefile 模式: 子进程继承父进程 _MEI 临时目录。
# 父进程退出时清理 _MEI, 子进程还在用 → bootloader 崩溃
# PYINSTALLER_RESET_ENVIRONMENT 让子进程创建独立 _MEI。
def _reset_env():
    env = os.environ.copy()
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env

# ================= 0.7 启动缓冲 =================
time.sleep(0.3)

# ================= 1. 配置管理与日志 =================

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'Mouse4'
        self.config_file = self.config_dir / 'config.json'
        self.log_file = self.config_dir / 'debug.log'
        self._cache = {}
        self._lock = threading.RLock()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._load()
        atexit.register(self._save_sync)

    def log(self, msg):
        try:
            t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = f"[{t}] {msg}\n"
            # 写入到文件头（倒序：最新在顶部）
            if self.log_file.exists():
                old = open(self.log_file, 'r', encoding='utf-8').read()
            else:
                old = ''
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(entry + old)
            self._prune_log()
        except: pass

    def _prune_log(self):
        """从文件尾删除超过 30 天的日志行（倒序存储，旧的在尾部），每天最多执行一次"""
        now = datetime.datetime.now()
        last_prune = getattr(self, '_last_prune_date', None)
        if last_prune and (now - last_prune).days < 1:
            return
        self._last_prune_date = now
        try:
            if not self.log_file.exists():
                return
            cutoff = now - datetime.timedelta(days=30)
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            kept = []
            for line in lines:
                if line[:11] == '[FATAL CRASH':
                    kept.append(line)
                    continue
                if line[0] == '[' and len(line) > 20:
                    try:
                        dt = datetime.datetime.strptime(line[1:11], '%Y-%m-%d')
                        if dt >= cutoff:
                            kept.append(line)
                    except:
                        kept.append(line)
                else:
                    kept.append(line)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.writelines(kept)
        except:
            pass
    
    def _load(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
        except: self._cache = {}
    
    def _save_sync(self):
        with self._lock:
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, ensure_ascii=False, indent=2)
            except: pass
    
    def get(self, key, default=None):
        with self._lock: return self._cache.get(key, default)
    
    def set(self, key, value):
        with self._lock:
            self._cache[key] = value
            self._save_sync()
    
    def get_color(self, key, default='#FF0000'): return self.get(key, default)
    def set_color(self, key, color): self.set(key, color.name() if hasattr(color, 'name') else str(color))
    def get_int(self, key, default=0): return int(self.get(key, default))

config_mgr = ConfigManager()
_startup_role = "restart-wait" if "--restart-wait" in sys.argv else ("paste" if "--paste" in sys.argv else "main")
config_mgr.log(
    f"=== Mouse4 V107 Started role={_startup_role} "
    f"(PID: {os.getpid()}, exe={sys.executable}, cwd={os.getcwd()}, args={sys.argv[1:]}) ==="
)

# ================= 1.5 特殊模式 (必须在 Mutex 之前) =================
# --paste:        右键粘贴, 短命工具进程, 绕过单实例
# --restart-wait: 重启等待器, 等旧进程死透再启动新主实例, 绕过单实例

def run_paste_mode_safe(args):
    """轻量进程：从剪贴板保存截图到目标文件夹"""
    try:
        target_folder = os.getcwd()
        if len(args) > 2 and '--paste' in args:
            try:
                idx = args.index('--paste')
                if idx + 1 < len(args):
                    target_folder = " ".join(args[idx+1:]).strip('"').strip()
            except: pass
        if not target_folder or not os.path.exists(target_folder):
             target_folder = os.path.join(os.path.expanduser("~"), "Desktop")
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img:
            fname = f"Screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(os.path.join(target_folder, fname), "PNG")
    except Exception as e:
        config_mgr.log(f"[PasteMode] Error: {e}")
    sys.exit(0)

def run_restart_wait(args):
    """重启等待器：等旧进程完全退出后，再启动新主实例
    旧进程在 restart_program() 中 Popen 此 helper 后即退出。
    Helper 用 Win32 API 等旧 PID signal，超时 10 秒后直接启动。
    """
    idx = args.index('--restart-wait')
    old_pid = int(args[idx + 1])
    config_mgr.log(f"[RestartWait] Monitoring old PID {old_pid}...")

    SYNCHRONIZE = 0x00100000
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, old_pid)
    if handle:
        ret = kernel32.WaitForSingleObject(handle, 10000)
        kernel32.CloseHandle(handle)
        if ret == 0:  # WAIT_OBJECT_0 = old process exited
            config_mgr.log(f"[RestartWait] Old PID {old_pid} exited cleanly.")
        else:  # WAIT_TIMEOUT
            config_mgr.log(f"[RestartWait] Old PID {old_pid} still alive after 10s; launching anyway.")
    else:
        config_mgr.log(f"[RestartWait] Old PID {old_pid} already gone; launching.")

    # 睡眠唤醒后系统服务/驱动/用户会话可能仍在恢复，稍等一会再拉主进程。
    settle_seconds = 3
    config_mgr.log(f"[RestartWait] Settling {settle_seconds}s before launching main...")
    time.sleep(settle_seconds)

    # 启动新主实例 (此时旧进程通常已死, Mutex 已被 OS 释放)
    if getattr(sys, 'frozen', False):
        cmd = [sys.executable]
        launch_cwd = os.path.dirname(sys.executable)
    else:
        script_path = os.path.abspath(sys.argv[0])
        cmd = [sys.executable, script_path]
        launch_cwd = os.path.dirname(script_path)

    DETACHED_PROCESS = 0x00000008
    for attempt in range(1, 4):
        try:
            proc = subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, cwd=launch_cwd,
                                   env=_reset_env() if getattr(sys, "frozen", False) else None)
            config_mgr.log(f"[RestartWait] Launch attempt {attempt}/3 requested (new PID: {proc.pid}, cwd={launch_cwd})")
            time.sleep(2)
            code = proc.poll()
            if code is None:
                config_mgr.log(f"[RestartWait] New main PID {proc.pid} still alive after 2s. Helper exiting.")
                sys.exit(0)
            config_mgr.log(f"[RestartWait] New main PID {proc.pid} exited early with code {code}; retrying...")
        except Exception as e:
            config_mgr.log(f"[RestartWait] Launch attempt {attempt}/3 failed: {e}")
        time.sleep(2)

    config_mgr.log("[RestartWait] All launch attempts failed or exited early. Helper exiting.")
    sys.exit(0)

if "--paste" in sys.argv:
    run_paste_mode_safe(sys.argv)
if "--restart-wait" in sys.argv:
    run_restart_wait(sys.argv)

# ================= 1.6 单实例保护 =================
# 命名 Mutex: 确保同时只有一个主实例运行
# --paste / --restart-wait 已在上面绕过, 不碰 Mutex
SINGLE_INSTANCE_MUTEX = "Mouse4_SingleInstance_JohnWish"
h_mutex = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    kernel32.CloseHandle(h_mutex)
    config_mgr.log("[Mutex] Another instance already running. Exiting.")
    sys.exit(0)

# ================= 1.7 全局异常拦截网 (黑匣子) =================

def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    config_mgr.log(f"[FATAL CRASH] Main Thread Unhandled Exception:\n{err_msg}")
    
    # 0x10 = MB_ICONERROR (红叉图标)
    msg = f"Mouse4 主线程发生致命错误并已终止！\n\n日志已保存至:\n{config_mgr.log_file}\n\n错误摘要:\n{err_msg[-300:]}"
    ctypes.windll.user32.MessageBoxW(0, msg, "Mouse4 崩溃拦截报告", 0x10)
    sys.exit(1)

def thread_exception_handler(args):
    err_msg = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    thread_name = args.thread.name if args.thread else "Unknown Thread"
    config_mgr.log(f"[FATAL CRASH] Background Thread ({thread_name}) Exception:\n{err_msg}")
    
    # 0x30 = MB_ICONWARNING (黄色感叹号)
    msg = f"Mouse4 后台线程 ({thread_name}) 发生崩溃！部分功能可能失效。\n\n日志已保存至:\n{config_mgr.log_file}\n\n错误摘要:\n{err_msg[-300:]}"
    ctypes.windll.user32.MessageBoxW(0, msg, "Mouse4 线程警告", 0x30)

# 挂载拦截器
sys.excepthook = global_exception_handler
threading.excepthook = thread_exception_handler

# ================= 2. 全局配置 =================

class GlobalConfig:
    hotkey = 'ctrl+1'
    double_click_speed = 0.3
    theme_color_hex = '#0A84FF'
    default_draw_color_hex = '#FF3B30'
    border_width = 2
    icon_filename = 'logo.ico'
    github_url = "https://github.com/JohnWish1590/Mouse4"
    context_menu_text = "粘贴刚才的截图 (Mouse4)"
    reg_key_name = "GeekPaste"
    
    KEY_LAST_COLOR = 'last_draw_color'
    KEY_LAST_FONT_SIZE = 'last_font_size'

    @property
    def screenshot_dir(self):
        d = config_mgr.get('screenshot_dir')
        if not d:
            d = os.path.join(os.path.expanduser('~'), 'Pictures', 'Mouse4Captures')
        return d
    
    @property
    def theme_color(self): return QColor(APPLE_THEME['accent'])
    def get_last_color(self): return QColor(config_mgr.get_color(self.KEY_LAST_COLOR, self.default_draw_color_hex))
    def save_last_color(self, color): config_mgr.set_color(self.KEY_LAST_COLOR, color)
    def get_last_font_size(self): return config_mgr.get_int(self.KEY_LAST_FONT_SIZE, 18)
    def save_last_font_size(self, size): config_mgr.set(self.KEY_LAST_FONT_SIZE, size)

config = GlobalConfig()

# ================= 2.5 Apple style design system (visual only, no coord/grab changes) =================
def _apple_invert_color(c):
    col = QColor(c)
    r, g, b = col.red(), col.green(), col.blue()
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return QColor(255 - r, 255 - g, 255 - b) if lum > 0.5 else QColor(0, 0, 0)

APPLE_THEME = {
    'accent': '#0A84FF',
    'invert': _apple_invert_color,
    'palette': ['#FF3B30', '#FFCC00', '#34C759', '#0A84FF', '#00FFFF', '#FF2D95', '#FFFFFF', '#000000'],
    'color_btn_css': "background-color: {color}; border-radius: 12px; border: 2px solid rgba(255,255,255,0.35);",
    'overlay_css': "background: rgba(255,255,255,0.06); border: 2px solid {inv}; color: {color}; "
                   "font-family: 'Microsoft YaHei'; font-weight: bold; font-size: {size}px;",
    'toolbar_css': "QWidget { background-color: rgba(40,42,48,0.92); border-radius: 14px; "
                   "border: 1px solid rgba(255,255,255,0.12); }"
                   "QPushButton { background: transparent; border: none; color: #E5E5EA; "
                   "font-size: 23px; min-width: 42px; min-height: 38px; padding: 2px 10px; "
                   "margin: 0; border-radius: 9px; }"
                   "QPushButton:hover { background: rgba(255,255,255,0.12); color: white; }"
                   "QPushButton:checked { background: rgba(10,132,255,0.30); color: #0A84FF; }",
    'panel_css': "background-color: rgba(40,42,48,0.92); border-radius: 14px; "
                 "border: 1px solid rgba(255,255,255,0.12);",
    'combo_css': "QComboBox { background: rgba(255,255,255,0.10); color: white; "
                 "border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; padding: 2px 6px; }"
                 "QComboBox QAbstractItemView { background: #2b2b2b; color: white; "
                 "selection-background-color: #0A84FF; }",
    'btn_ok_css': "color: #0A84FF; font-weight: bold; font-size: 22px;",
    'btn_cancel_css': "color: #FF3B30; font-weight: bold; font-size: 20px;",
    'toast_css': "color: #34C759; background: rgba(0,0,0,180); border: 1px solid #34C759; "
                 "padding: 6px 10px; border-radius: 8px; font-weight: bold;",
}

APPLE_SVGS = {
    'rect': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    'ellipse': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    'arrow': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 18 L18 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M10 6 H18 V14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'pen': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M14 4 L20 10 L11 19 L4 19 L4 12 Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    'text': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 6 H18 M12 6 V18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    'undo': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 9 L8 4 L13 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 4 H16 A6 6 0 0 1 16 16 H4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    'cancel': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 6 L18 18 M18 6 L6 18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>',
    'ok': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M5 13 L10 18 L19 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

def _make_icon(svg, color):
    # PyQt6 的 QSvgRenderer 没有 setColor(); 直接把颜色写进 SVG 字符串
    hexc = color.name() if hasattr(color, 'name') else str(color)
    svg2 = svg.replace('currentColor', hexc)
    r = QSvgRenderer(QByteArray(svg2.encode('utf-8')))
    r.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
    pm = QPixmap(24, 24); pm.fill(Qt.GlobalColor.transparent)
    pp = QPainter(pm); r.render(pp, QRectF(0, 0, 24, 24)); pp.end()
    return QIcon(pm)

class AppleIconButton(QPushButton):
    def __init__(self, svg, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self._svg = svg
        try:
            self._normal = _make_icon(svg, QColor('#E5E5EA'))
            self._active = _make_icon(svg, QColor('#0A84FF'))
            self.setIcon(self._normal)
            self.setIconSize(QSize(24, 24))
        except Exception as e:
            config_mgr.log(f"[Icon] SVG render failed: {e}")
    def setChecked(self, v):
        super().setChecked(v)
        if hasattr(self, '_active'):
            self.setIcon(self._active if v else self._normal)
def _add_apple_shadow(widget):
    # disabled: QGraphicsDropShadowEffect on a fullscreen capture window causes a black
    # overlay glitch. Kept as a no-op so the call sites stay unchanged for a future fix.
    return


def _draw_apple_size_label(painter, txt, rect, scale=1.0):
    font = QFont("SF Pro Text", max(10, int(11 * scale)), QFont.Weight.Bold)
    painter.setFont(font)
    pad_x = 10
    w = painter.fontMetrics().horizontalAdvance(txt) + pad_x * 2
    h = painter.fontMetrics().height() + 6
    lx = rect.x() + (rect.width() - w) / 2.0
    ly = rect.y() + 8
    if lx < 0: lx = 4
    bottom = rect.y() + rect.height() - h - 8
    if ly > bottom: ly = bottom
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, 170))
    painter.drawRoundedRect(int(lx), int(ly), int(w), int(h), int(h/2), int(h/2))
    painter.setPen(QColor('white'))
    painter.drawText(int(lx) + pad_x, int(ly) + h - 4, txt)

# ================= 3. 三角色重启 =================
# 重启流程:
#   旧主进程 ─Popen(helper)─→ helper ─Wait(10s)─→ 新主进程
#                └─quit()+timer──┘                └─CreateMutex OK
# 旧进程持 Mutex 到死透, 不提前释放。
# helper 绕过 Mutex, 等旧进程退出后启动新主实例。

def restart_program():
    """旧主进程：启动 restart-wait helper, 然后优雅退出"""
    old_pid = os.getpid()
    config_mgr.log(f"[Restart] Triggered. Launching restart-wait helper (old PID: {old_pid})...")
    try:
        DETACHED_PROCESS = 0x00000008
        if getattr(sys, 'frozen', False):
            helper_cmd = [sys.executable, '--restart-wait', str(old_pid)]
            launch_cwd = os.path.dirname(sys.executable)
        else:
            script_path = os.path.abspath(sys.argv[0])
            helper_cmd = [sys.executable, script_path, '--restart-wait', str(old_pid)]
            launch_cwd = os.path.dirname(script_path)

        helper_proc = subprocess.Popen(helper_cmd, creationflags=DETACHED_PROCESS, cwd=launch_cwd,
                               env=_reset_env() if getattr(sys, "frozen", False) else None)

        config_mgr.log(f"[Restart] Helper launched (PID: {helper_proc.pid}, cwd={launch_cwd}). Exiting gracefully...")
        # 不手动释放 Mutex! 由 OS 在进程退出时自然释放。

        # 优雅退出: 3 秒 timer 兜底, 防止 event loop 卡死
        app = QApplication.instance()
        if app:
            t = threading.Timer(3.0, lambda: os._exit(0))
            t.daemon = True
            t.start()
            app.quit()
        else:
            os._exit(0)
    except Exception as e:
        config_mgr.log(f"[Restart] Failed: {e}")
        os._exit(1)

def watchdog_thread():
    config_mgr.log("[Watchdog] Started monitoring...")
    last_check = time.time()
    while True:
        time.sleep(5)
        now = time.time()
        if now - last_check > 15:
            delta = now - last_check
            config_mgr.log(f"[Watchdog] Sleep detected! Time jump: {delta:.2f}s")
            time.sleep(2)
            restart_program()
        last_check = now

# ================= 4. 辅助函数 =================

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # PyInstaller 6 onedir: 资源放在 exe 旁的 _internal 目录 (V106 onedir 打包)
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    internal = os.path.join(exe_dir, '_internal', relative_path)
    if os.path.exists(internal):
        return internal
    return os.path.join(os.path.abspath("."), relative_path)


try: ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except: pass

# ================= 5. 鼠标双击回退监听 =================

def start_mouse_thread():
    # 这里移除了 pynput_mouse 的局部导入（已提至文件最顶部）
    import uiautomation as auto

    class MouseActionHandler:
        def __init__(self):
            self.last_click_time = 0
            self.click_count = 0
        def on_click(self, x, y, button, pressed):
            if not pressed or button != pynput_mouse.Button.left: return
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                cls = ctypes.create_unicode_buffer(256)
                ctypes.windll.user32.GetClassNameW(hwnd, cls, 256)
                if cls.value not in ["CabinetWClass", "WorkerW", "Progman"]:
                    self.click_count = 0; return
                
                now = time.time()
                if now - self.last_click_time < config.double_click_speed:
                    self.click_count += 1
                else: self.click_count = 1
                self.last_click_time = now
                
                if self.click_count == 2:
                    el = auto.ControlFromCursor()
                    if el.ControlTypeName in ['PaneControl', 'ListControl', 'WindowControl', 'GroupControl']:
                        win32api.keybd_event(0x08, 0, 0, 0)
                        win32api.keybd_event(0x08, 0, 2, 0)
                    self.click_count = 0
            except: self.click_count = 0

    with pynput_mouse.Listener(on_click=MouseActionHandler().on_click) as listener:
        listener.join()

# ================= 6. UI 组件 =================

class SignalComm(QObject):
    trigger_screenshot = pyqtSignal()
    show_toast = pyqtSignal(int, int, str)

comm = SignalComm()
active_windows = []

class ColorButton(QPushButton):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(24, 24); self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(APPLE_THEME['color_btn_css'].format(color=self.color.name()))

class OverlayInput(QLineEdit):
    def __init__(self, parent, pos, color, font_size):
        super().__init__(parent)
        self.move(pos); self.color = color; self.font_size = font_size
        self.update_style(); self.adjustSize(); self.setFocus()
        self.textChanged.connect(self.adjust_width)
    def update_style(self):
        inv = APPLE_THEME['invert'](self.color)
        self.setFont(QFont("Microsoft YaHei", self.font_size, QFont.Weight.Bold))
        self.setStyleSheet(APPLE_THEME['overlay_css'].format(color=self.color.name(), inv=inv.name(), size=self.font_size))
        self.adjust_width()
    def adjust_width(self):
        fm = self.fontMetrics()
        self.setFixedWidth(max(60, fm.horizontalAdvance(self.text()) + 24))
        self.setFixedHeight(fm.height() + 12)

class SnippingToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(6)

        self.tools_widget = QWidget()
        self.tools_widget.setStyleSheet(APPLE_THEME['toolbar_css'])
        t_layout = QHBoxLayout(self.tools_widget); t_layout.setContentsMargins(6,5,6,5); t_layout.setSpacing(0)

        self.btn_rect = AppleIconButton(APPLE_SVGS['rect'])
        self.btn_ellipse = AppleIconButton(APPLE_SVGS['ellipse'])
        self.btn_arrow = AppleIconButton(APPLE_SVGS['arrow'])
        self.btn_pen = AppleIconButton(APPLE_SVGS['pen'])
        self.btn_text = AppleIconButton(APPLE_SVGS['text'])
        for b in [self.btn_rect, self.btn_ellipse, self.btn_arrow, self.btn_pen, self.btn_text]:
            t_layout.addWidget(b)
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setFixedWidth(1)
            sep.setStyleSheet("background: rgba(255,255,255,0.14);"); t_layout.addWidget(sep)

        self.btn_undo = AppleIconButton(APPLE_SVGS['undo'])
        t_layout.addWidget(self.btn_undo)
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine); sep2.setFixedWidth(1)
        sep2.setStyleSheet("background: rgba(255,255,255,0.14);"); t_layout.addWidget(sep2)

        self.btn_cancel = AppleIconButton(APPLE_SVGS['cancel']); self.btn_cancel.setStyleSheet(APPLE_THEME['btn_cancel_css'])
        self.btn_ok = AppleIconButton(APPLE_SVGS['ok']); self.btn_ok.setStyleSheet(APPLE_THEME['btn_ok_css'])
        t_layout.addWidget(self.btn_cancel); t_layout.addWidget(self.btn_ok)

        self.colors_widget = QWidget(); self.colors_widget.setStyleSheet(APPLE_THEME['panel_css'])
        c_layout = QHBoxLayout(self.colors_widget); c_layout.setContentsMargins(10,6,10,6); c_layout.setSpacing(10)

        self.size_combo = QComboBox(); self.size_combo.addItems([str(s) for s in [12,14,16,18,24,36,48]])
        self.size_combo.setFixedWidth(68)
        self.size_combo.setStyleSheet(APPLE_THEME['combo_css'])
        c_layout.addWidget(self.size_combo)

        self.color_btns = []
        for c in APPLE_THEME['palette']:
            btn = ColorButton(c); self.color_btns.append(btn); c_layout.addWidget(btn)

        main_layout.addWidget(self.tools_widget); main_layout.addWidget(self.colors_widget)
        self.colors_widget.hide()
        self.setLayout(main_layout)

class SnippingWindow(QWidget):
    def __init__(self, virtual_geo):
        super().__init__()
        self.virtual_geo = virtual_geo
        self.full_screenshot = None; self.scale_factor = 1.0
        self.begin = QPoint(); self.end = QPoint()
        self.is_selecting = False; self.has_selected = False
        self.drawings = []; self.current_drawing = None; self.draw_mode = None
        self.current_color = config.get_last_color(); self.current_font_size = config.get_last_font_size()
        self.active_input = None
        self._last_click_time = 0; self._double_click_threshold = 400
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # V105: 窗口几何 = 整个虚拟桌面(所有显示器并集), 窗口本地坐标 == 虚拟桌面坐标
        self.setGeometry(virtual_geo)
        _t = time.time()
        self.grab_current_screen()
        config_mgr.log(f"[Shot] grab_virtual_desktop in {(time.time()-_t)*1000:.0f}ms")
        _t2 = time.time()
        # V105: 不用 showFullScreen()(全屏状态会被 Windows 钉在单块屏上), 用 show() 保留跨屏几何
        self.show()
        config_mgr.log(f"[Shot] window shown in {(time.time()-_t2)*1000:.0f}ms "
                       f"geo=({self.geometry().x()},{self.geometry().y()}) {self.geometry().width()}x{self.geometry().height()}")
        self.toolbar = SnippingToolBar(self); self.toolbar.hide()
        self.setup_ui()

    def setup_ui(self):
        last_c = config.get_last_color().name().lower()
        for b in self.toolbar.color_btns: b.setChecked(b.color.name().lower() == last_c)
        self.toolbar.size_combo.setCurrentText(str(self.current_font_size))
        
        self.toolbar.btn_cancel.clicked.connect(self.close_all)
        self.toolbar.btn_ok.clicked.connect(self.finish_capture)
        self.toolbar.btn_undo.clicked.connect(self.undo_drawing)
        self.toolbar.btn_rect.clicked.connect(lambda: self.set_draw_mode('rect'))
        self.toolbar.btn_ellipse.clicked.connect(lambda: self.set_draw_mode('ellipse'))
        self.toolbar.btn_arrow.clicked.connect(lambda: self.set_draw_mode('arrow'))
        self.toolbar.btn_pen.clicked.connect(lambda: self.set_draw_mode('pen'))
        self.toolbar.btn_text.clicked.connect(lambda: self.set_draw_mode('text'))
        for btn in self.toolbar.color_btns:
            btn.clicked.connect(lambda c, b=btn: self.set_color(b.color, b))
        self.toolbar.size_combo.currentIndexChanged.connect(lambda: self.set_font_size(int(self.toolbar.size_combo.currentText())))

    def grab_current_screen(self):
        """V107: 逐屏抓取(每屏物理像素) → 按物理偏移拼成虚拟画布。
        物理像素模式下 QScreen::geometry() 与 mss 均为物理像素、完全一致, 1:1 对齐。
        逐屏抓取消除混合 DPI 下单次整块虚拟桌面 BitBlt 的接缝垃圾(旧 V105 的白条)。"""
        try:
            vg = self.virtual_geo
            self._monitor_plan = self._build_monitor_plan()
            u = QRect()
            for geo, dpr, mon in self._monitor_plan:
                u = u.united(QRect(geo.x() - vg.x(), geo.y() - vg.y(), geo.width(), geo.height()))
            self._monitor_union = u

            canvas = QPixmap(vg.width(), vg.height())
            canvas.fill(QColor(0, 0, 0))  # 包围盒空隙区域为黑(与 ShareX/Flameshot 一致)
            p = QPainter(canvas)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            with mss.mss() as sct:
                for geo, dpr, mon in self._monitor_plan:
                    img = sct.grab(mon)
                    qimg = QImage(img.bgra, img.width, img.height, QImage.Format.Format_ARGB32)
                    pm = QPixmap.fromImage(qimg.copy())
                    p.drawPixmap(geo.x() - vg.x(), geo.y() - vg.y(), pm)
                    stats = self._grab_stats(img)
                    if stats and stats[1] == 0:
                        config_mgr.log(f"[Shot] WARNING screen ({geo.x()},{geo.y()}) {geo.width()}x{geo.height()} "
                                       f"grab all-black (lum={stats}) — possible HDR/bit-depth issue, need DXGI")
                    config_mgr.log(f"[Shot] screen {geo.width()}x{geo.height()} dpr={dpr:.3f} "
                                   f"phys={img.width}x{img.height} lum={stats}")
            p.end()
            self.full_screenshot = canvas
            self.scale_factor = 1.0
            config_mgr.log(f"[Shot] virtual canvas {vg.width()}x{vg.height()} "
                           f"monitors={len(self._monitor_plan)} union={u.width()}x{u.height()}")
        except Exception as e: 
            config_mgr.log(f"[Screenshot] Grab Error: {e}")
            self.full_screenshot = QPixmap()

    def _build_monitor_plan(self):
        """返回 [(dip_rect(QRect), dpr, mss_region), ...]
        用物理位置重叠把 QScreen(DIP) 与 mss 监视器(物理像素, 真值)配对, 顺序无关。"""
        plan = []
        try:
            with mss.mss() as sct:
                mons = sct.monitors[1:]
                for screen in QApplication.screens():
                    geo = screen.geometry()
                    dpr = screen.devicePixelRatio()
                    want = (int(round(geo.x() * dpr)), int(round(geo.y() * dpr)),
                            int(round(geo.width() * dpr)), int(round(geo.height() * dpr)))
                    best, best_ov = None, -1
                    for m in mons:
                        ov = (min(m['left'] + m['width'], want[0] + want[2]) - max(m['left'], want[0])) * \
                             (min(m['top'] + m['height'], want[1] + want[3]) - max(m['top'], want[1]))
                        if ov > best_ov:
                            best_ov, best = ov, m
                    if best is None:
                        best = {'left': want[0], 'top': want[1], 'width': want[2], 'height': want[3]}
                    plan.append((geo, dpr, best))
        except Exception as e:
            config_mgr.log(f"[Shot] monitor plan fallback: {e}")
            for screen in QApplication.screens():
                geo = screen.geometry(); dpr = screen.devicePixelRatio()
                plan.append((geo, dpr, {'left': int(round(geo.x()*dpr)), 'top': int(round(geo.y()*dpr)),
                                        'width': int(round(geo.width()*dpr)), 'height': int(round(geo.height()*dpr))}))
        return plan

    def _grab_stats(self, img):
        """采样统计抓取图像亮度范围(min,max), 用于 HDR/黑屏诊断"""
        try:
            from PIL import Image as PILImage
            pi = PILImage.frombytes('RGB', (img.width, img.height), img.bgra, 'raw', 'BGRX')
            return pi.convert('L').resize((32, 32)).getextrema()
        except Exception:
            return None

    def set_color(self, color, btn):
        self.current_color = color; config.save_last_color(color)
        for b in self.toolbar.color_btns: b.setChecked(False)
        btn.setChecked(True)
        if self.active_input: self.active_input.color = color; self.active_input.update_style()

    def set_font_size(self, size):
        self.current_font_size = size; config.save_last_font_size(size)
        if self.active_input: self.active_input.font_size = size; self.active_input.update_style()

    def set_draw_mode(self, mode):
        if self.active_input: self.commit_text()
        btns = {'rect':self.toolbar.btn_rect, 'ellipse':self.toolbar.btn_ellipse, 'arrow':self.toolbar.btn_arrow, 'pen':self.toolbar.btn_pen, 'text':self.toolbar.btn_text}
        if mode == self.draw_mode: btns[mode].setChecked(False); mode = None
        else:
            for k,v in btns.items(): v.setChecked(k==mode)
        self.draw_mode = mode
        self.toolbar.colors_widget.setVisible(mode is not None)
        self.toolbar.size_combo.setVisible(mode == 'text')
        self.setCursor(Qt.CursorShape.IBeamCursor if mode=='text' else (Qt.CursorShape.CrossCursor if mode else Qt.CursorShape.ArrowCursor))
        self.toolbar.adjustSize()
        if self.has_selected: self.show_toolbar(QRect(self.begin, self.end).normalized())

    def undo_drawing(self):
        if self.drawings: self.drawings.pop(); self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.full_screenshot:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(self.rect(), self.full_screenshot)
        
        painter.setBrush(QColor(0,0,0,100)); painter.setPen(Qt.PenStyle.NoPen)
        if not self.has_selected and not self.is_selecting:
            painter.drawRect(self.rect())
        else:
            painter.drawRect(self.rect())
            rect = QRect(self.begin, self.end).normalized()
            if not rect.isEmpty():
                sx, sy = int(rect.x()*self.scale_factor), int(rect.y()*self.scale_factor)
                sw, sh = int(rect.width()*self.scale_factor), int(rect.height()*self.scale_factor)
                painter.drawPixmap(rect, self.full_screenshot, QRect(sx,sy,sw,sh))
                painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(config.theme_color, 2))
                painter.drawRect(rect)
                for item in self.drawings:
                    painter.setPen(QPen(item['color'], 2)); self.draw_item(painter, item)
                if self.current_drawing:
                    painter.setPen(QPen(self.current_color, 2)); self.draw_item(painter, self.current_drawing)
                
                txt = f"{sw} x {sh}"
                _draw_apple_size_label(painter, txt, rect, 1.0)

    def draw_item(self, p, item):
        t = item['type']
        if t == 'rect': p.drawRect(item['rect'])
        elif t == 'ellipse': p.drawEllipse(item['rect'])
        elif t == 'pen': p.drawPath(item['path'])
        elif t == 'arrow': self.draw_arrow(p, item['start'], item['end'])
        elif t == 'text':
            p.setFont(QFont("Microsoft YaHei", item['size'], QFont.Weight.Bold))
            inv = APPLE_THEME['invert'](item['color'])
            p.setPen(QPen(inv, max(2, item['size'] // 8)))
            p.drawText(item['point'], item['text'])
            p.setPen(QPen(item['color']))
            p.drawText(item['point'], item['text'])

    def draw_arrow(self, p, start, end):
        start, end = QPointF(start), QPointF(end)
        main_pen = p.pen()
        inv = APPLE_THEME['invert'](main_pen.color())
        halo = QPen(inv, main_pen.width() + max(2, main_pen.width() // 3))
        p.setPen(halo)
        angle0 = math.atan2(end.y()-start.y(), end.x()-start.x())
        s = 15
        p1 = end - QPointF(math.cos(angle0+math.pi/6)*s, math.sin(angle0+math.pi/6)*s)
        p2 = end - QPointF(math.cos(angle0-math.pi/6)*s, math.sin(angle0-math.pi/6)*s)
        p.drawLine(start, end)
        p.drawPolygon(QPolygonF([QPointF(end), p1, p2]))
        p.setPen(main_pen)
        p1 = end - QPointF(math.cos(angle0+math.pi/6)*s, math.sin(angle0+math.pi/6)*s)
        p2 = end - QPointF(math.cos(angle0-math.pi/6)*s, math.sin(angle0-math.pi/6)*s)
        p.setBrush(QBrush(p.pen().color())); p.drawPolygon(QPolygonF([QPointF(end), p1, p2])); p.setBrush(Qt.BrushStyle.NoBrush)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.has_selected:
            curr = int(time.time()*1000)
            if curr - self._last_click_time < self._double_click_threshold: 
                self.finish_capture(); return
            self._last_click_time = curr
        
        if event.button() == Qt.MouseButton.RightButton:
            if self.draw_mode: self.set_draw_mode(None)
            else: self.close_all()
            return
        
        # V105: 本地坐标比较 (原 mapToGlobal 与本地 geometry() 比较在窗口原点非 0,0 时永远不成立)
        if self.toolbar.isVisible() and self.toolbar.geometry().contains(event.pos()): return

        if self.has_selected and self.draw_mode:
            if self.draw_mode == 'text':
                if self.active_input: self.commit_text()
                self.active_input = OverlayInput(self, event.pos(), self.current_color, self.current_font_size)
                self.active_input.show(); self.active_input.returnPressed.connect(self.commit_text)
                return
            self.current_drawing = {'type': self.draw_mode, 'color': self.current_color, 'start': event.pos(), 'end': event.pos(), 'rect': QRect(), 'path': QPainterPath(QPointF(event.pos()))}
            self.update(); return

        self.toolbar.hide(); self.toolbar.colors_widget.hide(); self.drawings.clear()
        self.begin = event.pos(); self.end = self.begin; self.is_selecting = True; self.has_selected = False
        if self.active_input: self.active_input.deleteLater(); self.active_input = None
        self.update()

    def mouseMoveEvent(self, event):
        if self.current_drawing:
            self.current_drawing['end'] = event.pos()
            self.current_drawing['rect'] = QRect(self.current_drawing['start'], event.pos()).normalized()
            if self.current_drawing['type'] == 'pen': self.current_drawing['path'].lineTo(QPointF(event.pos()))
            self.update()
        elif self.is_selecting: self.end = event.pos(); self.update()

    def mouseReleaseEvent(self, event):
        if self.current_drawing:
            self.drawings.append(self.current_drawing); self.current_drawing = None; self.update()
        elif self.is_selecting:
            self.is_selecting = False; self.has_selected = True; self.end = event.pos()
            rect = QRect(self.begin, self.end).normalized()
            # V106: 选区自动钳制到显示器联合区域, 避免把包围盒空隙(无显示器区域)截进图里
            if hasattr(self, '_monitor_union'):
                rect = rect.intersected(self._monitor_union)
            if rect.width() < 10 or rect.height() < 10: self.has_selected = False
            else: self.show_toolbar(rect)
            self.update()

    def commit_text(self):
        if self.active_input and self.active_input.text():
            self.drawings.append({'type':'text', 'text':self.active_input.text(), 'point':self.active_input.pos()+QPoint(0, self.active_input.height()-8), 'color':self.active_input.color, 'size':self.active_input.font_size})
            self.active_input.deleteLater(); self.active_input = None; self.update()

    # V107: 工具栏定位重写 — 优先级: 选区下方 → 选区上方 → 选区内侧顶部
    # 每个候选都必须满足: (1) 完全在窗口内 (2) 不落在无显示器空隙带(短屏下方没有屏幕)
    def show_toolbar(self, rect):
        self.toolbar.adjustSize()
        w, h = self.toolbar.width(), self.toolbar.height()

        def ok(x, y):
            if x < 0 or y < 0 or x + w > self.width() or y + h > self.height():
                return False
            return not self._toolbar_in_gap(x, y)

        x = min(max(rect.right() - w, 0), max(0, self.width() - w))
        y = rect.bottom() + 10                      # 1) 选区下方
        if not ok(x, y):
            y = rect.top() - h - 10                 # 2) 选区上方(靠近屏幕底部时自动翻上来)
            if not ok(x, y):
                y = rect.top() + 10                 # 3) 选区内侧顶部
                if not ok(x, y):
                    y = max(0, min(rect.top() + 10, self.height() - h))  # 兜底: 窗口内
        self.toolbar.move(x, y); self.toolbar.show()

    def _toolbar_in_gap(self, x, y):
        """工具栏中心点不在任何真实显示器区域内 → 落在空隙带"""
        if not hasattr(self, '_monitor_plan'):
            return False
        center = QPoint(x + self.toolbar.width() // 2, y + self.toolbar.height() // 2)
        for geo, dpr, mon in self._monitor_plan:
            r = QRect(geo.x() - self.virtual_geo.x(), geo.y() - self.virtual_geo.y(),
                      geo.width(), geo.height())
            if r.contains(center):
                return False
        return True

    def finish_capture(self):
        if self.active_input: self.commit_text()
        rect = QRect(self.begin, self.end).normalized()
        # V106: 双保险钳制到显示器联合区域
        if hasattr(self, '_monitor_union'):
            rect = rect.intersected(self._monitor_union)
        if rect.width() > 0 and rect.height() > 0:
            path = self._do_save_sync(rect)
            # V105: 窗口本地坐标 == 虚拟桌面坐标, 弹 toast 需换算回全局屏幕坐标
            gx = rect.right() + self.virtual_geo.x()
            gy = rect.top() + self.virtual_geo.y()
            comm.show_toast.emit(gx, gy, path or "\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f")
        self.close_all()

    def _do_save_sync(self, rect):
        try:
            sx = int(rect.x() * self.scale_factor)
            sy = int(rect.y() * self.scale_factor)
            sw = int(rect.width() * self.scale_factor)
            sh = int(rect.height() * self.scale_factor)
            source_rect = QRect(sx, sy, sw, sh)

            cropped_raw = self.full_screenshot.copy(source_rect)
            if cropped_raw.isNull() or cropped_raw.width() <= 0 or cropped_raw.height() <= 0:
                config_mgr.log(f"[Clipboard] Crop failed: src={source_rect}, shot={self.full_screenshot.size()}")
                return None

            if self.drawings:
                canvas = QPixmap(cropped_raw.size())
                canvas.fill(Qt.GlobalColor.transparent)
                p = QPainter(canvas)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                p.drawPixmap(0, 0, cropped_raw)
                p.scale(self.scale_factor, self.scale_factor)
                p.translate(-rect.x(), -rect.y())
                for item in self.drawings:
                    p.setPen(QPen(item['color'], 2))
                    self.draw_item(p, item)
                p.end()
                img_to_save = canvas
            else:
                img_to_save = cropped_raw

            # 保存为高清 PNG 文件 (原生分辨率)
            saved_path = None
            try:
                save_dir = config.get_screenshot_dir()
                os.makedirs(save_dir, exist_ok=True)
                fname = f"Mouse4_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
                fpath = os.path.join(save_dir, fname)
                img_to_save.save(fpath, "PNG")
                saved_path = fpath
                config_mgr.log(f"[File] Saved {sw}x{sh} -> {fpath}")
            except Exception as fe:
                config_mgr.log(f"[File] Save failed: {fe}")

            # 2) 复制到剪贴板 (优先 Qt, DIB 重试兜底)
            self._copy_to_clipboard(img_to_save, sw, sh)

            return saved_path

        except Exception as e:
            config_mgr.log(f"[Clipboard] Error: {e}")
            return None

    def _copy_to_clipboard(self, img_to_save, sw, sh):
        # 优先 Qt 剪贴板 (睡眠唤醒后比 win32clipboard 稳定)
        try:
            QApplication.clipboard().setPixmap(img_to_save)
            config_mgr.log(f"[Clipboard] Saved {sw}x{sh} (via Qt)")
            return True
        except Exception as e1:
            config_mgr.log(f"[Clipboard] Qt fallback failed: {e1}")

        # Qt 失败后再试 win32 DIB 方式 (带重试)
        try:
            buf_png = BytesIO()
            img_to_save.save(buf_png, "PNG")
            buf_png.seek(0)

            pil_img = Image.open(buf_png)
            output = BytesIO()
            pil_img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]

            for attempt in range(3):
                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                    win32clipboard.CloseClipboard()
                    config_mgr.log(f"[Clipboard] Saved {sw}x{sh} (via PIL/DIB attempt {attempt+1})")
                    return True
                except Exception as e2:
                    config_mgr.log(f"[Clipboard] DIB attempt {attempt+1} failed: {e2}")
                    time.sleep(0.2)
                    try: win32clipboard.CloseClipboard()
                    except: pass
        except Exception as e3:
            config_mgr.log(f"[Clipboard] DIB prepare failed: {e3}")

        # 全部失败，最后再试一次 Qt
        try:
            QApplication.clipboard().setPixmap(img_to_save)
            return True
        except: pass
        return False

    def close_all(self):
        close_all_windows()

def close_all_windows():
    global active_windows
    for w in active_windows: w.close()
    active_windows = []

class RegistryManager:
    def __init__(self):
        self.key_path = fr"Software\Classes\Directory\Background\shell\{config.reg_key_name}"
    def install(self):
        try:
            exe_path = sys.executable
            command_str = f'"{exe_path}" --paste "%V"'
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path)
            winreg.SetValue(key, "", winreg.REG_SZ, config.context_menu_text)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path + r"\command")
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, command_str)
            winreg.CloseKey(cmd_key)
            return True, "注册成功！"
        except Exception as e: return False, str(e)
    def uninstall(self):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.key_path + r"\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.key_path)
            return True, "已移除。"
        except: return True, "未安装。"

reg_manager = RegistryManager()
tray_icon = None

def _warmup_capture():
    """启动后预热屏幕捕获后端(mss/显卡DC/Qt渲染), 消除首次截图的迟滞感"""
    try:
        t0 = time.time()
        with mss.mss() as sct:
            sct.grab(sct.monitors[0])
        dt = (time.time() - t0) * 1000
        config_mgr.log(f"[Warmup] pre-grabbed screen in {dt:.0f}ms")
    except Exception as e:
        config_mgr.log(f"[Warmup] failed: {e}")

def do_show_windows():
    config_mgr.log(f"[Shot] trigger at {time.strftime('%H:%M:%S')}")
    t0 = time.time()
    if active_windows: close_all_windows()
    # V105: 单窗口覆盖整个虚拟桌面(所有显示器 geometry 并集), 本地坐标 == 虚拟桌面坐标
    vg = QRect()
    for screen in QApplication.screens():
        vg = vg.united(screen.geometry())
    config_mgr.log(f"[Shot] virtual desktop: ({vg.x()},{vg.y()}) {vg.width()}x{vg.height()} "
                   f"({len(QApplication.screens())} monitors)")
    w = SnippingWindow(vg)
    active_windows.append(w)
    config_mgr.log(f"[Shot] windows shown in {(time.time()-t0)*1000:.0f}ms")

class SuccessToast(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        l = QVBoxLayout(self); lab = QLabel(text); l.addWidget(lab)
        lab.setStyleSheet(APPLE_THEME['toast_css'])
        self.anim = QPropertyAnimation(self, b"windowOpacity"); self.anim.setDuration(1500)
        self.anim.finished.connect(self.close)
    def show_anim(self, x, y):
        self.move(x, y-30); self.show(); self.anim.setStartValue(1); self.anim.setEndValue(0); self.anim.start()

def _pick_save_dir():
    from PyQt6.QtWidgets import QFileDialog
    d = QFileDialog.getExistingDirectory(None, "选择截图保存目录", config.get_screenshot_dir())
    if d:
        config_mgr.set('screenshot_dir', d)
        QMessageBox.information(None, "Info", f"截图将保存到:\n{d}")

def setup_tray(app):
    global tray_icon
    icon_p = resource_path(config.icon_filename)
    icon = QIcon(icon_p) if os.path.exists(icon_p) else app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray_icon = QSystemTrayIcon(icon, app)
    m = QMenu()
    m.addAction("立即截图 (Ctrl+1)", comm.trigger_screenshot.emit)
    m.addAction("重启程序 (修复)", restart_program)
    m.addSeparator()
    m.addAction("注册右键菜单", lambda: QMessageBox.information(None, "Info", reg_manager.install()[1]))
    m.addAction("移除右键菜单", lambda: QMessageBox.information(None, "Info", reg_manager.uninstall()[1]))
    m.addAction("截图保存目录...", lambda: _pick_save_dir())
    m.addSeparator()
    m.addAction("Github", lambda: webbrowser.open(config.github_url))
    m.addAction("退出", app.quit)
    tray_icon.setContextMenu(m); tray_icon.show()
    
    # 【微创修复 3】: 返回实例，确保持有
    return tray_icon

# ================= 7. 原生热键 (RegisterHotKey) =================
# 热键两阶段设计:
#   Phase 1: RegisterHotKey (不依赖 QApp, 可提前执行)
#   Phase 2: GetMessageW 消息循环 (需要 QApp 就绪后才 emit 信号)
# 中间用 hotkey_ready event 同步, 避免 QApp 未初始化就 emit signal

hotkey_ready = threading.Event()

def start_hotkey_listener():
    """
    Phase 1: 注册热键 (可不依赖 QApp)
    """
    MOD_CONTROL = 0x0002
    VK_1 = 0x31  # 键盘数字 '1'
    HOTKEY_ID = 1
    WM_HOTKEY = 0x0312

    user32 = ctypes.windll.user32

    # 重试注册：旧进程刚退出, 热键还没清理干净
    for attempt in range(10):
        if user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL, VK_1):
            config_mgr.log(f"[Hotkey] RegisterHotKey Ctrl+1 OK (listening...)")
            break
        config_mgr.log(f"[Hotkey] RegisterHotKey attempt {attempt+1}/10 failed, retrying...")
        time.sleep(1)
    else:
        config_mgr.log("[Hotkey] RegisterHotKey Ctrl+1 FAILED after 10 attempts")
        return

    """
    Phase 2: 等待 QApp 就绪后再进入消息循环
    (emit 信号需要 QApplication 已创建且 signal 已 connect)
    """
    config_mgr.log("[Hotkey] Waiting for QApp to be ready...")
    hotkey_ready.wait()

    config_mgr.log("[Hotkey] QApp ready, entering message loop...")
    msg = ctypes.wintypes.MSG()
    while True:
        ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if ret <= 0:  # WM_QUIT or error
            break
        if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
            comm.trigger_screenshot.emit()

    user32.UnregisterHotKey(None, HOTKEY_ID)
    config_mgr.log("[Hotkey] Listener stopped")


if __name__ == '__main__':
    # 热键线程放最前面，不等 QApplication（睡眠后 QApp 初始化可能卡住）
    threading.Thread(target=start_hotkey_listener, daemon=True, name="HotkeyThread").start()
    threading.Thread(target=watchdog_thread, daemon=True, name="WatchdogThread").start()
    threading.Thread(target=start_mouse_thread, daemon=True, name="MouseHookThread").start()

    # V107: 恢复物理像素模式(重新禁用 Qt 缩放)。
    # V106 开启缩放后 QScreen::geometry() 返回"物理位置 + DIP 尺寸"的混合坐标,
    # 导致 DIP 画布拼接错位、左右屏黑屏。物理模式下 geometry 全为物理像素,
    # 与 mss 完全一致, 逐屏抓取拼接 1:1 对齐。
    # 进程保持 Per-Monitor V2 感知(-4), 跨屏窗口不会被 Windows 位图拉伸。
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 【微创修复 3】: 用全局变量强行引用托盘图标，防止其被垃圾回收机制(GC)回收导致丢失
    tray_icon_ref = setup_tray(app)

    comm.trigger_screenshot.connect(do_show_windows)
    comm.show_toast.connect(lambda x,y,t: SuccessToast(t).show_anim(x,y))

    # 预热: 在空闲时先抓一帧, 把 mss/显卡/Qt 渲染管线热好, 用户首次截图不再卡
    threading.Thread(target=_warmup_capture, daemon=True, name="WarmupThread").start()

    # 通知热键线程：QApp 就绪，可以开始 emit 信号了
    hotkey_ready.set()

    sys.exit(app.exec())
