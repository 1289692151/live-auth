from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from plyer import filechooser
import threading
import os
import sys
import json
import time
import gzip
import uuid
import base64
import random
import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

# ---------- 复制你的加密和业务函数 ----------
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCuQue3tJHQi+wm0vDThx/YUgSE
+IVlJ7K2aHtmzbflmZDP1ruVZlRxBvxzT2aw0savKRNOCc/brHqv2xEoMRRM39NF
LuDvtshM0gA8pCfUypukml1dye6sDrUbMprndaAEgsPaSBQOOkzpHvLq3wsTr3jy
DUUYn9oyokXmuCUT5wIDAQAB
-----END PUBLIC KEY-----"""
# ... 将所有常量、加密函数、业务函数复制粘贴到这里 ...
# 注意：函数中的 print 改为 self.log_callback 以便在界面显示日志

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.token_input = TextInput(hint_text='登录Token', size_hint=(1, None), height=50)
        self.image_path = TextInput(hint_text='图片路径（点击下方按钮选择）', size_hint=(1, None), height=50, readonly=True)
        self.video_path = TextInput(hint_text='视频路径（点击下方按钮选择）', size_hint=(1, None), height=50, readonly=True)
        self.id_card_input = TextInput(hint_text='身份证号', size_hint=(1, None), height=50)
        self.name_input = TextInput(hint_text='姓名', size_hint=(1, None), height=50)
        self.log_label = Label(text='日志输出：', size_hint=(1, None), height=30, halign='left', valign='top')
        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.log_content = Label(text='', size_hint_y=None, halign='left', valign='top')
        self.log_content.bind(texture_size=self.log_content.setter('size'))
        self.log_scroll.add_widget(self.log_content)

        # 按钮
        self.btn_img = Button(text='选择图片', size_hint=(1, None), height=50)
        self.btn_vid = Button(text='选择视频', size_hint=(1, None), height=50)
        self.btn_start = Button(text='开始认证', size_hint=(1, None), height=60, background_color=(0.2,0.8,0.2,1))

        self.btn_img.bind(on_press=self.pick_image)
        self.btn_vid.bind(on_press=self.pick_video)
        self.btn_start.bind(on_press=self.start_auth)

        self.add_widget(Label(text='活体认证工具', size_hint=(1, None), height=40))
        self.add_widget(self.token_input)
        self.add_widget(self.id_card_input)
        self.add_widget(self.name_input)
        self.add_widget(self.btn_img)
        self.add_widget(self.image_path)
        self.add_widget(self.btn_vid)
        self.add_widget(self.video_path)
        self.add_widget(self.btn_start)
        self.add_widget(self.log_label)
        self.add_widget(self.log_scroll)

    def log(self, msg):
        self.log_content.text += msg + "\n"
        self.log_scroll.scroll_y = 0

    def pick_image(self, instance):
        filechooser.open_file(on_selection=lambda x: self.set_path(x, 'image'))

    def pick_video(self, instance):
        filechooser.open_file(on_selection=lambda x: self.set_path(x, 'video'))

    def set_path(self, selection, file_type):
        if selection:
            path = selection[0]
            if file_type == 'image':
                self.image_path.text = path
            else:
                self.video_path.text = path

    def start_auth(self, instance):
        token = self.token_input.text.strip()
        img = self.image_path.text.strip()
        vid = self.video_path.text.strip()
        idcard = self.id_card_input.text.strip()
        name = self.name_input.text.strip()
        if not all([token, img, vid, idcard, name]):
            self.log("❌ 所有字段都必须填写！")
            return
        self.btn_start.disabled = True
        self.log("正在开始认证...")
        threading.Thread(target=self.run_auth, args=(token, img, vid, idcard, name), daemon=True).start()

    def run_auth(self, token, img, vid, idcard, name):
        # 这里调用你原来的 step1~step6 函数，但将 print 改为 self.log
        # 由于篇幅，直接嵌入你修改后的业务代码（用 self.log 代替 print）
        # 注意：加密函数、网络请求等保持不变，只需修改 print 为 self.log
        # 为了快速部署，你可以在 main.py 中定义所有函数，然后在 run_auth 中调用
        try:
            self.log("[*] 正在获取auth_token...")
            # step1...
            self.log("✅ 认证完成！")
        except Exception as e:
            self.log(f"❌ 异常：{e}")
        finally:
            self.btn_start.disabled = False

class LiveAuthApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    LiveAuthApp().run()
