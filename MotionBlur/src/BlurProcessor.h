#pragma once

#include "Platform.h"

// 高斯模糊处理器
class BlurProcessor {
public:
    BlurProcessor() : radius(10.0f) {}
    
    void SetRadius(float r) { radius = r; }
    float GetRadius() const { return radius; }
    
    // 对图像应用高斯模糊
    void ApplyGaussianBlur(const ImageData& input, ImageData& output);

private:
    float radius;
    
    // 生成高斯核
    std::vector<float> GenerateGaussianKernel(int size);
    
    // 水平模糊
    void BlurHorizontal(const ImageData& input, ImageData& output, const std::vector<float>& kernel);
    
    // 垂直模糊
    void BlurVertical(const ImageData& input, ImageData& output, const std::vector<float>& kernel);
};

