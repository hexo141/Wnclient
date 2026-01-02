import tkinter
import json
import subprocess
import tkinter.filedialog
import os
import lwjgl

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass  # 旧版Windows不支持，忽略

def StartGame(UseJson=True, GamePath="", UseTouch=False):
    if UseJson:
        lwjgl.info("Loading configuration from config.json")
        with open('Mod/StartMHY/config.json', 'r') as f:
            config = json.load(f)
            GamePath = config.get("GamePath", "")
            UseTouch = config.get("UseTouch", False)
    if not os.path.exists(GamePath):
        # 让tk选择游戏路径
        root = tkinter.Tk()
        root.withdraw()
        GamePath = tkinter.filedialog.askopenfilename(title="Select Genshin Impact Executable", filetypes=[("Executable Files", "*.exe")])
        root.destroy()
    if UseTouch:
        subprocess.Popen([GamePath, "use_moblie_platform", "-iscloud", "1", "-platform_type", "CLOUD_MOBILE"],start_new_session=True)
    else:
        subprocess.Popen([GamePath],start_new_session=True)