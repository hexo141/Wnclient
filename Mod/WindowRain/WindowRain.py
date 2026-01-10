import sys
import random
import math
import multiprocessing
import threading
import time
import atexit
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import QTimer, QPointF, Qt, Signal, Slot, QObject, QThread
from PySide6.QtGui import QPainter, QPen, QColor

# 全局控制变量
_rain_active = False
_rain_process = None
_rain_stop_event = None

class RainDrop:
    """雨滴类"""
    __slots__ = ('x', 'y', 'length', 'speed', 'thickness', 'color', 
                 'is_splash', 'splash_particles', 'splash_lifetime', 
                 'max_splash_lifetime', 'width', 'height')
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.reset(width, height)
    
    def reset(self, width: int, height: int):
        """重置雨滴状态"""
        self.width = width
        self.height = height
        self.x = random.randint(0, width)
        self.y = random.randint(-100, 0)
        self.length = random.randint(10, 25)
        self.speed = random.uniform(5, 15)
        self.thickness = random.uniform(1, 2)
        self.color = "#4682B4"
        
        self.is_splash = False
        self.splash_particles = []
        self.splash_lifetime = 0
        self.max_splash_lifetime = 20
    
    def update(self) -> bool:
        """更新雨滴位置，返回是否继续存在"""
        if not self.is_splash:
            self.y += self.speed
            self.x += random.uniform(-0.5, 0.5)
            
            if self.y >= self.height - 10:
                self.create_splash()
                return True
            elif self.x <= 0 or self.x >= self.width:
                return False
        else:
            self.splash_lifetime += 1
            if self.splash_lifetime >= self.max_splash_lifetime:
                self.is_splash = False
                return False
            else:
                for particle in self.splash_particles:
                    particle[1] += particle[3]  # py += dy
                    particle[2] += particle[4]  # px += dx
                    particle[5] *= 0.95  # speed衰减
        
        return True
    
    def create_splash(self):
        """创建水花效果"""
        self.is_splash = True
        self.splash_lifetime = 0
        self.splash_particles = []
        
        num_particles = random.randint(3, 8)
        for _ in range(num_particles):
            angle = random.uniform(math.pi/4, 3*math.pi/4)
            speed = random.uniform(1, 5)
            dx = math.cos(angle) * speed
            dy = -math.sin(angle) * speed
            lifetime = random.randint(10, 30)
            size = random.uniform(1, 3)
            self.splash_particles.append([
                size, self.y, self.x, dy, dx, speed, lifetime
            ])


class RainEngine(QObject):
    """雨滴引擎，负责管理和更新雨滴"""
    update_needed = Signal(list)
    
    def __init__(self, width: int, height: int):
        super().__init__()
        self.width = width
        self.height = height
        
        # 雨滴参数
        self.raindrop_count = 60
        self.frame_delay = 8
        
        # 颜色选项
        self.colors = ["#4682B4", "#87CEEB", "#5F9EA0", "#6495ED", "#1E90FF"]
        
        # 雨滴列表
        self.raindrops = []
        self.init_raindrops()
        
    def init_raindrops(self):
        """初始化雨滴"""
        self.raindrops = []
        for _ in range(self.raindrop_count):
            drop = RainDrop(self.width, self.height)
            drop.color = random.choice(self.colors)
            self.raindrops.append(drop)
    
    def start_animation(self):
        """开始动画"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(self.frame_delay)
    
    @Slot()
    def update_frame(self):
        """更新动画帧"""
        rain_data = []
        for drop in self.raindrops:
            if not drop.update():
                drop.reset(self.width, self.height)
                drop.color = random.choice(self.colors)
            
            if not drop.is_splash:
                rain_data.append({
                    'type': 'drop',
                    'x': drop.x,
                    'y': drop.y,
                    'length': drop.length,
                    'color': drop.color,
                    'thickness': drop.thickness
                })
            else:
                alpha = 1.0 - (drop.splash_lifetime / drop.max_splash_lifetime)
                if alpha > 0.1:
                    for particle in drop.splash_particles:
                        size, py, px, dy, dx = particle[:5]
                        rain_data.append({
                            'type': 'splash',
                            'x': px,
                            'y': py,
                            'dx': dx * 2,
                            'dy': dy * 2,
                            'color': drop.color,
                            'size': size * alpha
                        })
        
        self.update_needed.emit(rain_data)


class RainWidget(QWidget):
    """绘制雨滴的部件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rain_data = []
        
        # 窗口设置
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
    
    @Slot(list)
    def update_rain_data(self, rain_data):
        """更新雨滴数据并重绘"""
        self.rain_data = rain_data
        self.update()
    
    def paintEvent(self, event):
        """绘制雨滴"""
        if not self.rain_data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for item in self.rain_data:
            if item['type'] == 'drop':
                pen = QPen(QColor(item['color']))
                pen.setWidthF(item['thickness'])
                painter.setPen(pen)
                painter.drawLine(
                    QPointF(item['x'], item['y']),
                    QPointF(item['x'], item['y'] + item['length'])
                )
            elif item['type'] == 'splash':
                pen = QPen(QColor(item['color']))
                pen.setWidthF(item['size'])
                painter.setPen(pen)
                painter.drawLine(
                    QPointF(item['x'], item['y']),
                    QPointF(item['x'] + item['dx'], item['y'] + item['dy'])
                )
    
    def keyPressEvent(self, event):
        """按键事件，按ESC退出"""
        if event.key() == Qt.Key_Escape:
            self.close()


class RainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # 设置窗口
        self.setWindowTitle("WindowRain")
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # 设置透明度
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建雨滴部件
        self.rain_widget = RainWidget()
        self.setCentralWidget(self.rain_widget)
        
        # 创建雨滴引擎
        self.rain_engine = RainEngine(self.screen_width, self.screen_height)
        self.rain_engine.update_needed.connect(self.rain_widget.update_rain_data)
        self.rain_engine.start_animation()
    
    def closeEvent(self, event):
        """关闭事件"""
        self.rain_engine.timer.stop()
        super().closeEvent(event)


def run_rain_window():
    """在子进程中运行Qt窗口"""
    app = QApplication([])
    
    window = RainWindow()
    window.show()
    
    app.exec()


def _safe_stop():
    """安全停止雨滴效果"""
    global _rain_active, _rain_process
    
    if not _rain_active:
        return
    
    print("Stopping rain effect...")
    
    _rain_active = False
    
    # 终止进程
    if _rain_process is not None and _rain_process.is_alive():
        _rain_process.terminate()
        _rain_process.join(timeout=1.0)
        if _rain_process.is_alive():
            _rain_process.kill()
        _rain_process = None


def WindowRain(enable=True):
    """主接口函数，与原始API兼容"""
    global _rain_active, _rain_process
    
    if enable:
        if _rain_active:
            print("It is already running.")
            return
        
        _rain_active = True
        
        # 创建并启动雨滴进程
        _rain_process = multiprocessing.Process(target=run_rain_window, daemon=True)
        _rain_process.start()
        
        # 等待进程启动
        time.sleep(0.5)
        
    else:
        # 停止雨滴效果
        _safe_stop()


def cleanup_on_exit():
    """退出时清理"""
    if _rain_active:
        WindowRain(enable=False)

atexit.register(cleanup_on_exit)


# 为了与原始代码兼容，添加这些变量
_rain_root = None  # 保持API兼容性
_rain_stop_event = None
_rain_thread = None


if __name__ == "__main__":
    # 测试代码
    WindowRain(enable=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        WindowRain(enable=False)