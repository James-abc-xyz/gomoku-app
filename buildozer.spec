[app]

# 应用标题
title = 五子棋

# 包名（反向域名格式）
package.name = gomoku

# 包域名
package.domain = org.gomoku

# 源码目录（相对于 buildozer.spec 位置）
source.dir = .

# 包含的源文件
source.include_exts = py,png,jpg,kv,atlas

# 版本号
version = 1.0

# 主入口
entry_point = main.py:GomokuApp

# 依赖库
requirements = python3,kivy==2.3.0,kivymd

# 方向（portrait=竖屏，landscape=横屏）
orientation = portrait

# 是否全屏
fullscreen = 1

# Android 配置
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.arch = arm64-v8a

# 图标（如果有图标文件可以指定）
# icon.filename = %(source.dir)s/icon.png

# presplash（启动图）
# presplash.filename = %(source.dir)s/presplash.png

# Android 应用唯一标识
android.accept_sdk_license = True

# 日志级别
log_level = 2

[buildozer]
# 构建目录
build_dir = ./.buildozer
# APK输出目录
bin_dir = ./bin
