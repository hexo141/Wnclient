import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, 
                               QVBoxLayout, QCheckBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QColor, QPainter, QPen

# 全局变量，用于跟踪当前显示的通知数量和位置
active_notifications = []
notification_spacing = 10  # 通知之间的间距
app_instance = None  # 全局应用程序实例

# 自定义勾选框
class CustomCheckBox(QCheckBox):
    def __init__(self, is_ok=True, parent=None):
        super().__init__(parent)
        self.is_ok = is_ok
        self.setFixedSize(24, 24)
        # 移除基础样式，完全自定义绘制
        self.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 0px;
                height: 0px;
                border: none;
            }
        """)

    # 重写自身的paintEvent，完全自定义绘制
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 使用白色边框
        color = QColor("#FFFFFF")
        
        # 绘制背景和边框
        if self.isChecked():
            # 选中状态 - 填充背景
            painter.setBrush(color)
            painter.setPen(QPen(color, 2))
        else:
            # 未选中状态 - 只有边框
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(color, 2))
        
        # 绘制圆角矩形
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 4, 4)
        
        # 如果选中，绘制对勾或叉号
        if self.isChecked():
            # 绘制对勾或叉号 - 使用黑色以便在白色背景上可见
            painter.setPen(QPen(QColor("#000000"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            if self.is_ok:
                # 绘制对勾
                painter.drawLine(6, 12, 11, 17)
                painter.drawLine(11, 17, 18, 8)
            else:
                # 绘制叉号
                painter.drawLine(6, 6, 18, 18)
                painter.drawLine(18, 6, 6, 18)

class NotificationWidget(QWidget):
    def __init__(self, title="Module Toggled", description="Keystrokes has been Enabled!", 
                 duration=3000, isOK=True, parent=None):
        super().__init__(parent)
        # 窗口核心属性：无边框、置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose)  # 关闭时自动销毁
        
        # 初始化参数
        self.title_text = title
        self.desc_text = description
        self.duration = duration  # 存储显示时长
        self.isOK = isOK  # 存储状态
        
        # 初始化UI和动画
        self.init_ui()
        self.init_animation()

    def init_ui(self):
        # 设置窗口大小
        self.setFixedSize(300, 80)
        
        # 主布局（垂直）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 0)
        main_layout.setSpacing(8)
        
        # 内容区域布局（水平：勾选框 + 文本）
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # 使用自定义勾选框，根据isOK参数设置状态
        self.checkbox = CustomCheckBox(is_ok=self.isOK)
        self.checkbox.setChecked(True)
        content_layout.addWidget(self.checkbox, alignment=Qt.AlignVCenter)
        
        # 文本区域布局（垂直：标题 + 描述）
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        # 标题标签 - 白色文字
        self.title_label = QLabel(self.title_text)
        title_font = QFont("Segoe UI", 10, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #FFFFFF;")
        
        # 描述标签 - 白色文字
        self.desc_label = QLabel(self.desc_text)
        desc_font = QFont("Segoe UI", 9)
        self.desc_label.setFont(desc_font)
        self.desc_label.setStyleSheet("color: #FFFFFF;")  # 白色
        
        text_layout.addWidget(self.title_label, alignment=Qt.AlignLeft)
        text_layout.addWidget(self.desc_label, alignment=Qt.AlignLeft)
        content_layout.addLayout(text_layout)
        
        # 进度条（底部）- 使用白色
        self.progress_bar = QWidget()
        self.progress_bar.setStyleSheet("background-color: #FFFFFF; border-radius: 1px;")  # 白色
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setFixedWidth(0)  # 初始宽度为0
        
        # 添加到主布局
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignBottom | Qt.AlignLeft)
        
        # 设置窗口背景为不透明的玻璃黑效果
        self.setStyleSheet("""
            NotificationWidget {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def init_animation(self):
        # 进度条动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_progress)
        self.animation_duration = self.duration  # 使用传入的时长
        self.frame_interval = 20  # 帧率间隔（20ms）
        self.total_frames = self.animation_duration // self.frame_interval
        self.current_frame = 0
        
        # 入场动画
        self.enter_animation = QPropertyAnimation(self, b"geometry")
        self.enter_animation.setDuration(400)  # 入场动画持续400ms
        self.enter_animation.setEasingCurve(QEasingCurve.OutCubic)  # 缓动曲线

    def update_progress(self):
        self.current_frame += 1
        # 计算进度条宽度（线性增长）
        progress = self.current_frame / self.total_frames
        new_width = int(self.width() * progress)
        self.progress_bar.setFixedWidth(new_width)
        
        # 动画结束后关闭窗口
        if self.current_frame >= self.total_frames:
            self.animation_timer.stop()
            self.close()
            # 从活动通知列表中移除
            if self in active_notifications:
                active_notifications.remove(self)

    def show_notification(self):
        # 获取屏幕尺寸
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        
        # 计算目标位置（屏幕右下角，考虑其他通知的位置）
        target_x = screen_geometry.width() - self.width() - 10
        
        # 计算Y坐标：从底部开始，考虑已有通知的高度
        total_height = 0
        for notification in active_notifications:
            total_height += notification.height() + notification_spacing
            
        target_y = screen_geometry.height() - self.height() - 10 - total_height
        target_rect = QRect(target_x, target_y, self.width(), self.height())
        
        # 计算起始位置（屏幕右侧外部）
        start_x = screen_geometry.width() + 10
        start_y = target_y
        start_rect = QRect(start_x, start_y, self.width(), self.height())
        
        # 设置入场动画
        self.enter_animation.setStartValue(start_rect)
        self.enter_animation.setEndValue(target_rect)
        
        # 添加到活动通知列表
        active_notifications.append(self)
        
        # 显示窗口并启动入场动画
        self.show()
        self.enter_animation.start()
        
        # 入场动画结束后启动进度条动画
        self.enter_animation.finished.connect(
            lambda: self.animation_timer.start(self.frame_interval)
        )

# 一行调用的便捷函数
def show_notification(title="Module Toggled", description="Keystrokes has been Enabled!", 
                     duration=3000, isOK=True):
    global app_instance, active_notifications
    
    # 检查是否已有QApplication实例，如果没有则创建
    if not QApplication.instance():
        app_instance = QApplication([])  # 使用空列表而不是sys.argv
    else:
        app_instance = QApplication.instance()
    
    # 创建通知窗口
    notification = NotificationWidget(title=title, description=description, 
                                     duration=duration, isOK=isOK)
    notification.show_notification()
    
    # 只有在没有活动通知时才启动事件循环
    if len(active_notifications) == 1 and not QApplication.instance().startingUp():
        # 使用processEvents而不是exec()来避免阻塞主程序
        QApplication.instance().processEvents()

# 批量显示通知的函数
def show_multiple_notifications(notifications):
    """
    显示多个通知
    notifications: 一个包含通知参数的列表，每个元素是(title, description, duration, isOK)的元组
    """
    for title, description, duration, isOK in notifications:
        show_notification(title, description, duration, isOK)

# 独立运行时的主程序
if __name__ == "__main__":
    # 示例：同时显示多个通知
    notifications = [
        ("模块1已激活", "功能1现在已启用!", 3000, True),
        ("模块2已激活", "功能2现在已启用!", 4000, True),
        ("模块3失败", "无法启用功能3", 5000, False),
    ]
    
    show_multiple_notifications(notifications)