[app]
title = MyApp
package.name = myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
# Pinned dependencies for better reproducible builds on Android
requirements = python3,kivy==2.1.0,kivymd==1.1.1,requests
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[android]
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
# Build only 64-bit arm for modern devices (smaller APK and optimal for Snapdragon)
android.archs = arm64-v8a
android.accept_sdk_license = True
