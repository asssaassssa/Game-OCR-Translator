import sys
from PyQt6.QtWidgets import QWidget, QLabel, QApplication, QGraphicsDropShadowEffect, QVBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QPoint, QTimer, pyqtProperty, QSize
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen
import pyautogui

class Crosshair(QWidget):
    """
    屏幕中心的绿色瞄准镜 (PyQt6 Ver.)
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.resize(40, 40)
        self.offset_y = 40

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#00FF00"), 2)
        painter.setPen(pen)
        painter.drawEllipse(5, 5, 30, 30)
        
        painter.setBrush(QBrush(QColor("#00FF00")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(18, 18, 4, 4)

    def update_pos(self, x, y):
        self.move(int(x - 20), int(y - 20 - self.offset_y))
        if not self.isVisible():
            self.show()

class ResultPopup(QWidget):
    """
    PyQt6 高级动效悬浮窗 (完美自适应版)
    """
    def __init__(self):
        super().__init__()
        
        self._bg_alpha = 0
        self.is_expanded = False
        
        # 1. 窗口属性
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # 2. 核心容器 & 布局
        self.container = QFrame(self)
        self.layout_box = QVBoxLayout(self.container)
        
        # 💡【关键修复】在这里定义 Padding 变量
        self.padding_h = 20  # 水平边距
        self.padding_v = 15  # 垂直边距
        self.layout_box.setContentsMargins(self.padding_h, self.padding_v, self.padding_h, self.padding_v)
        
        # 3. 文本标签
        self.label = QLabel("")
        self.label.setFont(QFont("Microsoft YaHei UI", 11, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: rgba(0, 255, 0, 0); border: none; background: transparent;") 
        
        self.layout_box.addWidget(self.label)
        
        # 4. 阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow) 

        # 5. 动画
        self.anim_geometry = QPropertyAnimation(self, b"geometry")
        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.bg_anim = QPropertyAnimation(self, b"bg_alpha")

    def get_bg_alpha(self):
        return self._bg_alpha

    def set_bg_alpha(self, alpha):
        self._bg_alpha = alpha
        self.update()

    bg_alpha = pyqtProperty(int, get_bg_alpha, set_bg_alpha)

    def resizeEvent(self, event):
        self.container.resize(self.size())
        super().resizeEvent(event)

    def paintEvent(self, event):
        if self.width() < 10 or self.height() < 10:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        brush = QBrush(QColor(26, 26, 26, self._bg_alpha))
        painter.setBrush(brush)
        
        pen = QPen(QColor(50, 50, 50, self._bg_alpha), 1)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 15, 15)

    def show_text(self, text, x, y, is_error=False):
        """
        自适应计算尺寸的显示方法
        """
        self.anim_geometry.stop()
        self.bg_anim.stop()
        
        try:
            self.anim_geometry.finished.disconnect()
        except TypeError:
            pass 
        
        # 1. 设置文本和颜色
        self.label.setText(text)
        color_hex = "#FF5555" if is_error else "#55FF55"
        
        # 2. 计算尺寸
        MAX_WIDTH = 400 
        
        # 临时解除限制，测量单行宽度
        self.label.setFixedSize(QSize(16777215, 16777215)) 
        self.label.setWordWrap(False) 
        self.label.adjustSize()
        
        natural_width = self.label.width()
        
        if natural_width > MAX_WIDTH:
            # 太长了，折行
            self.label.setWordWrap(True)
            self.label.setFixedWidth(MAX_WIDTH)
            self.label.adjustSize() 
            
            final_content_w = MAX_WIDTH
            final_content_h = self.label.height()
        else:
            # 短文本，单行
            self.label.setWordWrap(False)
            self.label.setFixedWidth(natural_width + 10) 
            
            final_content_w = natural_width + 10
            final_content_h = self.label.height()
            
        # 3. 加上 Padding
        target_w = final_content_w + (self.padding_h * 2) + 10
        target_h = final_content_h + (self.padding_v * 2) + 10
        
        target_w = max(target_w, 80)
        target_h = max(target_h, 50)
        
        # 4. 位置计算
        screen_geo = QApplication.primaryScreen().geometry()
        target_x = x + 30
        target_y = y + 30
        
        if target_x + target_w > screen_geo.width():
            target_x = x - target_w - 30
        if target_y + target_h > screen_geo.height():
            target_y = y - target_h - 30
            
        target_x = max(0, target_x)
        target_y = max(0, target_y)

        final_rect = QRect(int(target_x), int(target_y), int(target_w), int(target_h))
        start_rect = QRect(x, y, 0, 0)
        
        # 5. 动画
        self.anim_geometry.setDuration(250)
        self.anim_geometry.setStartValue(start_rect)
        self.anim_geometry.setEndValue(final_rect)
        self.anim_geometry.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.bg_anim.setDuration(200)
        self.bg_anim.setStartValue(0)
        self.bg_anim.setEndValue(240)
        self.bg_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        QTimer.singleShot(100, lambda: self.label.setStyleSheet(f"color: {color_hex}; background: transparent;"))
        
        self.show()
        self.anim_geometry.start()
        self.bg_anim.start()
        self.is_expanded = True
        
    def hide_anim(self):
        if not self.isVisible() or not self.is_expanded:
            return
            
        self.anim_geometry.stop()
        self.bg_anim.stop()
        
        try:
            self.anim_geometry.finished.disconnect()
        except TypeError:
            pass
        
        mx, my = pyautogui.position()
        current_rect = self.geometry()
        target_rect = QRect(mx, my, 0, 0)
        
        self.anim_geometry.setDuration(150)
        self.anim_geometry.setStartValue(current_rect)
        self.anim_geometry.setEndValue(target_rect)
        self.anim_geometry.setEasingCurve(QEasingCurve.Type.InQuad)
        
        self.bg_anim.setDuration(100)
        self.bg_anim.setStartValue(self._bg_alpha)
        self.bg_anim.setEndValue(0)
        
        self.anim_geometry.finished.connect(self.hide)
        
        self.label.setStyleSheet("color: transparent; background: transparent;")
        
        self.anim_geometry.start()
        self.bg_anim.start()
        self.is_expanded = False