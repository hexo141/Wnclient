import sys
import os
import time
import threading
import inspect
from datetime import datetime
from enum import IntEnum
from typing import Any, Optional


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
        
        # 添加默认的控制台处理器
        self.add_handler(self._console_handler)
        
    def _get_caller_filename(self) -> str:
        """获取调用者的文件名"""
        try:
            # 获取调用者的栈帧
            frame = inspect.currentframe()
            # 向上查找调用者（跳过Logger内部方法）
            while frame:
                filename = os.path.basename(frame.f_code.co_filename)
                if filename != __file__:  # 不是当前文件
                    frame = None
                    return os.path.splitext(filename)[0]  # 去掉扩展名
                frame = frame.f_back
        except:
            pass
        return "unknown"
    
    def _console_handler(self, log_record: dict) -> None:
        """控制台输出处理器"""
        color_map = {
            LogLevel.DEBUG: "\033[36m",    # 青色
            LogLevel.INFO: "\033[32m",     # 绿色
            LogLevel.WARNING: "\033[33m",  # 黄色
            LogLevel.ERROR: "\033[31m",    # 红色
            LogLevel.CRITICAL: "\033[1;31m",  # 粗体红色
        }
        
        reset_color = "\033[0m"
        color = color_map.get(log_record["level"], "")
        
        print(f"{color}{log_record['formatted']}{reset_color}")
    
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
        caller_frame = None
        try:
            # 获取调用者的栈帧
            frame = inspect.currentframe()
            # 向上跳过Logger的_log方法
            frame = frame.f_back if frame else None
            # 再向上跳过debug/info/warning/error/critical方法
            frame = frame.f_back if frame else None
            
            caller_frame = frame
        except:
            pass
        
        # 构建日志记录
        log_record = {
            "timestamp": datetime.now(),
            "level": level,
            "level_name": level.name,
            "logger_name": self.name,
            "message": str(message) if args == () and kwargs == {} else str(message) % args if args else str(message),
            "process_name": threading.current_thread().name,
            "process_id": os.getpid(),
            "thread_id": threading.get_ident(),
            "filename": "unknown",
            "line_no": 0,
        }
        
        # 添加调用者文件信息
        if caller_frame:
            try:
                log_record["filename"] = os.path.basename(caller_frame.f_code.co_filename)
                log_record["line_no"] = caller_frame.f_lineno
                log_record["function"] = caller_frame.f_code.co_name
            except:
                pass
        
        # 格式化日志
        log_record["formatted"] = self._format_record(log_record)
        
        # 调用所有处理器
        for handler in self.handlers:
            try:
                handler(log_record)
            except Exception as e:
                print(f"日志处理器错误: {e}", file=sys.stderr)
    
    def _format_record(self, record: dict) -> str:
        """格式化日志记录"""
        time_str = record["timestamp"].strftime("%H:%M:%S.%f")[:-3]
        
        # 基本格式
        base_format = f"[{time_str}] [{record['level_name']:4}]"
        
        
        # 组合所有部分
        return f"{base_format} - {record['message']}"
    
    def debug(self, message: Any, *args, **kwargs) -> None:
        """记录调试信息"""
        self._log(LogLevel.DEBUG, message, *args, **kwargs)
    
    def info(self, message: Any, *args, **kwargs) -> None:
        """记录普通信息"""
        self._log(LogLevel.INFO, message, *args, **kwargs)
    
    def warning(self, message: Any, *args, **kwargs) -> None:
        """记录警告信息"""
        self._log(LogLevel.WARNING, message, *args, **kwargs)
    
    def error(self, message: Any, *args, **kwargs) -> None:
        """记录错误信息"""
        self._log(LogLevel.ERROR, message, *args, **kwargs)
    
    def critical(self, message: Any, *args, **kwargs) -> None:
        """记录严重错误信息"""
        self._log(LogLevel.CRITICAL, message, *args, **kwargs)
    
    # 为了方便替换print，提供以下方法
    def print(self, *args, **kwargs) -> None:
        """类似print的日志方法"""
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        message = sep.join(str(arg) for arg in args) + end
        self.info(message.rstrip())


# 创建默认日志器
_default_logger = None

def get_logger(name: Optional[str] = None, level: LogLevel = LogLevel.INFO) -> Logger:
    """获取日志记录器（单例模式）"""
    global _default_logger
    if _default_logger is None or (name and _default_logger.name != name):
        _default_logger = Logger(name, level)
    return _default_logger


# 快捷函数
def debug(message: Any, *args, **kwargs) -> None:
    """快捷调试日志"""
    get_logger().debug(message, *args, **kwargs)

def info(message: Any, *args, **kwargs) -> None:
    """快捷信息日志"""
    get_logger().info(message, *args, **kwargs)

def warning(message: Any, *args, **kwargs) -> None:
    """快捷警告日志"""
    get_logger().warning(message, *args, **kwargs)

def error(message: Any, *args, **kwargs) -> None:
    """快捷错误日志"""
    get_logger().error(message, *args, **kwargs)

def critical(message: Any, *args, **kwargs) -> None:
    """快捷严重错误日志"""
    get_logger().critical(message, *args, **kwargs)

def log_print(*args, **kwargs) -> None:
    """替换print的快捷函数"""
    get_logger().print(*args, **kwargs)


# 使用示例
if __name__ == "__main__":
    # 示例1: 使用默认日志器
    logger = get_logger()
    
    # 设置日志级别
    logger.set_level(LogLevel.DEBUG)
    
    # 记录不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("程序启动成功")
    logger.warning("磁盘空间不足")
    logger.error("文件读取失败")
    logger.critical("系统崩溃！")
    
    # 使用类似print的方法
    logger.print("Hello", "World", sep=", ", end="!\n")
    
    # 示例2: 使用快捷函数
    info("使用快捷函数记录信息")
    warning("使用快捷函数记录警告")
    
    # 示例3: 替换原有的print
    log_print("这条消息会以日志形式输出", "带有丰富的信息")
    
    # 示例4: 在多线程环境中使用
    def worker():
        worker_logger = get_logger("worker")
        worker_logger.info("工作线程开始执行")
        time.sleep(0.1)
        worker_logger.info("工作线程执行完成")
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, name=f"Worker-{i+1}")
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    info("所有线程执行完成")
    
    # 示例5: 添加文件处理器
    def file_handler(log_record):
        """文件输出处理器示例"""
        with open("app.log", "a", encoding="utf-8") as f:
            f.write(log_record["formatted"] + "\n")
    
    # 添加文件处理器到日志器
    logger.add_handler(file_handler)
    info("这条日志会同时输出到控制台和文件")