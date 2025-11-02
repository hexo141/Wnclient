import tqdm
import toml
from rich.console import Console
from rich.text import Text
import json
import subprocess
import importlib
import importlib.util
import sys
import os

# PySide6 GUI 组件
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QProgressBar, QLabel, QFrame)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QFontDatabase, QPixmap, QPainter, QPainterPath, QColor

class RoundedPixmapLabel(QLabel):
    """自定义圆角图片标签"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        
    def setPixmap(self, pixmap):
        # 创建圆角图片
        rounded_pixmap = self.create_rounded_pixmap(pixmap, 10)  # 10px圆角
        super().setPixmap(rounded_pixmap)
        
    def create_rounded_pixmap(self, pixmap, radius):
        """创建圆角图片"""
        # 调整图片大小
        pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 创建透明背景的图片
        rounded = QPixmap(self.size())
        rounded.fill(Qt.transparent)
        
        # 绘制圆角图片
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        painter.setClipPath(path)
        
        # 绘制图片
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        return rounded

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
        self.setFixedSize(500, 120)
        
        # 加载自定义字体
        font_id = QFontDatabase.addApplicationFont("./assets/AiDianFengYaHei（ShangYongMianFei）-2.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.custom_font = QFont(font_family, 12)
        else:
            self.custom_font = QFont("Microsoft YaHei", 12)
        
        # 主布局 - 水平排列
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 左侧图标 - 使用圆角图片标签
        self.icon_label = RoundedPixmapLabel()
        pixmap = QPixmap("./icon.png")
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # 右侧内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        # 标题 - Wnclient
        title_label = QLabel("Wnclient")
        title_label.setFont(self.custom_font)
        title_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        
        # 进度条布局
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)
        
        # 白色进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setMaximum(self.total_models)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(80, 80, 80, 200);
                border: 1px solid #666666;
                border-radius: 10px;
            }
            QProgressBar::chunk {
                background-color: #ffffff;
                border-radius: 9px;
                margin: 1px;
            }
        """)
        
        # 进度文本
        self.progress_text = QLabel("0%")
        self.progress_text.setFont(self.custom_font)
        self.progress_text.setStyleSheet("color: #cccccc; font-size: 14px; font-weight: bold;")
        self.progress_text.setFixedWidth(40)
        self.progress_text.setAlignment(Qt.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_text)
        
        # 当前模型标签
        self.current_model_label = QLabel("准备加载模型...")
        self.current_model_label.setFont(self.custom_font)
        self.current_model_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        
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
        self.animation = QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(300)
    
    def update_progress(self, model_name, current, total):
        self.current_model = current
        self.current_model_label.setText(f"加载: {model_name}")
        
        # 更新进度条
        self.animation.setStartValue(self.progress_bar.value())
        self.animation.setEndValue(current)
        self.animation.start()
        
        # 更新进度文本
        progress_percent = int((current / total) * 100)
        self.progress_text.setText(f"{progress_percent}%")
        
        # 处理事件以确保UI更新
        QApplication.processEvents()
    
    def paintEvent(self, event):
        # 绘制半透明黑色背景和边框
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        # 填充半透明黑色背景
        painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(30, 30, 30, 230))
        
        # 绘制边框
        painter.setPen(QColor(80, 80, 80, 255))
        painter.drawPath(path)

class cmd:
    def __init__(self):
        self.console = Console()
        self.conf = toml.load("./config.toml")
        self._dep_status = {}
        self._running_models = {}
        
        # 创建GUI应用（但不立即显示）
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.loading_window = None
        
        self.loadModels()
    
    def loadModels(self):
        len_models = len(self.conf['models']['enabled'])
        
        # 创建并显示加载窗口
        self.loading_window = LoadingWindow(len_models)
        self.loading_window.show()
        
        # 确保窗口显示
        QApplication.processEvents()
        
        for i in range(len_models):
            model_name = self.conf['models']['enabled'][i]
            
            # 更新GUI进度
            self.loading_window.update_progress(model_name, i, len_models)
            
            json_path = f"./models/{model_name}.json"
            with open(json_path, "r") as f:
                model_conf = json.load(f)
                for dependency in model_conf.get("dependence", []):
                    dep_key = dependency.lower()
                    status = self._dep_status.get(dep_key)
                    if status is True:
                        continue
                    if status is False:
                        self.loading_window.current_model_label.setText(f"跳过依赖: {dependency}")
                        QApplication.processEvents()
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
                        self.loading_window.current_model_label.setText(f"缺失依赖: {dependency}")
                        QApplication.processEvents()
                        
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
            try:
                mod = importlib.import_module(f"models.{model_name}")
                cls = getattr(mod, model_name)
                inst = cls()
                inst.start()
                self._running_models[model_name] = inst
                
                # 更新GUI显示加载成功
                self.loading_window.current_model_label.setText(f"已加载: {model_name}")
                QApplication.processEvents()
                
            except Exception as e:
                self.loading_window.current_model_label.setText(f"加载失败: {model_name}")
                QApplication.processEvents()
                continue
        
        # 完成加载，关闭窗口
        self.loading_window.update_progress("完成", len_models, len_models)
        self.loading_window.current_model_label.setText("所有模型加载完成!")
        QApplication.processEvents()
        
        # 延迟关闭窗口
        QTimer.singleShot(800, self.loading_window.close)
    
    def cmd(self):
        # 原有cmd方法保持不变
        isExit = False
        while not isExit:
            prompt_text = Text()
            prompt_text.append("Wnclient", style="blue underline")
            prompt_text.append("> ")
            user_input = self.console.input(prompt_text)
            
            if user_input.lower() == 'exit':
                print("Exiting the command interface.")
                for name, inst in list(self._running_models.items()):
                    try:
                        inst.stop()
                    except Exception as e:
                        self.console.print(f"[bold red]Failed to stop model {name}: {e}[/bold red]")
                        continue
                    self.console.print(f"[bold red]Model {name} stopped and unloaded.[/bold red]")
                    if name in self.conf.get('models', {}).get('enabled', []):
                        try:
                            self.conf['models']['enabled'].remove(name)
                        except ValueError:
                            pass
                self._running_models.clear()
                isExit = True
            elif len(user_input.strip()) == 0:
                continue
            else:
                try:
                    mod = importlib.import_module(f"models.{user_input}")
                except ImportError:
                    print(f"Model {user_input} not found.")
                except SyntaxError:
                    print("Invalid command syntax.")
                except Exception as e:
                    print(f"An error occurred: {e}")
                else:
                    print(f"Model {user_input} executed successfully.")
                    if user_input not in self._running_models:
                        try:
                            cls = getattr(mod, user_input)
                            inst = cls()
                            inst.start()
                            self._running_models[user_input] = inst
                            if user_input not in self.conf['models']['enabled']:
                                self.conf['models']['enabled'].append(user_input)
                        except Exception as e:
                            print(f"Failed to start model {user_input}: {e}")
                    else:
                        try:
                            inst = self._running_models.pop(user_input)
                            inst.stop()
                            if user_input in self.conf['models']['enabled']:
                                self.conf['models']['enabled'].remove(user_input)
                        except Exception as e:
                            print(f"Failed to stop model {user_input}: {e}")
                    with open("./config.toml", "w") as f:
                        toml.dump(self.conf, f)

if __name__ == "__main__":
    command = cmd()
    command.cmd()
