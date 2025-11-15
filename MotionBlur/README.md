# MotionBlur - 屏幕动态模糊效果

一个跨平台的C++应用程序，为整个屏幕添加动态模糊效果。支持Windows和Linux系统。

## 功能特性

- 🖥️ **全屏动态模糊**：对整个屏幕应用实时模糊效果
- 🔄 **多帧融合**：保留历史帧并使用透明度融合，产生运动模糊效果
- 🎨 **高斯模糊算法**：使用高质量的高斯模糊算法
- 🌐 **跨平台支持**：支持Windows和Linux系统
- 🪟 **透明窗口**：使用透明窗口显示模糊效果，不干扰正常使用

## 实现原理

1. **屏幕捕获**：实时捕获屏幕截图
   - Windows：使用GDI（Graphics Device Interface）
   - Linux：使用X11 API

2. **图像模糊**：对捕获的屏幕图像应用高斯模糊
   - 使用可分离的高斯滤波器（水平和垂直）
   - 可配置模糊半径

3. **多帧缓冲**：维护多帧历史图像
   - 默认保留5帧历史
   - 每帧应用不同权重（新帧权重更大）

4. **透明度融合**：将所有历史帧按权重融合
   - 使用加权平均算法
   - 产生运动轨迹效果

5. **透明窗口显示**：将融合结果显示在透明窗口上
   - Windows：使用Layered Window API
   - Linux：使用X11 Composite Extension

## 编译要求

### Windows
- CMake 3.10 或更高版本
- Visual Studio 2017 或更高版本（或其他支持C++17的编译器）
- Windows SDK

### Linux
- CMake 3.10 或更高版本
- GCC 7+ 或 Clang 5+（支持C++17）
- X11开发库
- X11 Composite Extension
- X11 Render Extension

安装Linux依赖（Ubuntu/Debian）：
```bash
sudo apt-get install build-essential cmake libx11-dev libxcomposite-dev libxrender-dev
```

安装Linux依赖（Fedora/RHEL）：
```bash
sudo dnf install gcc-c++ cmake libX11-devel libXcomposite-devel libXrender-devel
```

## 编译步骤

### Windows
```bash
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

编译完成后，可执行文件位于 `build/Release/MotionBlur.exe`

### Linux
```bash
mkdir build
cd build
cmake ..
make -j$(nproc)
```

编译完成后，可执行文件位于 `build/MotionBlur`

## 使用方法

### Windows
```bash
cd build/Release
MotionBlur.exe
```

### Linux
```bash
cd build
./MotionBlur
```

程序运行后：
- 会在整个屏幕上显示动态模糊效果
- 按 `ESC` 键退出程序

## 配置参数

可以在 `src/main.cpp` 中修改以下参数：

```cpp
blurProcessor.SetRadius(15.0f);  // 模糊半径（像素），值越大越模糊
FrameBuffer frameBuffer(5);      // 历史帧数量，默认5帧
const auto targetFrameTime = std::chrono::milliseconds(33);  // 目标帧率（~30 FPS）
```

## 性能优化建议

1. **降低帧率**：如果CPU占用过高，可以增加 `targetFrameTime` 的值
2. **减少历史帧**：减少 `FrameBuffer` 的帧数可以降低内存使用
3. **调整模糊半径**：较小的模糊半径可以提高性能

## 技术细节

### Windows实现
- 屏幕捕获：`BitBlt` + `GetDIBits`
- 透明窗口：`UpdateLayeredWindow` API
- 窗口样式：`WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST`

### Linux实现
- 屏幕捕获：`XGetImage`
- 透明窗口：ARGB视觉 + XRender
- 窗口管理：`_NET_WM_STATE_ABOVE` 属性

### 模糊算法
- 可分离的高斯模糊（水平和垂直两个方向）
- 使用3-sigma规则计算核大小
- 支持实时调整模糊半径

## 故障排除

### Linux：无法显示透明效果
确保您的窗口管理器支持Compositing（例如KWin、Compiz、Picom等）

### 性能问题
- 降低模糊半径
- 减少历史帧数量
- 增加帧间隔时间

### 窗口无法置顶
- Windows：可能需要管理员权限
- Linux：确保窗口管理器支持 `_NET_WM_STATE_ABOVE`

## 许可证

本项目代码采用MIT许可证。

## 作者

MotionBlur项目

