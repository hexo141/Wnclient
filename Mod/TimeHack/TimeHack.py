import os
import subprocess
import main
import lwjgl
def inject_by_window_title(window_title,time_scale=2.0):
    f = open("Mod/TimeHack/TimeHack.txt","r")
    if f.read().strip() != f"timeScale={time_scale}":
        f = open("Mod/TimeHack/TimeHack.txt","w")
        f.write(f"timeScale={time_scale}")
        f.close()
    if not os.path.exists("Mod/TimeHack/TimeHack.dll"):
        lwjgl.warning("TimeHack.dll not found! Try to compile it first.")
        subprocess.run(["g++", "-shared", "-o", "Mod/TimeHack/TimeHack.dll", "Mod/TimeHack/TimeHack.cpp", "-luser32", "-lwinmm", "-static"],shell=True)
        if not os.path.exists("Mod/TimeHack/TimeHack.dll"):
            lwjgl.error("TimeHack.dll compilation failed!")
            return False
    # subprocess.run(["Mod/TimeHack/injector.exe", window_title, os.path.abspath("Mod/TimeHack/TimeHack.dll")])
    main.load_mods(mod_name="Dll_injector")
    main.UseMod("Dll_injector","inject_by_window_title",args=[window_title,os.path.abspath("Mod/TimeHack/TimeHack.dll")])