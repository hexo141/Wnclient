#ifdef _WIN32

#include "TransparentWindow.h"
#include <windows.h>
#include <dwmapi.h>
#pragma comment(lib, "dwmapi.lib")

class TransparentWindowWindows : public TransparentWindow {
private:
    HWND hwnd;
    HDC hdc;
    HDC memDC;
    HBITMAP hBitmap;
    int width;
    int height;
    bool shouldExit;

    static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
        TransparentWindowWindows* self = (TransparentWindowWindows*)GetWindowLongPtr(hwnd, GWLP_USERDATA);
        
        if (msg == WM_CREATE) {
            CREATESTRUCT* cs = (CREATESTRUCT*)lParam;
            self = (TransparentWindowWindows*)cs->lpCreateParams;
            SetWindowLongPtr(hwnd, GWLP_USERDATA, (LONG_PTR)self);
        }
        
        if (self) {
            switch (msg) {
                case WM_KEYDOWN:
                    if (wParam == VK_ESCAPE) {
                        self->shouldExit = true;
                    }
                    return 0;
                case WM_DESTROY:
                    PostQuitMessage(0);
                    return 0;
            }
        }
        
        return DefWindowProc(hwnd, msg, wParam, lParam);
    }

public:
    TransparentWindowWindows() : hwnd(NULL), hdc(NULL), memDC(NULL), hBitmap(NULL), 
                                 width(0), height(0), shouldExit(false) {}

    bool Create(int w, int h) override {
        width = w;
        height = h;

        WNDCLASSEX wc = {};
        wc.cbSize = sizeof(WNDCLASSEX);
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = WndProc;
        wc.hInstance = GetModuleHandle(NULL);
        wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
        wc.lpszClassName = L"MotionBlurWindow";

        RegisterClassEx(&wc);

        // 创建分层窗口
        hwnd = CreateWindowEx(
            WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
            L"MotionBlurWindow",
            L"Motion Blur",
            WS_POPUP | WS_VISIBLE,
            0, 0, width, height,
            NULL, NULL, GetModuleHandle(NULL),
            this
        );

        if (!hwnd) return false;

        SetWindowLongPtr(hwnd, GWLP_USERDATA, (LONG_PTR)this);

        hdc = GetDC(hwnd);
        memDC = CreateCompatibleDC(hdc);
        
        BITMAPINFO bmi = {};
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        bmi.bmiHeader.biWidth = width;
        bmi.bmiHeader.biHeight = -height;
        bmi.bmiHeader.biPlanes = 1;
        bmi.bmiHeader.biBitCount = 32;
        bmi.bmiHeader.biCompression = BI_RGB;

        void* bits;
        hBitmap = CreateDIBSection(memDC, &bmi, DIB_RGB_COLORS, &bits, NULL, 0);
        SelectObject(memDC, hBitmap);

        // 设置窗口透明度支持
        SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA);

        return true;
    }

    void UpdateImage(const ImageData& image) override {
        if (!memDC || image.width != width || image.height != height) return;

        // 将RGBA转换为BGRA
        std::vector<uint8_t> bgraData(width * height * 4);
        for (int i = 0; i < width * height; i++) {
            bgraData[i * 4 + 0] = image.pixels[i * 4 + 2];  // B
            bgraData[i * 4 + 1] = image.pixels[i * 4 + 1];  // G
            bgraData[i * 4 + 2] = image.pixels[i * 4 + 0];  // R
            bgraData[i * 4 + 3] = image.pixels[i * 4 + 3];  // A
        }

        BITMAPINFO bmi = {};
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        bmi.bmiHeader.biWidth = width;
        bmi.bmiHeader.biHeight = -height;
        bmi.bmiHeader.biPlanes = 1;
        bmi.bmiHeader.biBitCount = 32;
        bmi.bmiHeader.biCompression = BI_RGB;

        SetDIBits(memDC, hBitmap, 0, height, bgraData.data(), &bmi, DIB_RGB_COLORS);

        // 使用UpdateLayeredWindow更新窗口
        POINT ptSrc = {0, 0};
        SIZE size = {width, height};
        BLENDFUNCTION blend = {};
        blend.BlendOp = AC_SRC_OVER;
        blend.BlendFlags = 0;
        blend.SourceConstantAlpha = 255;
        blend.AlphaFormat = AC_SRC_ALPHA;

        POINT ptDst = {0, 0};
        GetWindowRect(hwnd, (LPRECT)&ptDst);

        UpdateLayeredWindow(hwnd, hdc, &ptDst, &size, memDC, &ptSrc, 0, &blend, ULW_ALPHA);
    }

    void Show() override {
        ShowWindow(hwnd, SW_SHOW);
    }

    void Hide() override {
        ShowWindow(hwnd, SW_HIDE);
    }

    void Destroy() override {
        if (hBitmap) {
            DeleteObject(hBitmap);
            hBitmap = NULL;
        }
        if (memDC) {
            DeleteDC(memDC);
            memDC = NULL;
        }
        if (hdc) {
            ReleaseDC(hwnd, hdc);
            hdc = NULL;
        }
        if (hwnd) {
            DestroyWindow(hwnd);
            hwnd = NULL;
        }
    }

    bool ProcessMessages() override {
        MSG msg;
        while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) {
                return false;
            }
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        return !shouldExit;
    }
};

TransparentWindow* TransparentWindow::Create() {
    return new TransparentWindowWindows();
}

#endif

