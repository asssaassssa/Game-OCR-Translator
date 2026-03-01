#  Game-OCR-Translator | 游戏即时翻译助手

> **第 35 届“冯如杯”学生学术科技作品竞赛参赛项目**
>
> A Zero-Interference Screen Translator based on PyQt6 & PaddleOCR.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt)](https://pypi.org/project/PyQt6/)
[![PaddleOCR](https://img.shields.io/badge/OCR-PaddleOCR-red)](https://github.com/PaddlePaddle/PaddleOCR)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

---


https://github.com/user-attachments/assets/4e9b0fd0-fd4c-4b2b-b04f-45efc1bdaf51


##  项目简介 (Introduction)

针对外语游戏汉化缺失及传统查词方式（Alt+Tab 切屏）割裂沉浸感的问题，本项目设计并实现了一款**基于追踪光标状态与即时 OCR 技术的零干扰辅助查词工具**。（其实是作者玩喵基因时一时兴起了）

**特点：**
*    **无感交互**：采用无边框透明窗口与鼠标穿透，确保游戏操作零干扰。
*    **指哪译哪**：基于光标状态机与字符位置估算算法，实现快速精准取词。

---

##  功能架构 (Tech Stack)

*   **用户界面 (GUI)**: `PyQt6` (实现动画效果)
*   **光学识别 (OCR)**: `PaddleOCR` (PP-OCRv3 轻量级模型)
*   **屏幕捕获**: `mss` (高性能截图)
*   **逻辑控制**: Python 多线程 (`QThread`) 

---

##  快速开始 (Quick Start)

### 1. 环境准备
确保你的电脑已安装 Python 3.8 或更高版本（别用3.11，作者自己用的是3.10）。

```bash
# 克隆项目到本地
git clone https://github.com/[你的用户名]/Game-OCR-Translator.git
cd Game-OCR-Translator

# 安装依赖
pip install -r requirements.txt
```
注意：如果需要 GPU 加速，请根据你的显卡型号，参考 PaddlePaddle 官网 单独安装对应的 GPU 版本。本项目默认依赖 CPU 版本以保证最大兼容性（其实是作者不知道如何解决神秘依赖冲突😅）。

注意：运行项目时控制台出现一行报错是正常的（qt.qpa.window: SetProcessDpiAwarenessContext() failed...
）它似乎不影响功能，而作者不清楚如何将其去除。

### 2. 模型配置 (Model Setup)

本项目依赖 PaddleOCR 推理模型。程序启动时会自动检测 `assets/ocr_models` 目录，若缺失模型文件将无法运行（完整项目文件夹中已有）

**手动配置方式**：
1.  下载以下三个模型文件（PP-OCRv3 轻量级模型）：
    *   检测模型：[ch_PP-OCRv3_det_infer.tar](https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_det_infer.tar)
    *   识别模型：[ch_PP-OCRv3_rec_infer.tar](https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_rec_infer.tar)
    *   方向分类模型：[ch_PP-OCRv3_cls_infer.tar](https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_cls_infer.tar)（不一定需要，config中默认不启用以加快翻译速度）
2.  解压后，将文件夹重命名并放置在 `assets/ocr_models/` 目录下，确保目录结构如下：
    ```text
    assets/ocr_models/
    ├── det/                # 检测模型目录
    │   ├── inference.pdmodel
    │   └── inference.pdiparams
    ├── cls/                # 方向分类模型目录
    │   ├── inference.pdmodel
    │   └── inference.pdiparams
    └── rec/                # 识别模型目录
        ├── inference.pdmodel
        └── inference.pdiparams
    ```

### 3. 运行程序 (Run)

```bash
python main.py
```


---

##  目录结构 (Directory Structure)

```text
Game-OCR-Translator/
├── assets/                 # 资源文件
│   ├── ocr_models/         # OCR 推理模型 (需手动放置或自动下载)
│   └── dictionary.csv      # 本地离线词典数据库
├── config/                 # 配置文件
│   └── settings.py         # 路径、阈值、API Key 配置
├── core/                   # 核心算法模块
│   ├── ocr_engine.py       # PaddleOCR 封装类 (单例模式)
│   ├── translator.py       # 翻译数据获取类 (QThread)
│   ├── utils.py            # 图像预处理与工具函数
│   └── app.py              # 主线程、监控鼠标状态、执行具体任务
├── ui/                     # 界面显示模块
│   └── overlay.py          # 悬浮窗、准星与系统托盘
├── main.py                 # 程序主入口
├── requirements.txt        # 项目依赖列表
└── README.md               # 项目说明文档

```

---

##  致谢 (Acknowledgments)

*   感谢 **[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)** 提供的优秀开源 OCR 引擎。
*   感谢 **gemini**，虽然它经常胡说八道，但没有它，一个大一新生肯定无法将这一想法变成可运行的程序

---

##  开源协议 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。您可以自由地使用、修改和分发本项目，只需保留原作者署名。
