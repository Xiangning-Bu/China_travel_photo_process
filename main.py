import sys
from PySide6.QtWidgets import QApplication
import os
from src.utils.theme import STYLESHEET
from src.ui.main_window import ModernPhotoProcessor

def ensure_dirs():
    """确保必要的目录存在"""
    dirs = ['models', 'config', 'temp']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

if __name__ == '__main__':
    # 确保必要的目录存在
    ensure_dirs()
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 应用全局样式表
    app.setStyleSheet(STYLESHEET)
    
    # 设置应用信息
    app.setApplicationName("旅行证照片处理")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("照片处理工作室")
    
    # 创建并显示主窗口
    window = ModernPhotoProcessor()
    window.show()
    
    # 运行应用
    sys.exit(app.exec()) 