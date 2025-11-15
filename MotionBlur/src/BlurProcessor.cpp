#include "BlurProcessor.h"
#include <cmath>
#include <algorithm>

std::vector<float> BlurProcessor::GenerateGaussianKernel(int size) {
    if (size % 2 == 0) size++;  // 确保是奇数
    
    std::vector<float> kernel(size);
    float sigma = radius / 3.0f;  // 3-sigma规则
    float sum = 0.0f;
    int center = size / 2;

    for (int i = 0; i < size; i++) {
        int x = i - center;
        float value = exp(-(x * x) / (2 * sigma * sigma));
        kernel[i] = value;
        sum += value;
    }

    // 归一化
    for (float& val : kernel) {
        val /= sum;
    }

    return kernel;
}

void BlurProcessor::BlurHorizontal(const ImageData& input, ImageData& output, const std::vector<float>& kernel) {
    int kernelSize = kernel.size();
    int halfKernel = kernelSize / 2;

    for (uint32_t y = 0; y < input.height; y++) {
        for (uint32_t x = 0; x < input.width; x++) {
            float r = 0, g = 0, b = 0, a = 0;

            for (int k = 0; k < kernelSize; k++) {
                int px = x + k - halfKernel;
                px = std::max(0, std::min((int)input.width - 1, px));

                int idx = (y * input.width + px) * 4;
                float weight = kernel[k];

                r += input.pixels[idx + 0] * weight;
                g += input.pixels[idx + 1] * weight;
                b += input.pixels[idx + 2] * weight;
                a += input.pixels[idx + 3] * weight;
            }

            int idx = (y * output.width + x) * 4;
            output.pixels[idx + 0] = (uint8_t)std::min(255.0f, r);
            output.pixels[idx + 1] = (uint8_t)std::min(255.0f, g);
            output.pixels[idx + 2] = (uint8_t)std::min(255.0f, b);
            output.pixels[idx + 3] = (uint8_t)std::min(255.0f, a);
        }
    }
}

void BlurProcessor::BlurVertical(const ImageData& input, ImageData& output, const std::vector<float>& kernel) {
    int kernelSize = kernel.size();
    int halfKernel = kernelSize / 2;

    for (uint32_t y = 0; y < input.height; y++) {
        for (uint32_t x = 0; x < input.width; x++) {
            float r = 0, g = 0, b = 0, a = 0;

            for (int k = 0; k < kernelSize; k++) {
                int py = y + k - halfKernel;
                py = std::max(0, std::min((int)input.height - 1, py));

                int idx = (py * input.width + x) * 4;
                float weight = kernel[k];

                r += input.pixels[idx + 0] * weight;
                g += input.pixels[idx + 1] * weight;
                b += input.pixels[idx + 2] * weight;
                a += input.pixels[idx + 3] * weight;
            }

            int idx = (y * output.width + x) * 4;
            output.pixels[idx + 0] = (uint8_t)std::min(255.0f, r);
            output.pixels[idx + 1] = (uint8_t)std::min(255.0f, g);
            output.pixels[idx + 2] = (uint8_t)std::min(255.0f, b);
            output.pixels[idx + 3] = (uint8_t)std::min(255.0f, a);
        }
    }
}

void BlurProcessor::ApplyGaussianBlur(const ImageData& input, ImageData& output) {
    if (input.width == 0 || input.height == 0) return;

    output.resize(input.width, input.height);

    int kernelSize = (int)(radius * 2) + 1;
    if (kernelSize < 3) kernelSize = 3;
    if (kernelSize % 2 == 0) kernelSize++;

    std::vector<float> kernel = GenerateGaussianKernel(kernelSize);

    // 临时缓冲区用于中间结果
    ImageData temp(input.width, input.height);

    // 先水平模糊
    BlurHorizontal(input, temp, kernel);

    // 再垂直模糊
    BlurVertical(temp, output, kernel);
}

