import tkinter
import json
import subprocess
import tkinter.filedialog
import os
import lwjgl
import pygame
import threading
import win32gui

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass  # 旧版Windows不支持，忽略


def PlayStartAudio(audio_path,window_title):
    # 监听游戏窗口
    lwjgl.info("Listening for game window to start audio playback")
    isExit = False
    while not isExit:
        for title in window_title:
            hwnd = win32gui.FindWindow(None, title)
            if hwnd != 0:
                isExit = True
                break
    lwjgl.info("Game window detected, playing start audio")
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

def StartGame():
    lwjgl.info("Loading configuration from config.json")
    with open('Mod/StartMHY/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        GamePath = config.get("GamePath", "")
        UseTouch = config.get("UseTouch", False)
        EnableUseStartAudio = config.get("EnableUseStartAudio", True)
        ListenWindowTitle = config.get("ListenWindowTitle", ["原神","Genshin Impact","崩坏：星穹铁道","Honkai: Star Rail","崩坏3","Honkai Impact 3rd","绝区零","Zenless Zone Zero","未定事件簿","Tears of Themis"])
        StartAudioPath = config.get("StartAudioPath", "Mod/StartMHY/Audio/StartAudio.mp3")
    if not os.path.exists(GamePath):
        # 让tk选择游戏路径
        root = tkinter.Tk()
        root.withdraw()
        GamePath = tkinter.filedialog.askopenfilename(title="Select Genshin Impact Executable", filetypes=[("Executable Files", "*.exe")])
        # 回写json
        with open('Mod/StartMHY/config.json', 'w', encoding='utf-8') as f:
            config["GamePath"] = GamePath
            json.dump(config, f, ensure_ascii=False, indent=4)
        root.destroy()
    if UseTouch:
        subprocess.Popen([GamePath, "use_moblie_platform", "-iscloud", "1", "-platform_type", "CLOUD_MOBILE"],start_new_session=True)
    else:
        subprocess.Popen([GamePath],start_new_session=True)
    if EnableUseStartAudio:
        if os.path.exists(StartAudioPath):
            threading.Thread(target=PlayStartAudio, args=(StartAudioPath,ListenWindowTitle)).start()
        else:
            lwjgl.error(f"Start audio file not found: {StartAudioPath}")