import sys
import os
import ctypes
import datetime
import threading
import time
import webbrowser  # 用于打开网页

# ================= 1. 右键粘贴保存模式 (静默无弹窗) =================
def run_paste_mode_safe(args):
    try:
        from PIL import ImageGrab
    except ImportError:
        ctypes.windll.user32.MessageBoxW(0, "缺少 Pillow 库，请运行 pip install pillow", "错误", 0x10)
        sys.exit(1)

    try:
        if len(args) > 2:
            raw_path = " ".join(args[2:])
            target_folder = raw_path.strip('"').strip()
        else:
            target_folder = os.getcwd()

        if not target_folder or not os.path.exists(target_folder):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            target_folder = desktop

        img = ImageGrab.grabclipboard()
        
        if img is None:
            ctypes.windll.user32.MessageBoxW(0, "剪贴板里是空的 (或者不是图片)！\n请先按 F1 截图。", "保存失败", 0x30)
            sys.exit(0)
            
        t_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"Screenshot_{t_str}.png"
        save_path = os.path.join(target_folder, fname)
        
        img.save(save_path, "PNG")
        
        # 静默退出，无弹窗
        sys.exit(0)
            
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"程序错误:\n{str(e)}", "错误", 0x10)
        sys.exit(1)

if len(sys.argv) > 1 and sys.argv[1] == '--paste':
    run_paste_mode_safe(sys.argv)

# ================= 2. 主程序设置 =================
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except:
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass

# ================= 3. 导入 GUI =================
from PyQt6.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu, 
                             QInputDialog, QLabel, QVBoxLayout, QMessageBox, QStyle)
from PyQt6.QtCore import (Qt, QRect, QPoint, pyqtSignal, QObject, 
                          QPropertyAnimation, QEasingCurve, QTimer)
from PyQt6.QtGui import (QPainter, QColor, QPen, QImage, QAction, 
                         QFont, QIcon)
import keyboard
import mss
import winreg

# ================= 4. 全局配置 =================
class GlobalConfig:
    hotkey = 'ctrl+1'              
    double_click_speed = 0.3       
    theme_color = QColor('#00FF00')
    border_width = 2
    icon_filename = 'logo.ico'
    github_url = "https://github.com/JohnWish1590/Mouse4"
    context_menu_text = "粘贴刚才的截图 (GeekPaste)"
    reg_key_name = "GeekPaste"

config = GlobalConfig()

# ================= 5. 智能窗口识别 & 鼠标监听 =================
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

# ================= 6. 注册表管理器 =================
class RegistryManager:
    def __init__(self):
        self.base_key = winreg.HKEY_CURRENT_USER
        self.key_path = fr"Software\Classes\Directory\Background\shell\{config.reg_key_name}"
    
    def install(self):
        try:
            python_exe = sys.executable
            if "pythonw.exe" not in python_exe and "python.exe" in python_exe:
                python_exe = python_exe.replace("python.exe", "pythonw.exe")
            
            script_path = os.path.abspath(__file__)
            if script_path.endswith('.py') and os.path.exists(script_path + 'w'):
                script_path = script_path + 'w'
            
            command_str = f'"{python_exe}" "{script_path}" --paste "%V"'
            
            key = winreg.CreateKey(self.base_key, self.key_path)
            winreg.SetValue(key, "", winreg.REG_SZ, config.context_menu_text)
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "imageres.dll,-5302")
            winreg.CloseKey(key)
            
            cmd_key = winreg.CreateKey(self.base_key, self.key_path + r"\command")
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, command_str)
            winreg.CloseKey(cmd_key)
            return True, "注册成功！\n请先点'关闭'，该功能即刻生效。"
        except Exception as e:
            return False, f"注册失败: {e}"

    def uninstall(self):
        try:
            try: winreg.DeleteKey(self.base_key, self.key_path + r"\command")
            except FileNotFoundError: pass
            winreg.DeleteKey(self.base_key, self.key_path)
            return True, "已移除右键菜单。"
        except: return True, "未安装。"

# ================= 7. 截图功能 =================
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

class SnippingWindow(QWidget):
    def __init__(self, screen_info):
        super().__init__()
        self.screen_info = screen_info
        self.setGeometry(screen_info.geometry())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        if self.is_snipping and self.begin != self.end:
            local_begin = self.mapFromGlobal(self.begin)
            local_end = self.mapFromGlobal(self.end)
            rect = QRect(local_begin, local_end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(config.theme_color, config.border_width)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            w, h = rect.width(), rect.height()
            if w > 10:
                txt = f"{w} x {h}"
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor('#000000'))
                painter.drawRect(rect.x(), rect.y()-25, len(txt)*9, 20)
                painter.setPen(QColor('#FFFFFF'))
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.drawText(rect.x()+5, rect.y()-10, txt)

    def mousePressEvent(self, event):
        self.begin = event.globalPosition().toPoint()
        self.end = self.begin
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.globalPosition().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_snipping = False
        rect = QRect(self.begin, self.end).normalized()
        close_all_windows()
        if rect.width() > 5:
            self.capture(rect.x(), rect.y(), rect.width(), rect.height())
            comm.show_toast.emit(rect.x() + rect.width(), rect.y())

    def capture(self, x, y, w, h):
        try:
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h, "mon": -1}
                img = sct.grab(monitor)
                qimg = QImage(img.bgra, img.width, img.height, QImage.Format.Format_RGB32).copy()
                QApplication.clipboard().setImage(qimg)
        except Exception as e:
            print(f"Error: {e}")

def close_all_windows():
    global active_windows
    for win in active_windows: win.close()
    active_windows = []

# ================= 8. 托盘与控制 =================
reg_manager = RegistryManager()
tray_icon = None

def do_show_windows():
    global active_windows
    if active_windows: close_all_windows(); return
    for screen in QApplication.screens():
        active_windows.append(SnippingWindow(screen))

def do_show_toast(x, y):
    global toast
    toast = SuccessToast("Saved!")
    toast.show_animation(x, y)

def change_hotkey():
    txt, ok = QInputDialog.getText(None, "设置", "新热键:", text=config.hotkey)
    if ok and txt:
        try:
            keyboard.remove_hotkey(comm.trigger_screenshot.emit)
            keyboard.add_hotkey(txt, comm.trigger_screenshot.emit)
            config.hotkey = txt
            tray_icon.showMessage("成功", f"热键已更新: {txt}")
        except: tray_icon.showMessage("失败", "无效热键")

def change_speed():
    val, ok = QInputDialog.getDouble(
        None, 
        "设置 返回上一层文件夹双击速度", 
        "双击判定间隔 (秒):\n(默认0.3，越小越难触发，越大越容易误触)", 
        value=config.double_click_speed, 
        min=0.1, max=2.0, decimals=2
    )
    if ok:
        config.double_click_speed = val
        tray_icon.showMessage("设置更新", f"速度已调整为: {val}秒")

# 打开 GitHub 主页
def open_github():
    webbrowser.open(config.github_url)

def setup_tray(app):
    global tray_icon
    icon = QIcon(config.icon_filename) if os.path.exists(config.icon_filename) else app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray_icon = QSystemTrayIcon(icon, app)
    menu = QMenu()
    
    menu.addAction("立即截图 (Ctrl+1)", comm.trigger_screenshot.emit)
    menu.addSeparator()
    
    rmenu = menu.addMenu("右键保存功能 (管理)")
    rmenu.addAction("开启: 添加到系统右键", lambda: QMessageBox.information(None, "GeekPaste", reg_manager.install()[1]))
    rmenu.addAction("关闭: 从右键移除", lambda: QMessageBox.information(None, "GeekPaste", reg_manager.uninstall()[1]))
    
    menu.addSeparator()
    # [修改点] 更改了菜单文字
    menu.addAction("设置截图热键...", change_hotkey)
    menu.addAction("设置 返回上一层文件夹双击速度...", change_speed)
    
    menu.addSeparator()
    menu.addAction("访问 GitHub 主页", open_github)
    menu.addAction("退出", app.quit)
    
    tray_icon.setContextMenu(menu)
    tray_icon.show()

if __name__ == '__main__':
    t = threading.Thread(target=start_mouse_thread, daemon=True)
    t.start()
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    setup_tray(app)
    
    comm.trigger_screenshot.connect(do_show_windows)
    comm.show_toast.connect(do_show_toast)
    
    try: keyboard.add_hotkey(config.hotkey, comm.trigger_screenshot.emit)
    except: pass
    
    print("GeekTool V33 (Label Updated) Started.")
    sys.exit(app.exec())