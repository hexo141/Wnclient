#include <windows.h>
#include <tlhelp32.h>
#include <sddl.h>
#include <stdio.h>
#include <stdlib.h>

// 函数声明
BOOL ControlServiceW(const wchar_t* serviceName, const wchar_t* action);
BOOL IsCurrentProcessSystem(void);
DWORD Get_SYSTEM_Pid(void);
DWORD Get_TI_Pid(void);
wchar_t* getexepath(void);
void Get_system_process(const wchar_t* exePath);

// 控制服务启动/停止
BOOL ControlServiceW(const wchar_t* serviceName, const wchar_t* action) {
    SC_HANDLE hSCManager = OpenSCManagerW(NULL, NULL, SC_MANAGER_CONNECT);
    if (!hSCManager) {
        return FALSE;
    }
    
    SC_HANDLE hService = OpenServiceW(hSCManager, serviceName, 
                                     SERVICE_START | SERVICE_STOP | SERVICE_QUERY_STATUS);
    if (!hService) {
        CloseServiceHandle(hSCManager);
        return FALSE;
    }
    
    BOOL isSuccess = FALSE;
    
    if (wcscmp(action, L"start") == 0) {
        SERVICE_STATUS_PROCESS ssStatus = {0};
        DWORD dwBytesNeeded = 0;
        
        if (QueryServiceStatusEx(hService, SC_STATUS_PROCESS_INFO,
                               (LPBYTE)&ssStatus, sizeof(SERVICE_STATUS_PROCESS),
                               &dwBytesNeeded)) {
            if (ssStatus.dwCurrentState == SERVICE_RUNNING) {
                isSuccess = TRUE;
            } else {
                if (StartServiceW(hService, 0, NULL)) {
                    for (int i = 0; i < 50; ++i) {
                        Sleep(30);
                        if (QueryServiceStatusEx(hService, SC_STATUS_PROCESS_INFO,
                                               (LPBYTE)&ssStatus, sizeof(SERVICE_STATUS_PROCESS),
                                               &dwBytesNeeded) &&
                            ssStatus.dwCurrentState == SERVICE_RUNNING) {
                            isSuccess = TRUE;
                            break;
                        }
                    }
                }
            }
        }
    } else if (wcscmp(action, L"stop") == 0) {
        SERVICE_STATUS ssStatus = {0};
        if (ControlService(hService, SERVICE_CONTROL_STOP, &ssStatus)) {
            for (int i = 0; i < 50; ++i) {
                Sleep(100);
                if (QueryServiceStatus(hService, &ssStatus) && 
                    ssStatus.dwCurrentState == SERVICE_STOPPED) {
                    isSuccess = TRUE;
                    break;
                }
            }
        } else {
            if (GetLastError() == ERROR_SERVICE_NOT_ACTIVE) {
                isSuccess = TRUE;
            }
        }
    }
    
    CloseServiceHandle(hService);
    CloseServiceHandle(hSCManager);
    return isSuccess;
}

// 检查当前进程是否具有SYSTEM令牌
BOOL IsCurrentProcessSystem(void) {
    HANDLE hToken = NULL;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        return FALSE;
    }
    
    DWORD dwSize = 0;
    GetTokenInformation(hToken, TokenUser, NULL, 0, &dwSize);
    
    BYTE* pBuffer = (BYTE*)malloc(dwSize);
    if (!pBuffer) {
        CloseHandle(hToken);
        return FALSE;
    }
    
    PTOKEN_USER pTokenUser = (PTOKEN_USER)pBuffer;
    BOOL bResult = FALSE;
    
    if (GetTokenInformation(hToken, TokenUser, pTokenUser, dwSize, &dwSize)) {
        wchar_t* pSidString = NULL;
        if (ConvertSidToStringSidW(pTokenUser->User.Sid, &pSidString)) {
            bResult = (wcscmp(pSidString, L"S-1-5-18") == 0);
            LocalFree(pSidString);
        }
    }
    
    free(pBuffer);
    CloseHandle(hToken);
    return bResult;
}

// 获取SYSTEM进程PID
DWORD Get_SYSTEM_Pid(void) {
    PROCESSENTRY32W pe = { sizeof(pe) };
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) {
        return 0;
    }
    
    DWORD pid = 0;
    if (Process32FirstW(hSnap, &pe)) {
        do {
            if (_wcsicmp(pe.szExeFile, L"services.exe") == 0) {
                pid = pe.th32ProcessID;
                break;
            }
        } while (Process32NextW(hSnap, &pe));
    }
    
    CloseHandle(hSnap);
    return pid;
}

// 获取TrustedInstaller进程PID
DWORD Get_TI_Pid(void) {
    PROCESSENTRY32W pe = { sizeof(pe) };
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) {
        return 0;
    }
    
    DWORD pid = 0;
    if (Process32FirstW(hSnap, &pe)) {
        do {
            if (_wcsicmp(pe.szExeFile, L"TrustedInstaller.exe") == 0) {
                pid = pe.th32ProcessID;
                break;
            }
        } while (Process32NextW(hSnap, &pe));
    }
    
    CloseHandle(hSnap);
    return pid;
}

// 获取当前进程路径
wchar_t* getexepath(void) {
    static wchar_t szPath[MAX_PATH] = {0};
    GetModuleFileNameW(NULL, szPath, MAX_PATH);
    return szPath;
}

// 以SYSTEM权限启动进程
void Get_system_process(const wchar_t* exePath) {
    DWORD Pid1 = Get_SYSTEM_Pid();
    if (Pid1 == 0) return;
    
    HANDLE hProc1 = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, Pid1);
    if (!hProc1) return;
    
    HANDLE hToken1 = NULL;
    if (!OpenProcessToken(hProc1, TOKEN_QUERY | TOKEN_DUPLICATE, &hToken1)) {
        CloseHandle(hProc1);
        return;
    }
    
    HANDLE hSysToken1 = NULL;
    if (!DuplicateTokenEx(hToken1, TOKEN_ALL_ACCESS, NULL, SecurityImpersonation, 
                         TokenPrimary, &hSysToken1)) {
        CloseHandle(hToken1);
        CloseHandle(hProc1);
        return;
    }
    
    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = {0};
    
    if (!CreateProcessWithTokenW(hSysToken1, 0, exePath, NULL, 0, NULL, NULL, &si, &pi)) {
        // 启动失败
    } else {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }
    
    CloseHandle(hSysToken1);
    CloseHandle(hToken1);
    CloseHandle(hProc1);
}

int main() {
    // 获取命令行参数
    int argc;
    wchar_t** argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    
    // 检查命令行参数
    if (argc < 2) {
        wprintf(L"Usage: %s <executable_path>\n", argv[0]);
        wprintf(L"Example: %s cmd.exe\n", argv[0]);
        LocalFree(argv);
        
        // 如果没有参数，显示提示并等待用户按键
        wprintf(L"Press any key to exit...\n");
        getchar();
        return 1;
    }
    
    wchar_t* exePath = argv[1];
    
    if (!IsCurrentProcessSystem()) {
        // 重新以SYSTEM权限运行当前程序，并传递相同的参数
        wchar_t currentExe[MAX_PATH];
        GetModuleFileNameW(NULL, currentExe, MAX_PATH);
        
        // 构建命令行：当前程序路径 + 原始参数
        wchar_t cmdLine[1024];
        swprintf(cmdLine, 1024, L"\"%s\" \"%s\"", currentExe, exePath);
        
        DWORD Pid1 = Get_SYSTEM_Pid();
        if (Pid1 == 0) {
            LocalFree(argv);
            return 1;
        }
        
        HANDLE hProc1 = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, Pid1);
        if (!hProc1) {
            LocalFree(argv);
            return 1;
        }
        
        HANDLE hToken1 = NULL;
        if (!OpenProcessToken(hProc1, TOKEN_QUERY | TOKEN_DUPLICATE, &hToken1)) {
            CloseHandle(hProc1);
            LocalFree(argv);
            return 1;
        }
        
        HANDLE hSysToken1 = NULL;
        if (!DuplicateTokenEx(hToken1, TOKEN_ALL_ACCESS, NULL, SecurityImpersonation, 
                             TokenPrimary, &hSysToken1)) {
            CloseHandle(hToken1);
            CloseHandle(hProc1);
            LocalFree(argv);
            return 1;
        }
        
        STARTUPINFOW si = { sizeof(si) };
        PROCESS_INFORMATION pi = {0};
        
        if (!CreateProcessWithTokenW(hSysToken1, 0, currentExe, cmdLine, 0, NULL, NULL, &si, &pi)) {
            wprintf(L"Failed to restart with SYSTEM privileges\n");
        } else {
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
        }
        
        CloseHandle(hSysToken1);
        CloseHandle(hToken1);
        CloseHandle(hProc1);
        LocalFree(argv);
        return 0;
    }
    
    wprintf(L"Starting program with TrustedInstaller privileges: %s\n (by Wnclient)", exePath);
    
    ControlServiceW(L"TrustedInstaller", L"start");
    Sleep(1000); // 等待服务启动
    
    DWORD Pid = Get_TI_Pid();
    if (Pid == 0) {
        wprintf(L"TrustedInstaller process not found\n");
        LocalFree(argv);
        return 1;
    }
    
    HANDLE hProc = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, Pid);
    if (!hProc) {
        wprintf(L"Failed to open process: %d\n", GetLastError());
        LocalFree(argv);
        return 1;
    }
    
    HANDLE hToken = NULL;
    if (!OpenProcessToken(hProc, TOKEN_QUERY | TOKEN_DUPLICATE, &hToken)) {
        wprintf(L"Failed to open process token: %d\n", GetLastError());
        CloseHandle(hProc);
        LocalFree(argv);
        return 1;
    }
    
    HANDLE hSysToken = NULL;
    if (!DuplicateTokenEx(hToken, TOKEN_ALL_ACCESS, NULL, SecurityImpersonation, 
                         TokenPrimary, &hSysToken)) {
        wprintf(L"Failed to duplicate token: %d\n", GetLastError());
        CloseHandle(hToken);
        CloseHandle(hProc);
        LocalFree(argv);
        return 1;
    }
    
    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = {0};
    
    if (!CreateProcessWithTokenW(hSysToken, 0, exePath, NULL, 0, NULL, NULL, &si, &pi)) {
        wprintf(L"Startup failed, error code: %d\n", GetLastError());
    } else {
        wprintf(L"Startup successful!\n");
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }
    
    ControlServiceW(L"TrustedInstaller", L"stop");
    CloseHandle(hSysToken);
    CloseHandle(hToken);
    CloseHandle(hProc);
    LocalFree(argv);
    
    return 0;
}