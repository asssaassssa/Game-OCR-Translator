import os
import sys

# ==========================================
# 1. 恢复默认 DPI 设置 (移除 ctypes 强制锁定)
# ==========================================
# 之前这里有 ctypes.windll.shcore.SetProcessDpiAwareness(0)
# 现在我们去掉它，让系统和库自己协商。

# ==========================================
# 2. 仅保留 Qt 的环境变量设置
# ==========================================
# 这里的设置是为了防止 PyQt6 窗口在高分屏下模糊或错位
# Auto=1, Scaling=0, Factor=1 是最稳健的组合
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0" 
os.environ["QT_SCALE_FACTOR"] = "1"

from core.utils import setup_env

if __name__ == "__main__":
    setup_env()
    
    # 延迟导入，确保环境变量生效
    from core.app import GameTranslatorApp
    
    app = GameTranslatorApp()
    app.start()