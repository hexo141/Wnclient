import sys
import random
import math
import threading
import time
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QApplication, QWidget


class RainDrop:
    """Single raindrop class"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.reset()
        
    def reset(self):
        """Reset raindrop position and properties"""
        self.x = random.randint(0, self.width)
        self.y = random.randint(-100, 0)
        self.length = random.randint(10, 25)
        self.speed = random.uniform(5, 15)
        self.thickness = random.uniform(1, 2)
        
        # Random selection between dark blue and light blue
        if random.random() > 0.5:
            self.color = QColor(70, 130, 180, 200)  # Steel blue (dark blue)
        else:
            self.color = QColor(135, 206, 235, 200)  # Light blue
        
        self.is_splash = False
        self.splash_particles = []
        self.splash_lifetime = 0
        self.max_splash_lifetime = 20
        
    def update(self):
        """Update raindrop position"""
        if not self.is_splash:
            self.y += self.speed
            self.x += random.uniform(-0.5, 0.5)  # Slight horizontal movement
            
            # Check if hitting boundary
            if self.y >= self.height - 10 or self.x <= 0 or self.x >= self.width:
                self.create_splash()
        else:
            self.splash_lifetime += 1
            if self.splash_lifetime >= self.max_splash_lifetime:
                self.reset()
            else:
                # Update splash particles
                for particle in self.splash_particles:
                    particle[1] += particle[3]  # Update y coordinate
                    particle[2] += particle[4]  # Update x coordinate
                    particle[5] *= 0.95  # Speed decay
                    
    def create_splash(self):
        """Create splash effect"""
        try:
            self.is_splash = True
            self.splash_lifetime = 0
            self.splash_particles = []
            
            # Create multiple splash particles
            num_particles = random.randint(3, 8)
            for _ in range(num_particles):
                angle = random.uniform(math.pi/4, 3*math.pi/4)  # Splash upwards
                speed = random.uniform(1, 5)
                dx = math.cos(angle) * speed
                dy = -math.sin(angle) * speed
                lifetime = random.randint(10, 30)
                size = random.uniform(1, 3)
                self.splash_particles.append([size, self.y, self.x, dy, dx, speed, lifetime])
        except Exception as e:
            print(f"Error creating splash: {e}")
            
    def draw(self, painter):
        """Draw raindrop or splash"""
        try:
            if not self.is_splash:
                # Draw raindrop
                pen = QPen(self.color)
                pen.setWidthF(self.thickness)
                painter.setPen(pen)
                painter.drawLine(int(self.x), int(self.y), int(self.x), int(self.y + self.length))
            else:
                # Draw splash particles
                for particle in self.splash_particles:
                    size, py, px, _, _, _, lifetime = particle
                    alpha = int(200 * (1 - self.splash_lifetime / self.max_splash_lifetime))
                    # Use same color as raindrop with decreasing opacity
                    color = QColor(self.color)
                    color.setAlpha(alpha)
                    pen = QPen(color)
                    pen.setWidthF(size)
                    painter.setPen(pen)
                    
                    # Draw small line representing splash
                    end_x = px + particle[4] * 2
                    end_y = py + particle[3] * 2
                    painter.drawLine(int(px), int(py), int(end_x), int(end_y))
        except Exception as e:
            print(f"Error drawing raindrop: {e}")


class RainWindow(QWidget):
    """Main window class"""
    # 定义一个信号，用于请求关闭窗口
    close_requested = Signal()
    
    def __init__(self):
        super().__init__()
        
        print("Initializing RainWindow")
        
        # Window settings
        self.setWindowTitle("WindowRain")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Get screen dimensions
        try:
            screen_geometry = QApplication.primaryScreen().geometry()
            self.screen_width = screen_geometry.width()
            self.screen_height = screen_geometry.height()
            print(f"Screen size: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            print(f"Error getting screen geometry: {e}")
            self.screen_width = 1920
            self.screen_height = 1080
            
        # Set window to full screen
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        
        # Raindrop related
        self.raindrops = []
        self.raindrop_count = 150  # Number of raindrops
        self.is_active = True
        
        # Initialize raindrops
        self.init_raindrops()
        
        # Use QTimer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_raindrops)
        self.timer.start(16)  # ~60FPS
        
        # Connect close_requested signal to close method
        self.close_requested.connect(self.close)
        
        # Performance monitoring
        self.frame_count = 0
        self.last_log_time = 0
        
        print("RainWindow initialized successfully")
    
    def init_raindrops(self):
        """Initialize raindrops"""
        try:
            self.raindrops = []
            for i in range(self.raindrop_count):
                raindrop = RainDrop(self.screen_width, self.screen_height)
                self.raindrops.append(raindrop)
            print(f"Initialized {self.raindrop_count} raindrops")
        except Exception as e:
            print(f"Error initializing raindrops: {e}")
    
    def update_raindrops(self):
        """Update all raindrop states"""
        try:
            if not self.is_active:
                return
                
            self.frame_count += 1
                
            for raindrop in self.raindrops:
                raindrop.update()
                
            self.update()  # Trigger repaint
        except Exception as e:
            print(f"Error updating raindrops: {e}")
            # Try to recover by resetting timer
            try:
                if self.timer.isActive():
                    self.timer.stop()
                self.timer.start(16)
            except:
                pass
    
    def paintEvent(self, event):
        """Paint event"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw all raindrops
            for raindrop in self.raindrops:
                raindrop.draw(painter)
        except Exception as e:
            print(f"Error in paintEvent: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        print("Closing RainWindow")
        self.is_active = False
        if self.timer and self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            print("Escape key pressed, closing window")
            self.close()


# 全局变量，用于存储应用实例和线程
_rain_app = None
_rain_thread = None
_rain_window = None
_rain_app_running = False


def _run_qt_app():
    """在独立线程中运行Qt应用的函数"""
    global _rain_app, _rain_window, _rain_app_running
    
    try:
        # 创建QApplication实例
        _rain_app = QApplication(sys.argv)
        _rain_app_running = True
        
        # 创建窗口
        _rain_window = RainWindow()
        _rain_window.show()
        
        print("Rain window started in separate thread")
        
        # 运行Qt事件循环
        _rain_app.exec()
        
    except Exception as e:
        print(f"Error in Qt application: {e}")
    finally:
        # 确保资源被清理
        _rain_app_running = False
        _rain_app = None
        _rain_window = None
        print("Qt application thread finished")


def WindowRain(enable=True):
    """控制雨滴效果的主函数"""
    global _rain_app, _rain_thread, _rain_window, _rain_app_running
    
    if enable:
        if _rain_thread is not None and _rain_thread.is_alive():
            print("Rain effect is already running")
            return
            
        print("Starting rain effect in background thread")
        
        # 创建一个新的线程来运行Qt应用
        _rain_thread = threading.Thread(target=_run_qt_app, daemon=True)
        _rain_thread.start()
        
        # 等待一段时间确保Qt应用启动
        for i in range(10):
            if _rain_app_running:
                break
            time.sleep(0.1)
        
        print("Rain effect started. Press ESC in the rain window to close.")
        
    else:
        print("Stopping rain effect")
        
        # 尝试关闭窗口
        if _rain_window is not None:
            try:
                # 使用信号/槽机制安全地关闭窗口（线程安全）
                _rain_window.close_requested.emit()
                print("Close request emitted")
            except Exception as e:
                print(f"Error emitting close signal: {e}")
        
        # 等待一段时间让窗口关闭
        if _rain_thread is not None and _rain_thread.is_alive():
            print("Waiting for Qt thread to finish...")
            # 等待最多2秒
            for i in range(20):
                if not _rain_thread.is_alive():
                    break
                time.sleep(0.1)
            
            if _rain_thread.is_alive():
                print("Qt thread still alive, but will exit as daemon when main program exits")
        
        # 重置全局变量
        _rain_app = None
        _rain_thread = None
        _rain_window = None
        
        print("Rain effect stopped")


# 为了方便使用，可以添加一个简单的清理函数
def cleanup():
    """清理函数，用于程序退出时确保资源被释放"""
    WindowRain(enable=False)


if __name__ == "__main__":
    import atexit
    
    # 注册清理函数
    atexit.register(cleanup)
    
    WindowRain(enable=True)
    
    # 添加一个简单的命令行界面来测试关闭功能
    try:
        while True:
            cmd = input("\nEnter 'stop' to stop rain effect, 'start' to start, or 'exit' to quit: ").strip().lower()
            if cmd == 'stop':
                WindowRain(enable=False)
            elif cmd == 'start':
                WindowRain(enable=True)
            elif cmd == 'exit':
                WindowRain(enable=False)
                break
            else:
                print("Unknown command")
    except KeyboardInterrupt:
        print("\nProgram interrupted, cleaning up...")
        WindowRain(enable=False)