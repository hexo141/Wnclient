#include "FrameBuffer.h"
#include <algorithm>
#include <cmath>

void FrameBuffer::AddFrame(const ImageData& frame) {
    frames.push_back(frame);
    
    // 保持最大帧数
    if (frames.size() > maxFrames) {
        frames.erase(frames.begin());
    }
}

float FrameBuffer::GetAlphaWeight(size_t index) const {
    if (frames.empty()) return 0.0f;
    
    // 越新的帧权重越大，使用指数衰减
    // 最新帧权重最大，逐渐递减
    size_t totalFrames = frames.size();
    size_t reverseIndex = totalFrames - 1 - index;
    
    // 使用线性衰减：最新帧 = 1.0，最旧帧 = 0.2
    float minWeight = 0.2f;
    float maxWeight = 1.0f;
    
    if (totalFrames == 1) return maxWeight;
    
    float t = (float)reverseIndex / (totalFrames - 1);
    return minWeight + (maxWeight - minWeight) * (1.0f - t);
}

void FrameBuffer::BlendFrames(ImageData& output) const {
    if (frames.empty()) {
        output.resize(0, 0);
        return;
    }

    // 使用第一帧的尺寸
    const ImageData& firstFrame = frames[0];
    output.resize(firstFrame.width, firstFrame.height);

    // 初始化输出为0
    std::fill(output.pixels.begin(), output.pixels.end(), 0);

    // 计算总权重用于归一化
    float totalWeight = 0.0f;
    for (size_t i = 0; i < frames.size(); i++) {
        totalWeight += GetAlphaWeight(i);
    }

    // 如果总权重为0，返回
    if (totalWeight == 0.0f) return;

    // 融合所有帧
    for (size_t i = 0; i < frames.size(); i++) {
        const ImageData& frame = frames[i];
        float weight = GetAlphaWeight(i) / totalWeight;

        // 确保尺寸匹配
        if (frame.width != output.width || frame.height != output.height) {
            continue;
        }

        for (size_t j = 0; j < output.pixels.size(); j += 4) {
            float alpha = frame.pixels[j + 3] / 255.0f;
            float blendWeight = weight * alpha;

            output.pixels[j + 0] += (uint8_t)(frame.pixels[j + 0] * blendWeight);
            output.pixels[j + 1] += (uint8_t)(frame.pixels[j + 1] * blendWeight);
            output.pixels[j + 2] += (uint8_t)(frame.pixels[j + 2] * blendWeight);
            
            // Alpha通道累加
            output.pixels[j + 3] += (uint8_t)(frame.pixels[j + 3] * weight);
        }
    }

    // 确保Alpha不超过255
    for (size_t i = 3; i < output.pixels.size(); i += 4) {
        output.pixels[i] = std::min(255, (int)output.pixels[i]);
    }
}

