"""
证件照处理系统 - 主题样式
包含颜色定义、样式表和其他UI相关的全局设置
"""
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt

# 主题颜色
class Colors:
    """全局颜色常量"""
    # 主题色
    PRIMARY_DARK = "#1a87b0"  # 深蓝绿色
    PRIMARY = "#20a8d8"      # 蓝绿色
    PRIMARY_LIGHT = "#e8f5fa"  # 浅蓝绿色
    
    # 强调色
    ACCENT = "#4caf50"       # 绿色
    ACCENT_DARK = "#3d8c40"  # 深绿色
    
    # 背景色
    BACKGROUND = "#f0f0f0"   # 浅灰色
    BACKGROUND_LIGHT = "#ffffff"  # 白色
    
    # 文本色
    TEXT_DARK = "#333333"    # 深灰色
    TEXT_LIGHT = "#888888"   # 中灰色
    
    # 边框色
    BORDER = "#dddddd"       # 灰色
    HOVER = "#f5f9fc"        # 悬停色
    
    # 状态色
    SUCCESS = "#4CAF50"      # 绿色
    ERROR = "#F44336"        # 红色
    WARNING = "#FF9800"      # 橙色
    INFO = "#2196F3"         # 蓝色
    CARD_BG = "#ffffff"      # 卡片背景色

# 字体设置
class Fonts:
    TITLE_SIZE = 16             # 标题文字大小
    SUBTITLE_SIZE = 14          # 副标题大小
    BODY_SIZE = 12              # 正文大小
    SMALL_SIZE = 10             # 小字体大小
    
    FAMILY = ""                 # 空字符串表示使用系统默认字体

# 全局样式表
STYLESHEET = f"""
/* 全局样式 */
QWidget {{
    background-color: {Colors.BACKGROUND};
    color: {Colors.TEXT_DARK};
    font-size: {Fonts.BODY_SIZE}px;
    font-family: 'Microsoft YaHei', sans-serif;
}}

/* 主窗口样式 */
QMainWindow {{
    background-color: {Colors.BACKGROUND};
}}

/* 选项卡样式 - 现代化外观 */
QTabWidget::pane {{
    border: none;
    padding: 0px;
}}

QTabBar::tab {{
    background-color: {Colors.BACKGROUND_LIGHT}; 
    border: 1px solid {Colors.BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 12px 18px;
    margin-right: 5px;
    font-size: 14px;
    font-weight: normal;
    color: {Colors.TEXT_DARK};
}}

QTabBar::tab:selected {{
    background-color: {Colors.PRIMARY};
    color: white;
    font-weight: bold;
}}

QTabBar::tab:hover:!selected {{
    background-color: {Colors.HOVER};
}}

/* 按钮样式 */
QPushButton {{
    background-color: {Colors.PRIMARY};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {Colors.PRIMARY_DARK};
}}

QPushButton:pressed {{
    background-color: #157298;
}}

/* 强调按钮 */
QPushButton[accent="true"] {{
    background-color: {Colors.ACCENT};
}}

QPushButton[accent="true"]:hover {{
    background-color: {Colors.ACCENT_DARK};
}}

QPushButton[accent="true"]:pressed {{
    background-color: #2d6830;
}}

/* 标签样式 */
QLabel[heading="true"] {{
    font-size: {Fonts.TITLE_SIZE}px;
    font-weight: bold;
    color: {Colors.PRIMARY_DARK};
}}

QLabel[subheading="true"] {{
    font-size: {Fonts.SUBTITLE_SIZE}px;
    color: {Colors.PRIMARY};
}}

/* 卡片样式 */
QFrame[card="true"] {{
    background-color: {Colors.CARD_BG};
    border-radius: 8px;
    border: 1px solid {Colors.BORDER};
    padding: 15px;
    box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
}}

/* 进度条样式 */
QProgressBar {{
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    text-align: center;
    height: 12px;
}}

QProgressBar::chunk {{
    background-color: {Colors.PRIMARY};
    border-radius: 3px;
}}

/* 下拉框样式 */
QComboBox {{
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    padding: 6px;
    min-width: 120px;
    background-color: {Colors.BACKGROUND_LIGHT};
}}

QComboBox:hover {{
    border: 1px solid {Colors.PRIMARY};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: right;
    width: 20px;
    border-left: 1px solid {Colors.BORDER};
}}

QComboBox::item:selected {{
    background-color: {Colors.PRIMARY};
    color: white;
}}

/* 分割线样式 */
QSplitter::handle {{
    background-color: {Colors.BORDER};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* 图片预览区域 */
QLabel[preview="true"] {{
    background-color: {Colors.CARD_BG};
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
    padding: 5px;
}}
"""

# 卡片式框架的样式函数
def set_card_style(widget):
    """将部件设置为卡片式样式"""
    widget.setProperty("card", "true")
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {Colors.CARD_BG};
            border-radius: 8px;
            border: 1px solid {Colors.BORDER};
            padding: 15px;
        }}
        QWidget:hover {{
            border-color: {Colors.PRIMARY_LIGHT};
        }}
    """)

    # 应用阴影效果（如果支持）
    try:
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        widget.setGraphicsEffect(shadow)
    except:
        # 如果不支持阴影效果，忽略错误
        pass

# 标题标签样式函数
def set_heading_style(label):
    """将标签设置为标题样式"""
    label.setProperty("heading", "true")
    label.setStyleSheet(f"""
        font-size: {Fonts.TITLE_SIZE}px;
        font-weight: bold;
    """)

# 副标题标签样式函数
def set_subheading_style(label):
    """将标签设置为副标题样式"""
    label.setProperty("subheading", "true")
    label.setStyleSheet(f"""
        font-size: {Fonts.SUBTITLE_SIZE}px;
        color: #34495e;
    """)

# 设置主要操作按钮样式
def set_primary_button_style(button):
    """将按钮设置为主要操作样式"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            font-family: 'Microsoft YaHei', sans-serif;
            min-height: 32px;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {Colors.PRIMARY_DARK};
        }}
        QPushButton:pressed {{
            background-color: #157298;
        }}
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #888888;
        }}
    """)
    button.setCursor(QCursor(Qt.PointingHandCursor))

# 设置强调按钮样式
def set_accent_button_style(button):
    """将按钮设置为强调样式"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {Colors.ACCENT};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            font-family: 'Microsoft YaHei', sans-serif;
            min-height: 32px;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {Colors.ACCENT_DARK};
        }}
        QPushButton:pressed {{
            background-color: #2d6830;
        }}
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #888888;
        }}
    """)
    button.setCursor(QCursor(Qt.PointingHandCursor))

# 设置次要按钮样式
def set_secondary_button_style(button, color=Colors.TEXT_DARK, border_color=Colors.BORDER):
    """将按钮设置为次要样式"""
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {Colors.BACKGROUND_LIGHT};
            color: {color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            font-family: 'Microsoft YaHei', sans-serif;
            min-height: 32px;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {Colors.HOVER};
            border-color: {Colors.PRIMARY};
            color: {Colors.PRIMARY_DARK};
        }}
        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BACKGROUND};
            color: {Colors.TEXT_LIGHT};
            border-color: {Colors.BORDER};
        }}
    """)
    button.setCursor(QCursor(Qt.PointingHandCursor))

# 设置照片预览样式
def set_preview_style(label):
    """将标签设置为照片预览样式"""
    label.setProperty("preview", "true")
    label.setStyleSheet(f"""
        background-color: {Colors.CARD_BG};
        border: 1px solid {Colors.BORDER};
        border-radius: 4px;
    """) 