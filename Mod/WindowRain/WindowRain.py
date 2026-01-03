import tkinter as tk
import random
import math
import threading
import time
import sys
import atexit

# 全局控制变量
_rain_active = False
_rain_stop_event = threading.Event()
_rain_thread = None
_rain_root = None

class HighPerformanceRain:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        

        self.raindrop_count = 60
        self.frame_delay = 8
        

        self.colors = ["#4682B4", "#87CEEB", "#5F9EA0", "#6495ED", "#1E90FF"]
        

        self.raindrops = []
        self.init_raindrops()
        
    def init_raindrops(self):
        self.raindrops = []
        for _ in range(self.raindrop_count):
            drop = RainDrop(self.width, self.height)
            drop.color = random.choice(self.colors)
            self.raindrops.append(drop)
    
    def update_and_draw(self, canvas: tk.Canvas):
        item_ids = []
        
        for drop in self.raindrops:
            if not drop.update():
                drop.reset(self.width, self.height)
                drop.color = random.choice(self.colors)
            
            if not drop.is_splash:
                item_id = canvas.create_line(
                    drop.x, drop.y,
                    drop.x, drop.y + drop.length,
                    fill=drop.color,
                    width=drop.thickness
                )
                item_ids.append(item_id)
            else:
                alpha = 1.0 - (drop.splash_lifetime / drop.max_splash_lifetime)
                if alpha > 0.1:
                    for particle in drop.splash_particles:
                        size, py, px, dy, dx = particle[:5]
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
    
    __slots__ = ('x', 'y', 'length', 'speed', 'thickness', 'color', 
                 'is_splash', 'splash_particles', 'splash_lifetime', 
                 'max_splash_lifetime', 'width', 'height')
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.reset(width, height)
    
    def reset(self, width: int, height: int):

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

class RainCanvas:
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
        
        # 绑定退出键
        self.canvas.bind("<Escape>", lambda e: _rain_stop_event.set())
        self.canvas.focus_set()
        
        # 当前显示的图形项
        self.current_items = []
        
        # 启动动画
        self.animate()
    
    def animate(self):
        """动画循环"""
        # 检查是否需要停止
        if _rain_stop_event.is_set():
            self.cleanup()
            return
        
        try:
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
            
        except tk.TclError:
            pass  # Tkinter已经关闭，正常退出
        except Exception as e:
            print(f"动画循环异常: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.current_items:
                self.canvas.delete(*self.current_items)
                self.current_items.clear()
        except tk.TclError:
            pass  # 画布已销毁

def create_rain_window():
    """创建并运行雨滴窗口"""
    global _rain_root
    
    try:
        # 创建主窗口
        root = tk.Tk()
        _rain_root = root
        
        # 获取屏幕尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 窗口配置
        root.title("WindowRain")
        root.geometry(f"{screen_width}x{screen_height}+0+0")
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        
        # 透明度设置
        if sys.platform.startswith('win'):
            root.attributes('-transparentcolor', 'black')
        else:
            root.attributes('-alpha', 0.95)
        

        def on_closing():
            _rain_stop_event.set()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        

        RainCanvas(root, screen_width, screen_height)
        root.mainloop()
        
    except Exception as e:
        print(e)
    finally:
        # 确保清理
        try:
            if _rain_root and _rain_root.winfo_exists():
                _rain_root.destroy()
        except:
            pass
        finally:
            _rain_root = None

def _safe_stop():
    global _rain_active, _rain_thread
    
    if not _rain_active:
        return
    
    print("Stopping rain effect...")
    
    # 设置停止事件
    _rain_stop_event.set()
    _rain_active = False
    
    # 等待线程结束
    if _rain_thread and _rain_thread.is_alive():
        _rain_thread.join(timeout=1.0)

def WindowRain(enable=True):
    global _rain_active, _rain_thread
    
    if enable:
        if _rain_active:
            print("It is already running.")
            return
        
        # 重置停止事件
        _rain_stop_event.clear()
        _rain_active = True
        
        print("启动雨滴效果...")
        
        # 创建并启动雨滴线程
        _rain_thread = threading.Thread(target=create_rain_window, daemon=True)
        _rain_thread.start()
        
        # 等待窗口创建完成
        for _ in range(30):  # 最多等待3秒
            if _rain_root is not None:
                break
            time.sleep(0.1)
        
    else:
        # 在主线程中调用安全停止
        _safe_stop()

# 注册退出时的清理函数
def cleanup_on_exit():
    """程序退出时清理资源"""
    if _rain_active:
        WindowRain(enable=False)

atexit.register(cleanup_on_exit)

