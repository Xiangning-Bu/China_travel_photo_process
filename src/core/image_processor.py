import cv2
import numpy as np
from PIL import Image
import time
from PySide6.QtCore import QObject, Signal
import os
import rembg

class BackgroundRemovalSignals(QObject):
    """定义用于背景去除进度通信的信号类"""
    progress = Signal(int)
    
# 创建全局信号实例
bg_signals = BackgroundRemovalSignals()

class ImageProcessor:
    @staticmethod
    def _ensure_cascade_file(cascade_name, progress_callback=None):
        """确保级联分类器文件存在并返回路径"""
        # 检查文件是否已存在
        cascade_file = f'models/{cascade_name}'
        if os.path.exists(cascade_file):
            return cascade_file
            
        # 文件不存在，需要创建
        os.makedirs('models', exist_ok=True)
        
        # 尝试从OpenCV内置路径复制
        import shutil
        import cv2.data
        src_path = os.path.join(cv2.data.haarcascades, cascade_name)
        try:
            shutil.copy(src_path, cascade_file)
            print(f"已从OpenCV复制级联分类器文件: {cascade_name}")
            return cascade_file
        except Exception as e:
            print(f"无法从OpenCV复制级联分类器文件: {str(e)}")
            
        # 从网络下载
        import urllib.request
        url = f'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{cascade_name}'
        try:
            urllib.request.urlretrieve(url, cascade_file)
            print(f"已从GitHub下载级联分类器文件: {cascade_name}")
            return cascade_file
        except Exception as e2:
            print(f"无法下载级联分类器文件: {str(e2)}")
            if progress_callback:
                progress_callback(100, "人脸检测失败")
            return None
            
    @staticmethod
    def _load_face_cascade(progress_callback=None):
        """加载人脸检测级联分类器"""
        cascade_file = ImageProcessor._ensure_cascade_file('haarcascade_frontalface_default.xml', progress_callback)
        if not cascade_file:
            return None
            
        # 加载人脸检测器
        face_cascade = cv2.CascadeClassifier(cascade_file)
        
        # 检查级联分类器是否正确加载
        if face_cascade.empty():
            print("无法加载级联分类器")
            if progress_callback:
                progress_callback(100, "加载人脸检测器失败")
            return None
            
        return face_cascade
        
    @staticmethod
    def remove_background(image, progress_callback=None, method="rembg"):
        """
        移除图像背景
        
        参数:
        image -- PIL Image对象
        progress_callback -- 进度回调函数
        method -- 背景去除方法: "rembg"（推荐）、"grabcut"（快速）、"api"（在线服务）
        
        返回:
        去除背景后的PIL Image对象
        """
        # 更新进度回调的辅助函数
        def update_progress(value):
            if progress_callback:
                progress_callback(value)
            elif hasattr(bg_signals, 'progress'):
                bg_signals.progress.emit(value)
        
        update_progress(10)
        
        try:
            if method == "rembg":
                return ImageProcessor.remove_background_rembg(image, progress_callback)
            elif method == "api":
                api_key = ImageProcessor.get_api_key()
                if api_key:
                    return ImageProcessor.remove_background_api(image, api_key, progress_callback)
                else:
                    print("未设置API密钥，回退到rembg方法")
                    return ImageProcessor.remove_background_rembg(image, progress_callback)
            elif method == "grabcut":
                return ImageProcessor.remove_background_grabcut(image, progress_callback)
            else:
                # 默认使用rembg
                return ImageProcessor.remove_background_rembg(image, progress_callback)
        except Exception as e:
            print(f"背景去除失败: {str(e)}")
            # 如果首选方法失败，尝试GrabCut
            if method != "grabcut":
                print(f"尝试使用GrabCut方法")
                try:
                    return ImageProcessor.remove_background_grabcut(image, progress_callback)
                except Exception as e2:
                    print(f"GrabCut方法也失败: {str(e2)}")
            
            # 所有方法都失败，返回原图
            update_progress(100)
            return image.copy()

    @staticmethod
    def remove_background_rembg(image, progress_callback=None):
        """
        使用rembg库去除背景 - 简单高效的方法
        
        参数:
        image -- PIL Image对象
        progress_callback -- 进度回调函数
        
        返回:
        去除背景后的PIL Image对象
        """
        # 更新进度回调的辅助函数
        def update_progress(value):
            if progress_callback:
                progress_callback(value)
            elif hasattr(bg_signals, 'progress'):
                bg_signals.progress.emit(value)
        
        try:
            update_progress(10)
            
            # 转换为RGB模式确保兼容性
            input_image = image.convert("RGB")
            
            update_progress(30)
            
            # 使用rembg移除背景
            output_image = rembg.remove(input_image)
            
            update_progress(80)
            
            # 创建白色背景
            white_bg = Image.new("RGBA", output_image.size, (255, 255, 255, 255))
            
            # 将透明背景图像叠加到白色背景上
            result_image = Image.alpha_composite(white_bg.convert("RGBA"), output_image.convert("RGBA"))
            result_image = result_image.convert("RGB")
            
            update_progress(100)
            
            return result_image
            
        except Exception as e:
            print(f"Rembg背景去除出错: {str(e)}")
            raise e

    @staticmethod
    def remove_background_grabcut(image, progress_callback=None):
        """使用GrabCut算法去除背景"""
        # 更新进度回调的辅助函数
        def update_progress(value):
            if progress_callback:
                progress_callback(value)
            elif hasattr(bg_signals, 'progress'):
                bg_signals.progress.emit(value)
        
        try:
            # 设置超时时间（秒）
            timeout = 30
            start_time = time.time()
            
            update_progress(10)
            
            # 先缩小图像以加快处理速度
            max_dimension = 1000
            width, height = image.size
            scale_factor = 1.0
            
            if max(width, height) > max_dimension:
                scale_factor = max_dimension / max(width, height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                small_image = image.resize(new_size, Image.LANCZOS)
            else:
                small_image = image.copy()
            
            update_progress(20)
            
            # 转换为OpenCV格式
            cv_image = np.array(small_image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            update_progress(30)
            
            # 创建掩码和模型
            mask = np.zeros(cv_image.shape[:2], np.uint8)
            bgdModel = np.zeros((1, 65), np.float64)
            fgdModel = np.zeros((1, 65), np.float64)
            
            # 定义前景矩形 - 适当扩大范围
            height, width = cv_image.shape[:2]
            rect = (int(width*0.05), int(height*0.05), int(width*0.9), int(height*0.9))
            
            update_progress(40)
            
            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError("背景去除操作超时")
            
            # 应用GrabCut，减少迭代次数提高速度
            cv2.grabCut(cv_image, mask, rect, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_RECT)
            
            update_progress(70)
            
            # 创建二值掩码
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # 应用掩码
            result = cv_image * mask2[:, :, np.newaxis]
            
            update_progress(80)
            
            # 创建白色背景
            white_bg = np.ones_like(cv_image, dtype=np.uint8) * 255
            result = cv2.bitwise_or(white_bg, white_bg, mask=1-mask2) + result
            
            update_progress(90)
            
            # 转换回PIL格式并恢复原始大小
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            result_image = Image.fromarray(result_rgb)
            
            # 如果之前进行了缩放，现在恢复到原始大小
            if scale_factor < 1.0:
                result_image = result_image.resize(image.size, Image.LANCZOS)
            
            update_progress(100)
            
            return result_image
            
        except TimeoutError as e:
            print(f"背景去除超时: {str(e)}")
            raise e
        except Exception as e:
            print(f"背景去除出错: {str(e)}")
            raise e

    @staticmethod
    def remove_background_api(image, api_key, progress_callback=None):
        """使用Remove.bg API移除背景"""
        # 更新进度回调的辅助函数
        def update_progress(value):
            if progress_callback:
                progress_callback(value)
            elif hasattr(bg_signals, 'progress'):
                bg_signals.progress.emit(value)
        
        try:
            import requests
            import io
            
            update_progress(20)
            
            # 将图像转换为字节
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            update_progress(40)
            
            # 发送到Remove.bg API
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': img_byte_arr},
                data={'size': 'auto'},
                headers={'X-Api-Key': api_key},
            )
            
            update_progress(70)
            
            if response.status_code == requests.codes.ok:
                update_progress(90)
                
                # 从响应创建图像
                result_image = Image.open(io.BytesIO(response.content))
                
                update_progress(100)
                
                return result_image
            else:
                print(f"API错误: {response.status_code} {response.text}")
                raise Exception(f"API错误: {response.status_code}")
                
        except Exception as e:
            print(f"API背景去除出错: {str(e)}")
            raise e

    @staticmethod
    def get_api_key():
        """获取存储的API密钥"""
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
        config_file = os.path.join(config_dir, 'api_config.txt')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return f.read().strip()
            except:
                return None
        return None

    @staticmethod
    def auto_crop_id_photo(image, progress_callback=None):
        """自动裁剪证件照"""
        # 报告进度
        if progress_callback:
            progress_callback(10, "准备人脸检测...")
            
        # 转换为OpenCV格式
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 加载人脸检测器
        if progress_callback:
            progress_callback(20, "加载人脸检测器...")
            
        face_cascade = ImageProcessor._load_face_cascade(progress_callback)
        if face_cascade is None:
            return None
        
        # 检测人脸
        if progress_callback:
            progress_callback(30, "检测人脸中...")
            
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            if progress_callback:
                progress_callback(100, "未检测到人脸")
            return None
        
        # 获取人脸区域
        if progress_callback:
            progress_callback(50, "计算裁剪区域...")
            
        x, y, w, h = faces[0]
        
        # 计算证件照尺寸（390×567像素）
        target_width = 390
        target_height = 567
        
        # 计算缩放比例
        face_height = h
        required_face_height = int(target_height * 0.635)  # 63.5%为理想人脸高度比例
        scale = required_face_height / face_height
        
        # 缩放图像
        if progress_callback:
            progress_callback(70, "缩放图像...")
            
        new_width = int(cv_image.shape[1] * scale)
        new_height = int(cv_image.shape[0] * scale)
        resized = cv2.resize(cv_image, (new_width, new_height))
        
        # 计算裁剪区域
        face_x = int(x * scale)
        face_y = int(y * scale)
        face_w = int(w * scale)
        face_h = int(h * scale)
        
        # 计算最终裁剪坐标
        crop_x = face_x + face_w//2 - target_width//2
        crop_y = face_y - int(target_height * 0.08)  # 头顶到照片顶部的距离约8%
        
        # 确保裁剪区域在图像范围内
        crop_x = max(0, min(crop_x, resized.shape[1] - target_width))
        crop_y = max(0, min(crop_y, resized.shape[0] - target_height))
        
        # 裁剪图像
        if progress_callback:
            progress_callback(90, "裁剪图像...")
            
        cropped = resized[crop_y:crop_y+target_height, crop_x:crop_x+target_width]
        
        # 转换回PIL格式
        if progress_callback:
            progress_callback(100, "完成")
            
        return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

    @staticmethod
    def create_print_layout(photo, progress_callback=None):
        """创建证件照打印排版"""
        # 如果有进度回调，初始化进度
        if progress_callback:
            progress_callback(10, "准备打印排版...")
        
        # 创建4x6英寸（1200x1800像素，300dpi）的白色背景
        layout = Image.new('RGB', (1200, 1800), 'white')
        
        # 计算间距
        margin_x = (1200 - 390 * 3) // 4
        margin_y = (1800 - 567 * 3) // 4
        
        # 粘贴9张照片
        total_photos = 9
        for idx, (row, col) in enumerate([(r, c) for r in range(3) for c in range(3)]):
            x = margin_x + col * (390 + margin_x)
            y = margin_y + row * (567 + margin_y)
            layout.paste(photo, (x, y))
            
            # 更新进度
            if progress_callback:
                progress = 20 + int(70 * (idx + 1) / total_photos)
                progress_callback(progress, f"排版中... {idx+1}/{total_photos}")
        
        # 完成进度
        if progress_callback:
            progress_callback(100, "排版完成")
        
        return layout

    @staticmethod
    def manual_crop_id_photo(image, face_position, face_size, progress_callback=None, target_width=390, target_height=567):
        """手动调整裁剪证件照"""
        try:
            # 初始化进度
            if progress_callback:
                progress_callback(10, "准备处理图像...")
                
            # 转换为OpenCV格式
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 从人脸位置和大小计算裁剪区域
            face_x, face_y = face_position
            face_w, face_h = face_size
            
            if progress_callback:
                progress_callback(30, "计算裁剪区域...")
            
            # 计算人脸在证件照中的理想高度（约63.5%）
            required_face_height = int(target_height * 0.635)
            
            # 计算缩放比例
            scale = required_face_height / face_h
            
            # 缩放图像
            if progress_callback:
                progress_callback(50, "缩放图像...")
                
            new_width = int(cv_image.shape[1] * scale)
            new_height = int(cv_image.shape[0] * scale)
            resized = cv2.resize(cv_image, (new_width, new_height))
            
            # 调整人脸位置坐标
            scaled_face_x = int(face_x * scale)
            scaled_face_y = int(face_y * scale)
            
            # 计算裁剪区域的左上角坐标
            # 人脸中心位于照片中心偏上的位置
            crop_x = scaled_face_x - target_width // 2
            crop_y = scaled_face_y - int(target_height * 0.45)  # 人脸中心Y位置约为照片高度的45%处
            
            # 确保裁剪区域在图像范围内
            crop_x = max(0, min(crop_x, resized.shape[1] - target_width))
            crop_y = max(0, min(crop_y, resized.shape[0] - target_height))
            
            # 裁剪图像
            if progress_callback:
                progress_callback(80, "裁剪图像...")
                
            cropped = resized[crop_y:crop_y+target_height, crop_x:crop_x+target_width]
            
            # 转换回PIL格式
            if progress_callback:
                progress_callback(100, "裁剪完成")
                
            return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            print(f"手动裁剪出错: {str(e)}")
            if progress_callback:
                progress_callback(100, f"裁剪出错: {str(e)}")
            return None

    @staticmethod
    def detect_face(image):
        """检测图像中的人脸并返回位置和大小"""
        try:
            # 转换为OpenCV格式
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 加载人脸检测器
            face_cascade = ImageProcessor._load_face_cascade()
            if face_cascade is None:
                return None
            
            # 检测人脸
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return None
            
            # 获取第一个检测到的人脸
            x, y, w, h = faces[0]
            
            # 计算人脸中心位置
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # 返回人脸中心位置和大小
            return ((face_center_x, face_center_y), (w, h))
            
        except Exception as e:
            print(f"人脸检测出错: {str(e)}")
            return None

    @staticmethod
    def draw_face_ellipses(image, face_position, face_size, inner_scale=0.9, outer_scale=1.1, show_distances=True):
        """在图像上绘制椭圆用于调整人脸位置"""
        try:
            # 转换为OpenCV格式
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 获取人脸中心和大小
            center_x, center_y = face_position
            width, height = face_size
            
            # 获取图像大小
            img_height, img_width = cv_image.shape[:2]
            
            # 证件照标准尺寸（33mm×48mm，像素尺寸为390×567）
            target_width_px = 390
            target_height_px = 567
            
            # 计算缩放比例（基于人脸大小）
            required_face_height = int(target_height_px * 0.635)  # 人脸应占照片高度的63.5%
            scale = required_face_height / height
            
            # 计算实际裁剪框大小
            crop_width = int(target_width_px / scale)
            crop_height = int(target_height_px / scale)
            
            # 计算裁剪框位置（使人脸位于照片高度的45%处）
            crop_y = int(center_y - crop_height * 0.45)  # 人脸中心在照片45%的位置
            crop_x = int(center_x - crop_width / 2)      # 人脸水平居中
            
            # 确保裁剪框在图像范围内
            crop_x = max(0, min(crop_x, img_width - crop_width))
            crop_y = max(0, min(crop_y, img_height - crop_height))
            
            # 创建一个半透明的遮罩层
            overlay = cv_image.copy()
            mask = np.zeros((img_height, img_width), dtype=np.uint8)
            mask[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width] = 255
            
            # 在遮罩外区域应用轻微的暗化效果
            overlay[mask == 0] = (overlay[mask == 0] * 0.8).astype(np.uint8)
            
            # 绘制裁剪框边界线
            cv2.rectangle(overlay, 
                         (crop_x, crop_y), 
                         (crop_x + crop_width, crop_y + crop_height), 
                         (0, 255, 255),  # 黄色
                         3)  # 线宽
            
            # 绘制椭圆
            center = (int(center_x), int(center_y))
            inner_axes = (int(width * inner_scale * 0.5), int(height * inner_scale * 0.6))
            outer_axes = (int(width * outer_scale * 0.5), int(height * outer_scale * 0.6))
            
            cv2.ellipse(overlay, center, inner_axes, 0, 0, 360, (0, 255, 0), 2)  # 绿色
            cv2.ellipse(overlay, center, outer_axes, 0, 0, 360, (0, 0, 255), 2)  # 红色
            
            if show_distances:
                # 设置文字参数
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.8
                text_thickness = 2
                
                # 绘制带背景的距离文字
                def draw_text_with_background(img, text, pos, text_color):
                    text_size = cv2.getTextSize(text, font, font_scale, text_thickness)[0]
                    bg_rect = (
                        pos[0] - 5,
                        pos[1] - text_size[1] - 5,
                        pos[0] + text_size[0] + 5,
                        pos[1] + 5
                    )
                    cv2.rectangle(img, (bg_rect[0], bg_rect[1]), (bg_rect[2], bg_rect[3]), (255, 255, 255), -1)
                    cv2.putText(img, text, pos, font, font_scale, text_color, text_thickness)
                
                # 计算距离的通用函数
                def calculate_distance(center_pos, axes, crop_pos, crop_size):
                    top = center_pos[1] - axes[1] - crop_pos[1]
                    bottom = crop_pos[1] + crop_size[1] - (center_pos[1] + axes[1])
                    left = center_pos[0] - axes[0] - crop_pos[0]
                    right = crop_pos[0] + crop_size[0] - (center_pos[0] + axes[0])
                    return [d * (33/390) / scale for d in [top, bottom, left, right]]  # 转换为毫米
                
                # 计算外椭圆（红色）的距离
                outer_distances = calculate_distance(
                    center, outer_axes, 
                    (crop_x, crop_y), 
                    (crop_width, crop_height)
                )
                
                # 计算内椭圆（绿色）的距离
                inner_distances = calculate_distance(
                    center, inner_axes, 
                    (crop_x, crop_y), 
                    (crop_width, crop_height)
                )
                
                # 绘制距离标签
                # 上边缘
                draw_text_with_background(overlay, f"R:{outer_distances[0]:.1f}mm", 
                                       (center[0] - 80, center[1] - outer_axes[1] - 10), 
                                       (0, 0, 255))  # 红色
                draw_text_with_background(overlay, f"G:{inner_distances[0]:.1f}mm", 
                                       (center[0] + 10, center[1] - outer_axes[1] - 10), 
                                       (0, 255, 0))  # 绿色
                
                # 下边缘
                draw_text_with_background(overlay, f"R:{outer_distances[1]:.1f}mm", 
                                       (center[0] - 80, center[1] + outer_axes[1] + 30), 
                                       (0, 0, 255))
                draw_text_with_background(overlay, f"G:{inner_distances[1]:.1f}mm", 
                                       (center[0] + 10, center[1] + outer_axes[1] + 30), 
                                       (0, 255, 0))
                
                # 左边缘
                draw_text_with_background(overlay, f"R:{outer_distances[2]:.1f}mm", 
                                       (center[0] - outer_axes[0] - 120, center[1] - 20), 
                                       (0, 0, 255))
                draw_text_with_background(overlay, f"G:{inner_distances[2]:.1f}mm", 
                                       (center[0] - outer_axes[0] - 120, center[1] + 20), 
                                       (0, 255, 0))
                
                # 右边缘
                draw_text_with_background(overlay, f"R:{outer_distances[3]:.1f}mm", 
                                       (center[0] + outer_axes[0] + 10, center[1] - 20), 
                                       (0, 0, 255))
                draw_text_with_background(overlay, f"G:{inner_distances[3]:.1f}mm", 
                                       (center[0] + outer_axes[0] + 10, center[1] + 20), 
                                       (0, 255, 0))
                
                # 绘制参考线
                def draw_dashed_line(img, pt1, pt2, color, thickness):
                    dist = ((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2) ** 0.5
                    pts = []
                    gap = 10
                    for i in np.arange(0, dist, gap):
                        r = i / dist
                        x = int((pt1[0] * (1 - r) + pt2[0] * r))
                        y = int((pt1[1] * (1 - r) + pt2[1] * r))
                        pts.append((x, y))
                    
                    for i in range(len(pts) - 1):
                        if i % 2 == 0:
                            cv2.line(img, pts[i], pts[i+1], color, thickness)
                
                # 绘制外椭圆（红色）的参考线
                for pt1, pt2 in [
                    ((center[0], center[1] - outer_axes[1]), (center[0], crop_y)),
                    ((center[0], center[1] + outer_axes[1]), (center[0], crop_y + crop_height)),
                    ((center[0] - outer_axes[0], center[1]), (crop_x, center[1])),
                    ((center[0] + outer_axes[0], center[1]), (crop_x + crop_width, center[1]))
                ]:
                    draw_dashed_line(overlay, pt1, pt2, (0, 0, 255), 1)
                
                # 绘制内椭圆（绿色）的参考线
                for pt1, pt2 in [
                    ((center[0], center[1] - inner_axes[1]), (center[0], crop_y)),
                    ((center[0], center[1] + inner_axes[1]), (center[0], crop_y + crop_height)),
                    ((center[0] - inner_axes[0], center[1]), (crop_x, center[1])),
                    ((center[0] + inner_axes[0], center[1]), (crop_x + crop_width, center[1]))
                ]:
                    draw_dashed_line(overlay, pt1, pt2, (0, 255, 0), 1)
            
            # 转换回PIL格式
            result_image = Image.fromarray(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
            return result_image
            
        except Exception as e:
            print(f"绘制椭圆出错: {str(e)}")
            return image.copy() 

    @staticmethod
    def create_custom_print_layout(photo, params, progress_callback=None):
        """创建自定义证件照打印排版
        
        参数:
            photo: PIL.Image对象，证件照
            params: 字典，包含以下键:
                - rows: 行数
                - columns: 列数
                - spacing: 间距（像素）
                - dpi: 打印DPI
            progress_callback: 进度回调函数
        
        返回:
            PIL.Image对象，排版后的图像
        """
        # 如果有进度回调，初始化进度
        if progress_callback:
            progress_callback(10, "准备自定义排版...")
        
        # 获取参数
        rows = params.get('rows', 4)
        columns = params.get('columns', 3)
        spacing = params.get('spacing', 10)
        dpi = params.get('dpi', 300)
        
        # 获取照片尺寸
        photo_width, photo_height = photo.size
        
        # 计算排版尺寸（假设A4纸，8.27 x 11.69英寸）
        page_width = int(8.27 * dpi)
        page_height = int(11.69 * dpi)
        
        # 计算每张照片之间的间距
        h_spacing = spacing
        v_spacing = spacing
        
        # 计算每张照片的位置
        layout_width = columns * photo_width + (columns - 1) * h_spacing
        layout_height = rows * photo_height + (rows - 1) * v_spacing
        
        # 确保不超过页面尺寸
        if layout_width > page_width or layout_height > page_height:
            scale = min(page_width / layout_width, page_height / layout_height)
            new_photo_width = int(photo_width * scale)
            new_photo_height = int(photo_height * scale)
            photo = photo.resize((new_photo_width, new_photo_height), Image.LANCZOS)
            photo_width, photo_height = photo.size
            layout_width = columns * photo_width + (columns - 1) * h_spacing
            layout_height = rows * photo_height + (rows - 1) * v_spacing
        
        # 创建白色背景
        if progress_callback:
            progress_callback(20, "创建排版画布...")
        
        # 水平和垂直边距，使排版居中
        h_margin = (page_width - layout_width) // 2
        v_margin = (page_height - layout_height) // 2
        
        layout = Image.new('RGB', (page_width, page_height), 'white')
        
        # 粘贴照片
        total_photos = rows * columns
        photo_count = 0
        
        for row in range(rows):
            for col in range(columns):
                # 计算位置
                x = h_margin + col * (photo_width + h_spacing)
                y = v_margin + row * (photo_height + v_spacing)
                
                # 粘贴照片
                layout.paste(photo, (x, y))
                
                # 更新计数和进度
                photo_count += 1
                if progress_callback:
                    progress = 30 + int(60 * photo_count / total_photos)
                    progress_callback(progress, f"排版中... {photo_count}/{total_photos}")
        
        # 完成进度
        if progress_callback:
            progress_callback(100, "自定义排版完成")
        
        return layout 

    @staticmethod
    def create_mixed_print_layout(photo, params, progress_callback=None):
        """创建混合证件照打印排版 (一寸和二寸混合)
        
        参数:
            photo: PIL.Image对象，证件照
            params: 字典，包含以下键:
                - small_count: 一寸照片数量
                - large_count: 二寸照片数量
                - spacing: 间距（像素）
                - dpi: 打印DPI
            progress_callback: 进度回调函数
        
        返回:
            PIL.Image对象，排版后的图像
        """
        # 如果有进度回调，初始化进度
        if progress_callback:
            progress_callback(10, "准备混合排版...")
        
        # 获取参数
        small_count = params.get('small_count', 4)  # 一寸照片数量
        large_count = params.get('large_count', 2)  # 二寸照片数量
        spacing = params.get('spacing', 10)         # 间距
        dpi = params.get('dpi', 300)                # 打印DPI
        
        # 一寸照片尺寸 (25mm x 35mm)
        small_width = int(25 / 25.4 * dpi)
        small_height = int(35 / 25.4 * dpi)
        
        # 二寸照片尺寸 (35mm x 45mm)
        large_width = int(35 / 25.4 * dpi)
        large_height = int(45 / 25.4 * dpi)
        
        # 计算页面尺寸 (A4纸 - 210mm x 297mm)
        page_width = int(210 / 25.4 * dpi)
        page_height = int(297 / 25.4 * dpi)
        
        # 调整照片大小
        small_photo = photo.resize((small_width, small_height), Image.LANCZOS)
        large_photo = photo.resize((large_width, large_height), Image.LANCZOS)
        
        # 创建白色背景
        if progress_callback:
            progress_callback(20, "创建排版画布...")
            
        layout = Image.new('RGB', (page_width, page_height), 'white')
        
        # 计算布局
        # 为简化，一寸照片在上半部分，二寸照片在下半部分
        
        # 一寸照片布局
        sm_cols = min(4, small_count)  # 最多4列
        sm_rows = (small_count + sm_cols - 1) // sm_cols  # 计算所需行数
        
        # 计算一寸照片区域总宽高
        sm_total_width = sm_cols * small_width + (sm_cols - 1) * spacing
        sm_total_height = sm_rows * small_height + (sm_rows - 1) * spacing
        
        # 一寸照片起始位置（居中）
        sm_start_x = (page_width - sm_total_width) // 2
        sm_start_y = page_height // 4 - sm_total_height // 2  # 在页面上半部分居中
        
        # 粘贴一寸照片
        small_count_pasted = 0
        for row in range(sm_rows):
            for col in range(sm_cols):
                if small_count_pasted >= small_count:
                    break
                    
                x = sm_start_x + col * (small_width + spacing)
                y = sm_start_y + row * (small_height + spacing)
                
                layout.paste(small_photo, (x, y))
                small_count_pasted += 1
                
                # 更新进度
                if progress_callback:
                    progress = 30 + int(30 * small_count_pasted / small_count)
                    progress_callback(progress, f"一寸照片排版中... {small_count_pasted}/{small_count}")
        
        # 二寸照片布局
        lg_cols = min(3, large_count)  # 最多3列
        lg_rows = (large_count + lg_cols - 1) // lg_cols  # 计算所需行数
        
        # 计算二寸照片区域总宽高
        lg_total_width = lg_cols * large_width + (lg_cols - 1) * spacing
        lg_total_height = lg_rows * large_height + (lg_rows - 1) * spacing
        
        # 二寸照片起始位置（居中）
        lg_start_x = (page_width - lg_total_width) // 2
        lg_start_y = page_height * 3 // 4 - lg_total_height // 2  # 在页面下半部分居中
        
        # 粘贴二寸照片
        large_count_pasted = 0
        for row in range(lg_rows):
            for col in range(lg_cols):
                if large_count_pasted >= large_count:
                    break
                    
                x = lg_start_x + col * (large_width + spacing)
                y = lg_start_y + row * (large_height + spacing)
                
                layout.paste(large_photo, (x, y))
                large_count_pasted += 1
                
                # 更新进度
                if progress_callback:
                    progress = 60 + int(30 * large_count_pasted / large_count)
                    progress_callback(progress, f"二寸照片排版中... {large_count_pasted}/{large_count}")
        
        # 完成进度
        if progress_callback:
            progress_callback(100, "混合排版完成")
        
        return layout

# 修改处理按钮的样式，增加文字和背景的对比度
def set_primary_button_style(button):
    """将按钮设置为主要操作样式，增强对比度"""
    button.setStyleSheet(f"""
        background-color: #E53935;  /* 使用鲜艳的红色背景 */
        color: white;  /* 纯白色文字 */
        font-weight: bold;  /* 字体加粗 */
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        min-width: 80px;
    """) 