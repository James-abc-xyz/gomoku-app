[app]

title = 五子棋
package.name = gomoku
package.domain = org.gomoku

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

log_level = 2

[buildozer]
build_dir = ./.buildozer
bin_dir = ./bin
