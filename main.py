import time
import queue
import threading
import os
import sys
import webbrowser

# 引入依赖库
from pynput import mouse
import uiautomation as auto
import keyboard
import pystray
from PIL import Image

# ================= 配置区 =================
DOUBLE_CLICK_THRESHOLD = 0.25  # 双击判定时间
DEBUG_MODE = True              # 调试模式
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
    """ 判断是否点到了文件/图标 """
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

# --- 关键修改在这里 ---
def process_worker():
    print(">>> 工作线程已启动，等待双击...")
    
    # 【修复重点】告诉 Windows：这个后台线程也要用自动化组件
    with auto.UIAutomationInitializerInThread():
        while True:
            try:
                x, y = action_queue.get(timeout=1)
                
                if DEBUG_MODE: print(f"检测到双击位置: {x}, {y}")
                
                element = auto.ControlFromPoint(x, y)
                top_window = element.GetTopLevelControl()
                
                if not top_window or top_window.ClassName != "CabinetWClass":
                    if DEBUG_MODE: print("忽略：不是在资源管理器窗口")
                    continue

                if is_drive_or_file(element):
                    if DEBUG_MODE: print("忽略：点到了文件或图标")
                else:
                    if DEBUG_MODE: print(">>> 判定为空白处！执行 Alt+Up")
                    keyboard.send('alt+up')
                    
            except queue.Empty:
                continue
            except Exception as e:
                # 这里打印错误但不崩溃，方便调试
                if DEBUG_MODE: print(f"Work Error: {e}")

def on_open_github(icon, item):
    webbrowser.open(GITHUB_URL)

def on_exit(icon, item):
    icon.stop()
    os._exit(0) 

def run_tray_icon():
    icon_path = resource_path("logo.ico")
    
    if not os.path.exists(icon_path):
        print("未找到图标文件，使用默认红点")
        image = Image.new('RGB', (64, 64), color='red')
    else:
        image = Image.open(icon_path)
        image = image.resize((256, 256), Image.Resampling.LANCZOS)
    
    menu = (
        pystray.MenuItem(f'{APP_NAME} 运行中...', lambda icon, item: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('访问 GitHub', on_open_github),
        pystray.MenuItem('退出程序', on_exit)
    )

    icon = pystray.Icon("Mouse4", image, "Mouse4 双击空白返回", menu)
    icon.run()

def main():
    print("=== Mouse4 启动中 (V7 修复版) ===")
    
    monitor = MouseMonitor()
    listener = mouse.Listener(on_click=monitor.on_click)
    listener.start()
    
    t = threading.Thread(target=process_worker, daemon=True)
    t.start()
    
    print("程序已最小化到托盘。")
    run_tray_icon()

if __name__ == "__main__":
    main()