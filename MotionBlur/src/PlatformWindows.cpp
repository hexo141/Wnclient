#ifdef _WIN32

#include "Platform.h"
#include <windows.h>

ScreenSize Platform::GetScreenSize() {
    ScreenSize size;
    size.width = GetSystemMetrics(SM_CXSCREEN);
    size.height = GetSystemMetrics(SM_CYSCREEN);
    return size;
}

bool Platform::IsWindows() {
    return true;
}

bool Platform::IsLinux() {
    return false;
}

#endif

