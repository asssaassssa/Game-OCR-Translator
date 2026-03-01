import sys
import time
import mss
import pyautogui
import numpy as np
import os
import cv2

# 保持 DPI 设置不变
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0" 
os.environ["QT_SCALE_FACTOR"] = "1"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from config.settings import CAPTURE_CONFIG
from core.ocr_engine import PaddleOCREngine
from core.translator import LocalDictionary
from core.utils import find_word_in_text
from ui.overlay import Crosshair, ResultPopup

class Worker(QThread):
    result_signal = pyqtSignal(str, int, int, bool) # 文本, x, y, 是否错误
    crosshair_signal = pyqtSignal(int, int)         # x, y
    hide_signal = pyqtSignal()
    toggle_crosshair_signal = pyqtSignal(bool)      # True=显示, False=隐藏

    def __init__(self):
        super().__init__()
        self.is_running = True
        
        # 初始化 OCR 引擎
        print(">>> [系统] 正在加载 PaddleOCR 模型...")
        self.ocr = PaddleOCREngine()
        print(">>> [系统] OCR 模型加载完毕")
        
        self.dict = LocalDictionary()
        
        self.capture_w = CAPTURE_CONFIG["width"]
        self.capture_h = CAPTURE_CONFIG["height"]
        self.offset_y = CAPTURE_CONFIG["offset_y"]
        
        self.is_popup_visible = False

    def run(self):
        print(">>> [Worker] 监控线程已启动")
        
        last_pos = pyautogui.position()
        last_time = time.time()
        
        # 核心参数 (论文中提到的阈值)
        MOVE_THRESHOLD = 3   
        HIDE_THRESHOLD = 5   
        IDLE_TIME = 0.4      
        
        with mss.mss() as sct:
            while self.is_running:
                try:
                    curr_pos = pyautogui.position()
                    curr_time = time.time()
                    
                    # 实时更新准星位置
                    self.crosshair_signal.emit(curr_pos.x, curr_pos.y)

                    # 计算鼠标移动距离
                    dist = ((curr_pos.x - last_pos.x)**2 + (curr_pos.y - last_pos.y)**2)**0.5
                    
                    if dist > MOVE_THRESHOLD:
                        # 状态：鼠标移动中
                        last_time = curr_time # 重置静止计时器
                        
                        # 如果移动距离超过隐藏阈值，且弹窗还在显示，则隐藏弹窗
                        if self.is_popup_visible and dist > HIDE_THRESHOLD:
                            self.hide_signal.emit()
                            self.is_popup_visible = False
                    
                    else:
                        # 状态：鼠标静止
                        # 如果弹窗没显示，且静止时间超过阈值 -> 触发翻译流程
                        if not self.is_popup_visible and (curr_time - last_time > IDLE_TIME):
                            
                            # ==========================================
                            # [性能埋点] 流程开始
                            # ==========================================
                            t_start = time.perf_counter()
                            
                            # 执行核心业务逻辑 (截图 -> OCR -> 查词)
                            success = self.perform_ocr_task(sct, curr_pos.x, curr_pos.y, t_start)
                            
                            if success:
                                self.is_popup_visible = True
                                # 成功显示后，不重置 last_time，防止重复触发
                            else:
                                # 失败/无结果，重置计时器，避免死循环高频截图
                                last_time = time.time() 

                    last_pos = curr_pos
                    time.sleep(0.02) # 防止 CPU 占用过高
                    
                except Exception as e:
                    print(f"Worker Loop Error: {e}")
                    pass

    def perform_ocr_task(self, sct, x, y, t_start):
        """
        执行具体的截图、识别任务，并打印性能日志
        返回: Boolean (是否成功识别并弹窗)
        """
        try:
            # -------------------------------------------------
            # 阶段 1：准备与截图 (Capture)
            # -------------------------------------------------
            capture_w = self.capture_w
            capture_h = self.capture_h
            
            # 1.1 计算屏幕坐标
            screen_w = sct.monitors[1]["width"]
            screen_h = sct.monitors[1]["height"]
            
            theory_left = int(x - capture_w // 2)
            theory_top = int((y - self.offset_y) - capture_h // 2)
            
            left = max(0, min(theory_left, screen_w - capture_w))
            top = max(0, min(theory_top, screen_h - capture_h))
            
            monitor = {"top": top, "left": left, "width": capture_w, "height": capture_h}
            
            # 计算光标在截图中的相对坐标
            rel_target_x = int(x - left)
            rel_target_y = int((y - self.offset_y) - top)
            
            # 1.2 隐藏准星 (避免遮挡 OCR)
            self.toggle_crosshair_signal.emit(False)
            time.sleep(0.02) # 等待 UI 刷新 (短暂阻塞，计入截图耗时)
            
            # 1.3 执行截图
            t1 = time.perf_counter()
            sct_img = sct.grab(monitor)
            img_np = np.array(sct_img)
            t2 = time.perf_counter()
            cost_capture = (t2 - t1) * 1000 # ms
            
            # 截图完立刻恢复准星
            self.toggle_crosshair_signal.emit(True)

            # -------------------------------------------------
            # 阶段 2：OCR 推理 (Inference)
            # -------------------------------------------------
            t3 = time.perf_counter()
            ocr_results, scale = self.ocr.recognize(img_np)
            t4 = time.perf_counter()
            cost_ocr = (t4 - t3) * 1000 # ms
            
            if not ocr_results:
                self._print_perf_log(cost_capture, cost_ocr, 0, False)
                return False
            
            # -------------------------------------------------
            # 阶段 3：后处理与查词 (Post-process)
            # -------------------------------------------------
            t5 = time.perf_counter()
            
            found_word = None
            found_box = None
            
            # 3.1 遍历结果寻找光标命中的单词
            for line in ocr_results:
                box = line[0]
                text = line[1][0]
                
                # 获取包围盒坐标
                x_min = min(p[0] for p in box)
                x_max = max(p[0] for p in box)
                y_min = min(p[1] for p in box)
                y_max = max(p[1] for p in box)
                
                # 宽松判定：光标是否在框内 (允许 5px 误差)
                if (x_min - 5 < rel_target_x < x_max + 5) and \
                   (y_min - 5 < rel_target_y < y_max + 5):
                    
                    # 核心算法：基于比例估算单词
                    box_w = x_max - x_min
                    ratio = (rel_target_x - x_min) / box_w if box_w > 0 else 0.5
                    ratio = max(0.0, min(1.0, ratio)) # 限制在 0-1 之间
                    
                    found_word = find_word_in_text(text, ratio)
                    found_box = box
                    break
            
            t6 = time.perf_counter()
            cost_post = (t6 - t5) * 1000 # ms
            
            # -------------------------------------------------
            # 阶段 4：结果分发 (UI Dispatch)
            # -------------------------------------------------
            if found_word:
                definition = self.dict.query(found_word)
                if definition:
                    # 查到词了
                    fmt_def = self.dict.format_definition(definition)
                    full_text = f"{found_word}\n{fmt_def}"
                    self.result_signal.emit(full_text, x, y, False)
                    
                    # 打印成功日志
                    self._print_perf_log(cost_capture, cost_ocr, cost_post, True, found_word)
                    return True
                else:
                    # 没查到
                    self.result_signal.emit(f"未收录: {found_word}", x, y, True)
                    self._print_perf_log(cost_capture, cost_ocr, cost_post, True, found_word + "(无解)")
                    return True
            
            # 没命中任何单词
            self._print_perf_log(cost_capture, cost_ocr, cost_post, False)
            return False
            
        except Exception as e:
            self.toggle_crosshair_signal.emit(True)
            print(f"🚨 Task Error: {e}")
            return False

    def _print_perf_log(self, t_cap, t_ocr, t_post, success, word=""):
        """辅助函数：打印格式化的性能日志"""
        total = t_cap + t_ocr + t_post
        status = "✅" if success else "❌"
        # 格式化输出，方便复制到 Excel
        print(f"[性能监控] {status} 总耗时:{total:5.1f}ms | "
              f"截图:{t_cap:4.1f}ms | "
              f"OCR:{t_ocr:5.1f}ms | "
              f"处理:{t_post:4.1f}ms | "
              f"词汇: {word}")

class GameTranslatorApp:
    def __init__(self):
        # 强制开启高 DPI 支持，避免 UI 模糊
        if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        self.app = QApplication(sys.argv)
        
        # 初始化 UI 组件
        self.crosshair = Crosshair()
        self.popup = ResultPopup()
        self.crosshair.show()
        
        # 初始化工作线程
        self.worker = Worker()
        
        # 连接信号槽
        self.worker.crosshair_signal.connect(self.crosshair.update_pos)
        self.worker.result_signal.connect(self.popup.show_text)
        self.worker.hide_signal.connect(self.popup.hide_anim)
        self.worker.toggle_crosshair_signal.connect(self.crosshair.setVisible)
        
    def start(self):
        self.worker.start()
        sys.exit(self.app.exec())

# 程序入口
if __name__ == "__main__":
    game_app = GameTranslatorApp()
    game_app.start()