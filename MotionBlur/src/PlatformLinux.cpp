#ifndef _WIN32

#include "Platform.h"
#include <X11/Xlib.h>
#include <X11/Xutil.h>

ScreenSize Platform::GetScreenSize() {
    Display* display = XOpenDisplay(NULL);
    if (!display) {
        ScreenSize size = {1920, 1080};  // 默认值
        return size;
    }

    Screen* screen = DefaultScreenOfDisplay(display);
    ScreenSize size;
    size.width = WidthOfScreen(screen);
    size.height = HeightOfScreen(screen);
    
    XCloseDisplay(display);
    return size;
}

bool Platform::IsWindows() {
    return false;
}

bool Platform::IsLinux() {
    return true;
}

#endif

