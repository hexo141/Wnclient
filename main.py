#  /\_/\
# ( o.o )
#  > ^ <

#  /$$      /$$                     /$$ /$$                       /$$    
# | $$  /$ | $$                    | $$|__/                      | $$    
# | $$ /$$$| $$ /$$$$$$$   /$$$$$$$| $$ /$$  /$$$$$$  /$$$$$$$  /$$$$$$  
# | $$/$$ $$ $$| $$__  $$ /$$_____/| $$| $$ /$$__  $$| $$__  $$|_  $$_/  
# | $$$$_  $$$$| $$  \ $$| $$      | $$| $$| $$$$$$$$| $$  \ $$  | $$    
# | $$$/ \  $$$| $$  | $$| $$      | $$| $$| $$_____/| $$  | $$  | $$ /$$
# | $$/   \  $$| $$  | $$|  $$$$$$$| $$| $$|  $$$$$$$| $$  | $$  |  $$$$/
# |__/     \__/|__/  |__/ \_______/|__/|__/ \_______/|__/  |__/   \___/  
                                                                       

import subprocess
import sys
try:
    import toml
    from rich.console import Console
    from rich.text import Text
    import json
    import importlib
    import sys
    import Update
    import threading
    import platform
    import os
    # PySide6 GUI 组件
    from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                                QProgressBar, QLabel, QFrame)
    from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QThread, Signal
    from PySide6.QtGui import QFont, QFontDatabase, QPixmap, QPainter, QPainterPath, QColor
except ImportError as e:
    print(f"Missing module: {e.name}. Attempting to install...")
    try:
        import uv
    except ImportError as e:
        print(e)
        if hasattr(sys, 'real_prefix'):
            print("当前在虚拟环境中,请先退出虚拟环境")
            sys.exit(0)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install uv module: {e}")
        sys.exit(1)
    else:
        print("安装完成，请重新启动脚本")
        sys.exit(0)
    try:
        if not hasattr(sys, 'real_prefix'):
            if input("您现在系统环境中运行Wnclient,我们不建议，是否继续(y/n)?").lower() == "n":
                sys.exit(0)
        subprocess.check_call(["uv","pip","install","--requirement","requirements.txt","--python",sys.executable])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)
    else:
        print("依赖安装完成，请重启应用程序。")
        print("Dependencies installed. Please restart the application.")
        sys.exit(0)
import mes
client_config = toml.load("config.toml")
class SquarePixmapLabel(QLabel):
    """自定义方形图片标签"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)  # 更紧凑的尺寸
        
    def setPixmap(self, pixmap):
        # 创建方形图片
        square_pixmap = self.create_square_pixmap(pixmap)
        super().setPixmap(square_pixmap)
        
    def create_square_pixmap(self, pixmap):
        """创建方形图片"""
        # 调整图片大小
        pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap

class ModelLoaderThread(QThread):
    """模型加载线程"""
    progress_updated = Signal(str, int, int)  # 模型名, 当前进度, 总进度
    loading_finished = Signal()  # 加载完成信号
    
    def __init__(self, conf):
        super().__init__()
        self.conf = conf
        self._dep_status = {}
        self._running_models = {}
        
    def run(self):
        """线程主函数"""
        len_models = len(self.conf['models']['enabled'])
        
        for i in range(len_models):
            model_name = self.conf['models']['enabled'][i]
            
            # 发出进度更新信号
            self.progress_updated.emit(model_name, i, len_models)
            
            json_path = f"./models/{model_name}.json"
            try:
                with open(json_path, "r") as f:
                    model_conf = json.load(f)
                # 检查平台兼容性（现在依赖和平台信息在 Wnclient 字典内）
                wn_cfg = model_conf.get("Wnclient", {})
                support_platfrom = wn_cfg.get("platforms", []) # 类型有windows, linux, darwin
                if platform.system().lower() not in support_platfrom:
                    self.progress_updated.emit(f"跳过模型: {model_name} (不支持的平台)", i, len_models)
                    for dependency in wn_cfg.get("dependence", []):
                        dep_key = dependency.lower()
                        status = self._dep_status.get(dep_key)
                        if status is True:
                            continue
                        if status is False:
                            self.progress_updated.emit(f"跳过依赖: {dependency}", i, len_models)
                            continue

                        def _is_importable(name):
                            candidates = [name, name.replace('-', '_')]
                            if name.lower() == 'pyside6':
                                candidates.insert(0, 'PySide6')
                            seen = set()
                            out = []
                            for c in candidates:
                                if c not in seen:
                                    seen.add(c)
                                    out.append(c)
                            for cand in out:
                                try:
                                    importlib.import_module(cand)
                                    return True
                                except Exception:
                                    continue
                            return False

                        if not _is_importable(dependency):
                            self.progress_updated.emit(f"缺失依赖: {dependency}", i, len_models)

                            # 暂时使用控制台进行用户输入
                            print(f"\n依赖 {dependency} 对于模型 {model_name} 缺失。")
                            if input(f"是否安装 {dependency}? (y/n): ").lower() == 'y':
                                try:
                                    subprocess.check_call(["pip", "install", dependency])
                                except subprocess.CalledProcessError as e:
                                    print(f"安装 {dependency} 失败: {e}")
                                    self._dep_status[dep_key] = False
                                    break
                                else:
                                    if _is_importable(dependency):
                                        self._dep_status[dep_key] = True
                                    else:
                                        print(f"已安装 {dependency} 但仍无法导入。")
                                        self._dep_status[dep_key] = False
                                        break
                            else:
                                self._dep_status[dep_key] = False
                                break
                        else:
                            self._dep_status[dep_key] = True
            
                # 加载模型
                mod = importlib.import_module(f"models.{model_name}")
                cls = getattr(mod, model_name)
                inst = cls()
                try:
                    result = inst.start()
                except Exception as e:
                    mes.show_notification(title="Error", description=f"Failed to start model {model_name}", duration=2000, isOK=False)
                    self.progress_updated.emit(f"模型运行错误: {model_name}", i, len_models)
                    continue

                # 如果不是单次任务，则保存实例以便后续 stop
                if result != {"Wnclient": "Single mission"}:
                    self._running_models[model_name] = inst
                else:
                    # 单次任务不保留为已运行状态，防止被 stop 或重复启动
                    try:
                        if model_name in self.conf.get('models', {}).get('enabled', []):
                            self.conf['models']['enabled'].remove(model_name)
                    except Exception:
                        pass

                # 发出加载成功信号
                self.progress_updated.emit(f"已加载: {model_name}", i, len_models)
                
            except Exception as e:
                self.progress_updated.emit(f"加载失败: {model_name}", i, len_models)
                continue
        
        # 发出完成信号
        self.progress_updated.emit("完成", len_models, len_models)
        self.loading_finished.emit()

class LoadingWindow(QWidget):
    def __init__(self, total_models):
        super().__init__()
        self.total_models = total_models
        self.current_model = 0
        self.setup_ui()
        self.setup_animation()
        
    def setup_ui(self):
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 80)  # 更紧凑的尺寸
        
        # 加载自定义字体
        font_id = QFontDatabase.addApplicationFont("./assets/AiDianFengYaHei（ShangYongMianFei）-2.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.custom_font = QFont(font_family, 10)  # 更小的字体
        else:
            self.custom_font = QFont("Microsoft YaHei", 10)
        
        # 主布局 - 水平排列
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)  # 更紧凑的边距
        main_layout.setSpacing(15)
        
        # 左侧图标 - 使用方形图片标签
        self.icon_label = SquarePixmapLabel()
        pixmap = QPixmap("./icon.png")
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # 右侧内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)  # 更紧凑的间距
        
        # 标题 - Wnclient
        title_label = QLabel("Wnclient")
        title_label.setFont(self.custom_font)
        title_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")  # 更小的字体
        
        # 进度条布局
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        
        # 黑白风格进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)  # 更细的进度条
        self.progress_bar.setMaximum(self.total_models)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #000000;
                border: 1px solid #ffffff;
            }
            QProgressBar::chunk {
                background-color: #ffffff;
                margin: 0px;
            }
        """)
        
        # 进度文本
        self.progress_text = QLabel("0%")
        self.progress_text.setFont(self.custom_font)
        self.progress_text.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        self.progress_text.setFixedWidth(30)  # 更窄的宽度
        self.progress_text.setAlignment(Qt.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_text)
        
        # 当前模型标签
        self.current_model_label = QLabel("准备加载模型...")
        self.current_model_label.setFont(self.custom_font)
        self.current_model_label.setStyleSheet("color: #ffffff; font-size: 10px;")  # 更小的字体
        
        # 添加到内容布局
        content_layout.addWidget(title_label)
        content_layout.addLayout(progress_layout)
        content_layout.addWidget(self.current_model_label)
        
        # 添加到主布局
        main_layout.addWidget(self.icon_label)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
    
    def setup_animation(self):
        # 创建进度条动画
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.progress_animation.setDuration(300)
        
        # 创建窗口位置动画
        self.position_animation = QPropertyAnimation(self, b"pos")
        self.position_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.position_animation.setDuration(400)
    
    def showEvent(self, event):
        """重写显示事件，添加入场动画"""
        super().showEvent(event)
        
        # 获取屏幕尺寸和窗口尺寸
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_size = self.size()
        
        # 计算中央位置
        center_x = (screen_geometry.width() - window_size.width()) // 2
        center_y = (screen_geometry.height() - window_size.height()) // 2
        
        # 计算底部位置（屏幕外）
        bottom_x = center_x
        bottom_y = screen_geometry.height()  # 屏幕底部
        
        # 设置初始位置在屏幕底部外
        self.move(bottom_x, bottom_y)
        
        # 设置动画：从底部移动到中央
        self.position_animation.setStartValue(QPoint(bottom_x, bottom_y))
        self.position_animation.setEndValue(QPoint(center_x, center_y))
        self.position_animation.start()
    
    def hide_with_animation(self):
        """使用动画隐藏窗口"""
        # 获取屏幕尺寸和窗口尺寸
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_size = self.size()
        
        # 计算中央位置
        center_x = (screen_geometry.width() - window_size.width()) // 2
        center_y = (screen_geometry.height() - window_size.height()) // 2
        
        # 计算底部位置（屏幕外）
        bottom_x = center_x
        bottom_y = screen_geometry.height()  # 屏幕底部
        
        # 设置动画：从中央移动到底部
        self.position_animation.setStartValue(QPoint(center_x, center_y))
        self.position_animation.setEndValue(QPoint(bottom_x, bottom_y))
        self.position_animation.start()
        
        # 动画完成后关闭窗口
        self.position_animation.finished.connect(self.close)
    
    def update_progress(self, model_name, current, total):
        self.current_model = current
        self.current_model_label.setText(f"加载: {model_name}")
        
        # 更新进度条
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(current)
        self.progress_animation.start()
        
        # 更新进度文本
        progress_percent = int((current / total) * 100)
        self.progress_text.setText(f"{progress_percent}%")
        
        # 处理事件以确保UI更新
        QApplication.processEvents()

    def on_loading_finished(self):
        """加载完成后的处理"""
        self.current_model_label.setText("所有模型加载完成!")
        QApplication.processEvents()
        
        # 延迟后使用动画隐藏窗口
        QTimer.singleShot(800, self.hide_with_animation)
    
    def paintEvent(self, event):
        # 绘制黑白风格背景和白色边框
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建矩形路径（去掉圆角）
        path = QPainterPath()
        path.addRect(0, 0, self.width(), self.height())
        
        # 填充黑色背景
        painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 178)) 
        
        # 绘制白色边框
        painter.setPen(QColor(255, 255, 255, 255))  # 白色边框
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

class cmd:
    def __init__(self):
        self.console = Console()
        self.conf = toml.load("./config.toml")
        self._dep_status = {}
        self._running_models = {}
        
        # 创建GUI应用（但不立即显示）
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.loading_window = None
        self.loader_thread = None
        
        self.loadModels()
    
    def loadModels(self):
        len_models = len(self.conf['models']['enabled'])
        
        # 创建并显示加载窗口
        self.loading_window = LoadingWindow(len_models)
        self.loading_window.show()
        
        # 确保窗口显示
        QApplication.processEvents()
        
        # 创建并启动模型加载线程
        self.loader_thread = ModelLoaderThread(self.conf)
        self.loader_thread.progress_updated.connect(self.loading_window.update_progress)
        self.loader_thread.loading_finished.connect(self.loading_window.on_loading_finished)
        
        # 添加短暂延迟，确保动画开始
        QTimer.singleShot(50, self.loader_thread.start)
    
    def cmd(self):
        print(r"""
            /\_/\
           ( o.o )
            > ^ <""")
        isExit = False
        while not isExit:
            prompt_text = Text()
            prompt_text.append("Wnclient", style="blue underline")
            prompt_text.append("> ")
            user_input = self.console.input(prompt_text)
            
            if user_input.lower() == 'exit' or user_input.lower() == 'stop':
                print("Exiting the command interface.")
                for name, inst in list(self._running_models.items()):
                    try:
                        inst.stop()
                    except Exception as e:
                        self.console.print(f"[bold red]Failed to stop model {name}: {e}[/bold red]")
                        continue
                    self.console.print(f"[bold red]Model [underline][white]{name}[/white][/underline] stopped and unloaded.[/bold red]")
                    if name in self.conf.get('models', {}).get('enabled', []):
                        try:
                            self.conf['models']['enabled'].remove(name)
                        except ValueError:
                            pass
                self._running_models.clear()
                isExit = True
            elif len(user_input.strip()) == 0:
                continue
            # 以下划线为开头的命令视为无效
            elif user_input.lower().strip()[0] == "_":
                print("Invalid command syntax.")
            else:
                try:
                    mod = importlib.import_module(f"models.{user_input}")
                except ImportError as e:
                    print(f"Model {user_input} not found: {e}")
                except SyntaxError as e:
                    print(f"Invalid command syntax: {e}")
                except Exception as e:
                    print(f"An error occurred: {e}")
                else:
                    model_conf = json.load(open(f"./models/{user_input}.json", "r"))
                    wn_cfg = model_conf.get("Wnclient", {})
                    support_platfrom = wn_cfg.get("platforms", []) # 类型有windows, linux, darwin
                    if platform.system().lower() not in support_platfrom:
                        print(f"Platform not supported for model: {user_input}")
                        continue
                    print(f"Model {user_input} executed successfully.")
                    if user_input not in self._running_models:
                        try:
                            cls = getattr(mod, user_input)
                            inst = cls()
                            mes.show_notification(title="Starting Model...", description=f"Model {user_input} is Starting...", duration=2000, isOK=True)
                            result = inst.start()

                            # 检查返回值：单次任务不加入 enabled 列表，也不保存实例
                            if result != {"Wnclient": "Single mission"}:
                                if user_input not in self.conf['models']['enabled']:
                                    self.conf['models']['enabled'].append(user_input)
                                self._running_models[user_input] = inst
                            else:
                                # 单次任务：不保存实例，直接继续
                                pass
                        except Exception as e:
                            mes.show_notification(title="Starting Model...", description=f"Failed to start model {user_input}", duration=2000, isOK=False)
                            print(f"Failed to start model {user_input}: {e}")
                    else:
                        try:
                            inst = self._running_models.pop(user_input)
                            mes.show_notification(title="Stopping Model...", description=f"Model {user_input} is stopping...", duration=2000, isOK=True)
                            inst.stop()
                            # 停止时也需要检查返回值决定是否从 enabled 列表中移除
                            if user_input in self.conf['models']['enabled']:
                                self.conf['models']['enabled'].remove(user_input)
                        except Exception as e:
                            mes.show_notification(title="Error", description=f"Failed to stop model {user_input}", duration=2000, isOK=False)
                            print(f"Failed to stop model {user_input}: {e}")
                    with open("./config.toml", "w") as f:
                        toml.dump(self.conf, f)

if __name__ == "__main__":
    # 启动更新检查线程
    if client_config.get("AutoCheckUpdate", True):
        Update_task = threading.Thread(target=Update.main)
        Update_task.start()

    command = cmd()

    command.cmd()

