"""
API密钥设置对话框
用于设置和管理API密钥
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QCursor
import os

from src.utils.theme import Colors, set_card_style, set_primary_button_style, set_accent_button_style
from src.utils.icons import IconProvider

class ApiKeyDialog(QDialog):
    """API密钥设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置API密钥")
        self.setMinimumWidth(450)
        self.setWindowModality(Qt.ApplicationModal)
        
        # 初始化UI
        self.init_ui()
        
        # 加载已有的API密钥（如果存在）
        self.load_api_key()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("设置Remove.bg API密钥")
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_DARK}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 说明文本
        description = QLabel(
            "Remove.bg是一个专业的在线抠图服务，提供高质量的背景去除效果。\n"
            "使用该服务需要API密钥，可以从以下网站获取密钥：\n"
            "https://www.remove.bg/api"
        )
        description.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 13px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # API密钥输入框
        key_layout = QHBoxLayout()
        key_label = QLabel("API密钥:")
        key_label.setStyleSheet(f"color: {Colors.TEXT_DARK}; font-size: 14px;")
        key_layout.addWidget(key_label)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("输入您的Remove.bg API密钥")
        self.key_input.setMinimumHeight(30)
        self.key_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                background-color: {Colors.BACKGROUND_LIGHT};
            }}
            QLineEdit:focus {{
                border: 1px solid {Colors.PRIMARY};
            }}
        """)
        key_layout.addWidget(self.key_input)
        
        layout.addLayout(key_layout)
        
        # 记住选项
        self.remember_checkbox = QCheckBox("保存API密钥到本地")
        self.remember_checkbox.setChecked(True)
        self.remember_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_DARK};
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                background: {Colors.BACKGROUND_LIGHT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY_DARK};
                image: url(:/checkbox_checked.png);
            }}
        """)
        layout.addWidget(self.remember_checkbox)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet(f"""
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
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 确认按钮
        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setIcon(IconProvider.get_icon(IconProvider.SvgIcons.CONFIRM, Colors.BACKGROUND))
        set_primary_button_style(self.confirm_btn)
        self.confirm_btn.clicked.connect(self.save_api_key)
        button_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(button_layout)
    
    def load_api_key(self):
        """加载已有的API密钥"""
        config_dir = os.path.join('config')
        config_file = os.path.join(config_dir, 'api_config.txt')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        self.key_input.setText(api_key)
            except Exception as e:
                print(f"加载API密钥时出错: {str(e)}")
    
    def save_api_key(self):
        """保存API密钥并关闭对话框"""
        api_key = self.key_input.text().strip()
        
        if not api_key:
            # 如果没有输入API密钥，也接受（可能使用其他方法）
            self.accept()
            return
        
        # 如果选择记住密钥，保存到配置文件
        if self.remember_checkbox.isChecked():
            try:
                config_dir = os.path.join('config')
                os.makedirs(config_dir, exist_ok=True)
                
                config_file = os.path.join(config_dir, 'api_config.txt')
                with open(config_file, 'w') as f:
                    f.write(api_key)
            except Exception as e:
                print(f"保存API密钥时出错: {str(e)}")
        
        # 关闭对话框
        self.accept()
    
    def get_api_key(self):
        """获取输入的API密钥"""
        return self.key_input.text().strip() 