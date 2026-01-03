import tkinter as tk
import random
import math
import threading
import time
import queue
import sys
from typing import List

# 全局变量用于线程控制
_rain_active = False
_command_queue = queue.Queue()
_rain_lock = threading.Lock()

class HighPerformanceRain:
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # 性能优化参数
        self.raindrop_count = 78 # 雨滴数量
        self.fps = 25
        self.frame_delay = 10
        
        # 预计算的颜色值
        self.colors = ["#4682B4", "#87CEEB", "#5F9EA0", "#6495ED", "#1E90FF"]
        
        # 预计算的几何数据
        self.angle_range = (math.pi/4, 3*math.pi/4)
        
        # 初始化雨滴
        self.raindrops: List[RainDrop] = []
        self.init_raindrops()
        
        # 性能监控
        self.frame_count = 0
        self.last_time = time.time()
        
    def init_raindrops(self):
        """初始化雨滴数组"""
        self.raindrops = []
        for _ in range(self.raindrop_count):
            drop = RainDrop(self.width, self.height)
            drop.color = random.choice(self.colors)
            self.raindrops.append(drop)
    
    def update_and_draw(self, canvas: tk.Canvas) -> List[int]:
        """更新并绘制雨滴，返回绘制的对象ID列表"""
        item_ids = []
        
        for drop in self.raindrops:
            if not drop.update():
                drop.reset(self.width, self.height)
                drop.color = random.choice(self.colors)
            
            if not drop.is_splash:
                # 绘制直线雨滴 - 使用create_line
                item_id = canvas.create_line(
                    drop.x, drop.y,
                    drop.x, drop.y + drop.length,
                    fill=drop.color,
                    width=drop.thickness
                )
                item_ids.append(item_id)
            else:
                # 绘制溅射效果
                alpha = 1.0 - (drop.splash_lifetime / drop.max_splash_lifetime)
                if alpha > 0.1:
                    for particle in drop.splash_particles:
                        size, py, px, dy, dx, speed, lifetime = particle
                        end_x = px + dx * 2
                        end_y = py + dy * 2
                        
                        item_id = canvas.create_line(
                            px, py, end_x, end_y,
                            fill=drop.color,
                            width=size * alpha
                        )
                        item_ids.append(item_id)
        
        return item_ids

class RainDrop:
    """优化的雨滴类"""
    
    __slots__ = ('x', 'y', 'length', 'speed', 'thickness', 'color', 
                 'is_splash', 'splash_particles', 'splash_lifetime', 
                 'max_splash_lifetime', 'width', 'height')
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.reset(width, height)
    
    def reset(self, width: int, height: int):
        """重置雨滴"""
        self.width = width
        self.height = height
        self.x = random.randint(0, width)
        self.y = random.randint(-100, 0)
        self.length = random.randint(10, 25)
        self.speed = random.uniform(5, 15)
        self.thickness = random.uniform(1, 2)
        self.color = "#4682B4"  # 默认颜色
        
        self.is_splash = False
        self.splash_particles: List[List] = []
        self.splash_lifetime = 0
        self.max_splash_lifetime = 20
    
    def update(self) -> bool:
        if not self.is_splash:
            self.y += self.speed
            self.x += random.uniform(-0.5, 0.5)
            
            # 检查边界
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
                # 更新溅射粒子
                for particle in self.splash_particles:
                    particle[1] += particle[3]  # y
                    particle[2] += particle[4]  # x
                    particle[5] *= 0.95  # 速度衰减
        
        return True
    
    def create_splash(self):
        self.is_splash = True
        self.splash_lifetime = 0
        self.splash_particles = []
        
        # 创建溅射粒子
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

class OptimizedRainCanvas:
    
    def __init__(self, root: tk.Tk, width: int, height: int):
        self.root = root
        self.width = width
        self.height = height
        
        # 创建主画布
        self.canvas = tk.Canvas(
            root,
            width=width,
            height=height,
            highlightthickness=0,
            bg='black'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 创建雨滴引擎
        self.rain_engine = HighPerformanceRain(width, height)
        
        # 绑定事件
        self.canvas.bind("<Escape>", self.close_window)
        self.canvas.focus_set()
        
        # 性能优化：批量删除
        self.current_items = []
        
        # 启动动画
        self.is_running = True
        self.animate()
    
    def animate(self):
        """动画循环"""
        if not _rain_active or not self.is_running:
            return
        
        # 清空上一帧的图形
        if self.current_items:
            self.canvas.delete(*self.current_items)
            self.current_items.clear()
        
        # 更新并绘制新帧
        self.current_items = self.rain_engine.update_and_draw(self.canvas)
        
        # 限制项目数量，防止内存泄漏
        if len(self.current_items) > 500:
            self.canvas.delete(*self.current_items[:100])
            self.current_items = self.current_items[100:]
        
        # 调度下一帧
        self.root.after(self.rain_engine.frame_delay, self.animate)
    
    def close_window(self, event=None):
        """关闭窗口"""
        global _rain_active
        with _rain_lock:
            _rain_active = False
        self.is_running = False
        self.root.destroy()

def create_rain_window():
    """创建并运行雨滴窗口"""
    global _rain_active
    
    with _rain_lock:
        _rain_active = True
    
    # 创建主窗口
    root = tk.Tk()
    root.title("WindowRain - Optimized")
    
    # 获取屏幕尺寸
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # 窗口配置
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    
    # 透明度设置
    if sys.platform.startswith('win'):
        root.attributes('-transparentcolor', 'black')
    elif sys.platform.startswith('darwin'):
        root.attributes('-alpha', 0.99)
    else:
        root.attributes('-alpha', 0.95)
    
    # 创建优化的雨滴画布
    rain_canvas = OptimizedRainCanvas(root, screen_width, screen_height)
    
    # 开始主循环
    try:
        root.mainloop()
    except Exception as e:
        print(f"主循环错误: {e}")
    finally:
        with _rain_lock:
            _rain_active = False

def WindowRain(enable=True):
    global _rain_thread, _rain_active
    
    if enable:
        with _rain_lock:
            if _rain_active:
                print("雨滴效果已经在运行")
                return
        
        print("启动雨滴效果...")
        
        # 创建并启动雨滴线程
        _rain_thread = threading.Thread(target=create_rain_window, daemon=True)
        _rain_thread.start()
        
        time.sleep(0.5)
    else:
        with _rain_lock:
            if not _rain_active:
                return
        
        print("停止雨滴效果...")
        _rain_active = False
        
        if _rain_thread and _rain_thread.is_alive():
            _rain_thread.join(timeout=2.0)
        
        print("雨滴效果已停止。")

def cleanup():
    """清理函数"""
    global _rain_active
    with _rain_lock:
        _rain_active = False
    
    if _rain_thread and _rain_thread.is_alive():
        _rain_thread.join(timeout=2.0)
