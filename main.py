import time
import threading
from pynput import mouse
import uiautomation as auto
import keyboard

# ================= 配置区 =================
DOUBLE_CLICK_THRESHOLD = 0.3  # 双击判定时间间隔 (秒)
DEBUG_MODE = True             # 开启后会在控制台打印点击信息，方便调试
# ==========================================

class MouseMonitor:
    def __init__(self):
        self.last_click_time = 0
        self.click_count = 0
        
    def on_click(self, x, y, button, pressed):
        # 我们只关心左键按下
        if button == mouse.Button.left and pressed:
            current_time = time.time()
            
            # 判断是否是双击
            if current_time - self.last_click_time < DOUBLE_CLICK_THRESHOLD:
                self.handle_double_click(x, y)
                self.click_count = 0 # 重置
            else:
                self.click_count = 1
                
            self.last_click_time = current_time

    def handle_double_click(self, x, y):
        """处理双击逻辑"""
        try:
            # 1. 获取当前鼠标位置的 UI 元素
            element = auto.ElementFromPoint(x, y)
            
            # 2. 获取该元素所在的顶级窗口
            top_window = element.GetTopLevelControl()
            
            if not top_window:
                return

            # 3. 核心判断：窗口必须是“资源管理器”
            # Windows 11 资源管理器的类名通常是 'CabinetWClass'
            if top_window.ClassName != "CabinetWClass":
                if DEBUG_MODE: print(f"忽略：不是资源管理器 (类名: {top_window.ClassName})")
                return

            # 4. 核心判断：点击的是否是空白处
            # 逻辑：如果点到了具体的文件/文件夹，ControlType 通常是 'ListItem' 或 'TreeItem'
            # 如果点到了空白处，通常是 'Pane', 'List', 或 'Document'
            control_type = element.ControlTypeName
            
            # 黑名单模式：如果点到以下东西，说明点到了具体项目，不执行返回
            ignored_types = ['ListItem', 'TreeItem', 'Edit', 'Button', 'Hyperlink']
            
            if control_type in ignored_types:
                if DEBUG_MODE: print(f"忽略：点到了文件或控件 ({control_type})")
                return
            
            # 5. 执行返回上一层
            if DEBUG_MODE: print(f">>> 触发：在空白处 ({control_type}) 双击，返回上一层")
            
            # 发送 Alt + Up 组合键
            keyboard.send('alt+up')

        except Exception as e:
            print(f"发生错误: {e}")

def main():
    print("程序已启动...")
    print("请在 Windows 11 资源管理器空白处双击测试。")
    print("按 Ctrl+C 退出程序。")
    
    monitor = MouseMonitor()
    
    # 启动鼠标监听
    # pynput 的监听器是阻塞的，所以直接 join
    with mouse.Listener(on_click=monitor.on_click) as listener:
        listener.join()

if __name__ == "__main__":
    main()
