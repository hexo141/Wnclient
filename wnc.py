import json
import tkinter as tk
import lwjgl
import os
import subprocess
import sys
from tkinter import messagebox
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    # dpi 设置
except Exception as e:
    lwjgl.error(f"DPI setting failed: {e}")
def set_auto_use(mod_name, func , param):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    with open("set_auto_use.json", "r") as f:
        set_auto_use_data = json.loads(f.read())
        if "nocancel" in set_auto_use_data:
            if set_auto_use_data["nocancel"].get(mod_name, 0) == -1:
                return False
    if messagebox.askyesno("Select", f"{mod_name} wants to set auto use for {func} with parameters {param}. Do you allow this?"):
        try:
            with open("AutoUse.json", "r") as f:
                auto_use_data = json.loads(f.read())
                if mod_name not in auto_use_data:
                    auto_use_data[mod_name] = {}
                auto_use_data[mod_name][func] = param
            with open("AutoUse.json", "w") as f:
                json.dump(auto_use_data, f, indent=4)
        except Exception as e:
            lwjgl.error(f"Failed to set auto use: {e}")
            return False
        else:
            return True
    else:
        try:
            with open("set_auto_use.json", "r") as f:
                set_auto_use_data = json.loads(f.read())
                if "nocancel" not in set_auto_use_data:
                    set_auto_use_data["nocancel"] = {}
                    set_auto_use_data["nocancel"][mod_name] = 0
                else:
                    if set_auto_use_data["nocancel"].get(mod_name, 0) >=3:
                        if messagebox.askyesno("Confirm", f"You have previously denied {mod_name} three times. Do you want to permanently deny it setting auto use for {func}?"):
                            set_auto_use_data["nocancel"][mod_name] = -1
                            with open("set_auto_use.json", "w") as f:
                                json.dump(set_auto_use_data, f, indent=4)
                            return False
                        else:
                            set_auto_use_data["nocancel"][mod_name] = 0
                            return False
                    set_auto_use_data["nocancel"][mod_name] = set_auto_use_data["nocancel"].get(mod_name, 0) + 1
            with open("set_auto_use.json", "w") as f:
                json.dump(set_auto_use_data, f, indent=4)
        except Exception as e:
            lwjgl.error(f"Failed to record no-cancel decision: {e}")
        return False


def reload_client():
    lwjgl.info("Reloading client...")
    subprocess.run(["python", "main.py"] + sys.argv[1:], shell=True, start_new_session=True)
    sys.exit(0)