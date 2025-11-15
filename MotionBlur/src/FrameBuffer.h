#pragma once

#include "Platform.h"
#include <vector>
#include <memory>

// 帧缓冲区，用于存储多帧历史图像
class FrameBuffer {
public:
    FrameBuffer(size_t maxFrames = 5) : maxFrames(maxFrames) {}

    // 添加新帧
    void AddFrame(const ImageData& frame);

    // 融合所有帧（带透明度）
    void BlendFrames(ImageData& output) const;

    // 清空缓冲区
    void Clear() { frames.clear(); }

    // 设置最大帧数
    void SetMaxFrames(size_t max) { maxFrames = max; }

    size_t GetFrameCount() const { return frames.size(); }

private:
    std::vector<ImageData> frames;
    size_t maxFrames;

    // 计算每帧的透明度权重
    float GetAlphaWeight(size_t index) const;
};

