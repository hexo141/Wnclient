#include "ScreenCapture.h"
#include "BlurProcessor.h"
#include "TransparentWindow.h"
#include "FrameBuffer.h"
#include "Platform.h"
#include <chrono>
#include <thread>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

int main() {
    // 初始化
    ScreenCapture* capture = ScreenCapture::Create();
    if (!capture || !capture->Initialize()) {
        fprintf(stderr, "无法初始化屏幕捕获\n");
        return 1;
    }

    BlurProcessor blurProcessor;
    blurProcessor.SetRadius(15.0f);  // 模糊半径

    FrameBuffer frameBuffer(5);  // 存储5帧历史

    // 获取屏幕尺寸
    ScreenSize screenSize = Platform::GetScreenSize();
    printf("屏幕尺寸: %dx%d\n", screenSize.width, screenSize.height);

    // 创建透明窗口
    TransparentWindow* window = TransparentWindow::Create();
    if (!window || !window->Create(screenSize.width, screenSize.height)) {
        fprintf(stderr, "无法创建透明窗口\n");
        capture->Cleanup();
        delete capture;
        return 1;
    }

    window->Show();
    printf("动态模糊已启动，按ESC键退出\n");

    // 主循环
    ImageData screenImage;
    ImageData blurredImage;
    ImageData blendedImage;

    auto lastFrameTime = std::chrono::steady_clock::now();
    const auto targetFrameTime = std::chrono::milliseconds(33);  // ~30 FPS

    while (window->ProcessMessages()) {
        auto currentTime = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - lastFrameTime);

        // 控制帧率
        if (elapsed < targetFrameTime) {
            std::this_thread::sleep_for(targetFrameTime - elapsed);
        }
        lastFrameTime = std::chrono::steady_clock::now();

        // 捕获屏幕
        if (!capture->CaptureScreen(screenImage)) {
            fprintf(stderr, "屏幕捕获失败\n");
            continue;
        }

        // 应用模糊
        blurProcessor.ApplyGaussianBlur(screenImage, blurredImage);

        // 添加到帧缓冲区
        frameBuffer.AddFrame(blurredImage);

        // 融合所有帧
        frameBuffer.BlendFrames(blendedImage);

        // 更新窗口
        window->UpdateImage(blendedImage);
    }

    // 清理
    window->Destroy();
    delete window;
    capture->Cleanup();
    delete capture;

    printf("程序已退出\n");
    return 0;
}

