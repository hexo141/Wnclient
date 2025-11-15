#pragma once

#include "Platform.h"

// 透明窗口接口
class TransparentWindow {
public:
    virtual ~TransparentWindow() = default;
    virtual bool Create(int width, int height) = 0;
    virtual void UpdateImage(const ImageData& image) = 0;
    virtual void Show() = 0;
    virtual void Hide() = 0;
    virtual void Destroy() = 0;
    virtual bool ProcessMessages() = 0;  // 处理窗口消息，返回false表示应该退出

    static TransparentWindow* Create();
};

