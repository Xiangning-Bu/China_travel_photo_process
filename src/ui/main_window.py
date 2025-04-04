"""
旅行证照片处理 - 现代化主界面
整合了所有功能模块，提供美观直观的用户界面
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QTabWidget,
                            QMessageBox, QSplitter, QStackedWidget, QDialog, QFormLayout, QSpinBox, QDialogButtonBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QIcon, QCursor
from PIL import Image
import os
import sys

from src.utils.theme import Colors, set_card_style, set_primary_button_style, set_accent_button_style, set_secondary_button_style
from src.utils.icons import IconProvider
from src.ui.widgets.drag_drop_widget import DragDropWidget
from src.ui.widgets.image_preview import ModernImagePreview
from src.ui.widgets.progress_indicator import ModernProgressIndicator 
from src.ui.widgets.algorithm_cards import AlgorithmSelector, AlgorithmCard

from src.core.image_processor import ImageProcessor

class ModernPhotoProcessor(QMainWindow):
    """现代化的旅行证照片处理主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("旅行证照片处理")
        self.setMinimumSize(1200, 800)  # 增加最小高度
        
        # 初始化数据
        self.original_image = None
        self.processed_image = None
        self.cropped_image = None
        self.print_image = None
        
        # 创建UI
        self.init_ui()
        
        # 连接信号
        self.connect_signals()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)  # 减小外边距
        main_layout.setSpacing(10)
        
        # 创建标题
        title_layout = QHBoxLayout()
        title_label = QLabel("旅行证照片处理")
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_DARK}; font-size: 24px; font-weight: bold; font-family: 'Microsoft YaHei', sans-serif;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # 创建选项卡部件
        self.tabs = QTabWidget()
        # 确保不显示关闭按钮
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(False)
        self.tabs.setDocumentMode(False)
        
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{
                padding: 12px 18px;
                margin-right: 5px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                background: {Colors.BACKGROUND_LIGHT};
                font-weight: normal;
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 14px;
            }}
            
            QTabBar::tab:selected {{
                background: {Colors.PRIMARY};
                color: white;
                font-weight: bold;
            }}
            
            QTabBar::tab:hover:!selected {{
                background: {Colors.HOVER};
            }}
        """)
        
        # 添加选项卡
        self.tabs.addTab(self.create_background_tab(), "1. 背景去除")
        self.tabs.addTab(self.create_crop_tab(), "2. 照片裁剪")
        self.tabs.addTab(self.create_print_tab(), "3. 照片排版")
        
        main_layout.addWidget(self.tabs)
        
        # 创建底部操作栏
        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        
        # 版本信息
        version_label = QLabel("v2.0")
        version_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 12px;")
        bottom_layout.addWidget(version_label)
        
        # 添加工作流程说明
        workflow_label = QLabel("工作流程: 1.去除背景 → 2.照片裁剪 → 3.照片排版")
        workflow_label.setStyleSheet(f"""
            color: {Colors.PRIMARY}; 
            font-size: 14px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei', sans-serif;
            background-color: {Colors.PRIMARY_LIGHT};
            padding: 8px 15px;
            border-radius: 15px;
        """)
        workflow_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(workflow_label)
        
        bottom_layout.addStretch()
        
        # 退出按钮
        exit_btn = QPushButton("退出程序")
        set_secondary_button_style(exit_btn, color=Colors.TEXT_LIGHT, border_color=Colors.BORDER)
        exit_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.CANCEL, Colors.TEXT_LIGHT))
        exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(exit_btn)
        
        main_layout.addWidget(bottom_bar)
    
    def create_background_tab(self):
        """创建背景去除选项卡"""
        tab = QWidget()
        layout = QHBoxLayout(tab)  # 改为水平布局
        layout.setContentsMargins(15, 15, 15, 15)  # Increased overall padding
        layout.setSpacing(20)  # Increased spacing between left and right panels
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)  # Increased spacing between step label and control area
        
        # 步骤提示
        step_label = QLabel("第1步: 去除背景 - 上传照片并选择去除背景的算法")
        step_label.setStyleSheet(f"""
            color: {Colors.TEXT_DARK}; 
            font-size: 16px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei', sans-serif;
            background-color: {Colors.BACKGROUND_LIGHT};
            border-left: 4px solid {Colors.PRIMARY};
            padding: 12px;
            border-radius: 4px;
        """)
        step_label.setAlignment(Qt.AlignCenter)
        step_label.setWordWrap(True)  # 允许文字换行
        left_layout.addWidget(step_label)
        
        # 顶部区域 - 上传和算法选择
        control_area = QWidget()
        set_card_style(control_area)
        control_layout = QVBoxLayout(control_area)
        control_layout.setContentsMargins(20, 20, 20, 20) # Increased internal padding for the card
        control_layout.setSpacing(15) # Spacing within the card
        
        # 上传区域
        upload_label = QLabel("上传照片:")
        upload_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
        control_layout.addWidget(upload_label)
        
        # 拖放上传区域
        self.bg_upload_widget = DragDropWidget()
        self.bg_upload_widget.setMinimumWidth(200)
        self.bg_upload_widget.setMinimumHeight(200)
        self.base_style = f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 2px dashed {Colors.BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.HOVER};
            }}
        """
        self.drag_style = f"""
            QFrame {{
                background-color: {Colors.PRIMARY_LIGHT};
                border: 2px dashed {Colors.PRIMARY};
                border-radius: 8px;
                padding: 10px;
            }}
        """
        self.bg_upload_widget.setStyleSheet(self.base_style)
        control_layout.addWidget(self.bg_upload_widget, 1)  # 添加拉伸因子
        
        # 算法选择区域
        self.bg_algo_selector = AlgorithmSelector()
        
        # 添加算法选项
        self.bg_algo_selector.add_algorithm(
            "rembg",
            "AI抠图",
            "使用深度学习模型\n处理效果最佳，推荐使用",
            IconProvider.SvgIcons.ALGO_REMBG
        )
        
        self.bg_algo_selector.add_algorithm(
            "api",
            "在线API",
            "使用Remove.bg在线服务\n需要API密钥，效果极佳",
            IconProvider.SvgIcons.ALGO_API
        )
        
        control_layout.addWidget(self.bg_algo_selector)
        
        # 底部区域 - 操作按钮
        button_area = QWidget()
        button_layout = QHBoxLayout(button_area)
        button_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin for buttons
        button_layout.setSpacing(10) # Spacing between buttons
        
        # 处理按钮
        self.bg_process_btn = QPushButton("去除背景")
        self.bg_process_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.PROCESS, Colors.BACKGROUND))
        set_primary_button_style(self.bg_process_btn)
        button_layout.addWidget(self.bg_process_btn)
        
        # 保存按钮
        self.bg_save_btn = QPushButton("保存图片")
        self.bg_save_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.SAVE, Colors.ACCENT))
        set_accent_button_style(self.bg_save_btn)
        self.bg_save_btn.setEnabled(False)
        button_layout.addWidget(self.bg_save_btn)
        
        control_layout.addWidget(button_area)
        
        # 进度指示器
        self.bg_progress = ModernProgressIndicator()
        self.bg_progress.setVisible(False)
        control_layout.addWidget(self.bg_progress)
        
        left_layout.addWidget(control_area)
        left_layout.addStretch()  # 添加弹性空间
        
        # 右侧图像预览区域
        self.bg_image_preview = ModernImagePreview()
        self.bg_image_preview.setStyleSheet(f"""
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 5px;
        """)
        
        # 将左右两个面板添加到主布局
        layout.addWidget(left_panel, 1)  # 左侧面板占1份空间
        layout.addWidget(self.bg_image_preview, 2)  # 图像预览占2份空间
        
        return tab
    
    def create_crop_tab(self):
        """创建照片裁剪选项卡"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)  # Increased overall padding
        layout.setSpacing(20)  # Increased spacing between left and right panels
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20) # Increased spacing between step label and control area
        
        # 步骤提示
        step_label = QLabel("第2步: 照片裁剪 - 上传照片并选择自动裁剪或手动调整")
        step_label.setStyleSheet(f"""
            color: {Colors.TEXT_DARK}; 
            font-size: 16px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei', sans-serif;
            background-color: {Colors.BACKGROUND_LIGHT};
            border-left: 4px solid {Colors.PRIMARY};
            padding: 12px;
            border-radius: 4px;
        """)
        step_label.setAlignment(Qt.AlignCenter)
        step_label.setWordWrap(True)  # 允许文字换行
        left_layout.addWidget(step_label)
        
        # 控制区域
        control_area = QWidget()
        set_card_style(control_area)
        control_layout = QVBoxLayout(control_area)
        control_layout.setContentsMargins(20, 20, 20, 20) # Increased internal padding for the card
        control_layout.setSpacing(15) # Spacing within the card
        
        # 上传区域
        upload_label = QLabel("上传照片 (或使用上一步结果):")
        upload_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
        control_layout.addWidget(upload_label)
        
        self.crop_upload_widget = DragDropWidget()
        self.crop_upload_widget.setMinimumWidth(200)
        self.crop_upload_widget.setMinimumHeight(200)
        self.base_style = f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 2px dashed {Colors.BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.HOVER};
            }}
        """
        self.drag_style = f"""
            QFrame {{
                background-color: {Colors.PRIMARY_LIGHT};
                border: 2px dashed {Colors.PRIMARY};
                border-radius: 8px;
                padding: 10px;
            }}
        """
        self.crop_upload_widget.setStyleSheet(self.base_style)
        control_layout.addWidget(self.crop_upload_widget, 1)  # 添加拉伸因子
        
        # 裁剪方式选择
        crop_mode_label = QLabel("选择裁剪方式:")
        crop_mode_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
        control_layout.addWidget(crop_mode_label)
        
        self.crop_mode_selector = AlgorithmSelector() # Single selection
        
        self.crop_mode_selector.add_algorithm(
            "auto",
            "自动裁剪",
            "使用AI人脸检测\n自动计算裁剪位置",
            IconProvider.SvgIcons.ALGO_REMBG
        )
        
        self.crop_mode_selector.add_algorithm(
            "manual",
            "手动调整",
            "手动调整人脸位置\n更精确的控制",
            IconProvider.SvgIcons.EDIT
        )
        
        control_layout.addWidget(self.crop_mode_selector)
        
        # 底部区域 - 操作按钮
        button_area = QWidget()
        button_layout = QHBoxLayout(button_area)
        button_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin for buttons
        button_layout.setSpacing(10) # Spacing between buttons
        
        # 处理按钮
        self.crop_process_btn = QPushButton("开始裁剪")
        self.crop_process_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.CROP, Colors.BACKGROUND))
        set_primary_button_style(self.crop_process_btn)
        button_layout.addWidget(self.crop_process_btn)
        
        # 保存按钮
        self.crop_save_btn = QPushButton("保存证件照")
        self.crop_save_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.SAVE, Colors.ACCENT))
        set_accent_button_style(self.crop_save_btn)
        self.crop_save_btn.setEnabled(False)
        button_layout.addWidget(self.crop_save_btn)
        
        control_layout.addWidget(button_area)
        
        # 进度指示器
        self.crop_progress = ModernProgressIndicator()
        self.crop_progress.setVisible(False)
        control_layout.addWidget(self.crop_progress)
        
        left_layout.addWidget(control_area)
        left_layout.addStretch()
        
        # 右侧图像预览区域
        self.crop_image_preview = ModernImagePreview()
        self.crop_image_preview.setStyleSheet(f"""
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 5px;
        """)
        
        # 添加到主布局
        layout.addWidget(left_panel, 1)
        layout.addWidget(self.crop_image_preview, 2)
        
        return tab
    
    def create_print_tab(self):
        """创建照片排版选项卡"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15) # Increased overall padding
        layout.setSpacing(20) # Increased spacing between left and right panels

        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20) # Increased spacing between step label and control area

        # 步骤提示
        step_label = QLabel("第3步: 照片排版 - 上传照片并选择排版样式")
        step_label.setStyleSheet(f"""
            color: {Colors.TEXT_DARK}; 
            font-size: 16px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei', sans-serif;
            background-color: {Colors.BACKGROUND_LIGHT};
            border-left: 4px solid {Colors.PRIMARY};
            padding: 12px;
            border-radius: 4px;
        """)
        step_label.setAlignment(Qt.AlignCenter)
        step_label.setWordWrap(True)  # 允许文字换行
        left_layout.addWidget(step_label)

        # 控制区域
        control_area = QWidget()
        set_card_style(control_area)
        control_layout = QVBoxLayout(control_area)
        control_layout.setContentsMargins(20, 20, 20, 20) # Increased internal padding for the card
        control_layout.setSpacing(15) # Spacing within the card

        # 上传区域
        upload_label = QLabel("上传照片 (或使用上一步结果):")
        upload_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
        control_layout.addWidget(upload_label)

        self.print_upload_widget = DragDropWidget()
        self.print_upload_widget.setMinimumWidth(200)
        self.print_upload_widget.setMinimumHeight(200)
        self.base_style = f"""
            QFrame {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border: 2px dashed {Colors.BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.HOVER};
            }}
        """
        self.drag_style = f"""
            QFrame {{
                background-color: {Colors.PRIMARY_LIGHT};
                border: 2px dashed {Colors.PRIMARY};
                border-radius: 8px;
                padding: 10px;
            }}
        """
        self.print_upload_widget.setStyleSheet(self.base_style)
        control_layout.addWidget(self.print_upload_widget, 1)  # 添加拉伸因子

        # 排版参数选择
        print_params_label = QLabel("选择排版样式:")
        print_params_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
        control_layout.addWidget(print_params_label)

        self.print_params_selector = AlgorithmSelector()

        self.print_params_selector.add_algorithm(
            "standard",
            "标准排版",
            "一寸照9张 (4x6英寸纸张)",
            IconProvider.SvgIcons.PRINT_STANDARD
        )

        self.print_params_selector.add_algorithm(
            "mix",
            "混合排版",
            "一寸4张 + 二寸2张",
            IconProvider.SvgIcons.PRINT_STANDARD
        )

        self.print_params_selector.add_algorithm(
            "custom",
            "自定义排版",
            "自行设置行列和间距",
            IconProvider.SvgIcons.EDIT
        )

        control_layout.addWidget(self.print_params_selector)

        # 底部区域 - 操作按钮
        button_area = QWidget()
        button_layout = QHBoxLayout(button_area)
        button_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin for buttons
        button_layout.setSpacing(10) # Spacing between buttons

        # 处理按钮
        self.print_process_btn = QPushButton("生成排版")
        self.print_process_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.PROCESS, Colors.BACKGROUND))
        set_primary_button_style(self.print_process_btn)
        button_layout.addWidget(self.print_process_btn)

        # 保存按钮
        self.print_save_btn = QPushButton("保存排版图")
        self.print_save_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.SAVE, Colors.ACCENT))
        set_accent_button_style(self.print_save_btn)
        self.print_save_btn.setEnabled(False)
        button_layout.addWidget(self.print_save_btn)

        control_layout.addWidget(button_area)

        # 进度指示器
        self.print_progress = ModernProgressIndicator()
        self.print_progress.setVisible(False)
        control_layout.addWidget(self.print_progress)

        left_layout.addWidget(control_area)
        left_layout.addStretch()

        # 右侧图像预览区域
        self.print_image_preview = ModernImagePreview()
        self.print_image_preview.setStyleSheet(f"""
            background-color: {Colors.BACKGROUND_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 5px;
        """)

        # 添加到主布局
        layout.addWidget(left_panel, 1)
        layout.addWidget(self.print_image_preview, 2)

        return tab
    
    def connect_signals(self):
        """连接所有信号"""
        # 背景去除页面
        self.bg_upload_widget.image_dropped.connect(self.load_image_for_bg)
        self.bg_upload_widget.clicked.connect(self.upload_image_for_bg)
        self.bg_process_btn.clicked.connect(self.process_background_removal)
        self.bg_save_btn.clicked.connect(self.save_bg_image)
        
        # 照片裁剪页面
        self.crop_upload_widget.image_dropped.connect(self.load_image_for_crop)
        self.crop_upload_widget.clicked.connect(self.upload_image_for_crop)
        self.crop_process_btn.clicked.connect(self.process_crop)
        self.crop_save_btn.clicked.connect(self.save_crop_image)
        
        # 照片排版页面
        self.print_upload_widget.image_dropped.connect(self.load_image_for_print)
        self.print_upload_widget.clicked.connect(self.upload_image_for_print)
        self.print_process_btn.clicked.connect(self.process_print_layout)
        self.print_save_btn.clicked.connect(self.save_print_image)
        
        # 设置默认选择项 - 解决初次打开时无法选择算法的问题
        self.bg_algo_selector.set_selected("rembg")
        self.crop_mode_selector.set_selected("auto")
        self.print_params_selector.set_selected("standard")
    
    # ===== 背景去除功能 =====
    def load_image_for_bg(self, file_path):
        """从文件路径加载图像用于背景去除"""
        try:
            self.original_image = Image.open(file_path)
            self.bg_upload_widget.load_preview(file_path)
            self.bg_image_preview.set_image(QPixmap(file_path))
            self.processed_image = None
            self.bg_save_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开图片: {str(e)}")
    
    def upload_image_for_bg(self):
        """通过文件对话框上传图像用于背景去除"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择照片", "", "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.load_image_for_bg(file_path)
    
    def process_background_removal(self):
        """处理背景去除"""
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "请先上传图片")
            return
        
        # 获取选中的算法
        method = self.bg_algo_selector.get_selected()
        
        # 显示进度指示器
        self.bg_progress.start("正在去除背景...")
        
        # 定义进度回调
        def update_progress(value, text=None):
            update_text = text if text else f"处理中...{value}%"
            self.bg_progress.update_progress(value, update_text)
        
        # 使用QTimer延迟执行，以便UI能够更新
        self.bg_method = method
        QTimer.singleShot(100, lambda: self.execute_bg_removal(update_progress))
    
    def execute_bg_removal(self, progress_callback):
        """执行背景去除处理"""
        try:
            processor = ImageProcessor()
            
            if self.bg_method == "api":
                # 当用户选择"在线API"去除背景时
                # 首先显示提示信息
                QMessageBox.information(
                    self, 
                    "在线API说明", 
                    "您选择了Remove.bg在线API服务进行背景去除。\n\n"
                    "此功能需要API密钥才能使用。如果您没有API密钥，系统将自动使用AI抠图功能作为替代。\n\n"
                    "要获取API密钥，请访问: https://www.remove.bg/，注册账号并获取免费或付费的API密钥。"
                )
                
                # 检查API密钥是否设置
                api_key = processor.get_api_key()
                if not api_key:
                    # 显示API密钥设置对话框
                    from src.ui.dialogs.api_key_dialog import ApiKeyDialog
                    dialog = ApiKeyDialog(self)
                    if dialog.exec_():
                        api_key = dialog.get_api_key()
                        # 如果用户设置了API密钥，使用API方法
                        if api_key:
                            self.processed_image = processor.remove_background_api(
                                self.original_image,
                                api_key,
                                progress_callback=progress_callback
                            )
                        else:
                            # 回退到rembg方法
                            progress_callback(10, "API密钥未设置，使用AI抠图...")
                            self.processed_image = processor.remove_background(
                                self.original_image,
                                progress_callback=progress_callback,
                                method="rembg"
                            )
                    else:
                        # 用户取消了API密钥设置
                        progress_callback(10, "API密钥未设置，使用AI抠图...")
                        self.processed_image = processor.remove_background(
                            self.original_image,
                            progress_callback=progress_callback,
                            method="rembg"
                        )
                else:
                    # 使用已设置的API密钥
                    self.processed_image = processor.remove_background_api(
                        self.original_image,
                        api_key,
                        progress_callback=progress_callback
                    )
            else:
                # 使用选择的方法(rembg或grabcut)
                self.processed_image = processor.remove_background(
                    self.original_image,
                    progress_callback=progress_callback,
                    method=self.bg_method
                )
            
            # 显示处理结果
            if self.processed_image:
                # 将PIL图像转换为QPixmap
                self.processed_image.save("temp/processed.png", "PNG")
                processed_pixmap = QPixmap("temp/processed.png")
                
                # 更新预览
                self.bg_image_preview.set_processed_image(processed_pixmap)
                self.bg_save_btn.setEnabled(True)
                
                # 完成进度
                self.bg_progress.complete("背景去除完成")
            else:
                raise Exception("处理失败，未返回有效图像")
                
        except Exception as e:
            self.bg_progress.error(f"处理出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"背景去除过程中发生错误: {str(e)}")
    
    def save_bg_image(self):
        """保存处理后的图像"""
        if self.processed_image is None:
            return
            
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "保存图片", "", 
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;BMP (*.bmp);;WebP (*.webp)"
        )
        
        if file_path:
            # 从选择的过滤器提取格式
            format_mapping = {
                "PNG (*.png)": "PNG",
                "JPEG (*.jpg *.jpeg)": "JPEG",
                "TIFF (*.tif *.tiff)": "TIFF",
                "BMP (*.bmp)": "BMP",
                "WebP (*.webp)": "WebP"
            }
            
            # 默认为PNG
            format = format_mapping.get(file_type, "PNG")
            
            try:
                self.processed_image.save(file_path, format)
                QMessageBox.information(self, "成功", "图片已成功保存！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存图片时出错: {str(e)}")
    
    # ===== 照片裁剪功能 =====
    def load_image_for_crop(self, file_path):
        """从文件路径加载图像用于照片裁剪"""
        try:
            self.original_image = Image.open(file_path)
            self.crop_upload_widget.load_preview(file_path)
            self.crop_image_preview.set_image(QPixmap(file_path))
            self.cropped_image = None
            self.crop_save_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开图片: {str(e)}")
    
    def upload_image_for_crop(self):
        """通过文件对话框上传图像用于照片裁剪"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择照片", "", "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.load_image_for_crop(file_path)
    
    def process_crop(self):
        """处理照片裁剪"""
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "请先上传图片")
            return
        
        # 获取选中的裁剪方法
        crop_method = self.crop_mode_selector.get_selected()
        
        # 显示进度指示器
        self.crop_progress.start("正在处理证件照...")
        
        # 定义进度回调
        def update_progress(value, text=None):
            update_text = text if text else f"处理中...{value}%"
            self.crop_progress.update_progress(value, update_text)
        
        # 使用QTimer延迟执行，以便UI能够更新
        self.crop_method = crop_method
        QTimer.singleShot(100, lambda: self.execute_crop(update_progress))
    
    def execute_crop(self, progress_callback):
        """执行照片裁剪处理"""
        try:
            processor = ImageProcessor()
            
            if self.crop_method == "auto":
                # 自动裁剪
                progress_callback(10, "检测人脸中...")
                self.cropped_image = processor.auto_crop_id_photo(
                    self.original_image, 
                    progress_callback=progress_callback
                )
                
                if self.cropped_image is None:
                    raise Exception("未检测到人脸，请尝试使用清晰的正面照片或手动调整")
            
            elif self.crop_method == "manual":
                # 手动调整
                progress_callback(10, "启动人脸位置编辑器...")
                
                # 导入这里以避免循环引用
                from src.ui.dialogs.face_adjustment_editor import ModernFaceAdjustmentEditor
                
                # 暂时隐藏进度条，显示编辑器
                self.crop_progress.hide_animation()
                
                # 创建并显示编辑器
                editor = ModernFaceAdjustmentEditor(self, self.original_image)
                
                # 如果用户接受调整
                if editor.exec_():
                    # 显示进度条
                    self.crop_progress.start("应用调整...")
                    
                    # 获取调整后的人脸位置和大小
                    face_position, face_size = editor.get_result()
                    
                    # 手动裁剪
                    progress_callback(30, "裁剪证件照...")
                    self.cropped_image = processor.manual_crop_id_photo(
                        self.original_image,
                        face_position,
                        face_size,
                        progress_callback=progress_callback
                    )
                else:
                    # 用户取消了编辑
                    return
            
            # 显示处理结果
            if self.cropped_image:
                # 将PIL图像转换为QPixmap
                self.cropped_image.save("temp/cropped.png", "PNG")
                cropped_pixmap = QPixmap("temp/cropped.png")
                
                # 更新预览
                self.crop_image_preview.set_processed_image(cropped_pixmap)
                self.crop_save_btn.setEnabled(True)
                
                # 完成进度
                self.crop_progress.complete("证件照裁剪完成")
            else:
                raise Exception("处理失败，未返回有效图像")
                
        except Exception as e:
            self.crop_progress.error(f"处理出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"证件照裁剪过程中发生错误: {str(e)}")
    
    def save_crop_image(self):
        """保存裁剪后的证件照"""
        if self.cropped_image is None:
            return
            
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "保存证件照", "", 
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;BMP (*.bmp);;WebP (*.webp)"
        )
        
        if file_path:
            # 从选择的过滤器提取格式
            format_mapping = {
                "PNG (*.png)": "PNG",
                "JPEG (*.jpg *.jpeg)": "JPEG",
                "TIFF (*.tif *.tiff)": "TIFF",
                "BMP (*.bmp)": "BMP",
                "WebP (*.webp)": "WebP"
            }
            
            # 默认为PNG
            format = format_mapping.get(file_type, "PNG")
            
            try:
                self.cropped_image.save(file_path, format)
                QMessageBox.information(self, "成功", "证件照已成功保存！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存证件照时出错: {str(e)}")
    
    # ===== 照片排版功能 =====
    def load_image_for_print(self, file_path):
        """从文件路径加载图像用于照片排版"""
        try:
            self.cropped_image = Image.open(file_path)
            self.print_upload_widget.load_preview(file_path)
            self.print_image_preview.set_image(QPixmap(file_path))
            self.print_image = None
            self.print_save_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开图片: {str(e)}")
    
    def upload_image_for_print(self):
        """通过文件对话框上传图像用于照片排版"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择证件照", "", "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.load_image_for_print(file_path)
    
    def process_print_layout(self):
        """处理照片排版"""
        if self.cropped_image is None:
            QMessageBox.warning(self, "警告", "请先上传证件照")
            return
        
        # 获取选中的排版方法
        print_method = self.print_params_selector.get_selected()
        
        # 显示进度指示器
        self.print_progress.start("正在生成排版...")
        
        # 定义进度回调
        def update_progress(value, text=None):
            update_text = text if text else f"处理中...{value}%"
            self.print_progress.update_progress(value, update_text)
        
        # 使用QTimer延迟执行，以便UI能够更新
        self.print_method = print_method
        QTimer.singleShot(100, lambda: self.execute_print_layout(update_progress))
    
    def execute_print_layout(self, progress_callback):
        """执行照片排版处理"""
        try:
            processor = ImageProcessor()
            
            if self.print_method == "standard":
                # 标准排版
                progress_callback(20, "创建标准排版...")
                self.print_image = processor.create_print_layout(
                    self.cropped_image,
                    progress_callback=progress_callback
                )
            
            elif self.print_method == "mix":
                # 混合排版 (一寸4张 + 二寸2张)
                progress_callback(20, "创建混合排版...")
                mix_params = {
                    'small_count': 4,  # 一寸照片数量
                    'large_count': 2,  # 二寸照片数量
                    'spacing': 10,     # 间距(像素)
                    'dpi': 300         # 打印DPI
                }
                self.print_image = processor.create_mixed_print_layout(
                    self.cropped_image,
                    mix_params,
                    progress_callback=progress_callback
                )
            
            elif self.print_method == "custom":
                # 自定义排版
                progress_callback(20, "准备自定义排版...")
                
                # 导入对话框避免循环引用
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox, QDialogButtonBox, QLabel
                
                # 创建自定义参数对话框
                custom_dialog = QDialog(self)
                custom_dialog.setWindowTitle("自定义排版参数")
                dialog_layout = QVBoxLayout(custom_dialog)
                
                # 添加表单布局
                form_layout = QFormLayout()
                
                # 行数选择
                rows_spin = QSpinBox()
                rows_spin.setRange(1, 10)
                rows_spin.setValue(4)
                rows_spin.setToolTip("排版的行数")
                form_layout.addRow("行数:", rows_spin)
                
                # 列数选择
                cols_spin = QSpinBox()
                cols_spin.setRange(1, 10)
                cols_spin.setValue(3)
                cols_spin.setToolTip("排版的列数")
                form_layout.addRow("列数:", cols_spin)
                
                # 间距选择
                spacing_spin = QSpinBox()
                spacing_spin.setRange(0, 100)
                spacing_spin.setValue(10)
                spacing_spin.setSuffix(" px")
                spacing_spin.setToolTip("照片之间的间距(像素)")
                form_layout.addRow("间距:", spacing_spin)
                
                # DPI选择
                dpi_spin = QSpinBox()
                dpi_spin.setRange(72, 600)
                dpi_spin.setValue(300)
                dpi_spin.setToolTip("打印分辨率(DPI)")
                form_layout.addRow("DPI:", dpi_spin)
                
                # 添加表单到对话框
                dialog_layout.addLayout(form_layout)
                
                # 添加按钮
                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                button_box.accepted.connect(custom_dialog.accept)
                button_box.rejected.connect(custom_dialog.reject)
                dialog_layout.addWidget(button_box)
                
                # 暂时隐藏进度条，显示对话框
                self.print_progress.hide_animation()
                
                # 如果用户接受设置
                if custom_dialog.exec_():
                    # 显示进度条
                    self.print_progress.start("创建自定义排版...")
                    
                    # 获取用户设置的参数
                    custom_params = {
                        'rows': rows_spin.value(),        # 行数
                        'columns': cols_spin.value(),     # 列数
                        'spacing': spacing_spin.value(),  # 间距(像素)
                        'dpi': dpi_spin.value()           # 打印DPI
                    }
                    
                    # 创建自定义排版
                    self.print_image = processor.create_custom_print_layout(
                        self.cropped_image,
                        custom_params,
                        progress_callback=progress_callback
                    )
                else:
                    # 用户取消了设置
                    self.print_progress.error("已取消自定义排版")
                    return
            
            # 显示处理结果
            if self.print_image:
                # 将PIL图像转换为QPixmap
                self.print_image.save("temp/print_layout.png", "PNG")
                print_pixmap = QPixmap("temp/print_layout.png")
                
                # 更新预览
                self.print_image_preview.set_processed_image(print_pixmap)
                self.print_save_btn.setEnabled(True)
                
                # 完成进度
                self.print_progress.complete("排版生成完成")
            else:
                raise Exception("处理失败，未返回有效图像")
                
        except Exception as e:
            self.print_progress.error(f"处理出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"证件照排版过程中发生错误: {str(e)}")
    
    def save_print_image(self):
        """保存排版后的打印文件"""
        if self.print_image is None:
            return
            
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "保存打印文件", "", 
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;PDF (*.pdf)"
        )
        
        if file_path:
            try:
                # 从选择的过滤器提取格式
                if "PDF" in file_type:
                    # 保存为PDF
                    self.print_image.convert('RGB').save(file_path, "PDF", resolution=300.0)
                else:
                    # 保存为其他格式
                    format_mapping = {
                        "PNG (*.png)": "PNG",
                        "JPEG (*.jpg *.jpeg)": "JPEG",
                        "TIFF (*.tif *.tiff)": "TIFF"
                    }
                    
                    # 默认为PNG
                    format = format_mapping.get(file_type, "PNG")
                    self.print_image.save(file_path, format)
                    
                QMessageBox.information(self, "成功", "打印文件已成功保存！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存打印文件时出错: {str(e)}")