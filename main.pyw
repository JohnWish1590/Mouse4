"""
Mouse4 V73 - 睡眠修复终极版 (方案 A: 系统级强力重启)
核心保留：
1. V65 所有功能：双击保存、完整绘图、粘贴板修复 (PIL方案)、右键菜单。
2. 没有任何功能删减。

核心修复 (睡眠死机问题)：
1. Watchdog 检测到睡眠后，使用 os.startfile 强制重启（相当于双击重启）。
2. 旧进程使用 os._exit(0) 暴力退出，确保释放热键占用。
"""

import sys
import os
import ctypes
import datetime
import threading
import time
import webbrowser
import math
import subprocess
import json
import atexit
import winreg
from pathlib import Path
from io import BytesIO

# GUI 库
from PyQt6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QMessageBox, QStyle, QPushButton, QFrame, QLineEdit, QComboBox, 
                             QVBoxLayout, QHBoxLayout, QLabel)
from PyQt6.QtCore import (Qt, QRect, QPoint, pyqtSignal, QObject, 
                          QPropertyAnimation, QEasingCurve, QTimer, QSize, QPointF)
from PyQt6.QtGui import (QPainter, QColor, QPen, QImage, QAction, 
                         QFont, QIcon, QBrush, QPixmap, QCursor, QPainterPath, QPolygonF)
import keyboard 
import mss
# 图像处理库
from PIL import Image
import win32clipboard 

# ================= 0. 启动缓冲 =================
time.sleep(0.3)

# ================= 1. 配置管理 =================

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
    
    def get_color(self, key, default='#FF0000'): return self.get(key, default)
    def set_color(self, key, color): self.set(key, color.name() if hasattr(color, 'name') else str(color))
    def get_int(self, key, default=0): return int(self.get(key, default))

config_mgr = ConfigManager()
config_mgr.log(f"=== Mouse4 V73 Started (PID: {os.getpid()}) ===")

# ================= 2. 全局配置 =================

class GlobalConfig:
    hotkey = 'ctrl+1'
    double_click_speed = 0.3
    theme_color_hex = '#00FF00'
    default_draw_color_hex = '#FF0000'
    border_width = 2
    icon_filename = 'logo.ico'
    github_url = "https://github.com/JohnWish1590/Mouse4"
    context_menu_text = "粘贴刚才的截图 (Mouse4)"
    reg_key_name = "GeekPaste"
    
    KEY_LAST_COLOR = 'last_draw_color'
    KEY_LAST_FONT_SIZE = 'last_font_size'
    
    @property
    def theme_color(self): return QColor(self.theme_color_hex)
    def get_last_color(self): return QColor(config_mgr.get_color(self.KEY_LAST_COLOR, self.default_draw_color_hex))
    def save_last_color(self, color): config_mgr.set_color(self.KEY_LAST_COLOR, color)
    def get_last_font_size(self): return config_mgr.get_int(self.KEY_LAST_FONT_SIZE, 18)
    def save_last_font_size(self, size): config_mgr.set(self.KEY_LAST_FONT_SIZE, size)

config = GlobalConfig()

# ================= 3. 【方案 A】强力重启与看门狗 =================

def restart_program():
    config_mgr.log("[Restart] Triggered - Executing Hard Restart...")
    try:
        # 使用 Shell 执行机制，脱离当前进程链
        if getattr(sys, 'frozen', False):
            os.startfile(sys.executable)
        else:
            import win32api
            win32api.ShellExecute(0, 'open', sys.executable, sys.argv[0], '', 1)
        
        config_mgr.log("[Restart] New process requested via Shell. Exiting now.")
        # os._exit(0) 暴力销毁旧进程，不留隐患
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
            # 给系统硬件和驱动苏醒留一点缓冲时间
            time.sleep(2)
            restart_program()
        last_check = now

# ================= 4. 辅助函数 =================

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def run_paste_mode_safe(args):
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
    except: pass
    sys.exit(0)

if len(sys.argv) > 1 and '--paste' in sys.argv:
    run_paste_mode_safe(sys.argv)

try: ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except: pass

# ================= 5. 鼠标双击回退监听 =================

def start_mouse_thread():
    from pynput import mouse as pynput_mouse
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
                        keyboard.press_and_release('backspace')
                    self.click_count = 0
            except: self.click_count = 0

    with pynput_mouse.Listener(on_click=MouseActionHandler().on_click) as listener:
        listener.join()

# ================= 6. UI 组件 =================

class SignalComm(QObject):
    trigger_screenshot = pyqtSignal()
    show_toast = pyqtSignal(int, int)

comm = SignalComm()
active_windows = []

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
        self.update_style(); self.adjustSize(); self.setFocus()
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
        
        # Tools
        self.tools_widget = QWidget()
        self.tools_widget.setStyleSheet("QWidget { background-color: #2b2b2b; border-radius: 6px; border: 1px solid #444; } QPushButton { background: transparent; border: none; color: #B0B0B0; font-size: 20px; padding: 6px; } QPushButton:hover { background: #3f3f3f; color: white; } QPushButton:checked { background: #4a4a4a; color: #07c160; }")
        t_layout = QHBoxLayout(self.tools_widget); t_layout.setContentsMargins(10,8,10,8); t_layout.setSpacing(8)
        
        self.btn_rect = QPushButton("⬜"); self.btn_rect.setCheckable(True)
        self.btn_ellipse = QPushButton("⭕"); self.btn_ellipse.setCheckable(True)
        self.btn_arrow = QPushButton("↗"); self.btn_arrow.setCheckable(True)
        self.btn_pen = QPushButton("✎"); self.btn_pen.setCheckable(True)
        self.btn_text = QPushButton("T"); self.btn_text.setCheckable(True)
        self.btn_undo = QPushButton("↶")
        self.btn_cancel = QPushButton("✕"); self.btn_cancel.setStyleSheet("color: #ff5f57; font-weight: bold")
        self.btn_ok = QPushButton("✓"); self.btn_ok.setStyleSheet("color: #07c160; font-weight: bold; font-size: 22px")
        
        for b in [self.btn_rect, self.btn_ellipse, self.btn_arrow, self.btn_pen, self.btn_text, self.btn_undo, self.btn_cancel, self.btn_ok]:
            t_layout.addWidget(b)
            
        # Colors
        self.colors_widget = QWidget(); self.colors_widget.setStyleSheet("background-color: #2b2b2b; border-radius: 6px; border: 1px solid #444;")
        c_layout = QHBoxLayout(self.colors_widget); c_layout.setContentsMargins(10,6,10,6); c_layout.setSpacing(10)
        
        self.size_combo = QComboBox(); self.size_combo.addItems([str(s) for s in [12,14,16,18,24,36,48]])
        self.size_combo.setFixedWidth(68)
        self.size_combo.setStyleSheet("QComboBox { background: #3f3f3f; color: white; border: 1px solid #555; }")
        c_layout.addWidget(self.size_combo)
        
        self.color_btns = []
        for c in ['#FF0000', '#FFCC00', '#07c160', '#1E90FF', '#00FFFF', '#FF00FF', '#FFFFFF', '#000000']:
            btn = ColorButton(c); self.color_btns.append(btn); c_layout.addWidget(btn)
            
        main_layout.addWidget(self.tools_widget); main_layout.addWidget(self.colors_widget)
        self.colors_widget.hide()
        self.setLayout(main_layout)

class SnippingWindow(QWidget):
    def __init__(self, screen_info):
        super().__init__()
        self.setScreen(screen_info); self.setGeometry(screen_info.geometry())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.showFullScreen()
        
        self.full_screenshot = None; self.scale_factor = 1.0
        self.grab_current_screen()
        
        self.begin = QPoint(); self.end = QPoint()
        self.is_selecting = False; self.has_selected = False
        self.drawings = []; self.current_drawing = None; self.draw_mode = None
        self.current_color = config.get_last_color(); self.current_font_size = config.get_last_font_size()
        self.active_input = None
        
        self._last_click_time = 0; self._double_click_threshold = 400
        
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
        try:
            with mss.mss() as sct:
                geo = self.geometry()
                cx, cy = geo.x() + geo.width()//2, geo.y() + geo.height()//2
                monitor = sct.monitors[1]
                for m in sct.monitors[1:]:
                    if m['left'] <= cx < m['left']+m['width'] and m['top'] <= cy < m['top']+m['height']:
                        monitor = m; break
                
                img = sct.grab(monitor)
                self.scale_factor = img.width / max(1, geo.width())
                qimg = QImage(img.bgra, img.width, img.height, QImage.Format.Format_ARGB32)
                self.full_screenshot = QPixmap.fromImage(qimg.copy())
        except: self.full_screenshot = QPixmap()

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
                painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor('black'))
                painter.drawRect(rect.x(), rect.y()-25, len(txt)*9, 20)
                painter.setPen(QColor('white')); painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.drawText(rect.x()+5, rect.y()-10, txt)

    def draw_item(self, p, item):
        t = item['type']
        if t == 'rect': p.drawRect(item['rect'])
        elif t == 'ellipse': p.drawEllipse(item['rect'])
        elif t == 'pen': p.drawPath(item['path'])
        elif t == 'arrow': self.draw_arrow(p, item['start'], item['end'])
        elif t == 'text': 
            p.setFont(QFont("Microsoft YaHei", item['size'], QFont.Weight.Bold))
            p.setPen(QPen(item['color']))
            p.drawText(item['point'], item['text'])

    def draw_arrow(self, p, start, end):
        p.drawLine(start, end)
        angle = math.atan2(end.y()-start.y(), end.x()-start.x())
        s = 15
        p1 = end - QPointF(math.cos(angle+math.pi/6)*s, math.sin(angle+math.pi/6)*s)
        p2 = end - QPointF(math.cos(angle-math.pi/6)*s, math.sin(angle-math.pi/6)*s)
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
        
        if self.toolbar.isVisible() and self.toolbar.geometry().contains(self.mapToGlobal(event.pos())): return

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
            if rect.width() < 10: self.has_selected = False
            else: self.show_toolbar(rect)
            self.update()

    def commit_text(self):
        if self.active_input and self.active_input.text():
            self.drawings.append({'type':'text', 'text':self.active_input.text(), 'point':self.active_input.pos()+QPoint(0, self.active_input.height()-8), 'color':self.active_input.color, 'size':self.active_input.font_size})
            self.active_input.deleteLater(); self.active_input = None; self.update()

    def show_toolbar(self, rect):
        self.toolbar.adjustSize()
        x = rect.right()-self.toolbar.width()
        y = rect.bottom()+10
        if y + self.toolbar.height() > self.height(): y = rect.bottom() - self.toolbar.height() - 10
        if x < 0: x = 0
        self.toolbar.move(x, y); self.toolbar.show()

    def finish_capture(self):
        if self.active_input: self.commit_text()
        rect = QRect(self.begin, self.end).normalized()
        if rect.width() > 0:
            comm.show_toast.emit(rect.right(), rect.top())
            self._do_save_sync(rect)
        self.close_all()

    def _do_save_sync(self, rect):
        # 100% 保持 V65 稳定的 PIL 剪贴板处理机制，绝不修改
        try:
            sx = int(rect.x() * self.scale_factor)
            sy = int(rect.y() * self.scale_factor)
            sw = int(rect.width() * self.scale_factor)
            sh = int(rect.height() * self.scale_factor)
            source_rect = QRect(sx, sy, sw, sh)
            
            cropped_raw = self.full_screenshot.copy(source_rect)
            
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

            # 走内存 PNG 转 PIL
            buf_png = BytesIO()
            img_to_save.save(buf_png, "PNG")
            buf_png.seek(0)
            
            pil_img = Image.open(buf_png)
            output = BytesIO()
            pil_img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:] 
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            config_mgr.log(f"[Clipboard] Saved {sw}x{sh} (via PIL)")
            
        except Exception as e:
            config_mgr.log(f"[Clipboard] Error: {e}")
            try: QApplication.clipboard().setPixmap(img_to_save)
            except: pass

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

def do_show_windows():
    if active_windows: close_all_windows(); return
    for screen in QApplication.screens():
        w = SnippingWindow(screen); w.show(); active_windows.append(w)

class SuccessToast(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        l = QVBoxLayout(self); lab = QLabel(text); l.addWidget(lab)
        lab.setStyleSheet("color: #0f0; background: rgba(0,0,0,180); border: 1px solid #0f0; padding: 5px; border-radius: 4px; font-weight: bold;")
        self.anim = QPropertyAnimation(self, b"windowOpacity"); self.anim.setDuration(1500)
        self.anim.finished.connect(self.close)
    def show_anim(self, x, y):
        self.move(x, y-30); self.show(); self.anim.setStartValue(1); self.anim.setEndValue(0); self.anim.start()

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
    m.addSeparator()
    m.addAction("Github", lambda: webbrowser.open(config.github_url))
    m.addAction("退出", app.quit)
    tray_icon.setContextMenu(m); tray_icon.show()

def check_hotkey_and_trigger():
    if ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000:
        comm.trigger_screenshot.emit()

if __name__ == '__main__':
    threading.Thread(target=watchdog_thread, daemon=True).start()
    threading.Thread(target=start_mouse_thread, daemon=True).start()
    
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    setup_tray(app)
    
    comm.trigger_screenshot.connect(do_show_windows)
    comm.show_toast.connect(lambda x,y: SuccessToast("Saved!").show_anim(x,y))
    
    try: 
        keyboard.add_hotkey(config.hotkey, check_hotkey_and_trigger)
    except: pass
    
    sys.exit(app.exec())