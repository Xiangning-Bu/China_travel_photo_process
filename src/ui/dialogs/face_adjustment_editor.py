"""
证件照处理系统 - 现代化人脸位置调整编辑器
提供交互式工具调整人脸位置和大小
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSlider, QFrame, QGraphicsView, QGraphicsScene,
                            QGraphicsPixmapItem, QGraphicsEllipseItem, QSizePolicy, QWidget)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QPainter, QCursor
import numpy as np
from PIL import Image

from src.utils.theme import Colors, set_card_style, set_primary_button_style, set_accent_button_style
from src.utils.icons import IconProvider
from src.core.image_processor import ImageProcessor

class ModernFaceAdjustmentEditor(QDialog):
    """现代化人脸位置调整编辑器"""
    
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.setWindowTitle("人脸位置调整")
        self.setMinimumSize(1000, 800)
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")
        self.setWindowModality(Qt.ApplicationModal)
        
        # 存储原始图像和人脸位置信息
        self.original_image = image
        self.face_position = None
        self.face_size = None
        self.inner_ellipse = None
        self.outer_ellipse = None
        self.display_image = None
        self.control_point = None
        self.pixmap_item = None
        
        # 拖拽状态
        self.dragging = False
        self.last_pos = None
        
        # 缩放比例
        self.zoom_factor = 1.0
        
        # 创建UI
        self.create_ui()
        
        # 检测人脸并初始化显示
        self.detect_and_initialize()
    
    def create_ui(self):
        """创建用户界面"""
        # 使用水平布局作为主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # 添加标题
        title_label = QLabel("人脸位置调整")
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_DARK}; font-size: 18px; font-weight: bold;")
        left_layout.addWidget(title_label)
        
        # 添加证件照标准信息面板
        standards_frame = QFrame()
        set_card_style(standards_frame)
        standards_layout = QVBoxLayout(standards_frame)
        
        standards_title = QLabel("证件照标准参考")
        standards_title.setStyleSheet(f"color: {Colors.PRIMARY}; font-size: 14px; font-weight: bold;")
        standards_layout.addWidget(standards_title)
        
        standards_info = QLabel(
            "• 照片尺寸: 33mm × 48mm\n"
            "• 头部高度: 28mm - 33mm (占照片58% - 69%)\n"
            "• 头顶到照片顶部: 3mm - 5mm\n"
            "• 下巴到照片底部: 约7mm\n"
            "• 眼睛到照片底部: 15mm - 22mm"
        )
        standards_info.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 13px;")
        standards_layout.addWidget(standards_info)
        
        left_layout.addWidget(standards_frame)
        
        # 创建控制区域
        controls_frame = QFrame()
        set_card_style(controls_frame)
        controls_layout = QVBoxLayout(controls_frame)
        
        # 大小调整滑块
        size_layout = QHBoxLayout()
        size_label = QLabel("大小调整:")
        size_label.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 14px;")
        size_layout.addWidget(size_label)
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 400)
        self.size_slider.setValue(100)
        self.size_slider.valueChanged.connect(self.size_changed)
        self.size_slider.setStyleSheet(f"""
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
        size_layout.addWidget(self.size_slider)
        
        self.size_value = QLabel("100%")
        self.size_value.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 13px;")
        self.size_value.setMinimumWidth(40)
        size_layout.addWidget(self.size_value)
        
        controls_layout.addLayout(size_layout)
        
        # 添加缩放控制按钮
        zoom_layout = QHBoxLayout()
        
        # 缩放标签
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 12px;")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setMinimumWidth(50)
        zoom_layout.addWidget(self.zoom_label)
        
        # 缩小按钮
        zoom_out_btn = QPushButton()
        zoom_out_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.ZOOM_OUT, Colors.TEXT_DARK))
        zoom_out_btn.setFixedSize(28, 28)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_out_btn.setCursor(QCursor(Qt.PointingHandCursor))
        zoom_out_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        zoom_layout.addWidget(zoom_out_btn)
        
        # 适应窗口按钮
        zoom_fit_btn = QPushButton()
        zoom_fit_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.RESET, Colors.TEXT_DARK))
        zoom_fit_btn.setFixedSize(28, 28)
        zoom_fit_btn.clicked.connect(self.zoom_fit)
        zoom_fit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        zoom_fit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        zoom_layout.addWidget(zoom_fit_btn)
        
        # 原始大小按钮
        zoom_reset_btn = QPushButton()
        zoom_reset_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.EDIT, Colors.TEXT_DARK))
        zoom_reset_btn.setFixedSize(28, 28)
        zoom_reset_btn.clicked.connect(self.zoom_reset)
        zoom_reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        zoom_reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        zoom_layout.addWidget(zoom_reset_btn)
        
        # 放大按钮
        zoom_in_btn = QPushButton()
        zoom_in_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.ZOOM_IN, Colors.TEXT_DARK))
        zoom_in_btn.setFixedSize(28, 28)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_in_btn.setCursor(QCursor(Qt.PointingHandCursor))
        zoom_in_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_layout.addStretch()
        controls_layout.addLayout(zoom_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.RESET, Colors.ACCENT))
        self.reset_btn.clicked.connect(self.reset_adjustment)
        set_accent_button_style(self.reset_btn)
        btn_layout.addWidget(self.reset_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.CANCEL, Colors.TEXT_DARK))
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {Colors.TEXT_DARK};
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        btn_layout.addWidget(self.cancel_btn)
        
        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.CONFIRM, Colors.BACKGROUND))
        self.confirm_btn.clicked.connect(self.accept)
        set_primary_button_style(self.confirm_btn)
        btn_layout.addWidget(self.confirm_btn)
        
        controls_layout.addLayout(btn_layout)
        left_layout.addWidget(controls_frame)
        
        # 添加说明标签
        instructions = QLabel("使用说明: 拖动黄色圆点移动位置，使用滑块调整大小，鼠标滚轮缩放，按住鼠标中键拖动视图。\n"
                            "红色和绿色椭圆表示面部边缘范围，黄色边框区域为最终裁剪区域。")
        instructions.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 12px;")
        instructions.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(instructions)
        
        left_layout.addStretch()
        
        # 右侧图像预览区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 创建图像编辑区域
        image_frame = QFrame()
        set_card_style(image_frame)
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)  # 允许拖动视图
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setStyleSheet(f"background-color: {Colors.BACKGROUND_LIGHT};")
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 启用鼠标滚轮缩放
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.wheelEvent = self.wheel_event
        
        image_layout.addWidget(self.view)
        right_layout.addWidget(image_frame)
        
        # 将左右面板添加到主布局
        layout.addWidget(left_panel, 2)  # 左侧控制面板占2份
        layout.addWidget(right_panel, 3)  # 右侧图像预览占3份
    
    def wheel_event(self, event):
        """处理鼠标滚轮事件进行缩放"""
        # 获取鼠标滚轮增量
        delta = event.angleDelta().y()
        
        # 根据滚轮方向缩放视图
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        """放大视图"""
        self.zoom_factor *= 1.2
        self.view.scale(1.2, 1.2)
        self.update_zoom_label()
    
    def zoom_out(self):
        """缩小视图"""
        self.zoom_factor /= 1.2
        self.view.scale(1/1.2, 1/1.2)
        self.update_zoom_label()
    
    def zoom_fit(self):
        """缩放以适应窗口"""
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        # 计算新的缩放因子
        viewRect = self.view.viewport().rect()
        sceneRect = self.view.mapToScene(viewRect).boundingRect()
        self.zoom_factor = viewRect.width() / sceneRect.width()
        self.update_zoom_label()
    
    def zoom_reset(self):
        """重置缩放到原始大小"""
        self.view.resetTransform()
        self.zoom_factor = 1.0
        self.update_zoom_label()
    
    def update_zoom_label(self):
        """更新缩放比例标签"""
        zoom_percent = int(self.zoom_factor * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
    
    def detect_and_initialize(self):
        """检测人脸并初始化显示"""
        if self.original_image is None:
            return
        
        # 检测人脸
        processor = ImageProcessor()
        result = processor.detect_face(self.original_image)
        
        if result is None:
            # 使用图像中心作为默认人脸位置
            width, height = self.original_image.size
            self.face_position = (width // 2, height // 2)
            self.face_size = (width // 4, height // 3)
        else:
            self.face_position, self.face_size = result
        
        # 记录原始大小
        self.base_face_size = self.face_size
        
        # 初始化图像显示
        self.update_display()
    
    def update_display(self):
        """更新显示图像，保留控制点位置"""
        if self.original_image is None:
            return
        
        # 清除场景，但记住控制点位置
        control_pos = None
        if self.control_point is not None:
            control_pos = QPointF(self.face_position[0], self.face_position[1])
            self.scene.removeItem(self.control_point)
            self.control_point = None
        
        # 创建带椭圆和标记的图像
        processor = ImageProcessor()
        self.display_image = processor.draw_face_ellipses(
            self.original_image,
            self.face_position,
            self.face_size,
            show_distances=True
        )
        
        # 转换为QPixmap
        qimage = self.pil_to_qimage(self.display_image)
        pixmap = QPixmap.fromImage(qimage)
        
        # 清除场景并添加pixmap
        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # 适应视图大小
        if control_pos is None:  # 第一次加载时适应窗口
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        
        # 添加控制点
        self.add_control_point()
    
    def add_control_point(self):
        """添加可交互的控制点"""
        if self.face_position is None:
            return
        
        # 获取人脸中心位置
        x, y = self.face_position
        
        # 创建控制点（黄色圆点）
        control_size = 40
        control_rect = QRectF(-control_size/2, -control_size/2, control_size, control_size)
        
        self.control_point = self.scene.addEllipse(
            control_rect,
            QPen(QColor(Colors.ACCENT), 3),
            QBrush(QColor(Colors.ACCENT), Qt.BrushStyle.SolidPattern)
        )
        
        # 设置控制点位置到人脸中心
        self.control_point.setPos(x, y)
        
        # 设置控制点属性
        self.control_point.setFlag(QGraphicsEllipseItem.ItemIsMovable, False)
        self.control_point.setZValue(100)  # 确保控制点在最上层
        
        # 连接事件处理
        self.view.mousePressEvent = self.view_mouse_press
        self.view.mouseMoveEvent = self.view_mouse_move
        self.view.mouseReleaseEvent = self.view_mouse_release
    
    def view_mouse_press(self, event):
        """处理鼠标按下事件，检测是否点击到控制点"""
        if self.control_point is None:
            QGraphicsView.mousePressEvent(self.view, event)
            return
        
        # 获取鼠标在场景中的位置
        scene_pos = self.view.mapToScene(event.pos())
        
        # 获取控制点中心位置
        control_center = self.control_point.pos()
        
        # 检查点击是否在控制点附近
        distance = ((scene_pos.x() - control_center.x())**2 + 
                   (scene_pos.y() - control_center.y())**2)**0.5
        
        if distance <= 30:  # 允许一定误差范围
            self.dragging = True
            self.last_pos = scene_pos
            # 改变控制点颜色表示选中状态
            self.control_point.setBrush(QBrush(QColor(Colors.PRIMARY)))
            event.accept()
        else:
            self.dragging = False
            QGraphicsView.mousePressEvent(self.view, event)
    
    def view_mouse_move(self, event):
        """处理鼠标移动事件，如果正在拖动控制点则更新位置"""
        if not self.dragging or self.control_point is None:
            QGraphicsView.mouseMoveEvent(self.view, event)
            return
        
        # 获取鼠标在场景中的当前位置
        scene_pos = self.view.mapToScene(event.pos())
        
        # 计算移动距离
        delta_x = scene_pos.x() - self.last_pos.x()
        delta_y = scene_pos.y() - self.last_pos.y()
        
        # 更新人脸位置（在原图坐标系中）
        x, y = self.face_position
        new_x = x + delta_x
        new_y = y + delta_y
        
        # 更新人脸位置
        self.face_position = (new_x, new_y)
        
        # 更新控制点位置
        self.control_point.setPos(new_x, new_y)
        
        # 记住当前鼠标位置用于下次计算
        self.last_pos = scene_pos
        
        # 使用QGraphicsScene的update()而不是直接清除和重新添加项
        self.scene.update()
        
        # 重新绘制带椭圆的图像
        processor = ImageProcessor()
        self.display_image = processor.draw_face_ellipses(
            self.original_image,
            self.face_position,
            self.face_size,
            show_distances=True
        )
        
        # 更新显示图像 - 使用setPixmap而不是重新创建项
        qimage = self.pil_to_qimage(self.display_image)
        pixmap = QPixmap.fromImage(qimage)
        if self.pixmap_item:
            self.pixmap_item.setPixmap(pixmap)
        
        # 确保控制点在最上层
        self.control_point.setZValue(100)
        
        # 强制更新视图
        self.view.viewport().update()
        
        event.accept()
    
    def view_mouse_release(self, event):
        """处理鼠标释放事件"""
        if self.dragging and self.control_point is not None:
            self.dragging = False
            # 恢复控制点颜色
            self.control_point.setBrush(QBrush(QColor(Colors.ACCENT)))
            event.accept()
        else:
            QGraphicsView.mouseReleaseEvent(self.view, event)
    
    def size_changed(self, value):
        """处理大小滑块值变化"""
        if self.face_size is None:
            return
        
        # 计算缩放比例
        scale_factor = value / 100.0
        
        # 获取基准大小
        if not hasattr(self, 'base_face_size'):
            self.base_face_size = self.face_size
        
        base_w, base_h = self.base_face_size
        
        # 计算新大小
        self.face_size = (int(base_w * scale_factor), int(base_h * scale_factor))
        
        # 更新大小值标签
        self.size_value.setText(f"{value}%")
        
        # 更新显示
        self.update_display()
    
    def reset_adjustment(self):
        """重置人脸位置检测"""
        # 重新检测人脸
        self.detect_and_initialize()
        
        # 重置滑块
        self.size_slider.setValue(100)
    
    def pil_to_qimage(self, pil_image):
        """将PIL图像转换为QImage"""
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        # 使用numpy数组进行转换
        numpy_array = np.array(pil_image)
        height, width, channel = numpy_array.shape
        bytes_per_line = 3 * width
        
        qimage = QImage(numpy_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return qimage
    
    def get_result(self):
        """返回调整后的人脸位置和大小"""
        return self.face_position, self.face_size 