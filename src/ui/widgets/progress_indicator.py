"""
旅行证照片处理 - 进度指示器
提供现代化的进度显示组件
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, QSize, Property, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen
from src.utils.theme import Colors

class CircleProgressBar(QWidget):
    """圆形进度条"""
    
    def __init__(self, parent=None, size=100):
        super().__init__(parent)
        self.setFixedSize(QSize(size, size))
        
        # 进度值
        self._progress = 0
        # 颜色
        self._color = QColor(Colors.PRIMARY)
        # 背景色
        self._background_color = QColor(Colors.BORDER)
        # 线宽
        self._line_width = 8
        
    def get_progress(self):
        return self._progress
        
    def set_progress(self, value):
        """设置进度值 (0-100)"""
        self._progress = max(0, min(100, value))
        self.update()  # 触发重绘
        
    # 定义属性，用于属性动画
    progress = Property(int, get_progress, set_progress)
        
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算绘制区域
        rect = self.rect()
        rect = rect.adjusted(self._line_width // 2, self._line_width // 2, 
                             -self._line_width // 2, -self._line_width // 2)
        
        # 绘制背景圆
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self._background_color, self._line_width, Qt.SolidLine))
        painter.drawEllipse(rect)
        
        # 绘制进度圆弧
        if self._progress > 0:
            painter.setPen(QPen(self._color, self._line_width, Qt.SolidLine))
            # 从90度开始，顺时针方向
            span_angle = int(-self._progress * 3.6)  # 3.6 = 360/100
            painter.drawArc(rect, 90 * 16, span_angle * 16)
            
        painter.end()

class ModernProgressIndicator(QWidget):
    """现代风格进度指示器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # 圆形进度条
        self.circle_progress = CircleProgressBar(self)
        layout.addWidget(self.circle_progress, 0, Qt.AlignCenter)
        
        # 文本标签
        self.label = QLabel("处理中...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 14px;")
        layout.addWidget(self.label)
        
        # 百分比标签
        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignCenter)
        self.percent_label.setStyleSheet(f"color: {Colors.PRIMARY}; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.percent_label)
        
        self.setLayout(layout)
        
        # 不使用时初始隐藏
        self.setVisible(False)
        
        # 创建动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # 进度动画
        self.progress_animation = QPropertyAnimation(self.circle_progress, b"progress")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def start(self, text="处理中..."):
        """开始显示进度指示器"""
        self.label.setText(text)
        self.percent_label.setText("0%")
        self.circle_progress.set_progress(0)
        
        # 淡入显示
        self.setWindowOpacity(0)
        self.setVisible(True)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
    def update_progress(self, value, text=None):
        """更新进度值"""
        # 动画方式更新进度条
        self.progress_animation.setStartValue(self.circle_progress.get_progress())
        self.progress_animation.setEndValue(value)
        self.progress_animation.start()
        
        # 更新百分比文本
        self.percent_label.setText(f"{value}%")
        
        # 更新说明文本
        if text:
            self.label.setText(text)
            
    def complete(self, text="处理完成", auto_hide=True, delay=1000):
        """完成处理"""
        # 更新到100%
        self.progress_animation.setStartValue(self.circle_progress.get_progress())
        self.progress_animation.setEndValue(100)
        self.progress_animation.start()
        
        # 更新百分比和文本
        self.percent_label.setText("100%")
        self.label.setText(text)
        
        # 自动隐藏
        if auto_hide:
            QTimer.singleShot(delay, self.hide_animation)
    
    def error(self, text="处理出错", auto_hide=True, delay=2000):
        """显示错误"""
        # 将进度条颜色改为红色
        self.circle_progress._color = QColor(Colors.ERROR)
        self.circle_progress.update()
        
        # 更新文本
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {Colors.ERROR}; font-size: 14px;")
        
        # 自动隐藏
        if auto_hide:
            QTimer.singleShot(delay, self.hide_animation)
    
    def hide_animation(self):
        """动画方式隐藏"""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self._on_hide_finished)
        self.fade_animation.start()
    
    def _on_hide_finished(self):
        """隐藏动画完成后的处理"""
        # 断开信号连接
        self.fade_animation.finished.disconnect(self._on_hide_finished)
        # 隐藏组件
        self.setVisible(False)
        # 重置进度条颜色
        self.circle_progress._color = QColor(Colors.PRIMARY)
        self.label.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 14px;") 