#!/usr/bin/env python
"""
旅行证照片处理 - 样式应用工具
该脚本用于重新加载并应用更新后的UI样式
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox

def main():
    # 确保必要的目录存在
    dirs = ['models', 'config', 'temp']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 清除存在的样式缓存
    app.setStyleSheet("")
    
    try:
        # 导入主题样式
        from src.utils.theme import STYLESHEET
        # 应用全局样式表
        app.setStyleSheet(STYLESHEET)
        
        # 创建并显示主窗口
        from src.ui.main_window import ModernPhotoProcessor
        window = ModernPhotoProcessor()
        
        # 显示通知
        QMessageBox.information(window, "样式更新", "UI界面样式已成功更新！")
        
        # 显示窗口
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
    
    except Exception as e:
        # 创建一个简单的错误对话框
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        
        error_dialog = QDialog()
        error_dialog.setWindowTitle("样式应用错误")
        error_dialog.resize(400, 200)
        
        layout = QVBoxLayout(error_dialog)
        
        error_label = QLabel(f"应用样式时发生错误:\n{str(e)}")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(error_dialog.close)
        layout.addWidget(close_btn)
        
        error_dialog.exec()
        sys.exit(1)

if __name__ == "__main__":
    main() 