import os
import threading
import inspect
from datetime import datetime
from enum import IntEnum
from typing import Any, Optional
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.highlighter import NullHighlighter


class LogLevel(IntEnum):
    """日志级别"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logger:
    """日志记录器"""
    
    def __init__(self, name: Optional[str] = None, level: LogLevel = LogLevel.INFO):
        """
        初始化日志记录器
        
        Args:
            name: 日志器名称，如果为None则使用调用者的文件名
            level: 日志级别，低于此级别的日志不会被记录
        """
        self.name = name or self._get_caller_filename()
        self.level = level
        self.handlers = []
        self.console = Console(highlighter=NullHighlighter())
        
        # 添加默认的控制台处理器
        self.add_handler(self._console_handler)
        
    def _get_caller_filename(self) -> str:
        """获取调用者的文件名"""
        try:
            frame = inspect.currentframe()
            while frame:
                filename = os.path.basename(frame.f_code.co_filename)
                if filename != __file__:
                    return os.path.splitext(filename)[0]
                frame = frame.f_back
        except:
            pass
        return "unknown"
    
    def _console_handler(self, log_record: dict) -> None:
        """控制台输出处理器"""
        level_styles = {
            LogLevel.DEBUG: "cyan",
            LogLevel.INFO: "green",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red",
        }
        
        time_str = log_record["timestamp"].strftime("%H:%M:%S.%f")[:-3]
        level_name = log_record["level_name"]
        message = log_record["message"]
        
        # 创建带样式的文本
        text = Text()
        text.append(f"[{time_str}] ", style="dim")
        text.append(f"[{level_name:^7}] ", style=level_styles.get(log_record["level"], ""))
        text.append(message)


        self.console.print(text)
    
    def add_handler(self, handler) -> None:
        """添加日志处理器"""
        self.handlers.append(handler)
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        self.level = level
    
    def _log(self, level: LogLevel, message: Any, *args, **kwargs) -> None:
        """记录日志的内部方法"""
        if level < self.level:
            return
        
        # 获取调用者信息
        caller_info = {}
        try:
            frame = inspect.currentframe().f_back.f_back  # 跳过两层调用栈
            if frame:
                caller_info["filename"] = os.path.basename(frame.f_code.co_filename)
                caller_info["line_no"] = frame.f_lineno
                caller_info["function"] = frame.f_code.co_name
        except:
            pass
        
        # 构建日志记录
        log_record = {
            "timestamp": datetime.now(),
            "level": level,
            "level_name": level.name,
            "logger_name": self.name,
            "message": str(message) if not args and not kwargs else 
                      str(message) % args if args else str(message),
            "process_id": os.getpid(),
            "thread_id": threading.get_ident(),
            **caller_info
        }
        
        # 调用所有处理器
        for handler in self.handlers:
            try:
                handler(log_record)
            except Exception as e:
                self.console.print(f"日志处理器错误: {e}", style="red")
    
    def debug(self, message: Any, *args, **kwargs) -> None:
        self._log(LogLevel.DEBUG, message, *args, **kwargs)
    
    def info(self, message: Any, *args, **kwargs) -> None:
        self._log(LogLevel.INFO, message, *args, **kwargs)
    
    def warning(self, message: Any, *args, **kwargs) -> None:
        self._log(LogLevel.WARNING, message, *args, **kwargs)
    
    def error(self, message: Any, *args, **kwargs) -> None:
        self._log(LogLevel.ERROR, message, *args, **kwargs)
    
    def critical(self, message: Any, *args, **kwargs) -> None:
        self._log(LogLevel.CRITICAL, message, *args, **kwargs)
    
    def print(self, *args, **kwargs) -> None:
        """类似print的日志方法"""
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        message = sep.join(str(arg) for arg in args) + end
        self.info(message.rstrip())


# 单例日志器管理
_default_logger = None

def get_logger(name: Optional[str] = None, level: LogLevel = LogLevel.INFO) -> Logger:
    """获取日志记录器"""
    global _default_logger
    if _default_logger is None or (name and _default_logger.name != name):
        _default_logger = Logger(name, level)
    return _default_logger


# 快捷函数
def debug(message: Any, *args, **kwargs) -> None:
    get_logger().debug(message, *args, **kwargs)

def info(message: Any, *args, **kwargs) -> None:
    get_logger().info(message, *args, **kwargs)

def warning(message: Any, *args, **kwargs) -> None:
    get_logger().warning(message, *args, **kwargs)

def error(message: Any, *args, **kwargs) -> None:
    get_logger().error(message, *args, **kwargs)

def critical(message: Any, *args, **kwargs) -> None:
    get_logger().critical(message, *args, **kwargs)

def log_print(*args, **kwargs) -> None:
    get_logger().print(*args, **kwargs)
