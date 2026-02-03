import ctypes
from ctypes import windll, wintypes
import sys

# Structures and constants
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("nAccentState", ctypes.c_int),
        ("nFlags", ctypes.c_int),
        ("nColor", ctypes.c_int),
        ("nAnimationId", ctypes.c_int),
    ]

class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("nAttribute", wintypes.DWORD),
        ("pData", ctypes.c_void_p),
        ("ulDataSize", wintypes.ULONG),
    ]

# Windows API constants
WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_TRANSIENTWINDOW = 3

pSetWindowCompositionAttribute = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HWND, ctypes.POINTER(WINCOMPATTRDATA)
)

def enable_acrylic_win10(hwnd):
    try:
        # Get SetWindowCompositionAttribute function
        user32 = ctypes.WinDLL("user32.dll")
        func = getattr(user32, "SetWindowCompositionAttribute", None)
        if not func:
            # Get function address manually
            func_ptr = windll.kernel32.GetProcAddress(
                windll.kernel32.GetModuleHandleW("user32.dll"),
                "SetWindowCompositionAttribute"
            )
            if not func_ptr:
                return False
            func = pSetWindowCompositionAttribute(func_ptr)
        
        # Set acrylic effect
        accent = ACCENTPOLICY()
        accent.nAccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.nFlags = 2
        accent.nColor = 0x00FFFFFF  # Semi-transparent white
        accent.nAnimationId = 0
        
        data = WINCOMPATTRDATA()
        data.nAttribute = WCA_ACCENT_POLICY
        data.pData = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        data.ulDataSize = ctypes.sizeof(accent)
        
        return func(hwnd, ctypes.pointer(data))
    except Exception as e:
        print(f"Failed to enable Win10 acrylic: {e}")
        return False

def enable_acrylic_win11(hwnd):
    try:
        # Use DwmSetWindowAttribute
        dwmapi = ctypes.WinDLL("dwmapi.dll")
        backdrop_type = ctypes.c_int(DWMSBT_TRANSIENTWINDOW)
        
        result = dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type)
        )
        return result == 0  # S_OK
    except Exception as e:
        print(f"Failed to enable Win11 acrylic: {e}")
        return False

def find_windows_by_title(window_title):
    def enum_windows_callback(hwnd, lParam):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(length)
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length)
            
            title = buffer.value
            if window_title.lower() in title.lower():
                # Ensure it's a top-level window
                owner = ctypes.windll.user32.GetWindow(hwnd, 4)  # GW_OWNER
                if owner == 0:
                    windows.append(hwnd)
        return True
    
    windows = []
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback)
    ctypes.windll.user32.EnumWindows(enum_proc, 0)
    return windows

def is_windows11_or_later():
    try:
        # Windows 11 starts from version 10.0.22000
        version = sys.getwindowsversion()
        return version.major == 10 and version.build >= 22000
    except:
        return False

def apply_acrylic_to_window(window_title=""):
    if window_title.strip() == "":
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
    print(f"Searching for windows with title containing '{window_title}'...")
    
    # Find matching windows
    windows = find_windows_by_title(window_title)
    
    if not windows:
        print(f"No windows found with title containing '{window_title}'")
        return False
    
    print(f"Found {len(windows)} matching window(s)")
    
    success_count = 0
    for hwnd in windows:
        print(f"Processing window handle: {hwnd}")
        
        # Try to enable acrylic effect
        if is_windows11_or_later():
            # Try Windows 11 method first
            if enable_acrylic_win11(hwnd):
                print(f"  Window {hwnd}: Successfully applied Windows 11 acrylic")
                success_count += 1
            elif enable_acrylic_win10(hwnd):
                print(f"  Window {hwnd}: Successfully applied Windows 10 acrylic")
                success_count += 1
            else:
                print(f"  Window {hwnd}: Both methods failed")
        else:
            # Windows 10 and earlier - only try Win10 method
            if enable_acrylic_win10(hwnd):
                print(f"  Window {hwnd}: Successfully applied Windows 10 acrylic")
                success_count += 1
            else:
                print(f"  Window {hwnd}: Failed to apply acrylic effect")
    
    print(f"\nSuccessfully applied acrylic effect to {success_count}/{len(windows)} window(s)")
    return success_count > 0
