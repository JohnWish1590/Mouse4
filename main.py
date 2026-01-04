import time
import queue
import threading
import os
import sys
import webbrowser

from pynput import mouse
import uiautomation as auto
import keyboard
import pystray
from PIL import Image

# ================= 配置区 =================
DOUBLE_CLICK_THRESHOLD = 0.25
DEBUG_MODE = True
# 1. 修复：更新为正确的 GitHub 地址
GITHUB_URL = "https://github.com/JohnWish1590/Mouse4" 
APP_NAME = "Mouse4"
# ==========================================

action_queue = queue.Queue()

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MouseMonitor:
    def __init__(self):
        self.last_click_time = 0
        self.click_count = 0
        
    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed:
            current_time = time.time()
            if current_time - self.last_click_time < DOUBLE_CLICK_THRESHOLD:
                action_queue.put((x, y))
                self.click_count = 0 
            else:
                self.click_count = 1
            self.last_click_time = current_time

def is_drive_or_file(element):
    current = element
    try:
        for i in range(5): 
            if not current: break
            if current.GetPattern(10010): return True 
            if current.ControlTypeName in ['ListItem', 'TreeItem', 'Image', 'Text', 'Edit', 'Hyperlink']:
                return True
            current = current.GetParentControl()
    except: pass
    return False

def process_worker():
    while True:
        try:
            x, y = action_queue.get(timeout=1)
            element = auto.ControlFromPoint(x, y)
            top_window = element.GetTopLevelControl()
            if not top_window or top_window.ClassName != "CabinetWClass": continue
            if not is_drive_or_file(element):
                if DEBUG_MODE: print(">>> 空白处双击，返回上一级")
                keyboard.send('alt+up')
        except queue.Empty: continue
        except Exception as e:
            if DEBUG_MODE: print(f"Error: {e}")

# --- 托盘菜单逻辑 ---
def on_open_github(icon, item):
    webbrowser.open(GITHUB_URL)

def on_exit(icon, item):
    icon.stop()
    os._exit(0) 

def run_tray_icon():
    icon_path = resource_path("logo.ico")
    
    if not os.path.exists(icon_path):
        return

    image = Image.open(icon_path)
    
    # 2. 尝试修复：强制重新调整图片大小为标准托盘尺寸 (64x64)
    # 这有助于让 Windows 更准确地渲染它，而不是缩小得过分
    image = image.resize((64, 64), Image.Resampling.LANCZOS)
    
    menu = (
        pystray.MenuItem(f'{APP_NAME} 正在运行', lambda icon, item: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('给作者留言 (GitHub)', on_open_github),
        pystray.MenuItem('退出 (Exit)', on_exit)
    )

    icon = pystray.Icon("Mouse4", image, "Mouse4 双击空白返回", menu)
    icon.run()

def main():
    print("Mouse4 启动中...")
    monitor = MouseMonitor()
    listener = mouse.Listener(on_click=monitor.on_click)
    listener.start()
    t = threading.Thread(target=process_worker, daemon=True)
    t.start()
    run_tray_icon()

if __name__ == "__main__":
    main()