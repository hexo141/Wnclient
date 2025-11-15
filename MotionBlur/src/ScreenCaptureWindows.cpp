#ifdef _WIN32

#include "ScreenCapture.h"
#include <windows.h>

class ScreenCaptureWindows : public ScreenCapture {
public:
    bool Initialize() override {
        return true;
    }

    bool CaptureScreen(ImageData& image) override {
        HDC hScreenDC = GetDC(NULL);
        HDC hMemoryDC = CreateCompatibleDC(hScreenDC);

        int width = GetSystemMetrics(SM_CXSCREEN);
        int height = GetSystemMetrics(SM_CYSCREEN);

        HBITMAP hBitmap = CreateCompatibleBitmap(hScreenDC, width, height);
        HBITMAP hOldBitmap = (HBITMAP)SelectObject(hMemoryDC, hBitmap);

        BitBlt(hMemoryDC, 0, 0, width, height, hScreenDC, 0, 0, SRCCOPY);

        // 转换为RGBA格式
        image.resize(width, height);
        
        BITMAPINFO bmi;
        ZeroMemory(&bmi, sizeof(bmi));
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        bmi.bmiHeader.biWidth = width;
        bmi.bmiHeader.biHeight = -height;  // 负值表示从上到下
        bmi.bmiHeader.biPlanes = 1;
        bmi.bmiHeader.biBitCount = 32;
        bmi.bmiHeader.biCompression = BI_RGB;

        // 直接读取BGRA数据
        std::vector<uint8_t> bgraData(width * height * 4);
        GetDIBits(hMemoryDC, hBitmap, 0, height, bgraData.data(), &bmi, DIB_RGB_COLORS);

        // 转换为RGBA
        for (int i = 0; i < width * height; i++) {
            image.pixels[i * 4 + 0] = bgraData[i * 4 + 2];  // R
            image.pixels[i * 4 + 1] = bgraData[i * 4 + 1];  // G
            image.pixels[i * 4 + 2] = bgraData[i * 4 + 0];  // B
            image.pixels[i * 4 + 3] = bgraData[i * 4 + 3];  // A
        }

        SelectObject(hMemoryDC, hOldBitmap);
        DeleteObject(hBitmap);
        DeleteDC(hMemoryDC);
        ReleaseDC(NULL, hScreenDC);

        return true;
    }

    void Cleanup() override {
        // 无需清理
    }
};

ScreenCapture* ScreenCapture::Create() {
    return new ScreenCaptureWindows();
}

#endif

