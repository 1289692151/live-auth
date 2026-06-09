[app]
title = 看什么看
package.name = liveauth
package.domain = com.user
source.dir = .
version = 1.1
requirements = python3,kivy,plyer,pycryptodome,requests,urllib3,android
orientation = portrait
osx.python_version = 3
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
android.allow_backup = True
android.logcat_filters = *:S python:D
source.include_exts = py,png,jpg,kv,atlas,ttf
requirements = python3, kivy, requests, pycryptodome, plyer, androidstorage4kivy

