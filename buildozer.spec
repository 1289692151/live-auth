[app]
title = 看什么看
package.name = liveauth
package.domain = com.user
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,plyer,pycryptodome,requests,urllib3,android
orientation = portrait
osx.python_version = 3

# 权限
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Android 版本
android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a    # 注意这里是 archs，不是 arch
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
# 删除 android.sdk 这一行！
# 其他保持不变...
