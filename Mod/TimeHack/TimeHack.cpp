#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <string>
#include <fstream>
#include <sstream>
#pragma comment(lib, "winmm.lib")

volatile double g_timeScale = 2.0;

static DWORD (WINAPI *pOriginalGetTickCount)() = nullptr;
static ULONGLONG (WINAPI *pOriginalGetTickCount64)() = nullptr;
static DWORD (WINAPI *pOriginalTimeGetTime)() = nullptr;
static BOOL (WINAPI *pOriginalQPC)(LARGE_INTEGER*) = nullptr;
static BOOL (WINAPI *pOriginalQPF)(LARGE_INTEGER*) = nullptr; 


bool ReadTimeScaleFromConfig(HMODULE hModule) {
    char dllPath[MAX_PATH];
    if (!GetModuleFileNameA(hModule, dllPath, MAX_PATH)) {
        return false;
    }
    
    // 提取目录路径
    std::string configPath = dllPath;
    size_t pos = configPath.find_last_of("\\/");
    if (pos == std::string::npos) {
        return false;
    }
    
    // 构建配置文件路径
    configPath = configPath.substr(0, pos + 1) + "TimeHack.txt";
    
    // 读取配置文件
    std::ifstream configFile(configPath);
    if (!configFile.is_open()) {
        return false;
    }
    
    std::string line;
    while (std::getline(configFile, line)) {
        line.erase(0, line.find_first_not_of(" \t"));
        line.erase(line.find_last_not_of(" \t") + 1);
        
        // 查找 timeScale= 配置
        if (line.find("timeScale=") == 0) {
            std::string valueStr = line.substr(10);
            std::stringstream ss(valueStr);
            double value;
            if (ss >> value) {
                g_timeScale = value;
                return true;
            }
        }
    }
    
    return false;
}

DWORD WINAPI HookedGetTickCount() {
    if (pOriginalGetTickCount) {
        return static_cast<DWORD>(static_cast<double>(pOriginalGetTickCount()) * g_timeScale);
    }
    return 0;
}

ULONGLONG WINAPI HookedGetTickCount64() {
    if (pOriginalGetTickCount64) {
        return static_cast<ULONGLONG>(static_cast<double>(pOriginalGetTickCount64()) * g_timeScale);
    }
    return 0;
}

DWORD WINAPI HookedTimeGetTime() {
    if (pOriginalTimeGetTime) {
        return static_cast<DWORD>(static_cast<double>(pOriginalTimeGetTime()) * g_timeScale);
    }
    return 0;
}

BOOL WINAPI HookedQueryPerformanceCounter(LARGE_INTEGER* lpPerformanceCount) {
    if (pOriginalQPC && lpPerformanceCount && pOriginalQPC(lpPerformanceCount)) {
        double scaled = static_cast<double>(lpPerformanceCount->QuadPart) * g_timeScale;
        lpPerformanceCount->QuadPart = static_cast<LONGLONG>(scaled);
        return TRUE;
    }
    return FALSE;
}

BOOL WINAPI HookedQueryPerformanceFrequency(LARGE_INTEGER* lpFrequency) {
    if (pOriginalQPF && lpFrequency) {
        return pOriginalQPF(lpFrequency); // 直接返回原始频率
    }
    // 默认Windows频率
    if (lpFrequency) {
        lpFrequency->QuadPart = 10000000;
        return TRUE;
    }
    return FALSE;
}

bool IATHook(HMODULE hModule, const char* funcName, void* newFunc, void** origFunc) {
    if (!hModule || !funcName || !newFunc || !origFunc) return false;

    IMAGE_DOS_HEADER* dosHeader = (IMAGE_DOS_HEADER*)hModule;
    if (dosHeader->e_magic != IMAGE_DOS_SIGNATURE) return false;

    IMAGE_NT_HEADERS* ntHeader = (IMAGE_NT_HEADERS*)((BYTE*)hModule + dosHeader->e_lfanew);
    if (ntHeader->Signature != IMAGE_NT_SIGNATURE) return false;

    IMAGE_IMPORT_DESCRIPTOR* importDesc = (IMAGE_IMPORT_DESCRIPTOR*)(
        (BYTE*)hModule + ntHeader->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress
    );

    for (; importDesc->Name && importDesc->FirstThunk; ++importDesc) {
        IMAGE_THUNK_DATA* origThunk = (IMAGE_THUNK_DATA*)((BYTE*)hModule + importDesc->OriginalFirstThunk);
        IMAGE_THUNK_DATA* thunk = (IMAGE_THUNK_DATA*)((BYTE*)hModule + importDesc->FirstThunk);
        
        if (!origThunk) continue;

        for (; origThunk->u1.AddressOfData; ++origThunk, ++thunk) {
            if (IMAGE_SNAP_BY_ORDINAL(origThunk->u1.Ordinal)) continue;

            IMAGE_IMPORT_BY_NAME* importName = (IMAGE_IMPORT_BY_NAME*)((BYTE*)hModule + origThunk->u1.AddressOfData);
            if (_stricmp((char*)importName->Name, funcName) == 0) {
                // 保存原始地址
                *origFunc = (void*)thunk->u1.Function;

                // 修改IAT
                DWORD oldProtect;
                if (VirtualProtect(&thunk->u1.Function, sizeof(void*), PAGE_READWRITE, &oldProtect)) {
                    thunk->u1.Function = (ULONG_PTR)newFunc;
                    VirtualProtect(&thunk->u1.Function, sizeof(void*), oldProtect, &oldProtect);
                    return true;
                }
            }
        }
    }
    return false;
}

void InitializeHooks() {
    HMODULE hKernel32 = GetModuleHandleA("kernel32.dll");
    HMODULE hWinmm = GetModuleHandleA("winmm.dll");

    if (hKernel32) {
        IATHook(hKernel32, "GetTickCount", (void*)HookedGetTickCount, (void**)&pOriginalGetTickCount);
        IATHook(hKernel32, "GetTickCount64", (void*)HookedGetTickCount64, (void**)&pOriginalGetTickCount64);
        IATHook(hKernel32, "QueryPerformanceCounter", (void*)HookedQueryPerformanceCounter, (void**)&pOriginalQPC);
        IATHook(hKernel32, "QueryPerformanceFrequency", (void*)HookedQueryPerformanceFrequency, (void**)&pOriginalQPF);
    }

    if (hWinmm) {
        IATHook(hWinmm, "timeGetTime", (void*)HookedTimeGetTime, (void**)&pOriginalTimeGetTime);
    }
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        
        // 读取配置文件
        if (!ReadTimeScaleFromConfig(hModule)) {
            // 如果读取失败，使用默认值 2.0
            g_timeScale = 2.0;
        }
        
        InitializeHooks();
        
        char msg[256];
        sprintf_s(msg, "Inject success\nTime scale: %.1f", g_timeScale);
        MessageBoxA(NULL, msg, "(Wnclient)TimeHack Hook", MB_ICONINFORMATION | MB_OK);
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}