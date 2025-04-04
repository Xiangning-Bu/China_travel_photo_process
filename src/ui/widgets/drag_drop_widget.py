"""
旅行证照片处理 - 拖放上传组件
提供支持拖放功能的图片上传区域
"""
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QIcon
from PIL import Image
import os
from src.utils.icons import IconProvider
from src.utils.theme import Colors

class DragDropWidget(QFrame):
    """可拖放文件的上传组件"""
    
    # 定义信号
    image_dropped = Signal(str)  # 发送文件路径
    clicked = Signal()           # 点击信号
    
    def __init__(self, parent=None, width=250, height=250, text="拖放图片到此处<br>或<b>点击上传</b>"):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(QSize(width, height))
        self.text = text
        self.has_image = False

        # 设置样式
        self.base_style = f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 2px dashed {Colors.BORDER};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.HOVER};
            }}
        """
        self.drag_style = f"""
            QFrame {{
                background-color: {Colors.HOVER};
                border: 2px dashed {Colors.PRIMARY_DARK};
                border-radius: 8px;
            }}
        """
        self.setStyleSheet(self.base_style)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        # 创建图标标签 (Initially hidden)
        self.icon_label = QLabel()
        upload_icon = IconProvider.get_icon(IconProvider.SvgIcons.UPLOAD, Colors.TEXT_LIGHT)
        self.icon_label.setPixmap(upload_icon.pixmap(QSize(48, 48)))
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # 创建提示/图片标签
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_LIGHT};")
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.reset()
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖动进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.drag_style)
        
    def dragLeaveEvent(self, event):
        """拖动离开事件"""
        self.setStyleSheet(self.base_style)
        
    def dropEvent(self, event: QDropEvent):
        """放置事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 检查是否为支持的图片格式
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']:
                self.image_dropped.emit(file_path)
                self.load_preview(file_path)
            else:
                pass
                
        # 恢复样式
        self.setStyleSheet(self.base_style)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.clicked.emit()
        
    def reset(self):
        """重置为初始状态"""
        self.label.setPixmap(QPixmap())
        self.label.setText(self.text)
        self.icon_label.setVisible(True)
        self.has_image = False
        
    def resizeEvent(self, event):
        """处理大小调整事件"""
        super().resizeEvent(event)
        # 如果有图片，在大小变化时重新调整
        if self.has_image and hasattr(self, '_current_image_path'):
            self.load_preview(self._current_image_path)
            
    def load_preview(self, image_path):
        """加载图片预览"""
        try:
            # 保存当前图片路径用于调整大小
            self._current_image_path = image_path
            pixmap = QPixmap(image_path)
            
            # 缩放图片以适应大小
            scaled_pixmap = pixmap.scaled(
                self.width() - 20, self.height() - 40,  # 增加垂直方向的空间
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # 清除之前的标签内容并显示图片
            self.label.clear()
            self.label.setPixmap(scaled_pixmap)
            self.icon_label.setVisible(False)
            self.has_image = True

        except Exception as e:
            print(f"加载预览失败: {str(e)}")
            self.reset()
            self.label.setText("<font color='red'>图片加载失败</font>") 