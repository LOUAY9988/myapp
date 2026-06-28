[app]
title = MyApp
package.name = myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,requests
orientation = portrait

[buildozer]
log_level = 2

[android]
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
