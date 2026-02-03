import json
import tkinter as tk
import lwjgl
import rich
import toml
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


def reload_client(para="", para1=""):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)
    if not messagebox.askyesno("Reload WnClient", "The changes require a client reload to take effect. Do you want to reload now?"):
        return
    lwjgl.info("Reloading client...")
    if para.strip() == "" and para1.strip() == "":
        subprocess.run([sys.executable, "main.py"], shell=False, start_new_session=True)
    subprocess.run([sys.executable, "main.py"] + [para] + [para1], shell=False, start_new_session=True)
    sys.exit(0)

def modlist():
    with open("Modlist.json", "r") as f:
        modlist_data = json.loads(f.read())
    while True:
        try:
            page_input = input("Enter page number (or 'q' to quit): ")
            if page_input.lower() == 'q':
                break
            page = int(page_input)
        except ValueError:
            print("Invalid input. Please enter a valid page number or 'q' to quit.")
            continue
        items_per_page = 10
        total_mods = len(modlist_data)
        total_pages = (total_mods + items_per_page - 1) // items_per_page
        
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages
        
        start_index = (page - 1) * items_per_page
        end_index = min(start_index + items_per_page, total_mods)
        
        rich.print(f"[bold cyan]Page {page}/{total_pages} ({total_mods} mods total)[/bold cyan]")
        rich.print(f"[dim]Showing mods {start_index + 1}-{end_index}[/dim]")
        
        mods_list = list(modlist_data.items())
        
        for i in range(start_index, end_index):
            mod_name, mod_info = mods_list[i]
            mod_number = i + 1
            
            rich.print(f"[bold green]{mod_number}. {mod_name}[/bold green]")
            
            try:
                mod_data = toml.load(mod_info["toml"])
                for key in mod_data:
                    rich.print(f"    [yellow]{key}:[/yellow] {mod_data[key]}")
            except Exception as e:
                rich.print(f"    [red]Error loading TOML: {e}[/red]")
            
            if i < end_index - 1:
                rich.print()
        
        if total_pages > 1:
            rich.print(f"\n[dim]Call modlist(page=X) to view other pages[/dim]")