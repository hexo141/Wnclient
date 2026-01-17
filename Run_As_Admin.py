import ctypes
import platform
import lwjgl
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def Run_As_Admin(command=""):
    if platform.system() == 'Windows':
        if not is_admin():
            res_code = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, os.path.join(os.path.dirname(__file__),"main.py") + f" {command}", None, 1)
            if res_code <= 32:
                lwjgl.error(f"Failed to elevate power, return: {res_code}")
            else:
                exit()
    else:
        lwjgl.error("It can only run on Windows")

if __name__ == "__main__":
    Run_As_Admin()