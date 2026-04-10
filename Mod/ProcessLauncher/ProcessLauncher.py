#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProcessLauncher.py - Capture console output from target executable on Windows.
Usage:
    python ProcessLauncher.py [target.exe] [arguments...]
    python ProcessLauncher.py                 (opens file selection dialog)
"""

import sys
import os
import subprocess
import threading
import time
import signal
from datetime import datetime
from typing import Optional, List

# Attempt to import GUI modules for file dialog
try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

# Enable ANSI escape sequences on Windows 10+
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    # Also try to enable virtual terminal processing
    try:
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 
                                kernel32.GetConsoleMode(kernel32.GetStdHandle(-11)) | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except:
        pass

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    # Fallback for older terminals
    @staticmethod
    def disable():
        Colors.RED = Colors.GREEN = Colors.YELLOW = Colors.CYAN = Colors.WHITE = Colors.RESET = ''

# Global state
g_process: Optional[subprocess.Popen] = None
g_running = True

def log(level: str, message: str) -> None:
    """Print a formatted log message with timestamp and color."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = Colors.WHITE
    if level == "INFO":
        color = Colors.GREEN
    elif level == "WARN":
        color = Colors.YELLOW
    elif level == "ERROR":
        color = Colors.RED
    elif level == "DEBUG":
        color = Colors.CYAN
    print(f"{color}[{level}]{Colors.RESET} [{timestamp}] {message}")

def log_target(stream: str, message: str) -> None:
    """Print output from the target process."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = Colors.GREEN if stream == "STDOUT" else Colors.RED
    # Strip trailing newline to avoid double spacing, we'll add our own
    msg = message.rstrip('\n\r')
    print(f"{color}[TARGET:{stream}]{Colors.RESET} [{timestamp}] {msg}")

def select_exe_file() -> Optional[str]:
    """Open a file selection dialog and return the chosen .exe path."""
    if not TK_AVAILABLE:
        log("ERROR", "tkinter not available for file dialog. Please specify target.exe as command line argument.")
        return None
    
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)
    
    file_path = filedialog.askopenfilename(
        title="Select target executable",
        filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
    )
    root.destroy()
    
    if file_path:
        log("INFO", f"Selected: {file_path}")
    return file_path if file_path else None

def signal_handler(sig, frame):
    """Handle Ctrl+C to terminate child process."""
    global g_running, g_process
    log("INFO", "Received interrupt signal, terminating child process...")
    g_running = False
    if g_process and g_process.poll() is None:
        g_process.terminate()
        try:
            g_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            g_process.kill()
    sys.exit(0)

def read_pipe(pipe, stream_name: str) -> None:
    """Read lines from a pipe and log them."""
    global g_running
    for line in iter(pipe.readline, ''):
        if not g_running:
            break
        if line:
            log_target(stream_name, line)
    pipe.close()

def monitor_process(proc: subprocess.Popen) -> None:
    """Wait for process to exit and log exit code."""
    global g_running
    proc.wait()
    log("INFO", f"Target process exited with code: {proc.returncode}")
    g_running = False

def show_help() -> None:
    """Display usage help."""
    print(f"\n{Colors.GREEN}ProcessLauncher v1.0 (Python){Colors.RESET} - Capture console output from target executable\n")
    print("Usage:")
    print("  python ProcessLauncher.py <target.exe> [arguments]")
    print("  python ProcessLauncher.py                         (Select file via dialog)\n")
    print("Examples:")
    print("  python ProcessLauncher.py ping.exe 127.0.0.1 -t")
    print("  python ProcessLauncher.py cmd.exe /c dir\n")
    print(f"{Colors.YELLOW}Note: This tool captures console output from console applications.")
    print("      Press Ctrl+C to terminate the monitored process.\n")

def main() -> int:
    global g_process, g_running
    
    # Set up signal handler for graceful termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGBREAK, signal_handler)  # Windows Ctrl+Break
    
    # Set console title (Windows only)
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleW("ProcessLauncher - Target Output Viewer")
    
    log("INFO", "ProcessLauncher started")
    
    # Parse arguments
    target_exe = None
    target_args: List[str] = []
    
    if len(sys.argv) < 2:
        show_help()
        log("INFO", "No target specified, opening file selection dialog...")
        target_exe = select_exe_file()
        if not target_exe:
            log("ERROR", "No file selected, exiting")
            return 1
    else:
        target_exe = sys.argv[1]
        target_args = sys.argv[2:]
        
        log("INFO", f"Target: {target_exe}")
        if target_args:
            log("INFO", f"Arguments: {' '.join(target_args)}")
    
    # Verify file exists
    if not os.path.isfile(target_exe):
        log("ERROR", f"Target executable not found: {target_exe}")
        return 1
    
    # Prepare command line
    cmd = [target_exe] + target_args
    
    try:
        # Start process with pipes for stdout/stderr
        g_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,  # Line buffered
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            cwd=os.path.dirname(target_exe) or None
        )
    except Exception as e:
        log("ERROR", f"Failed to start process: {e}")
        return 1
    
    log("INFO", f"Target process started with PID: {g_process.pid}")
    log("INFO", "Capturing output from target process...")
    log("INFO", "-" * 40)
    
    # Create threads to read stdout and stderr
    stdout_thread = threading.Thread(target=read_pipe, args=(g_process.stdout, "STDOUT"))
    stderr_thread = threading.Thread(target=read_pipe, args=(g_process.stderr, "STDERR"))
    monitor_thread = threading.Thread(target=monitor_process, args=(g_process,))
    
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    monitor_thread.daemon = True
    
    stdout_thread.start()
    stderr_thread.start()
    monitor_thread.start()
    
    # Wait for threads (they will exit when process terminates or Ctrl+C)
    try:
        while g_running and g_process.poll() is None:
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    # Wait for threads to finish (give them a moment)
    stdout_thread.join(timeout=1)
    stderr_thread.join(timeout=1)
    monitor_thread.join(timeout=1)
    
    log("INFO", "-" * 40)
    log("INFO", "ProcessLauncher finished")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())