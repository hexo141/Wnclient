#pragma once

#include "Platform.h"

// 屏幕捕获接口
class ScreenCapture {
public:
    virtual ~ScreenCapture() = default;
    virtual bool Initialize() = 0;
    virtual bool CaptureScreen(ImageData& image) = 0;
    virtual void Cleanup() = 0;

    static ScreenCapture* Create();
};

