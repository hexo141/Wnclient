import ctypes
import ctypes.wintypes
import win32gui
import win32process
import keyboard
import os
import sys

# Windows API types and constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04

# Windows API functions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_last_error=True)

class DLLInjector:
    def __init__(self):
        pass
    
    def get_process_id_by_window_title(self, window_title):
        """Get process ID by window title"""
        try:
            hwnd = win32gui.FindWindow(None, window_title)
            if hwnd == 0:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return pid
        except Exception as e:
            print(f"Error getting process ID: {e}")
            return None
    
    def get_process_id_by_window_class(self, class_name):
        """Get process ID by window class name"""
        try:
            hwnd = win32gui.FindWindow(class_name, None)
            if hwnd == 0:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return pid
        except Exception as e:
            print(f"Error getting process ID: {e}")
            return None
    
    def get_active_window_process_id(self):
        """Get process ID of currently active window"""
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return None
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return pid.value
        except Exception as e:
            print(f"Error getting active window PID: {e}")
            return None
    
    def inject_dll(self, process_id, dll_path):
        """Inject DLL into target process"""
        
        if not os.path.exists(dll_path):
            print(f"Error: DLL file not found at {dll_path}")
            return False
        
        # Use wide-char (UTF-16) string for the target process and ensure correct ctypes prototypes
        dll_path_buf = ctypes.create_unicode_buffer(dll_path)
        buf_size = ctypes.sizeof(dll_path_buf)
        
        try:
            # Define prototypes/returns for used WinAPI functions to avoid type-related crashes
            kernel32.OpenProcess.argtypes = (ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD)
            kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE

            kernel32.VirtualAllocEx.argtypes = (ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD)
            kernel32.VirtualAllocEx.restype = ctypes.c_void_p

            kernel32.WriteProcessMemory.argtypes = (ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
            kernel32.WriteProcessMemory.restype = ctypes.wintypes.BOOL

            kernel32.GetModuleHandleW.argtypes = (ctypes.c_wchar_p,)
            kernel32.GetModuleHandleW.restype = ctypes.wintypes.HMODULE

            kernel32.GetProcAddress.argtypes = (ctypes.wintypes.HMODULE, ctypes.c_char_p)
            kernel32.GetProcAddress.restype = ctypes.c_void_p

            kernel32.CreateRemoteThread.argtypes = (ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD))
            kernel32.CreateRemoteThread.restype = ctypes.wintypes.HANDLE

            kernel32.WaitForSingleObject.argtypes = (ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD)
            kernel32.WaitForSingleObject.restype = ctypes.wintypes.DWORD

            kernel32.VirtualFreeEx.argtypes = (ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.wintypes.DWORD)
            kernel32.VirtualFreeEx.restype = ctypes.wintypes.BOOL

            kernel32.CloseHandle.argtypes = (ctypes.wintypes.HANDLE,)
            kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

            # Open target process
            process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, process_id)
            if not process_handle:
                print(f"Error: Failed to open process (PID: {process_id})")
                return False

            # Allocate memory in target process for the wide string
            allocated_memory = kernel32.VirtualAllocEx(
                process_handle,
                None,
                buf_size,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_READWRITE
            )

            if not allocated_memory:
                print("Error: Failed to allocate memory in target process")
                kernel32.CloseHandle(process_handle)
                return False

            # Write wide-character DLL path into the allocated memory
            written = ctypes.c_size_t(0)
            success_write = kernel32.WriteProcessMemory(
                process_handle,
                allocated_memory,
                ctypes.byref(dll_path_buf),
                buf_size,
                ctypes.byref(written)
            )
            if not success_write or written.value != buf_size:
                print("Error: Failed to write DLL path to target process memory")
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                kernel32.CloseHandle(process_handle)
                return False

            # Get address of LoadLibraryW in local kernel32 and use it for remote thread (wide version)
            kernel32_handle = kernel32.GetModuleHandleW("kernel32.dll")
            if not kernel32_handle:
                print("Error: Failed to get handle to kernel32.dll")
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                kernel32.CloseHandle(process_handle)
                return False

            loadlibrary_addr = kernel32.GetProcAddress(kernel32_handle, b"LoadLibraryW")
            if not loadlibrary_addr:
                print("Error: Failed to get address of LoadLibraryW")
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                kernel32.CloseHandle(process_handle)
                return False

            # Create remote thread to call LoadLibraryW with pointer to the wide string
            thread_handle = kernel32.CreateRemoteThread(
                process_handle,
                None,
                0,
                loadlibrary_addr,
                allocated_memory,
                0,
                None
            )

            if not thread_handle:
                print("Error: Failed to create remote thread")
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
                kernel32.CloseHandle(process_handle)
                return False

            # Wait for thread to complete (timeout in ms)
            kernel32.WaitForSingleObject(thread_handle, 5000)

            # Cleanup
            kernel32.CloseHandle(thread_handle)
            kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, 0x8000)
            kernel32.CloseHandle(process_handle)

            print(f"Successfully injected DLL into process {process_id}")
            return True

        except Exception as e:
            print(f"Error during injection: {e}")
            try:
                if 'process_handle' in locals() and process_handle:
                    kernel32.CloseHandle(process_handle)
            except Exception:
                pass
            return False
    
    def inject_dll_to_active_window(self, dll_path):
        """Inject DLL into currently active window's process"""
        pid = self.get_active_window_process_id()
        if pid:
            print(f"Target process ID: {pid}")
            return self.inject_dll(pid, dll_path)
        else:
            print("Error: Could not get active window process ID")
            return False
    
    def inject_dll_by_window_title(self, window_title, dll_path):
        """Inject DLL into process by window title"""
        pid = self.get_process_id_by_window_title(window_title)
        if pid:
            print(f"Target process ID: {pid}")
            return self.inject_dll(pid, dll_path)
        else:
            print(f"Error: Window with title '{window_title}' not found")
            return False
    
    def inject_dll_by_window_class(self, class_name, dll_path):
        """Inject DLL into process by window class name"""
        pid = self.get_process_id_by_window_class(class_name)
        if pid:
            print(f"Target process ID: {pid}")
            return self.inject_dll(pid, dll_path)
        else:
            print(f"Error: Window with class '{class_name}' not found")
            return False
    
    def inject_dll_by_process_id(self, process_id, dll_path):
        """Inject DLL into process by PID"""
        return self.inject_dll(process_id, dll_path)

# Functional API for direct use
def inject_by_window_title(window_title, dll_path):
    """Functional API: Inject DLL by window title"""
    injector = DLLInjector()
    return injector.inject_dll_by_window_title(window_title, dll_path)

def inject_by_window_class(class_name, dll_path):
    """Functional API: Inject DLL by window class"""
    injector = DLLInjector()
    return injector.inject_dll_by_window_class(class_name, dll_path)

def inject_by_process_id(process_id, dll_path):
    """Functional API: Inject DLL by process ID"""
    injector = DLLInjector()
    return injector.inject_dll_by_process_id(process_id, dll_path)

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='DLL Injection Tool')
    parser.add_argument('dll_path', help='Path to DLL file')
    parser.add_argument('-t', '--title', help='Window title to target')
    parser.add_argument('-c', '--class', dest='class_name', help='Window class to target')
    parser.add_argument('-p', '--pid', type=int, help='Process ID to target')
    
    args = parser.parse_args()
    
    # Validate DLL path
    if not os.path.exists(args.dll_path):
        print(f"Error: DLL file not found: {args.dll_path}")
        sys.exit(1)
    
    # Run in appropriate mode
    if args.title:
        success = inject_by_window_title(args.title, args.dll_path)
        sys.exit(0 if success else 1)
    elif args.class_name:
        success = inject_by_window_class(args.class_name, args.dll_path)
        sys.exit(0 if success else 1)
    elif args.pid:
        success = inject_by_process_id(args.pid, args.dll_path)
        sys.exit(0 if success else 1)
    else:
        print("No target specified. Use --help for options.")
        print("\nQuick usage examples:")
        print("  python dll_injector.py mydll.dll --title \"Target Window\"")
        print("  python dll_injector.py mydll.dll --pid 1234")