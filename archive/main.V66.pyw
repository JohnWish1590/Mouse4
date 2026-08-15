"""
Mouse4 V66 - 修复睡眠后快捷键失效
核心修复：看门狗检测到睡眠后优先重新注册热键，失败才重启
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
from pathlib import Path
from io import BytesIO

# ================= 0. 配置持久化系统 =================

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'Mouse4'
        self.config_file = self.config_dir / 'config.json'
        self._cache = {}
        self._lock = threading.Lock()
        self._dirty = False
        self._timer = None
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._load()
        atexit.register(self._save_sync)
    
    def _load(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                print(f"[Config] Loaded from {self.config_file}")
        except Exception as e:
            print(f"[Config] Load failed: {e}")
            self._cache = {}
    
    def _save_sync(self):
        with self._lock:
            if self._dirty:
                try:
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        json.dump(self._cache, f, ensure_ascii=False, indent=2)
                    print(f"[Config] Saved to {self.config_file}")
                except Exception as e:
                    print(f"[Config] Save failed: {e}")
    
    def _schedule_save(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(1.0, self._save_sync)
        self._timer.daemon = True
        self._timer.start()
    
    def get(self, key: str, default=None):
        with self._lock:
            return self._cache.get(key, default)
    
    def set(self, key: str, value):
        with self._lock:
            old_value = self._cache.get(key)
            if old_value != value:
                self._cache[key] = value
                self._dirty = True
                self._schedule_save()
    
    def get_color(self, key: str, default: str = '#FF0000') -> str:
        return self.get(key, default)
    
    def set_color(self, key: str, color):
        if hasattr(color, 'name'):
            self.set(key, color.name())
        else:
            self.set(key, str(color))
    
    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default

config_mgr = ConfigManager()

# ================= 1. 全局配置 =================

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
    def theme_color(self):
        from PyQt6.QtGui import QColor
        return QColor(self.theme_color_hex)
    
    @property
    def default_draw_color(self):
        from PyQt6.QtGui import QColor
        return QColor(self.default_draw_color_hex)
    
    def get_last_color(self):
        from PyQt6.QtGui import QColor
        color_hex = config_mgr.get_color(self.KEY_LAST_COLOR, self.default_draw_color_hex)
        return QColor(color_hex)
    
    def save_last_color(self, color):
        config_mgr.set_color(self.KEY_LAST_COLOR, color)
    
    def get_last_font_size(self) -> int:
        return config_mgr.get_int(self.KEY_LAST_FONT_SIZE, 18)
    
    def save_last_font_size(self, size: int):
        config_mgr.set(self.KEY_LAST_FONT_SIZE, size)

config = GlobalConfig()

# ================= 2. 基础函数 =================

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def run_paste_mode_safe(args):
    try:
        from PIL import ImageGrab
    except ImportError:
        ctypes.windll.user32.MessageBoxW(0, "缺少 Pillow 库", "错误", 0x10)
        sys.exit(1)

    try:
        target_folder = os.getcwd()
        if len(args) > 2:
            try:
                idx = args.index('--paste')
                if idx + 1 < len(args):
                    raw_path = " ".join(args[idx+1:])
                    target_folder = raw_path.strip('"').strip()
            except ValueError:
                pass

        if not target_folder or not os.path.exists(target_folder):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            target_folder = desktop

        img = ImageGrab.grabclipboard()
        if img is None:
            ctypes.windll.user32.MessageBoxW(0, "剪贴板为空或不是图片", "提示", 0x30)
            sys.exit(0)
            
        t_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"Screenshot_{t_str}.png"
        save_path = os.path.join(target_folder, fname)
        img.save(save_path, "PNG")
        sys.exit(0)
            
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"Error: {str(e)}", "错误", 0x10)
        sys.exit(1)

if len(sys.argv) > 1 and '--paste' in sys.argv:
    run_paste_mode_safe(sys.argv)

# V66: DPI 感知设置
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

from PyQt6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QInputDialog, QLabel, QVBoxLayout, QHBoxLayout, 
                             QMessageBox, QStyle, QPushButton, QFrame, QLineEdit, QComboBox)
from PyQt6.QtCore import (Qt, QRect, QPoint, pyqtSignal, QObject, 
                          QPropertyAnimation, QEasingCurve, QTimer, QSize, QPointF)
from PyQt6.QtGui import (QPainter, QColor, QPen, QImage, QAction, 
                         QFont, QIcon, QBrush, QPixmap, QCursor, QPainterPath, QPolygonF)
import keyboard 
import mss
import winreg
from PIL import Image

# ================= 3. 鼠标监听 =================

def start_mouse_thread():
    from pynput import mouse as pynput_mouse
    import uiautomation as auto

    class MouseActionHandler:
        def __init__(self):
            self.last_click_time = 0
            self.click_count = 0

        def is_explorer_window(self):
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                class_name = ctypes.create_unicode_buffer(256)
                ctypes.windll.user32.GetClassNameW(hwnd, class_name, 256)
                return class_name.value in ["CabinetWClass", "WorkerW", "Progman"]
            except:
                return False

        def is_pointer_on_empty_space(self):
            try:
                element = auto.ControlFromCursor()
                return element.ControlTypeName in ['PaneControl', 'ListControl', 'WindowControl', 'GroupControl']
            except:
                return False

        def on_click(self, x, y, button, pressed):
            if not pressed or button != pynput_mouse.Button.left: return
            if not self.is_explorer_window():
                self.click_count = 0
                return
            current_time = time.time()
            if current_time - self.last_click_time < config.double_click_speed:
                self.click_count += 1
            else:
                self.click_count = 1
            self.last_click_time = current_time
            if self.click_count == 2:
                if self.is_pointer_on_empty_space():
                    keyboard.press_and_release('backspace')
                self.click_count = 0

    handler = MouseActionHandler()
    with pynput_mouse.Listener(on_click=handler.on_click) as listener:
        listener.join()

# ================= 4. 注册表管理器 =================

class RegistryManager:
    def __init__(self):
        self.base_key = winreg.HKEY_CURRENT_USER
        self.key_path = fr"Software\Classes\Directory\Background\shell\{config.reg_key_name}"
    
    def install(self):
        try:
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                command_str = f'"{exe_path}" --paste "%V"'
            else:
                python_exe = sys.executable
                if "pythonw.exe" not in python_exe and "python.exe" in python_exe:
                    python_exe = python_exe.replace("python.exe", "pythonw.exe")
                script_path = os.path.abspath(__file__)
                if script_path.endswith('.py') and os.path.exists(script_path + 'w'):
                    script_path = script_path + 'w'
                command_str = f'"{python_exe}" "{script_path}" --paste "%V"'
            
            key = winreg.CreateKey(self.base_key, self.key_path)
            winreg.SetValue(key, "", winreg.REG_SZ, config.context_menu_text)
            
            icon_path = sys.executable if getattr(sys, 'frozen', False) else "imageres.dll,-5302"
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
            winreg.CloseKey(key)
            
            cmd_key = winreg.CreateKey(self.base_key, self.key_path + r"\command")
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, command_str)
            winreg.CloseKey(cmd_key)
            return True, "注册成功！\n请先点'关闭'，该功能立刻生效。"
        except Exception as e:
            return False, f"注册失败: {e}"

    def uninstall(self):
        try:
            try: winreg.DeleteKey(self.base_key, self.key_path + r"\command")
            except FileNotFoundError: pass
            winreg.DeleteKey(self.base_key, self.key_path)
            return True, "已移除右键菜单。"
        except: return True, "未安装。"

# ================= 5. 截图功能核心 =================

class SignalComm(QObject):
    trigger_screenshot = pyqtSignal()
    show_toast = pyqtSignal(int, int)

comm = SignalComm()
active_windows = []

class SuccessToast(QWidget):
    def __init__(self, text="Saved!", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setStyleSheet("QLabel { color: #00FF00; background-color: rgba(0,0,0,180); border: 1px solid #00FF00; border-radius: 4px; padding: 5px 10px; font-weight: bold; font-family: Arial; font-size: 12px; }")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1500)
        self.anim.finished.connect(self.close)

    def show_animation(self, x, y):
        self.adjustSize()
        self.move(x, y - self.height())
        self.show()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.anim.start()
        QTimer.singleShot(50, lambda: self.move(self.x(), self.y()-2))

class ColorButton(QPushButton):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.name()};
                border-radius: 12px;
                border: 2px solid #555555;
            }}
            QPushButton:hover {{
                border: 2px solid #FFFFFF;
            }}
            QPushButton:checked {{
                border: 3px solid #FFFFFF;
            }}
        """)

class OverlayInput(QLineEdit):
    def __init__(self, parent, pos, color, font_size):
        super().__init__(parent)
        self.move(pos)
        self.setPlaceholderText("") 
        self.color = color
        self.font_size = font_size
        self.update_style()
        self.adjustSize()
        self.setFocus()
        self.textChanged.connect(self.adjust_width)
        
    def update_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: 1px dashed rgba(255, 255, 255, 0.5);
                color: {self.color.name()};
                font-family: "Microsoft YaHei";
                font-size: {self.font_size}px;
                font-weight: bold;
                padding: 2px;
            }}
        """)
        self.adjust_width()
        
    def adjust_width(self):
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self.text()) + 30
        self.setFixedWidth(max(50, w))
        self.setFixedHeight(fm.height() + 10)

class SnippingToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. 工具栏
        self.tools_widget = QWidget()
        self.tools_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-radius: 6px;
                border: 1px solid #444444;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #B0B0B0;
                font-size: 20px;
                font-family: "Segoe UI Symbol", "Arial";
                padding: 6px 10px;
                border-radius: 4px;
                min-width: 30px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #3f3f3f;
                color: white;
            }
            QPushButton:checked {
                background-color: #4a4a4a;
                color: #07c160;
            }
        """)
        tools_layout = QHBoxLayout(self.tools_widget)
        tools_layout.setContentsMargins(10, 8, 10, 8)
        tools_layout.setSpacing(8)
        
        self.btn_rect = QPushButton("⬜")
        self.btn_rect.setCheckable(True)
        self.btn_rect.setToolTip("矩形")
        
        self.btn_ellipse = QPushButton("⭕")
        self.btn_ellipse.setCheckable(True)
        self.btn_ellipse.setToolTip("圆形")
        
        self.btn_arrow = QPushButton("↗")
        self.btn_arrow.setCheckable(True)
        self.btn_arrow.setToolTip("箭头")
        
        self.btn_pen = QPushButton("✎")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setToolTip("画笔")
        
        self.btn_text = QPushButton("T")
        self.btn_text.setCheckable(True)
        self.btn_text.setFont(QFont("Times New Roman", 18, QFont.Weight.Bold))
        self.btn_text.setToolTip("文字")
        
        self.btn_undo = QPushButton("↶")
        self.btn_undo.setToolTip("撤销")
        
        line = QLabel("|")
        line.setStyleSheet("color: #555555; margin: 0px 5px;")
        
        self.btn_cancel = QPushButton("✕")
        self.btn_cancel.setStyleSheet("color: #ff5f57; font-weight: bold;") 
        self.btn_ok = QPushButton("✓")
        self.btn_ok.setStyleSheet("color: #07c160; font-weight: bold; font-size: 22px;")

        tools_layout.addWidget(self.btn_rect)
        tools_layout.addWidget(self.btn_ellipse)
        tools_layout.addWidget(self.btn_arrow)
        tools_layout.addWidget(self.btn_pen)
        tools_layout.addWidget(self.btn_text)
        tools_layout.addWidget(self.btn_undo)
        tools_layout.addWidget(line)
        tools_layout.addWidget(self.btn_cancel)
        tools_layout.addWidget(self.btn_ok)
        
        # 2. 底部属性栏（字号 + 颜色）
        self.colors_widget = QWidget()
        self.colors_widget.setStyleSheet("background-color: #2b2b2b; border-radius: 6px; border: 1px solid #444444;")
        bottom_layout = QHBoxLayout(self.colors_widget)
        bottom_layout.setContentsMargins(10, 6, 10, 6)
        bottom_layout.setSpacing(10)
        
        self.size_combo = QComboBox()
        self.size_combo.addItems([str(s) for s in [12, 14, 16, 18, 24, 36, 48, 64, 72]])
        self.size_combo.setCurrentText("18")
        self.size_combo.setFixedWidth(68)
        
        arrow_svg = """url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 15l5 5 5-5'/%3E%3Cpath d='M7 9l5-5 5 5'/%3E%3C/svg%3E")"""
        
        self.size_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #3f3f3f;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 2px 0px 2px 10px;
                font-family: "Arial";
                font-weight: bold;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }}
            QComboBox::down-arrow {{
                image: {arrow_svg};
                width: 14px;
                height: 14px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #07c160;
                outline: none;
                min-width: 60px;
            }}
        """)
        bottom_layout.addWidget(self.size_combo)
        
        self.line_sep = QFrame()
        self.line_sep.setFrameShape(QFrame.Shape.VLine)
        self.line_sep.setFrameShadow(QFrame.Shadow.Plain)
        self.line_sep.setFixedWidth(1)
        self.line_sep.setFixedHeight(16)
        self.line_sep.setStyleSheet("background-color: #555555; border: none;")
        bottom_layout.addWidget(self.line_sep)

        self.colors = ['#FF0000', '#FFCC00', '#07c160', '#1E90FF', '#00FFFF', '#FF00FF', '#FFFFFF', '#000000']
        self.color_btns = []
        for c in self.colors:
            btn = ColorButton(c)
            self.color_btns.append(btn)
            bottom_layout.addWidget(btn)
            
        self.selected_color = QColor('#FF0000')
        self.color_btns[0].setChecked(True)
        
        self.main_layout.addWidget(self.tools_widget)
        self.main_layout.addWidget(self.colors_widget)
        self.colors_widget.hide()
        
        self.setLayout(self.main_layout)

class SnippingWindow(QWidget):
    def __init__(self, screen_info):
        super().__init__()
        self.screen_info = screen_info
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        self.setScreen(screen_info)
        self.setGeometry(screen_info.geometry())
        self.showFullScreen()
        
        self.scale_factor = 1.0 
        self.full_screenshot = None
        self.grab_current_screen()
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        self.has_selected = False
        
        self.draw_mode = None 
        self.drawings = []
        self.current_drawing = None 
        
        # V63: 从持久化加载上次的颜色和字号
        self.current_color = config.get_last_color()
        self.current_font_size = config.get_last_font_size()
        self.active_input = None 
        
        # V63 Fix: 双击检测专用变量
        self._last_click_time = 0
        self._click_count = 0
        self._double_click_threshold = 400  # 毫秒
        
        self.toolbar = SnippingToolBar(self)
        self.toolbar.hide()
        
        # V63: 恢复上次选择的颜色按钮
        self._restore_last_color()
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
            btn.clicked.connect(lambda checked, c=btn.color, b=btn: self.set_color(c, b))
            
        self.toolbar.size_combo.currentIndexChanged.connect(self.update_font_size_from_combo)

    def _restore_last_color(self):
        """恢复上次选择的颜色"""
        last_color = config.get_last_color()
        for btn in self.toolbar.color_btns:
            if btn.color.name().lower() == last_color.name().lower():
                btn.setChecked(True)
                self.toolbar.selected_color = btn.color
            else:
                btn.setChecked(False)

    def grab_current_screen(self):
        """V66: 高清截图 - 使用mss直接获取物理像素"""
        try:
            win_geo = self.geometry()
            
            with mss.mss() as sct:
                # 找到包含窗口中心的显示器
                cx = win_geo.x() + win_geo.width() // 2
                cy = win_geo.y() + win_geo.height() // 2
                
                target_mon = None
                for mon in sct.monitors[1:]:
                    if (mon["left"] <= cx < mon["left"] + mon["width"] and 
                        mon["top"] <= cy < mon["top"] + mon["height"]):
                        target_mon = mon
                        break
                
                if not target_mon:
                    target_mon = {
                        "top": win_geo.y(), 
                        "left": win_geo.x(), 
                        "width": win_geo.width(), 
                        "height": win_geo.height()
                    }
                
                # V66: 使用mss抓取屏幕
                img = sct.grab(target_mon)
                
                # V66: 正确的缩放因子计算
                self.scale_factor = img.width / max(1, win_geo.width())
                
                # V66: 关键修复 - 使用bgra数据创建QImage，然后转换
                # mss返回的是BGRA格式，我们需要手动转换为RGB
                qimg = QImage(img.bgra, img.width, img.height, QImage.Format.Format_ARGB32)
                
                self.full_screenshot = QPixmap.fromImage(qimg.copy())
                
                print(f"[V66] Screen captured: {img.width}x{img.height}, scale: {self.scale_factor:.2f}")
                
        except Exception as e:
            print(f"[V66] Screen grab failed: {e}")
            self.full_screenshot = QPixmap()
            self.scale_factor = 1.0

    def set_color(self, color, btn_obj):
        self.current_color = color
        for b in self.toolbar.color_btns:
            b.setChecked(False)
        btn_obj.setChecked(True)
        
        config.save_last_color(color)
        
        if self.active_input:
            self.active_input.color = color
            self.active_input.update_style()

    def update_font_size_from_combo(self):
        try:
            size = int(self.toolbar.size_combo.currentText())
            self.current_font_size = size
            config.save_last_font_size(size)
            if self.active_input:
                self.active_input.font_size = size
                self.active_input.update_style()
        except:
            pass

    def set_draw_mode(self, mode):
        if self.active_input:
            self.commit_text_input()

        buttons = {
            'rect': self.toolbar.btn_rect,
            'ellipse': self.toolbar.btn_ellipse,
            'arrow': self.toolbar.btn_arrow,
            'pen': self.toolbar.btn_pen,
            'text': self.toolbar.btn_text
        }
        
        if mode is not None and mode == self.draw_mode:
            buttons[mode].setChecked(False)
            mode = None
        
        for btn in buttons.values():
            btn.setChecked(False)
        
        if mode is not None:
            buttons[mode].setChecked(True)
            self.toolbar.colors_widget.show()
            
            is_text = (mode == 'text')
            self.toolbar.size_combo.setVisible(is_text)
            self.toolbar.line_sep.setVisible(is_text)
            
            if mode == 'text':
                self.setCursor(Qt.CursorShape.IBeamCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.toolbar.colors_widget.hide()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        self.draw_mode = mode
        self.toolbar.adjustSize()
        
        if self.has_selected:
            rect = QRect(self.begin, self.end).normalized()
            self.show_toolbar(rect)

    def undo_drawing(self):
        if self.drawings:
            self.drawings.pop()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        window_rect = self.rect()
        
        if self.full_screenshot:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(window_rect, self.full_screenshot, self.full_screenshot.rect())
            
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if not self.has_selected and not self.is_selecting:
            painter.drawRect(window_rect)
        else:
            painter.drawRect(window_rect)
            
            rect = QRect(self.begin, self.end).normalized()
            
            if rect.width() > 0 and rect.height() > 0:
                sx = int(rect.x() * self.scale_factor)
                sy = int(rect.y() * self.scale_factor)
                sw = int(rect.width() * self.scale_factor)
                sh = int(rect.height() * self.scale_factor)
                source_rect = QRect(sx, sy, sw, sh)
                painter.drawPixmap(rect, self.full_screenshot, source_rect)
            
            pen = QPen(config.theme_color, config.border_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
            
            for item in self.drawings:
                painter.setPen(QPen(item['color'], 2)) 
                self.draw_shape(painter, item)
            
            if self.current_drawing:
                painter.setPen(QPen(self.current_color, 2))
                self.draw_shape(painter, self.current_drawing)

            if rect.width() > 0:
                w, h = rect.width(), rect.height()
                phy_w = int(w * self.scale_factor)
                phy_h = int(h * self.scale_factor)
                txt = f"{phy_w} x {phy_h}"
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor('#000000'))
                painter.drawRect(rect.x(), rect.y()-25, len(txt)*9, 20)
                painter.setPen(QColor('#FFFFFF'))
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.drawText(rect.x()+5, rect.y()-10, txt)

    def draw_shape(self, painter, item):
        if item['type'] == 'rect':
            painter.drawRect(item['rect'])
        elif item['type'] == 'ellipse':
            painter.drawEllipse(item['rect'])
        elif item['type'] == 'pen':
            painter.drawPath(item['path'])
        elif item['type'] == 'arrow':
            self.draw_arrow(painter, item['start'], item['end'])
        elif item['type'] == 'text':
            size = item.get('size', 18)
            font = QFont("Microsoft YaHei", size, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QPen(item['color']))
            painter.drawText(item['point'], item['text'])

    def draw_arrow(self, painter, start, end):
        line_pen = painter.pen()
        start_f = QPointF(start)
        end_f = QPointF(end)
        
        painter.drawLine(start_f, end_f)
        
        angle = math.atan2(end_f.y() - start_f.y(), end_f.x() - start_f.x())
        arrow_size = 15
        
        p1 = end_f - QPointF(math.cos(angle + math.pi / 6) * arrow_size, math.sin(angle + math.pi / 6) * arrow_size)
        p2 = end_f - QPointF(math.cos(angle - math.pi / 6) * arrow_size, math.sin(angle - math.pi / 6) * arrow_size)
        
        arrow_head = QPolygonF([end_f, p1, p2])
        painter.setBrush(QBrush(line_pen.color()))
        painter.drawPolygon(arrow_head)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def mousePressEvent(self, event):
        # 双击检测（必须在其他逻辑之前）
        if event.button() == Qt.MouseButton.LeftButton and self.has_selected:
            current_time = int(time.time() * 1000)
            
            if hasattr(self, '_last_click_time') and (current_time - self._last_click_time) < self._double_click_threshold:
                print(f"[Debug] Double click detected! Saving...")
                self.finish_capture()
                return
            else:
                self._last_click_time = current_time
                self._click_count = 1
        
        # 检查是否点击在工具栏上
        if self.childAt(event.pos()) and (self.toolbar.isAncestorOf(self.childAt(event.pos())) or self.childAt(event.pos()) == self.toolbar): 
            return
        
        # 右键取消
        if event.button() == Qt.MouseButton.RightButton:
            if self.draw_mode:
                self.set_draw_mode(None)
            else:
                self.close_all()
            return

        # 绘图模式下的点击
        if self.has_selected and self.draw_mode:
            if self.draw_mode == 'text':
                if self.active_input:
                    self.commit_text_input()
                
                self.active_input = OverlayInput(self, event.pos(), self.current_color, self.current_font_size)
                self.active_input.show()
                self.active_input.returnPressed.connect(self.commit_text_input)
                return

            self.is_selecting = False
            start_p = event.pos()
            
            drawing_data = {
                'type': self.draw_mode, 
                'color': self.current_color, 
                'start': start_p, 
                'end': start_p, 
                'rect': QRect()
            }
            
            if self.draw_mode == 'pen':
                path = QPainterPath(QPointF(start_p))
                drawing_data['path'] = path
                
            self.current_drawing = drawing_data
            self.update()
            return

        # 开始新选区
        click_pos = event.pos()
        if self.has_selected:
            rect = QRect(self.begin, self.end).normalized()
            if rect.contains(click_pos):
                return
        
        self.toolbar.hide()
        self.toolbar.colors_widget.hide()
        self.drawings.clear()
        self.set_draw_mode(None)
        self.begin = click_pos
        self.end = self.begin
        self.is_selecting = True
        self.has_selected = False
        
        if self.active_input:
            self.active_input.deleteLater()
            self.active_input = None
            
        self.update()

    def commit_text_input(self):
        if self.active_input:
            text = self.active_input.text()
            if text:
                pos = self.active_input.pos() + QPoint(0, self.active_input.height() - 8)
                self.drawings.append({
                    'type': 'text',
                    'color': self.active_input.color,
                    'size': self.active_input.font_size,
                    'point': pos,
                    'text': text
                })
            self.active_input.deleteLater()
            self.active_input = None
            self.update()

    def mouseMoveEvent(self, event):
        if self.current_drawing:
            if self.current_drawing['type'] in ['rect', 'ellipse']:
                self.current_drawing['rect'] = QRect(self.current_drawing['start'], event.pos()).normalized()
            elif self.current_drawing['type'] == 'arrow':
                self.current_drawing['end'] = event.pos()
            elif self.current_drawing['type'] == 'pen':
                self.current_drawing['path'].lineTo(QPointF(event.pos()))
            self.update()
            return
            
        if self.is_selecting:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton: 
            return

        if self.current_drawing:
            self.drawings.append(self.current_drawing)
            self.current_drawing = None
            self.update()
            return

        if self.is_selecting:
            self.is_selecting = False
            self.has_selected = True
            self.end = event.pos()
            rect = QRect(self.begin, self.end).normalized()
            
            if rect.width() < 10 or rect.height() < 10:
                self.has_selected = False
                self.update()
                return

            self.show_toolbar(rect)
            self.update()

    def show_toolbar(self, rect):
        self.toolbar.adjustSize()
        x = rect.x() + rect.width() - self.toolbar.width()
        y = rect.y() + rect.height() + 8
        
        screen_geo = self.geometry()
        if y + self.toolbar.height() > screen_geo.height():
            y = rect.y() + rect.height() - self.toolbar.height() - 10
        if x < 0: x = 0
            
        self.toolbar.move(x, y)
        self.toolbar.show()

    def finish_capture(self):
        """V66: 修复剪贴板为空问题 - 在主线程同步执行保存"""
        if self.active_input:
            self.commit_text_input()
            
        rect = QRect(self.begin, self.end).normalized()
        if rect.width() <= 0:
            self.close_all()
            return
        
        try:
            # V66: 立即显示提示
            comm.show_toast.emit(rect.x() + rect.width(), rect.y())
            
            # V66: 关键修复 - 在主线程直接执行保存，不延迟
            self._do_save_sync(rect)
            
        except Exception as e:
            print(f"[V66] Capture error: {e}")
        
        self.close_all()
    
    def _do_save_sync(self, rect):
        """V66: 同步执行保存到剪贴板（必须在主线程）"""
        try:
            sx = int(rect.x() * self.scale_factor)
            sy = int(rect.y() * self.scale_factor)
            sw = int(rect.width() * self.scale_factor)
            sh = int(rect.height() * self.scale_factor)
            source_rect = QRect(sx, sy, sw, sh)
            
            # 从高清截图中裁剪
            cropped_raw = self.full_screenshot.copy(source_rect)
            
            # V66: 关键修复 - 使用PIL作为中间层确保格式正确
            # 将QPixmap转换为PIL Image
            buffer = BytesIO()
            # 先保存为PNG到内存
            cropped_raw.save(buffer, 'PNG')
            buffer.seek(0)
            
            # 用PIL打开确保格式正确
            pil_img = Image.open(buffer)
            
            # 如果有标注，需要叠加
            if self.drawings:
                # 创建透明画布用于标注
                canvas = QPixmap(cropped_raw.size())
                canvas.fill(Qt.GlobalColor.transparent)
                
                p = QPainter(canvas)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                p.drawPixmap(0, 0, cropped_raw)
                p.scale(self.scale_factor, self.scale_factor)
                p.translate(-rect.x(), -rect.y())
                
                p.setBrush(Qt.BrushStyle.NoBrush)
                for item in self.drawings:
                    p.setPen(QPen(item['color'], 2))
                    self.draw_shape(p, item)
                p.end()
                
                # 将标注后的图像转为PIL
                buffer2 = BytesIO()
                canvas.save(buffer2, 'PNG')
                buffer2.seek(0)
                pil_img = Image.open(buffer2)
            
            # V66: 关键修复 - 使用PIL的ImageQt将图像放入剪贴板
            # 这是Windows下最可靠的方式
            output = BytesIO()
            pil_img.convert('RGB').save(output, 'BMP')  # BMP格式最兼容
            output.seek(0)
            
            # 使用win32clipboard直接操作Windows剪贴板
            import win32clipboard
            from PIL import ImageWin
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, output.getvalue())
            win32clipboard.CloseClipboard()
            
            print(f"[V66] Saved to clipboard: {pil_img.width}x{pil_img.height}")
            
        except Exception as e:
            print(f"[V66] Save error: {e}")
            # 备用方案：使用Qt的剪贴板
            try:
                QApplication.clipboard().setPixmap(cropped_raw)
                print("[V66] Fallback to Qt clipboard")
            except Exception as e2:
                print(f"[V66] Fallback failed: {e2}")

    def close_all(self):
        close_all_windows()

def close_all_windows():
    global active_windows
    for win in active_windows: win.close()
    active_windows = []

# ================= 6. 托盘控制 =================

reg_manager = RegistryManager()
tray_icon = None

def do_show_windows():
    global active_windows
    if active_windows: 
        close_all_windows()
        return
    
    for screen in QApplication.screens():
        win = SnippingWindow(screen)
        win.show()
        active_windows.append(win)

def do_show_toast(x, y):
    global toast
    toast = SuccessToast("Saved!")
    toast.show_animation(x, y)

def open_github():
    webbrowser.open(config.github_url)

# V66: 修复重启时热键注册问题 - 干净重启
def restart_program():
    """干净重启：彻底释放资源并启动新进程"""
    try:
        print("[Restart] Initiating clean restart...")
        
        # 关键：先清理keyboard钩子
        try:
            keyboard.unhook_all()
            print("[Restart] All hotkeys unhooked")
        except Exception as e:
            print(f"[Restart] Unhook warning: {e}")
        
        # 启动新进程
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + sys.argv[1:])
        else:
            subprocess.Popen([sys.executable, sys.argv[0]] + sys.argv[1:])
        
        print("[Restart] New process started, exiting old process...")
        
        # 关键延迟：确保新进程初始化完成，旧进程钩子释放
        time.sleep(0.8)
        
        # 优雅退出
        QApplication.quit()
        time.sleep(0.2)
        os._exit(0)  # 强制退出，不执行清理（避免钩子重新注册）
        
    except Exception as e:
        print(f"[Restart] Fatal error: {e}")
        os._exit(1)

# V66: 修复看门狗 - 优先重新注册热键，失败才重启
def watchdog_thread():
    """增强型看门狗：睡眠检测后优先重新注册，失败才重启"""
    last_check = time.time()
    while True:
        time.sleep(5)
        now = time.time()
        if now - last_check > 15:
            print("[Watchdog] Sleep detected!")
            
            # 策略：先尝试轻量级重新注册
            try:
                keyboard.unhook_all()
                time.sleep(0.5)
                keyboard.add_hotkey(config.hotkey, check_hotkey_and_trigger)
                print("[Watchdog] Hotkey re-registered successfully")
            except Exception as e:
                print(f"[Watchdog] Re-register failed ({e}), forcing restart...")
                restart_program()
                return  # 重启后此线程结束
                
        last_check = now

def setup_tray(app):
    global tray_icon
    icon_path = resource_path(config.icon_filename)
    if os.path.exists(icon_path):
        src_img = QImage(icon_path)
        size = src_img.size()
        out_img = QImage(size, QImage.Format.Format_ARGB32)
        out_img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out_img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        brush = QBrush(src_img)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size.width(), size.height())
        painter.end()
        icon = QIcon(QPixmap.fromImage(out_img))
    else:
        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        
    tray_icon = QSystemTrayIcon(icon, app)
    menu = QMenu()
    
    menu.addAction("立即截图 (Ctrl+1)", comm.trigger_screenshot.emit)
    menu.addAction("重启程序 (修复失效)", restart_program)
    menu.addSeparator()
    
    rmenu = menu.addMenu("右键保存功能 (管理)")
    rmenu.addAction("开启: 添加到系统右键", lambda: QMessageBox.information(None, "GeekPaste", reg_manager.install()[1]))
    rmenu.addAction("关闭: 从右键移除", lambda: QMessageBox.information(None, "GeekPaste", reg_manager.uninstall()[1]))
    
    menu.addSeparator()
    menu.addAction("访问 GitHub 主页", open_github)
    menu.addAction("退出", app.quit)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()

def check_hotkey_and_trigger():
    if ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000:
        comm.trigger_screenshot.emit()

# V66: 带重试的热键注册
def setup_hotkey_with_retry(max_retries=3):
    """带重试的热键注册"""
    for i in range(max_retries):
        try:
            keyboard.add_hotkey(config.hotkey, check_hotkey_and_trigger)
            print(f"[Setup] Hotkey registered on attempt {i+1}")
            return True
        except Exception as e:
            print(f"[Setup] Attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(0.5 * (i + 1))
    return False

if __name__ == '__main__':
    t_mouse = threading.Thread(target=start_mouse_thread, daemon=True)
    t_mouse.start()
    
    t_watchdog = threading.Thread(target=watchdog_thread, daemon=True)
    t_watchdog.start()
    
    # V66: 禁用Qt的自动缩放，我们手动处理
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    setup_tray(app)
    
    comm.trigger_screenshot.connect(do_show_windows)
    comm.show_toast.connect(do_show_toast)
    
    # V66: 使用带重试的热键注册
    hotkey_ok = setup_hotkey_with_retry()
    if not hotkey_ok:
        print("[Main] WARNING: Failed to register hotkey after retries")
    
    print("Mouse4 V66 (Sleep Fix) Started.")
    print(f"Config file: {config_mgr.config_file}")
    sys.exit(app.exec())