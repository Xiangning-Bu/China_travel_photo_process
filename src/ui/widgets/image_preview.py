"""
旅行证照片处理 - 图像预览组件
提供增强型图像预览功能，支持缩放、平移和对比
"""
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                              QPushButton, QSlider, QGraphicsView, QGraphicsScene,
                              QGraphicsPixmapItem, QFrame, QSizePolicy, QStackedWidget)
from PySide6.QtCore import Qt, Signal, QRectF, QPoint, QPointF, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QBrush, QPen, QCursor
import numpy as np
from src.utils.icons import IconProvider
from src.utils.theme import Colors, set_card_style

class ZoomableGraphicsView(QGraphicsView):
    """
    可缩放的图形视图
    支持鼠标缩放和平移功能
    """
    
    zoomChanged = Signal(float)  # 缩放比例变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建场景
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # 图像项
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        # 设置渲染质量
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # 缩放级别
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # 设置视图属性
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        
        # 拖动状态
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # 背景色
        self.setBackgroundBrush(QBrush(QColor(Colors.BACKGROUND_LIGHT)))
    
    def set_image(self, pixmap):
        """设置图像"""
        if pixmap and not pixmap.isNull():
            self.pixmap_item.setPixmap(pixmap)
            self.setSceneRect(QRectF(self.pixmap_item.boundingRect()))
            self.fit_in_view()
    
    def fit_in_view(self):
        """适应视图大小"""
        if not self.pixmap_item.pixmap() or self.pixmap_item.pixmap().isNull():
            return
            
        # 重置变换
        self.resetTransform()
        
        # 计算图像和视图的尺寸
        pixmap_size = self.pixmap_item.boundingRect().size()
        view_size = self.viewport().size()
        
        # 计算适应视图的缩放比例
        scale_w = view_size.width() / pixmap_size.width()
        scale_h = view_size.height() / pixmap_size.height()
        scale = min(scale_w, scale_h)
        
        # 适当放大图像，确保图像不会太小（最低缩放比例为0.9）
        if scale < 0.9:
            # 如果图像过大，则缩小到适应视图
            self.scale(scale, scale)
            self.zoom_factor = scale
        else:
            # 如果图像较小，固定使用1.2倍放大，使图像细节更清晰
            self.scale(1.2, 1.2) 
            self.zoom_factor = 1.2
        
        # 居中显示
        self.centerOn(self.pixmap_item)
        
        # 发出缩放信号
        self.zoomChanged.emit(self.zoom_factor)
    
    def zoom_in(self):
        """放大"""
        self.scale_view(1.25)
    
    def zoom_out(self):
        """缩小"""
        self.scale_view(0.8)
    
    def scale_view(self, factor):
        """缩放视图"""
        # 计算新的缩放比例
        new_zoom = self.zoom_factor * factor
        
        # 限制缩放范围
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return
            
        # 应用缩放
        self.scale(factor, factor)
        self.zoom_factor = new_zoom
        
        # 发出缩放信号
        self.zoomChanged.emit(self.zoom_factor)
    
    def wheelEvent(self, event):
        """鼠标滚轮事件处理"""
        # 计算缩放因子
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8
        
        # 获取当前鼠标位置
        old_pos = self.mapToScene(event.position().toPoint())
        
        # 根据滚轮方向确定缩放方式
        if event.angleDelta().y() > 0:
            # 放大
            self.scale_view(zoom_in_factor)
        else:
            # 缩小
            self.scale_view(zoom_out_factor)
            
        # 更新视图
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
    
    def resizeEvent(self, event):
        """窗口大小调整事件"""
        super().resizeEvent(event)
        if not self.pixmap_item.pixmap() or self.pixmap_item.pixmap().isNull():
            return
            
        # 当大小变化时保持缩放状态
        self.setSceneRect(QRectF(self.pixmap_item.boundingRect()))
        
        # 如果之前的缩放非常小（图像几乎不可见），则重新适应视图
        if self.zoom_factor < 0.5:
            self.fit_in_view()

class ImageComparisonView(QWidget):
    """
    图像对比视图
    支持滑动对比两张图像
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 图像标签
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)
        
        # 滑动控制
        slider_layout = QHBoxLayout()
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {Colors.BORDER};
                height: 8px;
                background: {Colors.BACKGROUND_LIGHT};
                margin: 2px 0;
                border-radius: 4px;
            }}
            
            QSlider::handle:horizontal {{
                background: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY_DARK};
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
        """)
        self.slider.valueChanged.connect(self.update_comparison)
        slider_layout.addWidget(self.slider)
        
        layout.addLayout(slider_layout)
        self.setLayout(layout)
        
        # 图像数据
        self.original_image = None
        self.processed_image = None
        self.comparison_pixmap = None
        
    def set_images(self, original, processed):
        """设置对比的两张图像"""
        self.original_image = original
        self.processed_image = processed
        self.update_comparison(self.slider.value())
    
    def update_comparison(self, value):
        """更新对比图像显示"""
        if self.original_image is None or self.processed_image is None:
            return
            
        # 确保图像尺寸一致
        if self.original_image.size() != self.processed_image.size():
            self.processed_image = self.processed_image.scaled(
                self.original_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 转换为QImage以便像素操作
        orig_img = self.original_image.toImage()
        proc_img = self.processed_image.toImage()
        
        # 创建合成图像
        result = QImage(orig_img.size(), QImage.Format_ARGB32)
        
        # 计算分割线位置
        split_x = int(orig_img.width() * value / 100)
        
        # 绘制合成图像
        painter = QPainter(result)
        
        # 绘制原始图像部分
        painter.drawImage(QRectF(0, 0, split_x, orig_img.height()),
                         orig_img, QRectF(0, 0, split_x, orig_img.height()))
        
        # 绘制处理后图像部分
        painter.drawImage(QRectF(split_x, 0, orig_img.width() - split_x, orig_img.height()),
                         proc_img, QRectF(split_x, 0, orig_img.width() - split_x, orig_img.height()))
        
        # 绘制分割线
        pen = QPen(QColor(Colors.PRIMARY))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(split_x, 0, split_x, orig_img.height())
        
        # 结束绘制
        painter.end()
        
        # 显示结果
        self.comparison_pixmap = QPixmap.fromImage(result)
        self.image_label.setPixmap(self.comparison_pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def resizeEvent(self, event):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        if self.comparison_pixmap and not self.comparison_pixmap.isNull():
            self.image_label.setPixmap(self.comparison_pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

class ModernImagePreview(QWidget):
    """
    现代化图像预览组件
    整合缩放预览和对比功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        set_card_style(self)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 工具栏 - 移至顶部
        tools_layout = QHBoxLayout()
        
        # 缩放比例显示
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 12px;")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setMinimumWidth(50)
        tools_layout.addWidget(self.zoom_label)
        
        # 缩小按钮
        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.ZOOM_OUT, Colors.TEXT_DARK))
        self.zoom_out_btn.setFixedSize(28, 28)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.zoom_out_btn.setToolTip("缩小图像")
        self.zoom_out_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        tools_layout.addWidget(self.zoom_out_btn)
        
        # 重置按钮
        self.reset_zoom_btn = QPushButton()
        self.reset_zoom_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.RESET, Colors.TEXT_DARK))
        self.reset_zoom_btn.setFixedSize(28, 28)
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.reset_zoom_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_zoom_btn.setToolTip("重置图像大小")
        self.reset_zoom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        tools_layout.addWidget(self.reset_zoom_btn)
        
        # 放大按钮
        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.ZOOM_IN, Colors.TEXT_DARK))
        self.zoom_in_btn.setFixedSize(28, 28)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.zoom_in_btn.setToolTip("放大图像")
        self.zoom_in_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        tools_layout.addWidget(self.zoom_in_btn)
        
        # 对比模式切换
        self.compare_btn = QPushButton("对比模式")
        self.compare_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.compare_btn.setToolTip("切换到对比模式，查看处理前后的差异")
        self.compare_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {Colors.TEXT_DARK};
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        self.compare_btn.clicked.connect(self.toggle_compare_mode)
        tools_layout.addWidget(self.compare_btn)
        
        tools_layout.addStretch()
        
        # 添加状态指示文本
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Colors.PRIMARY}; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignRight)
        tools_layout.addWidget(self.status_label)
        
        layout.addLayout(tools_layout)
        
        # 创建图像视图 - 占据大部分空间
        self.stack = QStackedWidget()
        
        # 图像预览
        self.graphics_view = ZoomableGraphicsView(self)
        self.stack.addWidget(self.graphics_view)
        
        # 创建对比视图
        self.comparison_view = ImageComparisonView(self)
        self.stack.addWidget(self.comparison_view)
        
        layout.addWidget(self.stack, 1)  # 使图像视图占据所有剩余空间
        
        # 连接信号
        self.graphics_view.zoomChanged.connect(self.update_zoom_label)
        
        # 存储图像
        self.original_pixmap = None
        self.processed_pixmap = None
        self.current_pixmap = None
        
        # 初始状态
        self.compare_mode = False
    
    def set_image(self, pixmap):
        """设置预览图像"""
        self.original_pixmap = pixmap
        self.current_pixmap = pixmap
        self.graphics_view.set_image(pixmap)
        self.status_label.setText("原始图像")
    
    def set_processed_image(self, pixmap):
        """设置处理后的图像"""
        self.processed_pixmap = pixmap
        
        # 如果在对比模式，更新对比视图
        if self.compare_mode and self.original_pixmap is not None:
            self.comparison_view.set_images(self.original_pixmap, pixmap)
        else:
            # 否则更新主预览
            self.current_pixmap = pixmap
            self.graphics_view.set_image(pixmap)
            self.status_label.setText("处理后图像")
            
            # 自动调整以显示整个处理后的图像
            QTimer.singleShot(100, self.graphics_view.fit_in_view)
    
    def toggle_compare_mode(self):
        """切换对比模式"""
        self.compare_mode = not self.compare_mode
        
        # 更新界面
        if self.compare_mode:
            self.compare_btn.setText("正常模式")
            self.stack.setCurrentWidget(self.comparison_view)
            self.zoom_out_btn.setEnabled(False)
            self.zoom_in_btn.setEnabled(False)
            self.reset_zoom_btn.setEnabled(False)
            self.status_label.setText("对比模式")
            
            # 显示对比视图
            if self.original_pixmap is not None and self.processed_pixmap is not None:
                self.comparison_view.set_images(self.original_pixmap, self.processed_pixmap)
        else:
            self.compare_btn.setText("对比模式")
            self.stack.setCurrentWidget(self.graphics_view)
            self.zoom_out_btn.setEnabled(True)
            self.zoom_in_btn.setEnabled(True)
            self.reset_zoom_btn.setEnabled(True)
            self.status_label.setText("处理后图像" if self.processed_pixmap else "原始图像")
    
    def update_zoom_label(self, zoom_factor):
        """更新缩放比例标签"""
        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
    
    def zoom_in(self):
        """放大"""
        self.graphics_view.zoom_in()
    
    def zoom_out(self):
        """缩小"""
        self.graphics_view.zoom_out()
    
    def reset_zoom(self):
        """重置缩放"""
        self.graphics_view.fit_in_view()
    
    def reset(self):
        """重置预览状态"""
        self.original_pixmap = None
        self.processed_pixmap = None
        self.current_pixmap = None
        self.status_label.setText("")
        
        # 重置视图
        self.graphics_view.scene.clear()
        self.graphics_view.pixmap_item = QGraphicsPixmapItem()
        self.graphics_view.scene.addItem(self.graphics_view.pixmap_item)
        
        # 重置对比视图
        self.comparison_view.original_image = None
        self.comparison_view.processed_image = None
        self.comparison_view.image_label.clear()
        
        # 重置模式
        if self.compare_mode:
            self.toggle_compare_mode()
            
        # 重置缩放
        self.update_zoom_label(1.0) 