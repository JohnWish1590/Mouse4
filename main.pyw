"""
Mouse4 V83.3 - 终极全量大满贯版
核心架构：
1. 原生热键： RegisterHotKey 实现硬件级拦截，0延迟且免疫睡眠。
2. 强力重启： Watchdog 监控系统跳变，唤醒后 Hard Restart 刷新进程。
3. 标注全家桶： 矩形、椭圆、箭头、自由画笔、文字录入、撤销系统。
4. 资源管理器助手： 保持经典的“空白处双击返回上一级”。
5. 注册表自愈： 支持一键更新右键“粘贴到这里”的 EXE 路径。
"""

import sys
import os
import ctypes
from ctypes import wintypes
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

# --- 核心依赖强力前置 (解决 PyInstaller 运行时解压风险) ---
try:
    from PIL import Image, ImageGrab
except ImportError:
    pass

from PyQt6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QMessageBox, QStyle, QPushButton, QFrame, QLineEdit, QComboBox, 
                             QVBoxLayout, QHBoxLayout, QLabel)
from PyQt6.QtCore import (Qt, QRect, QPoint, pyqtSignal, QObject, 
                          QPropertyAnimation, QEasingCurve, QTimer, QSize, QPointF,
                          QBuffer, QIODevice)
from PyQt6.QtGui import (QPainter, QColor, QPen, QImage, QAction, 
                         QFont, QIcon, QBrush, QPixmap, QCursor, QPainterPath, QPolygonF)

import mss
import win32clipboard 
from pynput import mouse as pynput_mouse
import uiautomation as auto
import win32api

# ================= 1. 配置管理与日志系统 =================
class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'Mouse4'
        self.config_file = self.config_dir / 'config.json'
        self.log_file = self.config_dir / 'debug.log'
        self._cache = {}
        self._lock = threading.Lock()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._load()
        atexit.register(self._save_sync)

    def log(self, msg):
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{t}] {msg}\n")
        except: pass
    
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

config_mgr = ConfigManager()

# ================= 1.5 异常拦截 (黑匣子) =================
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    config_mgr.log(f"[FATAL CRASH]:\n{err_msg}")
    msg = f"Mouse4 发生致命错误！\n日志路径: {config_mgr.log_file}\n\n错误摘要:\n{err_msg[-300:]}"
    ctypes.windll.user32.MessageBoxW(0, msg, "Mouse4 核心拦截器", 0x10)
    sys.exit(1)

sys.excepthook = global_exception_handler

# ================= 2. 右键菜单处理模式 =================
def run_paste_mode_safe(args):
    """单独启动一个轻量进程处理粘贴任务"""
    try:
        config_mgr.log(f"[PasteMode] Args: {args}")
        target_folder = ""
        if len(args) > 2 and '--paste' in args:
            idx = args.index('--paste')
            if idx + 1 < len(args):
                target_folder = " ".join(args[idx+1:]).strip('"').strip()
        
        if not target_folder or not os.path.exists(target_folder):
            target_folder = os.path.join(os.path.expanduser("~"), "Desktop")

        img = ImageGrab.grabclipboard()
        if img:
            if isinstance(img, list): img = img[0]
            fname = f"Screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(os.path.join(target_folder, fname), "PNG")
    except Exception as e:
        config_mgr.log(f"[PasteMode] Error: {e}")
    sys.exit(0)

if len(sys.argv) > 1 and '--paste' in sys.argv:
    run_paste_mode_safe(sys.argv)

# ================= 3. 全局配置 =================
class GlobalConfig:
    hotkey = 'ctrl+1'
    double_click_speed = 0.3
    theme_color = QColor('#00FF00')
    icon_filename = 'logo.ico'
    reg_key_name = "GeekPaste"
    github_url = "https://github.com/JohnWish1590/Mouse4"
    context_menu_text = "粘贴刚才的截图 (Mouse4)"

config = GlobalConfig()

class SignalComm(QObject):
    trigger_screenshot = pyqtSignal()
    show_toast = pyqtSignal(int, int)

comm = SignalComm()
active_windows = []
main_tray = None

# ================= 4. UI 核心组件 =================
class ColorButton(QPushButton):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(24, 24); self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"background-color: {self.color.name()}; border-radius: 12px; border: 2px solid #555;")

class OverlayInput(QLineEdit):
    def __init__(self, parent, pos, color, font_size):
        super().__init__(parent)
        self.move(pos); self.color = color; self.font_size = font_size
        self.update_style(); self.setFocus()
        self.textChanged.connect(self.adjust_width)
    def update_style(self):
        self.setStyleSheet(f"background: transparent; border: 1px dashed rgba(255,255,255,0.5); color: {self.color.name()}; font-family: 'Microsoft YaHei'; font-weight: bold; font-size: {self.font_size}px;")
        self.adjust_width()
    def adjust_width(self):
        self.setFixedWidth(max(50, self.fontMetrics().horizontalAdvance(self.text()) + 30))
        self.setFixedHeight(self.fontMetrics().height() + 10)

class SnippingToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(0)
        
        self.tools_widget = QWidget()
        self.tools_widget.setStyleSheet("QWidget { background-color: #2b2b2b; border-radius: 6px; border: 1px solid #444; } QPushButton { background: transparent; border: none; color: #B0B0B0; font-size: 18px; padding: 6px; } QPushButton:hover { background: #3f3f3f; color: white; } QPushButton:checked { background: #4a4a4a; color: #07c160; }")
        t_layout = QHBoxLayout(self.tools_widget); t_layout.setContentsMargins(10,5,10,5); t_layout.setSpacing(8)
        
        self.btn_rect = QPushButton("⬜"); self.btn_rect.setCheckable(True)
        self.btn_ellipse = QPushButton("⭕"); self.btn_ellipse.setCheckable(True)
        self.btn_arrow = QPushButton("↗"); self.btn_arrow.setCheckable(True)
        self.btn_pen = QPushButton("✎"); self.btn_pen.setCheckable(True)
        self.btn_text = QPushButton("T"); self.btn_text.setCheckable(True)
        self.btn_undo = QPushButton("↶")
        line = QFrame(); line.setFrameShape(QFrame.Shape.VLine); line.setStyleSheet("background: #555;")
        self.btn_cancel = QPushButton("✕"); self.btn_cancel.setStyleSheet("color: #ff5f57;")
        self.btn_ok = QPushButton("✓"); self.btn_ok.setStyleSheet("color: #07c160; font-size: 22px;")
        
        for b in [self.btn_rect, self.btn_ellipse, self.btn_arrow, self.btn_pen, self.btn_text, self.btn_undo, line, self.btn_cancel, self.btn_ok]:
            t_layout.addWidget(b)
            
        self.colors_widget = QWidget()
        self.colors_widget.setStyleSheet("background-color: #2b2b2b; border-radius: 6px; border: 1px solid #444;")
        c_layout = QHBoxLayout(self.colors_widget); c_layout.setContentsMargins(10,5,10,5)
        
        self.size_combo = QComboBox(); self.size_combo.addItems(["12","14","18","24","36","48"]); self.size_combo.setFixedWidth(60)
        c_layout.addWidget(self.size_combo)
        
        self.color_btns = []
        for c in ['#FF0000', '#FFCC00', '#07c160', '#1E90FF', '#FFFFFF', '#000000']:
            btn = ColorButton(c); self.color_btns.append(btn); c_layout.addWidget(btn)
            
        main_layout.addWidget(self.tools_widget); main_layout.addWidget(self.colors_widget)
        self.colors_widget.hide(); self.setLayout(main_layout)

class SnippingWindow(QWidget):
    def __init__(self, screen_info):
        super().__init__()
        self.setScreen(screen_info); self.setGeometry(screen_info.geometry())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.showFullScreen()
        
        self.full_screenshot = None; self.scale_factor = 1.0; self.grab_current_screen()
        self.begin = QPoint(); self.end = QPoint()
        self.is_selecting = False; self.has_selected = False
        self.drawings = []; self.current_drawing = None; self.draw_mode = None
        self.current_color = QColor(config_mgr.get('last_draw_color', '#FF0000'))
        self.current_font_size = int(config_mgr.get('last_font_size', 18))
        self.active_input = None; self.toolbar = SnippingToolBar(self); self.toolbar.hide()
        self.setup_ui()

    def grab_current_screen(self):
        try:
            with mss.mss() as sct:
                geo = self.geometry(); monitor = sct.monitors[1]
                for m in sct.monitors[1:]:
                    if m['left'] <= geo.x() < m['left']+m['width'] and m['top'] <= geo.y() < m['top']+m['height']:
                        monitor = m; break
                img = sct.grab(monitor)
                self.scale_factor = img.width / max(1, geo.width())
                qimg = QImage(img.bgra, img.width, img.height, QImage.Format.Format_ARGB32)
                self.full_screenshot = QPixmap.fromImage(qimg.copy())
        except: self.full_screenshot = QPixmap()

    def setup_ui(self):
        self.toolbar.btn_ok.clicked.connect(self.finish_capture)
        self.toolbar.btn_cancel.clicked.connect(self.close_all)
        self.toolbar.btn_undo.clicked.connect(self.undo_draw)
        self.toolbar.btn_rect.clicked.connect(lambda: self.set_mode('rect'))
        self.toolbar.btn_ellipse.clicked.connect(lambda: self.set_mode('ellipse'))
        self.toolbar.btn_arrow.clicked.connect(lambda: self.set_mode('arrow'))
        self.toolbar.btn_pen.clicked.connect(lambda: self.set_mode('pen'))
        self.toolbar.btn_text.clicked.connect(lambda: self.set_mode('text'))
        self.toolbar.size_combo.currentTextChanged.connect(self.set_font_size)
        for btn in self.toolbar.color_btns: btn.clicked.connect(lambda c, b=btn: self.set_color(b.color, b))

    def set_mode(self, mode):
        if self.active_input: self.commit_text()
        self.draw_mode = mode; self.toolbar.colors_widget.show()
        self.setCursor(Qt.CursorShape.CrossCursor if mode != 'text' else Qt.CursorShape.IBeamCursor)
        # 视觉反馈
        btns = {'rect':self.toolbar.btn_rect, 'ellipse':self.toolbar.btn_ellipse, 'arrow':self.toolbar.btn_arrow, 'pen':self.toolbar.btn_pen, 'text':self.toolbar.btn_text}
        for k, b in btns.items(): b.setChecked(k == mode)

    def set_color(self, color, btn):
        self.current_color = color; config_mgr.set('last_draw_color', color.name())
        for b in self.toolbar.color_btns: b.setChecked(False)
        btn.setChecked(True)

    def set_font_size(self, size):
        self.current_font_size = int(size); config_mgr.set('last_font_size', self.current_font_size)

    def undo_draw(self):
        if self.drawings: self.drawings.pop(); self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.full_screenshot: p.drawPixmap(self.rect(), self.full_screenshot)
        p.setBrush(QColor(0,0,0,100)); p.drawRect(self.rect())
        
        if self.is_selecting or self.has_selected:
            rect = QRect(self.begin, self.end).normalized()
            if not rect.isEmpty():
                sx, sy, sw, sh = int(rect.x()*self.scale_factor), int(rect.y()*self.scale_factor), int(rect.width()*self.scale_factor), int(rect.height()*self.scale_factor)
                p.drawPixmap(rect, self.full_screenshot, QRect(sx,sy,sw,sh))
                p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(config.theme_color, 2)); p.drawRect(rect)
                for d in self.drawings: self.draw_item(p, d)
                if self.current_drawing: self.draw_item(p, self.current_drawing)
                txt = f"{sw} x {sh}"
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0,0,0,180)); p.drawRect(rect.x(), rect.y()-25, 85, 20)
                p.setPen(Qt.GlobalColor.white); p.setFont(QFont("Arial", 9, QFont.Weight.Bold)); p.drawText(rect.x()+5, rect.y()-10, txt)

    def draw_item(self, p, d):
        p.setPen(QPen(d['color'], 2))
        if d['type'] == 'rect': p.drawRect(d['rect'])
        elif d['type'] == 'ellipse': p.drawEllipse(d['rect'])
        elif d['type'] == 'pen': p.drawPath(d['path'])
        elif d['type'] == 'arrow': self.draw_arrow(p, d['start'], d['end'])
        elif d['type'] == 'text':
            p.setFont(QFont("Microsoft YaHei", d['size'], QFont.Weight.Bold)); p.drawText(d['pos'], d['text'])

    def draw_arrow(self, p, start, end):
        p.drawLine(start, end); angle = math.atan2(end.y()-start.y(), end.x()-start.x()); s = 15
        p1 = end - QPointF(math.cos(angle+math.pi/6)*s, math.sin(angle+math.pi/6)*s)
        p2 = end - QPointF(math.cos(angle-math.pi/6)*s, math.sin(angle-math.pi/6)*s)
        p.setBrush(QBrush(p.pen().color())); p.drawPolygon(QPolygonF([QPointF(end), p1, p2])); p.setBrush(Qt.BrushStyle.NoBrush)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            if self.draw_mode: self.draw_mode = None; self.setCursor(Qt.CursorShape.ArrowCursor)
            else: self.close_all()
            return
        if self.draw_mode:
            if self.draw_mode == 'text':
                if self.active_input: self.commit_text()
                self.active_input = OverlayInput(self, event.pos(), self.current_color, self.current_font_size)
                self.active_input.show()
            else:
                self.current_drawing = {'type':self.draw_mode, 'color':self.current_color, 'start':event.pos(), 'rect':QRect(), 'path':QPainterPath(QPointF(event.pos()))}
        else:
            self.begin = event.pos(); self.end = self.begin; self.is_selecting = True; self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting: self.end = event.pos(); self.update()
        elif self.current_drawing:
            self.current_drawing['end'] = event.pos()
            self.current_drawing['rect'] = QRect(self.current_drawing['start'], event.pos()).normalized()
            if self.current_drawing['type'] == 'pen': self.current_drawing['path'].lineTo(QPointF(event.pos()))
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_selecting:
            self.is_selecting = False; self.has_selected = True
            rect = QRect(self.begin, self.end).normalized()
            if rect.width() > 5: self.show_toolbar(rect)
            else: self.has_selected = False
            self.update()
        elif self.current_drawing:
            self.drawings.append(self.current_drawing); self.current_drawing = None; self.update()

    def commit_text(self):
        if self.active_input and self.active_input.text():
            self.drawings.append({'type':'text', 'text':self.active_input.text(), 'pos':self.active_input.pos()+QPoint(0, self.active_input.height()-5), 'color':self.current_color, 'size':self.current_font_size})
            self.active_input.deleteLater(); self.active_input = None; self.update()

    def show_toolbar(self, rect):
        self.toolbar.adjustSize()
        y = rect.bottom() + 10
        if y + self.toolbar.height() > self.height(): y = rect.top() - self.toolbar.height() - 10
        self.toolbar.move(max(0, rect.right()-self.toolbar.width()), y); self.toolbar.show()

    def finish_capture(self):
        if self.active_input: self.commit_text()
        rect = QRect(self.begin, self.end).normalized()
        if not rect.isEmpty():
            comm.show_toast.emit(rect.right(), rect.top())
            sx, sy, sw, sh = int(rect.x()*self.scale_factor), int(rect.y()*self.scale_factor), int(rect.width()*self.scale_factor), int(rect.height()*self.scale_factor)
            pix = self.full_screenshot.copy(QRect(sx, sy, sw, sh))
            if self.drawings:
                canvas = QPixmap(pix.size()); canvas.fill(Qt.GlobalColor.transparent); painter = QPainter(canvas)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.drawPixmap(0,0,pix)
                painter.scale(self.scale_factor, self.scale_factor); painter.translate(-rect.x(), -rect.y())
                for d in self.drawings: self.draw_item(painter, d)
                painter.end(); pix = canvas
            q_buf = QBuffer(); q_buf.open(QIODevice.OpenModeFlag.ReadWrite); pix.save(q_buf, "PNG")
            img = Image.open(BytesIO(q_buf.data().data())).convert("RGB"); out = BytesIO(); img.save(out, "BMP")
            win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, out.getvalue()[14:]); win32clipboard.CloseClipboard()
        self.close_all()

    def close_all(self):
        global active_windows
        for w in active_windows: w.close()
        active_windows = []

# ================= 5. 系统核心功能 (热键、鼠标、看门狗) =================
class RegistryManager:
    def __init__(self): self.key_path = fr"Software\Classes\Directory\Background\shell\{config.reg_key_name}"
    def install(self):
        try:
            exe_path = os.path.abspath(sys.executable); command_str = f'"{exe_path}" --paste "%V"'
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path)
            winreg.SetValue(key, "", winreg.REG_SZ, config.context_menu_text)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, exe_path)
            cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path + r"\command")
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, command_str); return True, "注册/更新成功！"
        except Exception as e: return False, str(e)
    def uninstall(self):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.key_path + r"\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.key_path); return True, "已清理。"
        except: return True, "未安装。"

reg_mgr = RegistryManager()

def native_hotkey_thread():
    user32 = ctypes.windll.user32
    while True:
        if user32.RegisterHotKey(None, 99, 0x0002, 0x31): break
        time.sleep(2)
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == 0x0312: comm.trigger_screenshot.emit()
        user32.TranslateMessage(ctypes.byref(msg)); user32.DispatchMessageW(ctypes.byref(msg))

def start_mouse_thread():
    class MouseHandler:
        def __init__(self): self.last_t = 0; self.count = 0
        def on_click(self, x, y, button, pressed):
            if not pressed or button != pynput_mouse.Button.left: return
            try:
                hwnd = win32api.GetForegroundWindow(); cls = win32api.GetClassName(hwnd)
                if cls not in ["CabinetWClass", "WorkerW"]: return
                now = time.time()
                if now - self.last_t < config.double_click_speed: self.count += 1
                else: self.count = 1
                self.last_t = now
                if self.count == 2:
                    if auto.ControlFromCursor().ControlTypeName in ['PaneControl', 'ListControl']:
                        win32api.keybd_event(0x08, 0, 0, 0); win32api.keybd_event(0x08, 0, 2, 0)
                    self.count = 0
            except: pass
    with pynput_mouse.Listener(on_click=MouseHandler().on_click) as l: l.join()

def watchdog_thread():
    lc = time.time()
    while True:
        time.sleep(5)
        if time.time() - lc > 15:
            if getattr(sys, 'frozen', False): os.startfile(sys.executable)
            os._exit(0)
        lc = time.time()

def do_show_windows():
    global active_windows
    if active_windows: return
    for s in QApplication.screens():
        w = SnippingWindow(s); w.show(); active_windows.append(w)

class SuccessToast(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        l = QVBoxLayout(self); lab = QLabel(text); l.addWidget(lab)
        lab.setStyleSheet("color: #0f0; background: rgba(0,0,0,180); padding: 8px; border-radius: 4px; font-weight: bold;")
        self.anim = QPropertyAnimation(self, b"windowOpacity"); self.anim.setDuration(1200); self.anim.finished.connect(self.close)
    def show_anim(self, x, y):
        self.move(x-50, y-40); self.show(); self.anim.setStartValue(1); self.anim.setEndValue(0); self.anim.start()

if __name__ == '__main__':
    # 环境静音与 DPI 接管
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    threading.Thread(target=watchdog_thread, daemon=True).start()
    threading.Thread(target=native_hotkey_thread, daemon=True).start()
    threading.Thread(target=start_mouse_thread, daemon=True).start()
    
    app = QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    
    main_tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app)
    m = QMenu()
    m.addAction("立即截图 (Ctrl+1)", comm.trigger_screenshot.emit)
    m.addAction("注册/更新右键菜单", lambda: QMessageBox.information(None, "提示", reg_mgr.install()[1]))
    m.addAction("移除右键菜单", lambda: QMessageBox.information(None, "提示", reg_mgr.uninstall()[1]))
    m.addSeparator()
    m.addAction("访问 GitHub", lambda: webbrowser.open(config.github_url))
    m.addAction("退出", app.quit)
    main_tray.setContextMenu(m); main_tray.show()
    
    comm.trigger_screenshot.connect(do_show_windows)
    comm.show_toast.connect(lambda x,y: SuccessToast("Saved!").show_anim(x,y))
    
    sys.exit(app.exec())