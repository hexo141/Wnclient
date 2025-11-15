#ifndef _WIN32

#include "ScreenCapture.h"
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <cstring>

class ScreenCaptureLinux : public ScreenCapture {
private:
    Display* display;
    Window rootWindow;
    int screen;

public:
    bool Initialize() override {
        display = XOpenDisplay(NULL);
        if (!display) {
            return false;
        }
        screen = DefaultScreen(display);
        rootWindow = RootWindow(display, screen);
        return true;
    }

    bool CaptureScreen(ImageData& image) override {
        XWindowAttributes attrs;
        XGetWindowAttributes(display, rootWindow, &attrs);

        int width = attrs.width;
        int height = attrs.height;

        XImage* ximage = XGetImage(display, rootWindow, 0, 0, width, height, AllPlanes, ZPixmap);
        if (!ximage) {
            return false;
        }

        image.resize(width, height);

        // X11返回的数据格式取决于显示器的深度
        // 这里假设是32位深度（RGBA或BGRA）
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                unsigned long pixel = XGetPixel(ximage, x, y);
                
                // 提取颜色分量（顺序可能因系统而异）
                uint8_t r = (pixel >> 16) & 0xFF;
                uint8_t g = (pixel >> 8) & 0xFF;
                uint8_t b = pixel & 0xFF;
                uint8_t a = (pixel >> 24) & 0xFF;
                if (a == 0) a = 255;  // 默认不透明

                int idx = (y * width + x) * 4;
                image.pixels[idx + 0] = r;
                image.pixels[idx + 1] = g;
                image.pixels[idx + 2] = b;
                image.pixels[idx + 3] = a;
            }
        }

        XDestroyImage(ximage);
        return true;
    }

    void Cleanup() override {
        if (display) {
            XCloseDisplay(display);
            display = nullptr;
        }
    }
};

ScreenCapture* ScreenCapture::Create() {
    return new ScreenCaptureLinux();
}

#endif

