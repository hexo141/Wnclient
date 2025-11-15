#ifndef _WIN32

#include "TransparentWindow.h"
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/Xcomposite.h>
#include <X11/extensions/Xrender.h>
#include <X11/keysym.h>
#include <cstring>
#include <cstdlib>

class TransparentWindowLinux : public TransparentWindow {
private:
    Display* display;
    Window window;
    Visual* visual;
    XRenderPictFormat* format;
    Picture picture;
    Pixmap pixmap;
    int width;
    int height;
    bool shouldExit;

    static int XErrorHandler(Display* dpy, XErrorEvent* ev) {
        return 0;  // 忽略错误
    }

public:
    TransparentWindowLinux() : display(nullptr), window(0), visual(nullptr), 
                               format(nullptr), picture(0), pixmap(0),
                               width(0), height(0), shouldExit(false) {}

    bool Create(int w, int h) override {
        width = w;
        height = h;

        display = XOpenDisplay(NULL);
        if (!display) return false;

        XSetErrorHandler(XErrorHandler);

        int screen = DefaultScreen(display);
        Window root = RootWindow(display, screen);

        // 查找ARGB视觉
        XVisualInfo visualInfo;
        XMatchVisualInfo(display, screen, 32, TrueColor, &visualInfo);
        visual = visualInfo.visual;

        // 创建窗口属性
        XSetWindowAttributes attr;
        attr.override_redirect = True;
        attr.colormap = XCreateColormap(display, root, visual, AllocNone);
        attr.background_pixmap = None;
        attr.border_pixmap = None;
        attr.border_pixel = 0;
        attr.event_mask = KeyPressMask | KeyReleaseMask;

        // 创建窗口
        unsigned long mask = CWOverrideRedirect | CWColormap | CWBackPixmap | CWBorderPixel | CWEventMask;
        window = XCreateWindow(display, root, 0, 0, width, height, 0,
                               visualInfo.depth, InputOutput, visual, mask, &attr);

        // 设置窗口属性以实现透明度和置顶
        Atom wm_state_above = XInternAtom(display, "_NET_WM_STATE_ABOVE", False);
        Atom wm_state = XInternAtom(display, "_NET_WM_STATE", False);
        XChangeProperty(display, window, wm_state, XA_ATOM, 32, PropModeReplace,
                        (unsigned char*)&wm_state_above, 1);

        Atom wm_window_type = XInternAtom(display, "_NET_WM_WINDOW_TYPE", False);
        Atom wm_window_type_dock = XInternAtom(display, "_NET_WM_WINDOW_TYPE_DOCK", False);
        XChangeProperty(display, window, wm_window_type, XA_ATOM, 32, PropModeReplace,
                        (unsigned char*)&wm_window_type_dock, 1);

        // 设置窗口不可点击穿透
        // 如果需要点击穿透，可以设置_NET_WM_BYPASS_COMPOSITOR

        // 初始化XRender
        if (XRenderQueryExtension(display, NULL, NULL)) {
            format = XRenderFindVisualFormat(display, visual);
        }

        // 创建Pixmap和Picture
        pixmap = XCreatePixmap(display, window, width, height, 32);
        if (format && pixmap) {
            XRenderPictureAttributes pa;
            pa.repeat = RepeatNone;
            picture = XRenderCreatePicture(display, pixmap, format, CPRepeat, &pa);
        }

        return true;
    }

    void UpdateImage(const ImageData& image) override {
        if (!display || !pixmap || image.width != width || image.height != height) return;

        // 创建图像数据
        std::vector<uint32_t> pixels(width * height);
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int idx = (y * width + x) * 4;
                uint8_t r = image.pixels[idx + 0];
                uint8_t g = image.pixels[idx + 1];
                uint8_t b = image.pixels[idx + 2];
                uint8_t a = image.pixels[idx + 3];

                // ARGB格式
                pixels[y * width + x] = (a << 24) | (r << 16) | (g << 8) | b;
            }
        }

        // 使用XPutImage写入Pixmap
        // 创建不会自动释放数据的XImage
        XImage* ximage = XCreateImage(display, visual, 32, ZPixmap, 0,
                                      NULL, width, height, 32, 0);
        if (ximage) {
            // 分配数据并复制
            ximage->data = (char*)malloc(width * height * 4);
            ximage->bytes_per_line = width * 4;
            if (ximage->data) {
                memcpy(ximage->data, pixels.data(), width * height * 4);
                GC gc = XCreateGC(display, pixmap, 0, NULL);
                XPutImage(display, pixmap, gc, ximage, 0, 0, 0, 0, width, height);
                XFreeGC(display, gc);
                free(ximage->data);
                ximage->data = NULL;  // 防止XDestroyImage释放已释放的内存
            }
            XDestroyImage(ximage);
        }

        // 复制Pixmap到窗口
        GC gc = XCreateGC(display, window, 0, NULL);
        XCopyArea(display, pixmap, window, gc, 0, 0, width, height, 0, 0);
        XFreeGC(display, gc);
        XFlush(display);
    }

    void Show() override {
        if (display && window) {
            XMapWindow(display, window);
            XFlush(display);
        }
    }

    void Hide() override {
        if (display && window) {
            XUnmapWindow(display, window);
            XFlush(display);
        }
    }

    void Destroy() override {
        if (picture) {
            XRenderFreePicture(display, picture);
            picture = 0;
        }
        if (pixmap) {
            XFreePixmap(display, pixmap);
            pixmap = 0;
        }
        if (window) {
            XDestroyWindow(display, window);
            window = 0;
        }
        if (display) {
            XCloseDisplay(display);
            display = nullptr;
        }
    }

    bool ProcessMessages() override {
        if (!display) return false;

        while (XPending(display)) {
            XEvent event;
            XNextEvent(display, &event);

            if (event.type == KeyPress) {
                KeySym keysym = XLookupKeysym(&event.xkey, 0);
                if (keysym == XK_Escape) {
                    shouldExit = true;
                    return false;
                }
            }
        }

        return !shouldExit;
    }
};

TransparentWindow* TransparentWindow::Create() {
    return new TransparentWindowLinux();
}

#endif

