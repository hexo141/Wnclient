cmake_minimum_required(VERSION 3.10)
project(MotionBlur)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 根据平台设置
if(WIN32)
    add_definitions(-DWIN32_LEAN_AND_MEAN)
    set(PLATFORM_SOURCES
        src/PlatformWindows.cpp
        src/ScreenCaptureWindows.cpp
        src/TransparentWindowWindows.cpp
    )
    set(PLATFORM_LIBS
        user32
        gdi32
        dwmapi
    )
else()
    # Linux
    find_package(X11 REQUIRED)
    set(PLATFORM_SOURCES
        src/PlatformLinux.cpp
        src/ScreenCaptureLinux.cpp
        src/TransparentWindowLinux.cpp
    )
    set(PLATFORM_LIBS
        ${X11_LIBRARIES}
        X11
        Xcomposite
        Xrender
    )
    include_directories(${X11_INCLUDE_DIR})
endif()

# 源文件
set(SOURCES
    src/main.cpp
    src/BlurProcessor.cpp
    src/FrameBuffer.cpp
    ${PLATFORM_SOURCES}
)

# 可执行文件
add_executable(${PROJECT_NAME} ${SOURCES})

# 链接库
target_link_libraries(${PROJECT_NAME} ${PLATFORM_LIBS})

# 编译选项
if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE /W4)
else()
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra)
endif()

