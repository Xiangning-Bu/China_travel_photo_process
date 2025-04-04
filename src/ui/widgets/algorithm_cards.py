"""
旅行证照片处理 - 算法选择卡片
提供卡片式的算法选择界面
"""
from PySide6.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout, 
                              QLabel, QButtonGroup, QPushButton, QRadioButton)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon
from src.utils.theme import Colors, set_card_style
from src.utils.icons import IconProvider

class AlgorithmCard(QFrame):
    """单个算法选择卡片"""
    
    def __init__(self, parent=None, title="算法", description="描述", icon=None, value=None):
        super().__init__(parent)
        
        self.value = value
        
        # 设置卡片样式和边框
        self.setStyleSheet(f"""
            background-color: {Colors.BACKGROUND_LIGHT};
            border-radius: 6px;
            border: 1px solid {Colors.BORDER};
            padding: 5px;
        """)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # 减小内边距，让更多内容可见
        layout.setSpacing(5)  # 减小布局内元素间距
        
        # 标题和图标
        title_layout = QHBoxLayout()
        title_layout.setSpacing(5)  # 减小标题布局的间距
        
        if icon:
            # 如果icon是字符串，假设它是SVG内容
            if isinstance(icon, str):
                # 使用IconProvider创建图标
                icon = IconProvider.get_icon(icon)
            
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(QSize(24, 24)))
            title_layout.addWidget(icon_label)
            
        # 创建标题标签
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 创建单选按钮并设置尺寸
        self.radio = QRadioButton()
        self.radio.setStyleSheet("QRadioButton::indicator { width: 18px; height: 18px; }")
        title_layout.addWidget(self.radio)
        
        layout.addLayout(title_layout)
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_DARK}; line-height: 120%;")
        desc_label.setWordWrap(True)
        desc_label.setMinimumHeight(50)  # 改为最小高度而不是固定高度
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        
        # 调整高度和宽度设置
        self.setMinimumHeight(100)  # 改为最小高度而不是固定高度
        self.setMinimumWidth(220)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.radio.setChecked(True)
        super().mousePressEvent(event)
        
    def setChecked(self, checked):
        """设置选中状态"""
        self.radio.setChecked(checked)
        if checked:
            # 选中状态使用强烈的视觉反馈
            self.setStyleSheet(f"""
                background-color: {Colors.PRIMARY_LIGHT};
                border-radius: 6px;
                border: 2px solid {Colors.PRIMARY};
                padding: 6px;
            """)
            # 更新文字样式，使选中项更明显
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if isinstance(item, QHBoxLayout):  # 标题布局
                    for j in range(item.count()):
                        widget = item.itemAt(j).widget()
                        if isinstance(widget, QLabel):  # 标题标签
                            widget.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
                if isinstance(item.widget(), QLabel) and item.widget().wordWrap():  # 描述标签
                    item.widget().setStyleSheet(f"font-size: 13px; color: {Colors.PRIMARY_DARK}; font-weight: bold; line-height: 120%;")
        else:
            # 未选中状态使用淡色边框
            self.setStyleSheet(f"""
                background-color: {Colors.BACKGROUND_LIGHT};
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
                padding: 5px;
            """)
            # 恢复默认文字样式
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if isinstance(item, QHBoxLayout):  # 标题布局
                    for j in range(item.count()):
                        widget = item.itemAt(j).widget()
                        if isinstance(widget, QLabel):  # 标题标签
                            widget.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {Colors.PRIMARY_DARK};")
                if isinstance(item.widget(), QLabel) and item.widget().wordWrap():  # 描述标签
                    item.widget().setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_DARK}; line-height: 120%;")
        
class AlgorithmSelector(QWidget):
    """算法选择组件"""
    
    # 定义选择改变信号
    selection_changed = Signal(str)  # 发送所选算法的值
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        self.layout.setSpacing(10)  # 增加间距使组件更清晰
        
        # 创建卡片容器
        self.cards_layout = QVBoxLayout()  # 垂直布局以确保算法卡片完全显示
        self.cards_layout.setSpacing(10)  # 增加卡片之间的间距
        
        # 创建按钮组
        self.button_group = QButtonGroup(self)
        
        self.layout.addLayout(self.cards_layout)
        self.setLayout(self.layout)
        
        # 存储卡片
        self.cards = {}
        
    def add_algorithm(self, key, title, description, icon=None):
        """添加算法卡片"""
        card = AlgorithmCard(self, title, description, icon, key)
        self.cards_layout.addWidget(card)
        self.button_group.addButton(card.radio)
        self.cards[key] = card
        
        # 连接信号
        card.radio.toggled.connect(lambda checked, k=key: self._on_selection_changed(k, checked))
        
        return card
        
    def _on_selection_changed(self, key, checked):
        """选择变更处理"""
        if checked:
            self.selection_changed.emit(key)
            # 更新选中样式
            for k, card in self.cards.items():
                card.setChecked(k == key)
                
    def get_selected(self):
        """获取当前选中的算法值"""
        for key, card in self.cards.items():
            if card.radio.isChecked():
                return key
        return None
    
    def set_selected(self, key):
        """设置选中的算法"""
        if key in self.cards:
            self.cards[key].radio.setChecked(True) 