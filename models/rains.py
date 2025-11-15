import pygame
import threading

class rains:
    def __init__(self):
        self.is_playing = False
        self.thread = None
        self.sound = None
        
    def start(self):
        """开始播放雨声"""
        if self.is_playing:
            return
            
        self.is_playing = True
        self.thread = threading.Thread(target=self._play_rain_sound)
        self.thread.daemon = True
        self.thread.start()
        print("雨声模块启动")
        
    def stop(self):
        """停止播放雨声"""
        self.is_playing = False
        if self.sound:
            self.sound.stop()
        print("雨声模块停止")
    
    def _play_rain_sound(self):
        """在后台线程中连续播放雨声"""
        try:
            pygame.mixer.init()
            self.sound = pygame.mixer.Sound('assets/rains.wav')
            self.sound.set_volume(0.25)
            
            # 使用循环播放，-1表示无限循环
            self.sound.play(loops=-1)
            
            # 保持线程运行，直到停止信号
            while self.is_playing:
                pygame.time.wait(100)  # 每100毫秒检查一次
                
        except Exception as e:
            print(f"播放雨声时出错: {e}")
        finally:
            if self.sound:
                self.sound.stop()
            pygame.mixer.quit()