import ctypes
from ctypes import wintypes

# --- Constants ---
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_DEBUG_NAME = "SeDebugPrivilege"
SE_PRIVILEGE_ENABLED = 0x00000002
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS = 0x00000002
MAX_PATH = 260

# --- Structures ---
class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG)
    ]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Luid", LUID),
        ("Attributes", wintypes.DWORD)
    ]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Privileges", LUID_AND_ATTRIBUTES * 1)
    ]

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * MAX_PATH)
    ]

# --- Load Libraries ---
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

# --- Function Prototypes ---
# OpenProcessToken
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi32.OpenProcessToken.restype = wintypes.BOOL

# LookupPrivilegeValueW
advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL

# AdjustTokenPrivileges
advapi32.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES), wintypes.DWORD, ctypes.POINTER(TOKEN_PRIVILEGES), ctypes.POINTER(wintypes.DWORD)]
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL

# CreateToolhelp32Snapshot
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

# Process32FirstW
kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32FirstW.restype = wintypes.BOOL

# Process32NextW
kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32NextW.restype = wintypes.BOOL

# OpenProcess
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

# TerminateProcess
kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype = wintypes.BOOL

# CloseHandle
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

# WaitForSingleObject
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype = wintypes.DWORD

# GetLastError
kernel32.GetLastError.restype = wintypes.DWORD


def enable_debug_privilege():
    """Enables SeDebugPrivilege to allow terminating protected processes."""
    h_token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(-1, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(h_token)):
        raise ctypes.WinError(ctypes.get_last_error())

    luid = LUID()
    if not advapi32.LookupPrivilegeValueW(None, SE_DEBUG_NAME, ctypes.byref(luid)):
        kernel32.CloseHandle(h_token)
        raise ctypes.WinError(ctypes.get_last_error())

    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

    if not advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp), 0, None, None):
        kernel32.CloseHandle(h_token)
        raise ctypes.WinError(ctypes.get_last_error())
    
    kernel32.CloseHandle(h_token)
    print("[+] SeDebugPrivilege enabled.")


def get_pid_by_name_ctypes(process_name: str) -> list:
    """
    使用 ctypes 和 Windows API 根据进程名查找 PID
    """
    # Use kernel32 already loaded at module level
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError()

    pe32 = PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
    
    pids = []
    target_name = process_name.lower()
    
    if kernel32.Process32FirstW(snapshot, ctypes.byref(pe32)):
        while True:
            exe_file = pe32.szExeFile
            if isinstance(exe_file, bytes):
                exe_file = exe_file.decode('utf-8', errors='ignore')
            exe_file = exe_file.rstrip('\x00').lower()
            if '\\' in exe_file:
                exe_file = exe_file.split('\\')[-1]
            
            if exe_file == target_name:
                pids.append(pe32.th32ProcessID)
            
            if not kernel32.Process32NextW(snapshot, ctypes.byref(pe32)):
                break
                 
    kernel32.CloseHandle(snapshot)
    return pids

def SDP_kill_process_by_pid(pid: int):
    """Terminates a process by PID using TerminateProcess."""
    h_process = kernel32.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, pid)
    
    if not h_process:
        print(f"[-] Could not open process PID: {pid}. Error: {ctypes.get_last_error()}")
        return False

    print(f"[*] Attempting to terminate PID: {pid}")

    if not kernel32.TerminateProcess(h_process, 1):
        print(f"[-] Failed to terminate process. Error: {ctypes.get_last_error()}")
        kernel32.CloseHandle(h_process)
        return False

    print(f"[+] Successfully terminated PID: {pid}")
    
    # Wait for process to exit
    kernel32.WaitForSingleObject(h_process, 0xFFFFFFFF)  # INFINITE
    kernel32.CloseHandle(h_process)
    return True


