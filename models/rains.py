import pygame
import threading
import time

class rains:
    def __init__(self):
        self.is_playing = False
        self.thread = None
        
    def start(self):
        """开始播放雨声"""
        if self.is_playing:
            return
            
        self.is_playing = True
        self.thread = threading.Thread(target=self._play_rain_sound)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """停止播放雨声"""
        self.is_playing = False
        if hasattr(self, 'sound'):
            self.sound.stop()
    
    def _play_rain_sound(self):
        """在后台线程中播放雨声"""
        try:
            pygame.mixer.init()
            self.sound = pygame.mixer.Sound('assets/mc_rain.ogg')
            self.sound.set_volume(0.25)
            
            while self.is_playing:
                self.sound.play()
                # 等待音效播放完毕或停止信号
                while self.is_playing and pygame.mixer.get_busy():
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"播放雨声时出错: {e}")
        finally:
            if hasattr(self, 'sound'):
                self.sound.stop()