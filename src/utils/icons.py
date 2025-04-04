"""
证件照处理系统 - 图标管理
提供所有图标资源和图标加载函数
"""
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvg import QSvgRenderer
from io import BytesIO

# SVG图标定义
class SvgIcons:
    # 界面图标
    UPLOAD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M4 19h16v-7h2v8a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-8h2v7zm9-10v7h-2V9H6l6-6 6 6h-5z"/></svg>"""
    SAVE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M7 19v-6h10v6h2V7.828L16.172 5H5v14h2zM4 3h13l4 4v13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zm5 12v4h6v-4H9z"/></svg>"""
    PROCESS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M2 13h6v8H2v-8zm14-5h6v13h-6V8zm-7 3h6v10H9v-10zM4 15v4h2v-4H4zm7-4v8h2v-8h-2zm7-1v10h2V10h-2z"/></svg>"""
    
    # 工具图标
    CROP = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M15 17v2H6a1 1 0 0 1-1-1V7H2V5h3V2h2v15h8zm2 5V7H9V5h9a1 1 0 0 1 1 1v16h-2z"/></svg>"""
    EDIT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M5 19h1.414l9.314-9.314-1.414-1.414L5 17.586V19zm16 2H3v-4.243L16.435 3.322a1 1 0 0 1 1.414 0l2.829 2.829a1 1 0 0 1 0 1.414L9.243 19H21v2zM15.728 6.858l1.414 1.414 1.414-1.414-1.414-1.414-1.414 1.414z"/></svg>"""
    ZOOM_IN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M18.031 16.617l4.283 4.282-1.415 1.415-4.282-4.283A8.96 8.96 0 0 1 11 20c-4.968 0-9-4.032-9-9s4.032-9 9-9 9 4.032 9 9a8.96 8.96 0 0 1-1.969 5.617zm-2.006-.742A6.977 6.977 0 0 0 18 11c0-3.868-3.133-7-7-7-3.868 0-7 3.132-7 7 0 3.867 3.132 7 7 7a6.977 6.977 0 0 0 4.875-1.975l.15-.15zm-3.847-8.699a.75.75 0 0 0-.628.628l-.278 1.671a2.517 2.517 0 0 1-1.556 1.556l-1.67.279a.75.75 0 0 0-.629.627l-.278 1.671a2.517 2.517 0 0 1-1.555 1.556l-1.67.279a.75.75 0 0 0 0 1.5l1.67.279a2.517 2.517 0 0 1 1.556 1.555l.278 1.67a.75.75 0 0 0 1.256 0l.278-1.67a2.517 2.517 0 0 1 1.556-1.556l1.67-.278a.75.75 0 0 0 0-1.5l-1.67-.279a2.517 2.517 0 0 1-1.556-1.556l-.278-1.67a.75.75 0 0 0-.628-.628zm.627 3.443a4.525 4.525 0 0 0 1.565 1.564l.3.1-.3.1a4.525 4.525 0 0 0-1.564 1.565l-.1.3-.1-.3a4.525 4.525 0 0 0-1.565-1.564l-.3-.1.3-.1a4.525 4.525 0 0 0 1.564-1.565l.1-.3.1.3z"/>
    </svg>"""
    ZOOM_OUT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M18.031 16.617l4.283 4.282-1.415 1.415-4.282-4.283A8.96 8.96 0 0 1 11 20c-4.968 0-9-4.032-9-9s4.032-9 9-9 9 4.032 9 9a8.96 8.96 0 0 1-1.969 5.617zm-2.006-.742A6.977 6.977 0 0 0 18 11c0-3.868-3.133-7-7-7-3.868 0-7 3.132-7 7 0 3.867 3.132 7 7 7a6.977 6.977 0 0 0 4.875-1.975l.15-.15zM8 8h6v6H8V8z"/></svg>"""
    
    # 控制图标
    RESET = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M18.537 19.567A9.961 9.961 0 0 1 12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10c0 2.136-.67 4.116-1.81 5.74L17 12h3a8 8 0 1 0-2.46 5.772l.997 1.795z"/></svg>"""
    CONFIRM = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm-.997-4L6.76 11.757l1.414-1.414 2.829 2.829 5.656-5.657 1.415 1.414L11.003 16z"/></svg>"""
    CANCEL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm0-9.414l2.828-2.829 1.415 1.415L13.414 12l2.829 2.828-1.415 1.415L12 13.414l-2.828 2.829-1.415-1.415L10.586 12 7.757 9.172l1.415-1.415L12 10.586z"/></svg>"""
    
    # 算法图标
    ALGO_REMBG = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="12" cy="12" r="5" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
    </svg>
    """
    
    ALGO_GRABCUT = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M3 9h18" />
      <path d="M3 15h18" />
      <path d="M9 3v18" />
      <path d="M15 3v18" />
    </svg>
    """
    
    ALGO_API = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v8" />
      <path d="M8 12h8" />
      <path d="M8.5 8.5l7 7" />
      <path d="M15.5 8.5l-7 7" />
    </svg>
    """
    
    # 打印排版图标
    PRINT_STANDARD = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M3 9h18" />
      <path d="M3 15h18" />
      <path d="M9 3v18" />
      <path d="M15 3v18" />
    </svg>
    """

class IconProvider:
    """图标提供器"""
    
    # 使图标定义在IconProvider中也可访问
    SvgIcons = SvgIcons
    
    @staticmethod
    def get_icon(svg_content, color=None):
        """
        从SVG内容创建QIcon
        
        Args:
            svg_content (str): SVG内容
            color (str, optional): 颜色（十六进制格式）
        
        Returns:
            QIcon: 图标对象
        """
        from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
        from PySide6.QtCore import QByteArray, Qt, QSize
        from PySide6.QtWidgets import QApplication
        
        # 如果设置了颜色，替换SVG中的颜色
        if color:
            svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')
            svg_content = svg_content.replace('fill="currentColor"', f'fill="{color}"')
        
        # 创建空白pixmap
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        # 创建简单的颜色图标（替代SVG渲染）
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if "rect" in svg_content:
            # 绘制矩形
            painter.setPen(QColor(color or "#000000"))
            painter.drawRect(4, 4, 16, 16)
        elif "circle" in svg_content:
            # 绘制圆形
            painter.setPen(QColor(color or "#000000"))
            painter.drawEllipse(4, 4, 16, 16)
        else:
            # 默认绘制一个简单图形
            painter.setPen(QColor(color or "#000000"))
            painter.drawLine(4, 4, 20, 20)
            painter.drawLine(4, 20, 20, 4)
        
        painter.end()
        
        # 返回图标
        return QIcon(pixmap)
    
    @staticmethod
    def get_icon_for_button(button, svg_content, color=None, size=20):
        """设置按钮图标"""
        from PySide6.QtCore import QSize
        
        icon = IconProvider.get_icon(svg_content, color)
        button.setIcon(icon)
        button.setIconSize(QSize(size, size)) 