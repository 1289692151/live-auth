[app]
title = 成功
package.name = liveauth
package.domain = com.eipp.cuya.mallex.app
source.dir = .
version = 1.0.1
version.numeric = 10001
requirements = python3, kivy, requests, pycryptodome, androidstorage4kivy, jnius
orientation = portrait
osx.python_version = 3
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.build_tools_version = 33.0.0
android.allow_backup = True
android.logcat_filters = *:S python:D
source.include_exts = py,png,jpg,kv,atlas,ttf
# android.release = True

# 签名
android.keystore = %(source.dir)s/release.keystore
android.keystore_passwd = mallex2026
android.keyalias = mallex
android.keypasswd = mallex2026

