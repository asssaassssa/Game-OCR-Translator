import os
import sys
import cv2
import numpy as np
import logging
# 压制 Paddle 日志
logging.getLogger("ppocr").setLevel(logging.ERROR)

from paddleocr import PaddleOCR
from config.settings import OCR_CONFIG, MODEL_DIR

class PaddleOCREngine:
    def __init__(self):
        print("🚀 [Core] 初始化 OCR 引擎...")
        
        # 路径检查
        det_dir = os.path.join(MODEL_DIR, "det")
        rec_dir = os.path.join(MODEL_DIR, "rec")
        cls_dir = os.path.join(MODEL_DIR, "cls")
        
            # 打印出 Python 真正去查找的完整绝对路径
        target_file = os.path.join(det_dir, "inference.pdmodel")
        print(f"🔍 正在寻找文件: {target_file}")

    # 打印出 det 目录下到底有什么
        if os.path.exists(det_dir):
            print(f"📂 det 目录下的内容: {os.listdir(det_dir)}")
        else:
            print(f"❌ det 目录本身就不存在: {det_dir}")
        if not os.path.exists(os.path.join(det_dir, "inference.pdmodel")):
            raise FileNotFoundError(f"❌ 模型文件未找到，请检查路径: {det_dir}")

        # GPU 显卡指定
        if OCR_CONFIG["use_gpu"]:
            os.environ["CUDA_VISIBLE_DEVICES"] = str(OCR_CONFIG["gpu_id"])
            
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=OCR_CONFIG["use_angle_cls"],
                lang=OCR_CONFIG["lang"],
                use_gpu=OCR_CONFIG["use_gpu"],
                gpu_id=0, # 环境变量已屏蔽其他卡，这里固定为0
                show_log=OCR_CONFIG["show_log"],
                enable_mkldnn=OCR_CONFIG["enable_mkldnn"],
                det_model_dir=det_dir,
                rec_model_dir=rec_dir,
                cls_model_dir=cls_dir,
                det_db_thresh=OCR_CONFIG["det_db_thresh"],
                det_db_box_thresh=OCR_CONFIG["det_db_box_thresh"]
            )
            # 预热
            self.warmup()
            print("✅ [Core] OCR 引擎就绪")
            
        except Exception as e:
            print(f"❌ [Core] OCR 初始化失败: {e}")
            sys.exit(1)

    def warmup(self):
        """预热 GPU，防止第一次识别卡顿"""
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        self.ocr.ocr(dummy_img, cls=False)

    def recognize(self, img_np):
        """执行识别，包含前处理"""
        # 1. 移除 Alpha 通道 (BGRA -> BGR)
        # mss 截图默认是 BGRA (4通道)，Paddle 只要 3通道
        if img_np.shape[-1] == 4:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)

        # 2. 确保 uint8 类型
        if img_np.dtype != np.uint8:
            img_np = img_np.astype(np.uint8)
            
        # 3. 转 RGB (Paddle 偏好 RGB)
        # 这一步非常关键！
        img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        
        # 4. 识别
        # cls=True 有时候会提高识别率，但在游戏里容易把单词倒过来，建议 False
        result = self.ocr.ocr(img_rgb, cls=False)
        
        # 调试打印 (可选)
        # print(f"DEBUG: OCR result raw: {result}")
        
        if not result or result[0] is None:
            return [], 1.0
            
        return result[0], 1.0