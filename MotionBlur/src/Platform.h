#pragma once

#include <vector>
#include <cstdint>

// 图像数据结构
struct ImageData {
    uint32_t width;
    uint32_t height;
    std::vector<uint8_t> pixels;  // RGBA格式

    ImageData(uint32_t w = 0, uint32_t h = 0) : width(w), height(h) {
        pixels.resize(w * h * 4);
    }

    void resize(uint32_t w, uint32_t h) {
        width = w;
        height = h;
        pixels.resize(w * h * 4);
    }
};

// 屏幕尺寸
struct ScreenSize {
    int width;
    int height;
};

// 平台相关函数声明
class Platform {
public:
    static ScreenSize GetScreenSize();
    static bool IsWindows();
    static bool IsLinux();
};

