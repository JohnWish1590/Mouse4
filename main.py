import time
import queue
from pynput import mouse
import uiautomation as auto
import keyboard

# ================= 配置区 =================
DOUBLE_CLICK_THRESHOLD = 0.25  
DEBUG_MODE = True              
# ==========================================

action_queue = queue.Queue()

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
    """
    V4 核心逻辑：不看名字，看能力。
    如果是文件或驱动器，它一定支持 'SelectionItemPattern' (可被选中模式)。
    空白处是不支持这个模式的。
    """
    current = element
    try:
        # 向上查 5 代
        for i in range(5): 
            if not current:
                break
            
            # 1. 获取控件的基本信息
            ctype = current.ControlTypeName
            name = current.Name
            
            # 调试打印：让你看到你到底点到了哪一层
            if DEBUG_MODE:
                print(f"  [Layer {i}] Type: {ctype}, Name: {name}")

            # 2. 【必杀技】检查是否支持“被选中”模式
            # 10010 是 SelectionItemPattern 的 ID
            # 只要支持这个，说明它是一个可以被选中的“物体”，绝对不是空白
            if current.GetPattern(10010): 
                if DEBUG_MODE: print(f"  >>> 发现可选中对象！判定为文件/驱动器。")
                return True

            # 3. 辅助黑名单 (防止某些不支持 Pattern 的纯文字/图片漏网)
            if ctype in ['ListItem', 'TreeItem', 'Image', 'Text', 'Edit', 'Hyperlink']:
                if DEBUG_MODE: print(f"  >>> 命中黑名单类型 ({ctype})。")
                return True

            # 继续往上找爸爸
            current = current.GetParentControl()
            
    except Exception as e:
        print(f"检测出错: {e}")
    
    return False

def process_double_click(x, y):
    try:
        element = auto.ControlFromPoint(x, y)
        top_window = element.GetTopLevelControl()
        
        if not top_window or top_window.ClassName != "CabinetWClass":
            if DEBUG_MODE: print(f"忽略：不是资源管理器")
            return

        print(f"\n--- 检测点击位置 ---")
        # 检查是否是文件/驱动器
        if is_drive_or_file(element):
            if DEBUG_MODE: print(f"结果：忽略 (点到了内容)")
            return
            
        if DEBUG_MODE: print(f"结果：>>> 触发返回 (确认为空白处)")
        keyboard.send('alt+up')

    except Exception as e:
        print(f"Error: {e}")

def main():
    print("MouseMaster V4 (底层能力检测版) 已启动...")
    print("请测试双击 D 盘图标 (应该只有日志，不返回)。")
    print("请测试双击 空白处 (应该返回)。")
    
    monitor = MouseMonitor()
    listener = mouse.Listener(on_click=monitor.on_click)
    listener.start()

    try:
        while True:
            try:
                x, y = action_queue.get(timeout=0.1)
                process_double_click(x, y)
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        listener.stop()

if __name__ == "__main__":
    main()