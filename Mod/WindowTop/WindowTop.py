import win32gui
import win32con


# Alternative function to find window by title
def set_window_topmost_by_title(window_title):
    """Set window to topmost by its title"""
    found_hwnds = []  # 存储找到的窗口句柄
    
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_title.lower() in title.lower():
                found_hwnds.append(hwnd)
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                )
        return True  # 始终返回True以继续枚举所有窗口
    
    win32gui.EnumWindows(callback, None)
    return found_hwnds  # 返回找到的所有句柄

def unset_window_topmost_by_title(window_title):
    """Unset topmost for windows whose title contains window_title"""
    found_hwnds = []  # 存储找到的窗口句柄
    
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_title.lower() in title.lower():
                found_hwnds.append(hwnd)
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_NOTOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                )
        return True  # 始终返回True以继续枚举所有窗口
    
    win32gui.EnumWindows(callback, None)
    return found_hwnds  # 返回找到的所有句柄