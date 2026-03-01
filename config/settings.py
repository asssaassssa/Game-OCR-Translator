import os
from pickle import FALSE
import sys

# =========================
# 路径配置
# =========================
# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 模型存储路径 (推荐使用绝对路径，避免环境差异)
# 如果用户没有配置环境变量，默认使用 D:/ocr_models
MODEL_DIR = os.path.join(BASE_DIR,"assets", "ocr_models")
#MODEL_DIR = os.getenv("OCR_MODEL_DIR", "D:/ocr_models")
# 词典路径
DICT_PATH = os.path.join(BASE_DIR, "assets", "dictionary.csv")

# =========================
# OCR 引擎配置
# =========================
OCR_CONFIG = {
    "use_gpu": False,           # 是否开启 GPU
    "gpu_id": 0,               # 显卡 ID (根据实际情况修改)
    "use_angle_cls": False,    # 是否启用方向分类
    "lang": "ch",              # 模型语言 (ch 模型泛化最好)
    "det_db_thresh": 0.3,      # 检测阈值
    "det_db_box_thresh": 0.6,  # 文本框阈值
    "show_log": False,
    "enable_mkldnn": True      # CPU 加速开关 (仅在 use_gpu=False 时有效)
}

# =========================
# 截图配置
# =========================
CAPTURE_CONFIG = {
    "width": 800,
    "height": 250,
    "offset_y": 40  # 鼠标上方多少像素开始截图
}
# =========================
# 调试配置
# =========================
DEBUG_MODE = False  # ❗ 开启这个！会打印详细日志并保存截图