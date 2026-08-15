# -*- coding: utf-8 -*-
"""临时诊断脚本: 打印真实显示器布局 + 逐屏抓取亮度统计"""
import sys, ctypes
ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
app = QApplication(sys.argv)
if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

import mss
from PIL import Image

print("=== QApplication.screens() ===")
for s in QApplication.screens():
    g = s.geometry()
    print(f"  name={s.name()} geo=({g.x()},{g.y()}) {g.width()}x{g.height()} dpr={s.devicePixelRatio()} primary={s is QApplication.primaryScreen()}")

with mss.mss() as sct:
    print("=== mss.monitors ===")
    for i, m in enumerate(sct.monitors):
        print(f"  [{i}] left={m['left']} top={m['top']} w={m['width']} h={m['height']}")
    print("=== per-monitor mss grab lum ===")
    for i, m in enumerate(sct.monitors[1:]):
        try:
            img = sct.grab(m)
            pi = Image.frombytes('RGB', (img.width, img.height), img.bgra, 'raw', 'BGRX')
            ext = pi.convert('L').resize((32, 32)).getextrema()
            print(f"  monitor[{i}] {m} -> grab {img.width}x{img.height} lum(min,max)={ext}")
        except Exception as e:
            print(f"  monitor[{i}] {m} -> GRAB FAILED: {e}")
    print("=== monitors[0] (whole virtual) grab lum ===")
    try:
        img = sct.grab(sct.monitors[0])
        pi = Image.frombytes('RGB', (img.width, img.height), img.bgra, 'raw', 'BGRX')
        small = pi.convert('L').resize((64, 64))
        ext = small.getextrema()
        # 分段亮度: 看哪一列黑
        import math
        w, h = small.size
        cols = []
        for cx in range(0, w, 8):
            crop = small.crop((cx, 0, min(cx + 8, w), h))
            e = crop.getextrema()
            cols.append((cx, e))
        print(f"  monitors[0] -> {img.width}x{img.height} lum={ext}")
        print("  column bands (x, lum):", cols)
    except Exception as e:
        print(f"  monitors[0] GRAB FAILED: {e}")

print("=== Qt QScreen.grabWindow(0) per screen ===")
for s in QApplication.screens():
    try:
        pm = s.grabWindow(0)
        pm.setDevicePixelRatio(1.0)
        qimg = pm.toImage()
        ext = qimg.scaled(32, 32).convertToFormat(__import__('PyQt6.QtGui', fromlist=['QImage']).QImage.Format.Format_Grayscale8)
        # 简化: 用 bytes 采样
        b = ext.bits().asstring(32 * 32)
        vals = list(b)
        print(f"  screen {s.geometry().width()}x{s.geometry().height()} -> grabWindow {pm.width()}x{pm.height()} lum(min,max)=({min(vals)},{max(vals)})")
    except Exception as e:
        print(f"  screen {s.geometry().width()}x{s.geometry().height()} -> FAILED: {e}")

app.quit()
