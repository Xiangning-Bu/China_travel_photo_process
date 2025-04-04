import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, QTabWidget,
                            QProgressBar, QSplitter, QMessageBox, QDialog, QFrame, 
                            QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                            QGraphicsEllipseItem, QComboBox, QInputDialog, QLineEdit)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QPainter
import cv2
import numpy as np
from PIL import Image
import io
import os
from src.core.image_processor import ImageProcessor, bg_signals

class FaceAdjustmentEditor(QDialog):
    """交互式人脸位置和大小调整编辑器"""
    
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.setWindowTitle("人脸位置调整")
        self.setGeometry(100, 100, 1000, 800)  # 增大默认窗口尺寸
        
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
        layout = QVBoxLayout(self)
        
        # 添加证件照标准信息面板
        standards_frame = QFrame()
        standards_frame.setFrameShape(QFrame.StyledPanel)
        standards_frame.setStyleSheet("background-color: #f0f0f0;")
        standards_layout = QVBoxLayout(standards_frame)
        
        standards_title = QLabel("<b>证件照标准参考:</b>")
        standards_layout.addWidget(standards_title)
        
        standards_info = QLabel(
            "• 照片尺寸: 33mm × 48mm\n"
            "• 头部高度: 28mm - 33mm (占照片58% - 69%)\n"
            "• 头顶到照片顶部: 3mm - 5mm\n"
            "• 下巴到照片底部: 约7mm\n"
            "• 眼睛到照片底部: 15mm - 22mm"
        )
        standards_layout.addWidget(standards_info)
        
        layout.addWidget(standards_frame)
        
        # 创建图像编辑区域
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)  # 允许拖动视图
        layout.addWidget(self.view)
        
        # 添加缩放控制按钮
        zoom_layout = QHBoxLayout()
        
        zoom_in_btn = QPushButton("放大 (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("缩小 (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        zoom_fit_btn = QPushButton("适应窗口")
        zoom_fit_btn.clicked.connect(self.zoom_fit)
        zoom_layout.addWidget(zoom_fit_btn)
        
        zoom_reset_btn = QPushButton("原始大小 (1:1)")
        zoom_reset_btn.clicked.connect(self.zoom_reset)
        zoom_layout.addWidget(zoom_reset_btn)
        
        layout.addLayout(zoom_layout)
        
        # 创建控制区域
        controls_layout = QHBoxLayout()
        
        # 大小调整滑块
        size_layout = QVBoxLayout()
        size_label = QLabel("大小调整:")
        size_layout.addWidget(size_label)
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 400)
        self.size_slider.setValue(100)
        self.size_slider.valueChanged.connect(self.size_changed)
        size_layout.addWidget(self.size_slider)
        
        controls_layout.addLayout(size_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_adjustment)
        btn_layout.addWidget(self.reset_btn)
        
        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        controls_layout.addLayout(btn_layout)
        layout.addLayout(controls_layout)
        
        # 添加说明标签
        instructions = QLabel("使用说明: 拖动黄色圆点移动位置，使用滑块调整大小，鼠标滚轮缩放，按住鼠标中键拖动视图。\n"
                            "红色和绿色椭圆表示面部边缘范围，黄色边框区域为最终裁剪区域(边框外区域会被裁剪掉)。\n"
                            "红色数字显示面部椭圆到裁剪框的实际距离(mm)，调整时确保符合标准要求。")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # 启用鼠标滚轮缩放
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.wheelEvent = self.wheel_event
    
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
    
    def zoom_out(self):
        """缩小视图"""
        self.zoom_factor /= 1.2
        self.view.scale(1/1.2, 1/1.2)
    
    def zoom_fit(self):
        """缩放以适应窗口"""
        self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        # 计算新的缩放因子
        viewRect = self.view.viewport().rect()
        sceneRect = self.view.mapToScene(viewRect).boundingRect()
        self.zoom_factor = viewRect.width() / sceneRect.width()
    
    def zoom_reset(self):
        """重置缩放到原始大小"""
        self.view.resetTransform()
        self.zoom_factor = 1.0
    
    def detect_and_initialize(self):
        if self.original_image is None:
            return
        
        # 检测人脸
        processor = ImageProcessor()
        result = processor.detect_face(self.original_image)
        
        if result is None:
            QMessageBox.warning(self, "警告", "无法检测到人脸，请手动调整位置。")
            # 使用图像中心作为默认人脸位置
            width, height = self.original_image.size
            self.face_position = (width // 2, height // 2)
            self.face_size = (width // 4, height // 3)
        else:
            self.face_position, self.face_size = result
        
        # 初始化图像显示
        self.update_display()
    
    def update_display(self):
        """更新显示图像，保留控制点位置"""
        if self.original_image is None:
            print("[DEBUG] update_display: No original image")
            return
        
        print(f"[DEBUG] update_display: Starting update with image size: {self.original_image.size}")
        
        # 清除场景，但记住控制点位置
        control_pos = None
        if self.control_point is not None:
            control_pos = QPointF(self.face_position[0], self.face_position[1])
            print(f"[DEBUG] Saved control point position: {control_pos.x()}, {control_pos.y()}")
            self.scene.removeItem(self.control_point)
            self.control_point = None
        
        # 创建带椭圆和标记的图像
        processor = ImageProcessor()
        print(f"[DEBUG] Face position: {self.face_position}, Face size: {self.face_size}")
        self.display_image = processor.draw_face_ellipses(
            self.original_image,
            self.face_position,
            self.face_size,
            show_distances=True
        )
        
        print(f"[DEBUG] Generated display image size: {self.display_image.size}")
        
        # 转换为QPixmap
        qimage = self.pil_to_qimage(self.display_image)
        print(f"[DEBUG] Converted to QImage size: {qimage.width()}x{qimage.height()}")
        pixmap = QPixmap.fromImage(qimage)
        
        # 清除场景并添加pixmap
        print("[DEBUG] Clearing scene and adding new pixmap")
        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # 适应视图大小
        if control_pos is None:  # 第一次加载时适应窗口
            print("[DEBUG] First load - fitting to view")
            self.view.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        
        # 添加控制点
        self.add_control_point()
        print("[DEBUG] Display update completed")
    
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
            QPen(QColor(255, 255, 0), 3),
            QBrush(QColor(255, 255, 0, 200))
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
            self.control_point.setBrush(QBrush(QColor(255, 165, 0, 200)))  # 橙色
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
        print(f"[DEBUG] Mouse scene position: {scene_pos.x()}, {scene_pos.y()}")
        
        # 计算移动距离
        delta_x = scene_pos.x() - self.last_pos.x()
        delta_y = scene_pos.y() - self.last_pos.y()
        print(f"[DEBUG] Movement delta: {delta_x}, {delta_y}")
        
        # 更新人脸位置（在原图坐标系中）
        x, y = self.face_position
        new_x = x + delta_x
        new_y = y + delta_y
        print(f"[DEBUG] New face position: {new_x}, {new_y}")
        
        # 更新人脸位置
        self.face_position = (new_x, new_y)
        
        # 更新控制点位置
        self.control_point.setPos(new_x, new_y)
        print(f"[DEBUG] Control point updated position: {new_x}, {new_y}")
        
        # 记住当前鼠标位置用于下次计算
        self.last_pos = scene_pos
        
        # 使用QGraphicsScene的update()而不是直接清除和重新添加项
        print("[DEBUG] Starting scene update")
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
            print("[DEBUG] Updating existing pixmap")
            self.pixmap_item.setPixmap(pixmap)
        else:
            print("[DEBUG] Creating new pixmap item")
            self.pixmap_item = self.scene.addPixmap(pixmap)
        
        # 确保控制点在最上层
        self.control_point.setZValue(100)
        print("[DEBUG] Control point Z-value set to 100")
        
        # 强制更新视图
        self.view.viewport().update()
        print("[DEBUG] View update completed")
        
        event.accept()
    
    def view_mouse_release(self, event):
        """处理鼠标释放事件"""
        if self.dragging and self.control_point is not None:
            self.dragging = False
            # 恢复控制点颜色
            self.control_point.setBrush(QBrush(QColor(255, 255, 0, 200)))  # 黄色
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
        print(f"[DEBUG] Converting PIL image: mode={pil_image.mode}, size={pil_image.size}")
        if pil_image.mode != "RGB":
            print("[DEBUG] Converting image to RGB mode")
            pil_image = pil_image.convert("RGB")
        
        # 使用numpy数组进行转换，可能更快更可靠
        numpy_array = np.array(pil_image)
        height, width, channel = numpy_array.shape
        bytes_per_line = 3 * width
        
        print(f"[DEBUG] Creating QImage: {width}x{height}, bytes per line: {bytes_per_line}")
        qimage = QImage(numpy_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return qimage
    
    def get_result(self):
        """返回调整后的人脸位置和大小"""
        return self.face_position, self.face_size

class PhotoProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("证件照处理系统")
        self.setGeometry(100, 100, 950, 700)
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 创建选项卡
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # 添加三个功能选项卡
        tabs.addTab(self.create_background_tab(), "背景去除")
        tabs.addTab(self.create_crop_tab(), "证件照裁剪")
        tabs.addTab(self.create_print_tab(), "证件照排版")
        
        # 添加退出按钮
        exit_btn = QPushButton("退出程序")
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        
        # 初始化变量
        self.original_image = None
        self.processed_image = None
        self.cropped_image = None
        self.print_image = None
        
        # 创建定时器用于进度条动画
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        self.active_progress_bar = None

    def create_background_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加上传按钮
        upload_btn = QPushButton("上传照片")
        upload_btn.clicked.connect(self.upload_photo)
        layout.addWidget(upload_btn)
        
        # 创建分割器显示原始图像和处理后的图像
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 原始图像显示区域
        original_container = QWidget()
        original_layout = QVBoxLayout(original_container)
        original_label = QLabel("原始图像")
        original_layout.addWidget(original_label)
        self.original_image_label = QLabel()
        self.original_image_label.setAlignment(Qt.AlignCenter)
        self.original_image_label.setMinimumSize(400, 300)
        original_layout.addWidget(self.original_image_label)
        splitter.addWidget(original_container)
        
        # 处理后图像显示区域
        processed_container = QWidget()
        processed_layout = QVBoxLayout(processed_container)
        processed_label = QLabel("处理后图像")
        processed_layout.addWidget(processed_label)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        processed_layout.addWidget(self.image_label)
        splitter.addWidget(processed_container)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
        # 添加进度条
        self.bg_progress_bar = QProgressBar()
        self.bg_progress_bar.setRange(0, 100)
        self.bg_progress_bar.setValue(0)
        self.bg_progress_bar.setVisible(False)
        layout.addWidget(self.bg_progress_bar)
        
        # 添加背景移除方法选择
        method_layout = QHBoxLayout()
        method_label = QLabel("选择背景移除方法:")
        method_layout.addWidget(method_label)
        
        self.bg_method_combo = QComboBox()
        self.bg_method_combo.addItem("Rembg (效果最佳，推荐)", "rembg")
        self.bg_method_combo.addItem("GrabCut算法 (快速但效果一般)", "grabcut")
        self.bg_method_combo.addItem("在线API (需要API密钥)", "api")
        method_layout.addWidget(self.bg_method_combo)
        
        # 添加API密钥设置按钮
        api_key_btn = QPushButton("设置API密钥")
        api_key_btn.clicked.connect(self.set_api_key)
        method_layout.addWidget(api_key_btn)
        
        layout.addLayout(method_layout)
        
        # 添加处理按钮
        process_btn = QPushButton("去除背景")
        process_btn.clicked.connect(self.remove_background)
        layout.addWidget(process_btn)
        
        # 添加保存按钮
        save_btn = QPushButton("保存图片")
        save_btn.clicked.connect(self.save_photo)
        layout.addWidget(save_btn)
        
        return tab

    def create_crop_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加上传按钮
        upload_btn = QPushButton("上传照片")
        upload_btn.clicked.connect(self.upload_photo_for_crop)
        layout.addWidget(upload_btn)
        
        # 创建分割器显示原始图像和处理后的图像
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 原始图像显示区域
        original_container = QWidget()
        original_layout = QVBoxLayout(original_container)
        original_label = QLabel("原始图像")
        original_layout.addWidget(original_label)
        self.original_crop_image_label = QLabel()
        self.original_crop_image_label.setAlignment(Qt.AlignCenter)
        self.original_crop_image_label.setMinimumSize(400, 300)
        original_layout.addWidget(self.original_crop_image_label)
        splitter.addWidget(original_container)
        
        # 处理后图像显示区域
        processed_container = QWidget()
        processed_layout = QVBoxLayout(processed_container)
        processed_label = QLabel("裁剪后图像")
        processed_layout.addWidget(processed_label)
        self.crop_image_label = QLabel()
        self.crop_image_label.setAlignment(Qt.AlignCenter)
        self.crop_image_label.setMinimumSize(400, 300)
        processed_layout.addWidget(self.crop_image_label)
        splitter.addWidget(processed_container)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
        # 添加进度条
        self.crop_progress_bar = QProgressBar()
        self.crop_progress_bar.setRange(0, 100)
        self.crop_progress_bar.setValue(0)
        self.crop_progress_bar.setVisible(False)
        layout.addWidget(self.crop_progress_bar)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        
        # 添加自动裁剪按钮
        auto_crop_btn = QPushButton("自动裁剪")
        auto_crop_btn.clicked.connect(self.auto_crop)
        button_layout.addWidget(auto_crop_btn)
        
        # 添加手动调整按钮
        manual_adjust_btn = QPushButton("手动调整")
        manual_adjust_btn.clicked.connect(self.manual_adjust)
        button_layout.addWidget(manual_adjust_btn)
        
        layout.addLayout(button_layout)
        
        # 添加保存按钮
        save_btn = QPushButton("保存证件照")
        save_btn.clicked.connect(self.save_cropped_photo)
        layout.addWidget(save_btn)
        
        return tab

    def create_print_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加上传按钮
        upload_btn = QPushButton("上传证件照")
        upload_btn.clicked.connect(self.upload_photo_for_print)
        layout.addWidget(upload_btn)
        
        # 创建分割器显示原始图像和处理后的图像
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 原始图像显示区域
        original_container = QWidget()
        original_layout = QVBoxLayout(original_container)
        original_label = QLabel("原始证件照")
        original_layout.addWidget(original_label)
        self.original_print_image_label = QLabel()
        self.original_print_image_label.setAlignment(Qt.AlignCenter)
        self.original_print_image_label.setMinimumSize(400, 300)
        original_layout.addWidget(self.original_print_image_label)
        splitter.addWidget(original_container)
        
        # 处理后图像显示区域
        processed_container = QWidget()
        processed_layout = QVBoxLayout(processed_container)
        processed_label = QLabel("排版预览")
        processed_layout.addWidget(processed_label)
        self.print_image_label = QLabel()
        self.print_image_label.setAlignment(Qt.AlignCenter)
        self.print_image_label.setMinimumSize(400, 300)
        processed_layout.addWidget(self.print_image_label)
        splitter.addWidget(processed_container)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
        # 添加进度条
        self.print_progress_bar = QProgressBar()
        self.print_progress_bar.setRange(0, 100)
        self.print_progress_bar.setValue(0)
        self.print_progress_bar.setVisible(False)
        layout.addWidget(self.print_progress_bar)
        
        # 添加排版按钮
        layout_btn = QPushButton("生成排版")
        layout_btn.clicked.connect(self.create_print_layout)
        layout.addWidget(layout_btn)
        
        # 添加保存按钮
        save_btn = QPushButton("保存打印文件")
        save_btn.clicked.connect(self.save_print_layout)
        layout.addWidget(save_btn)
        
        return tab

    def start_progress(self, progress_bar):
        self.active_progress_bar = progress_bar
        self.active_progress_bar.setValue(0)
        self.active_progress_bar.setVisible(True)
        self.progress_value = 0
        self.timer.start(30)  # 每30毫秒更新一次进度条

    def update_progress(self):
        if self.active_progress_bar:
            self.progress_value += 1
            if self.progress_value > 100:
                self.timer.stop()
                self.active_progress_bar = None
                return
            self.active_progress_bar.setValue(self.progress_value)

    def complete_progress(self):
        if self.active_progress_bar:
            self.active_progress_bar.setValue(100)
            self.timer.stop()
            
            # 保存对当前进度条的引用
            current_bar = self.active_progress_bar
            
            # 重置活动进度条
            self.active_progress_bar = None
            
            # 使用保存的引用安全地设置延迟隐藏
            QTimer.singleShot(1000, lambda bar=current_bar: bar.setVisible(False))

    def upload_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择照片", "", "图像文件 (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                self.original_image = Image.open(file_name)
                # 显示原始图像
                self.display_image(self.original_image, self.original_image_label)
                # 清空处理后图像
                self.image_label.clear()
                self.processed_image = None
                self.image_label.setText("等待处理...")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开图片: {str(e)}")

    def display_image(self, image, label, max_size=400):
        if image is None:
            return
            
        try:
            # 复制图像以避免修改原始图像
            display_image = image.copy()
            
            # 调整图像大小以适应标签
            width, height = display_image.size
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            display_image = display_image.resize(new_size)
            
            # 转换为QImage
            # 确保图像是RGB模式
            if display_image.mode != "RGB":
                display_image = display_image.convert("RGB")
            
            # 获取图像数据并创建QImage
            data = display_image.tobytes("raw", "RGB")
            qimage = QImage(data, display_image.width, display_image.height, display_image.width * 3, QImage.Format_RGB888)
            
            # 显示图像
            label.setPixmap(QPixmap.fromImage(qimage))
        except Exception as e:
            print(f"显示图像时出错: {str(e)}")
            label.setText(f"显示错误: {str(e)}")

    def remove_background(self):
        if self.original_image is None:
            print("错误：没有上传图片")
            return
            
        # 启动进度条
        self.start_progress(self.bg_progress_bar)
        
        # 使用计时器延迟执行，以便进度条有时间显示
        QTimer.singleShot(100, self._process_background_removal)

    def _process_background_removal(self):
        try:
            # 获取选中的背景去除方法
            method = self.bg_method_combo.currentData()
            
            # 定义进度回调函数
            def update_progress(value):
                self.bg_progress_bar.setValue(value)
                # 强制处理UI事件，保持界面响应
                QApplication.processEvents()
            
            processor = ImageProcessor()
            
            # 使用选择的方法去除背景
            if method == "api":
                # 检查API密钥是否已设置
                api_key = processor.get_api_key()
                if not api_key:
                    QMessageBox.warning(self, "API密钥缺失", "请先设置Remove.bg API密钥。")
                    self.set_api_key()
                    api_key = processor.get_api_key()
                    if not api_key:
                        # 用户取消输入API密钥，回退到rembg方法
                        QMessageBox.information(self, "使用备选方法", "将使用Rembg方法去除背景。")
                        self.processed_image = processor.remove_background(
                            self.original_image, 
                            progress_callback=update_progress,
                            method="rembg"
                        )
                    else:
                        self.processed_image = processor.remove_background_api(
                            self.original_image,
                            api_key,
                            progress_callback=update_progress
                        )
                else:
                    self.processed_image = processor.remove_background_api(
                        self.original_image,
                        api_key,
                        progress_callback=update_progress
                    )
            else:
                # 使用选择的方法（rembg或grabcut）
                self.processed_image = processor.remove_background(
                    self.original_image, 
                    progress_callback=update_progress, 
                    method=method
                )
            
            # 显示处理后的图像
            if self.processed_image is not None:
                print("背景去除完成")
                self.display_image(self.processed_image, self.image_label)
            else:
                print("背景去除失败")
        except Exception as e:
            print(f"处理过程中发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"背景去除过程中发生错误: {str(e)}")
        finally:
            # 完成进度条
            self.complete_progress()

    def save_photo(self):
        if self.processed_image is None:
            return
            
        file_name, file_type = QFileDialog.getSaveFileName(self, "保存图片", "", 
                                                        "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;BMP (*.bmp);;WebP (*.webp)")
        if file_name:
            # 从选择的过滤器提取格式
            if "JPEG" in file_type:
                format = "JPEG"
            elif "TIFF" in file_type:
                format = "TIFF"
            elif "BMP" in file_type:
                format = "BMP"
            elif "WebP" in file_type:
                format = "WebP"
            else:
                format = "PNG"
            
            self.processed_image.save(file_name, format)

    def upload_photo_for_crop(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择照片", "", "图像文件 (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                self.original_image = Image.open(file_name)
                # 显示原始图像
                self.display_image(self.original_image, self.original_crop_image_label)
                # 清空处理后图像
                self.crop_image_label.clear()
                self.cropped_image = None
                self.crop_image_label.setText("等待裁剪...")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开图片: {str(e)}")

    def auto_crop(self):
        if self.original_image is None:
            return
            
        # 启动进度条
        self.start_progress(self.crop_progress_bar)
        
        # 使用计时器延迟执行，以便进度条有时间显示
        QTimer.singleShot(100, self._process_auto_crop)

    def _process_auto_crop(self):
        try:
            # 使用ImageProcessor类自动裁剪照片
            processor = ImageProcessor()
            self.cropped_image = processor.auto_crop_id_photo(self.original_image)
            
            if self.cropped_image is not None:
                print("证件照裁剪完成")
                # 显示裁剪后的图像
                self.display_image(self.cropped_image, self.crop_image_label)
            else:
                print("裁剪失败")
                self.crop_image_label.setText("裁剪失败 - 无法检测到人脸")
                QMessageBox.warning(self, "裁剪失败", "无法在图像中检测到人脸。请尝试使用正面清晰的照片。")
        except Exception as e:
            print(f"裁剪过程中发生错误: {str(e)}")
            self.crop_image_label.setText(f"裁剪错误: {str(e)}")
            QMessageBox.critical(self, "裁剪错误", f"裁剪过程中发生错误: {str(e)}")
        finally:
            # 完成进度条
            self.complete_progress()

    def save_cropped_photo(self):
        if self.cropped_image is None:
            return
            
        file_name, file_type = QFileDialog.getSaveFileName(self, "保存证件照", "", 
                                                        "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;BMP (*.bmp);;WebP (*.webp)")
        if file_name:
            # 从选择的过滤器提取格式
            if "JPEG" in file_type:
                format = "JPEG"
            elif "TIFF" in file_type:
                format = "TIFF"
            elif "BMP" in file_type:
                format = "BMP"
            elif "WebP" in file_type:
                format = "WebP"
            else:
                format = "PNG"
            
            self.cropped_image.save(file_name, format)

    def upload_photo_for_print(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择证件照", "", "图像文件 (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                self.cropped_image = Image.open(file_name)
                # 显示原始证件照
                self.display_image(self.cropped_image, self.original_print_image_label)
                # 清空处理后图像
                self.print_image_label.clear()
                self.print_image = None
                self.print_image_label.setText("等待排版...")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开图片: {str(e)}")

    def create_print_layout(self):
        if self.cropped_image is None:
            return
            
        # 启动进度条
        self.start_progress(self.print_progress_bar)
        
        # 使用计时器延迟执行，以便进度条有时间显示
        QTimer.singleShot(100, self._process_print_layout)

    def _process_print_layout(self):
        try:
            # 使用ImageProcessor类创建排版
            processor = ImageProcessor()
            self.print_image = processor.create_print_layout(self.cropped_image)
            
            if self.print_image is not None:
                print("排版完成")
                # 显示排版后的图像
                self.display_image(self.print_image, self.print_image_label)
            else:
                print("排版失败")
                self.print_image_label.setText("排版失败")
        except Exception as e:
            print(f"排版过程中发生错误: {str(e)}")
            self.print_image_label.setText(f"排版错误: {str(e)}")
            QMessageBox.critical(self, "排版错误", f"排版过程中发生错误: {str(e)}")
        finally:
            # 完成进度条
            self.complete_progress()

    def save_print_layout(self):
        if self.print_image is None:
            return
            
        file_name, file_type = QFileDialog.getSaveFileName(self, "保存打印文件", "", 
                                                        "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;BMP (*.bmp);;PDF (*.pdf)")
        if file_name:
            # 从选择的过滤器提取格式
            if "JPEG" in file_type:
                format = "JPEG"
            elif "TIFF" in file_type:
                format = "TIFF"
            elif "BMP" in file_type:
                format = "BMP"
            elif "PDF" in file_type:
                # PDF需要特殊处理
                self.print_image.convert('RGB').save(file_name, "PDF", resolution=300.0)
                return
            else:
                format = "PNG"
            
            self.print_image.save(file_name, format)

    def manual_adjust(self):
        """打开手动调整对话框，让用户调整人脸位置和大小"""
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "请先上传照片")
            return
        
        # 创建人脸调整编辑器
        editor = FaceAdjustmentEditor(self, self.original_image)
        
        # 如果用户接受调整结果
        if editor.exec_() == QDialog.Accepted:
            # 获取调整后的人脸位置和大小
            face_position, face_size = editor.get_result()
            
            # 启动进度条
            self.start_progress(self.crop_progress_bar)
            
            # 使用计时器延迟执行，以便进度条有时间显示
            self.manual_face_position = face_position
            self.manual_face_size = face_size
            QTimer.singleShot(100, self._process_manual_crop)
    
    def _process_manual_crop(self):
        """处理手动裁剪操作"""
        try:
            # 使用ImageProcessor类根据手动调整的位置裁剪照片
            processor = ImageProcessor()
            self.cropped_image = processor.manual_crop_id_photo(
                self.original_image,
                self.manual_face_position,
                self.manual_face_size
            )
            
            if self.cropped_image is not None:
                print("证件照手动裁剪完成")
                # 显示裁剪后的图像
                self.display_image(self.cropped_image, self.crop_image_label)
            else:
                print("手动裁剪失败")
                self.crop_image_label.setText("裁剪失败")
                QMessageBox.warning(self, "裁剪失败", "手动裁剪照片失败，请重试。")
        except Exception as e:
            print(f"手动裁剪过程中发生错误: {str(e)}")
            self.crop_image_label.setText(f"裁剪错误: {str(e)}")
            QMessageBox.critical(self, "裁剪错误", f"裁剪过程中发生错误: {str(e)}")
        finally:
            # 完成进度条
            self.complete_progress()

    def set_api_key(self):
        """设置Remove.bg API密钥"""
        current_key = self.get_api_key()
        
        text, ok = QInputDialog.getText(
            self, 
            "设置API密钥", 
            "请输入Remove.bg API密钥\n(可从https://www.remove.bg/获取):", 
            QLineEdit.Normal, 
            current_key if current_key else ""
        )
        
        if ok and text:
            # 存储API密钥到配置文件
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config_file = os.path.join(config_dir, 'api_config.txt')
            with open(config_file, 'w') as f:
                f.write(text)
            
            QMessageBox.information(self, "成功", "API密钥已设置成功！")

    def get_api_key(self):
        """获取存储的API密钥"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        config_file = os.path.join(config_dir, 'api_config.txt')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return f.read().strip()
            except:
                return None
        return None 