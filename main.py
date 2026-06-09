# -*- coding: utf-8 -*-
import os
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path, resource_find

# ========== 字体设置 ==========
if hasattr(os, 'environ') and 'ANDROID_ARGUMENT' in os.environ:
    font_path = resource_find('fonts/DroidSansFallback.ttf')
    if font_path:
        LabelBase.register(name='Roboto', fn_regular=font_path)
else:
    resource_add_path(r"C:\Windows\Fonts")
    LabelBase.register(name='Roboto', fn_regular='msyh.ttc')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from plyer import filechooser
import threading
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

# ========== 配置 ==========
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCuQue3tJHQi+wm0vDThx/YUgSE
+IVlJ7K2aHtmzbflmZDP1ruVZlRxBvxzT2aw0savKRNOCc/brHqv2xEoMRRM39NF
LuDvtshM0gA8pCfUypukml1dye6sDrUbMprndaAEgsPaSBQOOkzpHvLq3wsTr3jy
DUUYn9oyokXmuCUT5wIDAQAB
-----END PUBLIC KEY-----"""

APP_KEY = "kTee33zj"
BUNDLE_ID = "com.mallex.pg.app"
HOTFIX_VERSION = "91"
LANGUAGE = "zh-CN"
OS = "Android"
VERSION = "1.3.1"
SIGN_VERSION = "2"
FIXED_SIGN = "b87766420f91cbfcfde1c0d232de5b99"

URL_AUTH_TOKEN = "https://api.mallex.io/gateway/user/realNameToken"
URL_IMAGE = "https://wsapi.253.com/identity_auth/faceAlive/v3/imageVerify"
URL_ACTIONS = "https://wsapi.253.com/identity_auth/faceAlive/v3/actions"
URL_VIDEO = "https://wsapi.253.com/identity_auth/faceAlive/v3/videoVerify"
URL_SUBMIT_REAL = "https://api.mallex.io/gateway/user/submitRealName"
URL_FIND_ACCOUNT = "https://api.mallex.io/gateway/realnameReview/createUserRealNameReviewForFind"

ACTION_MAP = {"0":"闭眼", "5":"点头", "6":"张口", "7":"左右摇头"}

# ========== 工具函数 ==========
def gen_request_id():
    return str(random.randint(10**18, 10**19-1))

def gen_sign_time():
    return time.strftime("%Y%m%d%H%M%S", time.gmtime())

def gen_sign_timestamp():
    return str(int(time.time() * 1000))

def build_mallex_headers(token):
    return {
        "User-Agent": "okhttp/4.9.2",
        "accept": "application/json, text/plain, */*",
        "bundleid": BUNDLE_ID,
        "hotfixversion": HOTFIX_VERSION,
        "language": LANGUAGE,
        "os": OS,
        "version": VERSION,
        "sign-version": SIGN_VERSION,
        "sign": FIXED_SIGN,
        "sign-time": gen_sign_time(),
        "sign-timestamp": gen_sign_timestamp(),
        "requestid": gen_request_id(),
        "token": token,
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive"
    }

def rsa_encrypt(data: bytes) -> str:
    public_key = RSA.import_key(RSA_PUBLIC_KEY)
    cipher = PKCS1_v1_5.new(public_key)
    encrypted = cipher.encrypt(data)
    return encrypted.hex().upper()

def aes_encrypt(plain: bytes, key: str, iv: str) -> bytes:
    key_bytes = key.encode("utf-8")
    iv_bytes = iv.encode("utf-8")
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded = pad(plain, AES.block_size)
    return cipher.encrypt(padded)

def encrypt_file(file_path: str):
    with open(file_path, "rb") as f:
        raw = f.read()
    uid = uuid.uuid4().hex
    key = uid[:16]
    iv = uid[16:]
    compressed = gzip.compress(raw)
    encrypted = aes_encrypt(compressed, key, iv)
    b64_data = base64.b64encode(encrypted).decode()
    data_key = "0" + rsa_encrypt(uid.encode("utf-8"))
    return b64_data, data_key, uid

def fetch_proxy(api_url):
    """从API获取代理IP"""
    try:
        resp = requests.get(api_url, timeout=10)
        if resp.status_code == 200:
            proxy = resp.text.strip()
            if ':' in proxy:
                return proxy
    except:
        pass
    return None

def test_proxy(proxy_addr):
    """测试代理是否可用"""
    try:
        proxies = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"}
        resp = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=8)
        if resp.status_code == 200:
            return True
    except:
        pass
    return False

def get_proxies(proxy_addr):
    if proxy_addr:
        return {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"}
    return None

def safe_request(method, url, log, proxy_api=None, use_proxy=True, **kwargs):
    """网络请求，若use_proxy为True且提供了proxy_api，则使用代理；否则直连。
       如果代理失败，自动更换一次代理重试。
    """
    if use_proxy and proxy_api:
        proxy = fetch_proxy(proxy_api)
        if proxy and test_proxy(proxy):
            kwargs['proxies'] = get_proxies(proxy)
            log(f"  [代理] 使用代理 {proxy}")
        else:
            log("  [代理] 未获取到有效代理，使用直连")
    try:
        return requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as e:
        if use_proxy and proxy_api and 'proxies' in kwargs:
            log(f"  [代理] 代理失败({e})，尝试更换IP重试...")
            new_proxy = fetch_proxy(proxy_api)
            if new_proxy and test_proxy(new_proxy):
                kwargs['proxies'] = get_proxies(new_proxy)
                try:
                    return requests.request(method, url, **kwargs)
                except:
                    pass
        raise e

# ========== 业务步骤（图片/视频上传强制不走代理） ==========
def step1_get_auth_token(log, login_token, proxy_api=None, use_proxy=True):
    log("⏳ 正在获取活体检测授权...")
    try:
        headers = build_mallex_headers(login_token)
        resp = safe_request('GET', URL_AUTH_TOKEN, log, proxy_api, use_proxy, headers=headers, timeout=15, verify=False)
        data = resp.json()
        if data.get("code") != "OK":
            log(f"❌ 授权失败，错误码：{data.get('code')}，信息：{data.get('msg', '未知')}")
            return None
        auth_token = data["data"]
        log("✅ 授权成功")
        return auth_token
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return None

def step2_upload_image(log, image_path, auth_token):
    """图片上传永远不走代理"""
    log("⏳ 正在上传人脸图片...")
    if not os.path.exists(image_path):
        log("❌ 图片文件不存在")
        return False
    b64, dk, uid = encrypt_file(image_path)
    headers = {
        "Content-Type": "application/json",
        "Content-Encoding": "gzip",
        "Data-Key": dk,
        "User-Agent": "Dalvik/2.1.0"
    }
    payload = {
        "images": [{"image": b64, "face_field": "quality", "image_type": "BASE64"}],
        "app_key": APP_KEY,
        "platform_type": 2,
        "auth_token": auth_token
    }
    try:
        # 强制直连
        resp = requests.post(URL_IMAGE, headers=headers, json=payload, timeout=30, verify=False)
        result = resp.json()
        if result.get("code") == "000000":
            score = result.get("data", {}).get("face_liveness", "未知")
            log(f"✅ 图片上传成功（活体分数：{score}）")
            return True
        else:
            log(f"❌ 图片上传失败：{result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False

def step3_get_session_id(log, auth_token, proxy_api=None, use_proxy=True):
    log("⏳ 正在获取视频检测指令...")
    payload = {
        "app_key": APP_KEY,
        "actions_count": "1",
        "auth_token": auth_token,
        "platform_type": 2,
        "security_level": 1
    }
    try:
        resp = safe_request('POST', URL_ACTIONS, log, proxy_api, use_proxy, json=payload, timeout=15, verify=False)
        data = resp.json()
        if data.get("code") != "000000":
            log(f"❌ 获取检测指令失败：{data}")
            return None, None
        session_id = data["data"]["session_id"]
        actions = data["data"].get("actions", [])
        action_desc = [ACTION_MAP.get(a, a) for a in actions]
        log(f"✅ 本次需要做的动作：{', '.join(action_desc)}")
        return session_id, actions
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return None, None

def step4_upload_video(log, video_path, auth_token, session_id):
    """视频上传永远不走代理"""
    log("⏳ 正在上传视频...")
    if not os.path.exists(video_path):
        log("❌ 视频文件不存在")
        return False, None, ""
    b64, dk, uid = encrypt_file(video_path)
    headers = {
        "Content-Type": "application/json",
        "Content-Encoding": "gzip",
        "Data-Key": dk,
        "User-Agent": "Dalvik/2.1.0"
    }
    payload = {
        "app_key": APP_KEY,
        "platform_type": 2,
        "session_id": session_id,
        "auth_token": auth_token,
        "video": b64,
        "video_type": "BASE64"
    }
    try:
        # 强制直连
        resp = requests.post(URL_VIDEO, headers=headers, json=payload, timeout=60, verify=False)
        result = resp.json()
        if result.get("code") == "000000":
            action_verify = result.get("data", {}).get("action_verify", "")
            score = result.get("data", {}).get("score", 0)
            if action_verify == "pass":
                log(f"✅ 视频验证通过（动作完成度：{score}）")
                return True, action_verify, ""
            else:
                reason = f"动作完成度 {score} 过低"
                log(f"⚠️ 视频中动作未通过。{reason}")
                return True, action_verify, reason
        else:
            log(f"❌ 视频上传失败：{result.get('msg', '未知错误')}")
            return False, None, result.get('msg', '')
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False, None, str(e)

def step5_submit_real_name(log, login_token, id_card, real_name, proxy_api=None, use_proxy=True):
    log("⏳ 正在提交实名认证...")
    headers = build_mallex_headers(login_token)
    headers["Content-Type"] = "application/json"
    payload = {"idCard": id_card, "realName": real_name}
    try:
        resp = safe_request('POST', URL_SUBMIT_REAL, log, proxy_api, use_proxy, headers=headers, json=payload, timeout=15, verify=False)
        result = resp.json()
        code = result.get("code")
        if code == "OK" and result.get("data", {}).get("status") == "pass":
            log("✅ 实名认证通过！")
            return True, False
        elif code == "REAL_NAME_AUTH_OTHER":
            log("⚠️ 该身份证已被其他账号绑定，正在尝试找回...")
            return False, True
        else:
            log(f"❌ 实名认证失败：{result.get('msg', '未知错误')}")
            return False, False
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False, False

def step6_find_account(log, login_token, id_card, proxy_api=None, use_proxy=True):
    log("⏳ 正在申请找回身份证...")
    headers = build_mallex_headers(login_token)
    headers["Content-Type"] = "application/json"
    payload = {"idCard": id_card, "liveAuthPassed": 1, "defineCondition": "createNew", "defined": "yes"}
    try:
        resp = safe_request('POST', URL_FIND_ACCOUNT, log, proxy_api, use_proxy, headers=headers, json=payload, timeout=15, verify=False)
        result = resp.json()
        if result.get("code") == "OK" and result.get("data") == True:
            log("✅ 找回成功！")
            return True
        else:
            log(f"❌ 找回失败：{result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False

# ========== 主界面 ==========
class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.token_input = TextInput(hint_text='登录Token', size_hint=(1, None), height=50)
        self.image_path = TextInput(hint_text='图片路径', size_hint=(1, None), height=50, readonly=True)
        self.video_path = TextInput(hint_text='视频路径', size_hint=(1, None), height=50, readonly=True)
        self.id_card_input = TextInput(hint_text='身份证号', size_hint=(1, None), height=50)
        self.name_input = TextInput(hint_text='姓名', size_hint=(1, None), height=50)

        # 代理设置
        proxy_box = BoxLayout(size_hint=(1, None), height=50, spacing=5)
        proxy_box.add_widget(Label(text='代理API', size_hint=(None, 1), width=60))
        self.proxy_api_input = TextInput(
            text='',
            size_hint=(1, 1), multiline=False)
        proxy_box.add_widget(self.proxy_api_input)
        self.btn_get_proxy = Button(text='获取代理', size_hint=(None, 1), width=80)
        self.btn_get_proxy.bind(on_press=self.on_get_proxy)
        proxy_box.add_widget(self.btn_get_proxy)
        self.proxy_status_label = Label(text='未获取', size_hint=(None, 1), width=100, halign='left', valign='middle')
        proxy_box.add_widget(self.proxy_status_label)
        self.use_proxy_check = CheckBox(active=False, size_hint=(None, 1), width=50)
        proxy_box.add_widget(Label(text='启用代理', size_hint=(None, 1), width=70))
        proxy_box.add_widget(self.use_proxy_check)

        self.status_label = Label(text='状态：准备就绪', size_hint=(1, None), height=30, halign='left', valign='top', color=(0,1,0,1))
        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.log_content = Label(text='', size_hint=(1, None), halign='left', valign='top')
        self.log_content.bind(texture_size=self.log_content.setter('size'))
        self.log_scroll.add_widget(self.log_content)

        self.btn_img = Button(text='选择图片', size_hint=(1, None), height=50)
        self.btn_vid = Button(text='选择视频', size_hint=(1, None), height=50)
        self.btn_start = Button(text='开始认证', size_hint=(1, None), height=60, background_color=(0.2,0.8,0.2,1))

        self.btn_img.bind(on_press=self.pick_image)
        self.btn_vid.bind(on_press=self.pick_video)
        self.btn_start.bind(on_press=self.start_auth)

        self.add_widget(Label(text='活体认证助手', size_hint=(1, None), height=40))
        self.add_widget(self.token_input)
        self.add_widget(self.id_card_input)
        self.add_widget(self.name_input)
        self.add_widget(self.btn_img)
        self.add_widget(self.image_path)
        self.add_widget(self.btn_vid)
        self.add_widget(self.video_path)
        self.add_widget(proxy_box)
        self.add_widget(self.btn_start)
        self.add_widget(self.status_label)
        self.add_widget(Label(text='认证日志：', size_hint=(1, None), height=30, halign='left', valign='top'))
        self.add_widget(self.log_scroll)

        self.continue_event = threading.Event()
        self.user_confirmed = False
        self.new_video_path = ""
        self.last_video_error = ""

        # 日志左对齐
        self.log_content.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))

    def log(self, msg):
        self.log_content.text += msg + "\n"
        self.log_scroll.scroll_y = 0

    def set_status(self, text, color=(0,1,0,1)):
        self.status_label.text = "状态：" + text
        self.status_label.color = color

    def on_get_proxy(self, instance):
        api_url = self.proxy_api_input.text.strip()
        if not api_url:
            self.log("❌ 请输入代理API地址")
            return
        self.log("⏳ 正在获取代理IP...")
        def _get():
            proxy = fetch_proxy(api_url)
            if proxy:
                if test_proxy(proxy):
                    self.proxy_addr = proxy
                    Clock.schedule_once(lambda dt: self.proxy_status_label.setter('text')(self.proxy_status_label, proxy))
                    Clock.schedule_once(lambda dt: self.log(f"✅ 获取代理成功，当前代理：{proxy}"))
                else:
                    self.proxy_addr = None
                    Clock.schedule_once(lambda dt: self.proxy_status_label.setter('text')(self.proxy_status_label, '无效'))
                    Clock.schedule_once(lambda dt: self.log("❌ 代理无效，请更换API"))
            else:
                self.proxy_addr = None
                Clock.schedule_once(lambda dt: self.proxy_status_label.setter('text')(self.proxy_status_label, '获取失败'))
                Clock.schedule_once(lambda dt: self.log("❌ 获取代理失败"))
        threading.Thread(target=_get, daemon=True).start()

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
            self.log("❌ 请填写所有信息并选择文件")
            self.set_status("信息不完整", color=(1,0,0,1))
            return

        use_proxy = self.use_proxy_check.active
        proxy_api = self.proxy_api_input.text.strip() if use_proxy else None
        self.btn_start.disabled = True
        self.log("===== 开始认证流程 =====")
        self.set_status("正在认证...", color=(1,1,0,1))
        threading.Thread(target=self.run_auth, args=(token, img, vid, idcard, name, use_proxy, proxy_api), daemon=True).start()

    def run_auth(self, token, img, vid, idcard, name, use_proxy, proxy_api):
        try:
            auth_token = step1_get_auth_token(self.log, token, proxy_api, use_proxy)
            if not auth_token:
                self.set_status("授权失败", (1,0,0,1))
                return

            # 图片上传永远不使用代理
            if not step2_upload_image(self.log, img, auth_token):
                self.set_status("图片上传失败", (1,0,0,1))
                return

            while True:
                session_id, actions = step3_get_session_id(self.log, auth_token, proxy_api, use_proxy)
                if not session_id:
                    self.set_status("获取指令失败", (1,0,0,1))
                    return

                action_desc = [ACTION_MAP.get(a, a) for a in actions] if actions else []
                action_str = ', '.join(action_desc) if action_desc else "无特定动作"
                self.log(f"📢 视频需包含动作：{action_str}")

                confirmed, new_vid = self.ask_user_for_video(action_str, vid, self.last_video_error)
                if not confirmed:
                    self.set_status("已取消", (1,0,0,1))
                    return
                if new_vid:
                    vid = new_vid
                    self.video_path.text = vid

                # 视频上传永远不使用代理
                ok, action_verify, err_msg = step4_upload_video(self.log, vid, auth_token, session_id)
                if not ok:
                    self.set_status("视频上传失败", (1,0,0,1))
                    return

                if action_verify == "pass":
                    self.last_video_error = ""
                    break
                else:
                    self.last_video_error = err_msg
                    self.log("🔄 动作未通过，将重新获取指令并重试...")
                    time.sleep(1)

            success, need_find = step5_submit_real_name(self.log, token, idcard, name, proxy_api, use_proxy)
            if success:
                self.set_status("实名认证通过", (0,1,0,1))
                self.log("🎉 恭喜！实名认证全部完成")
            elif need_find:
                if step6_find_account(self.log, token, idcard, proxy_api, use_proxy):
                    self.set_status("找回成功", (0,1,0,1))
                    self.log("🎉 找回并认证成功！")
                else:
                    self.set_status("找回失败", (1,0,0,1))
                    self.log("⚠️ 请稍后重试找回步骤")
            else:
                self.set_status("实名认证失败", (1,0,0,1))
                self.log("❌ 认证失败，请检查日志")
        except Exception as e:
            self.log(f"❌ 程序异常：{e}")
            self.set_status("程序异常", (1,0,0,1))
        finally:
            self.btn_start.disabled = False
            self.log("===== 流程结束 =====")

    def ask_user_for_video(self, action_str, current_video, error_msg=""):
        self.continue_event.clear()
        self.user_confirmed = False
        self.new_video_path = ""
        Clock.schedule_once(lambda dt: self._show_video_popup(action_str, current_video, error_msg), 0)
        self.continue_event.wait()
        return self.user_confirmed, self.new_video_path

    def _show_video_popup(self, action_str, current_video, error_msg):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text=f"当前视频：{os.path.basename(current_video)}"))
        layout.add_widget(Label(text=f"要求动作：{action_str}"))
        if error_msg:
            layout.add_widget(Label(text=f"⚠️ 上次失败原因：{error_msg}", color=(1,0,0,1), size_hint_y=None, height=40))
        btn_box = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        popup = Popup(title="确认视频文件", content=layout, size_hint=(0.9, 0.5), auto_dismiss=False)

        def on_continue(instance):
            self.user_confirmed = True
            popup.dismiss()
            self.continue_event.set()

        def on_change(instance):
            popup.dismiss()
            filechooser.open_file(on_selection=lambda x: self._on_new_video(x, action_str))

        btn_continue = Button(text="使用当前视频")
        btn_change = Button(text="更换视频")
        btn_continue.bind(on_press=on_continue)
        btn_change.bind(on_press=on_change)
        btn_box.add_widget(btn_continue)
        btn_box.add_widget(btn_change)
        layout.add_widget(btn_box)
        popup.open()

    def _on_new_video(self, selection, action_str):
        if selection:
            new_path = selection[0]
            self.new_video_path = new_path
            self.video_path.text = new_path
        Clock.schedule_once(lambda dt: self._show_video_popup(action_str, self.new_video_path or self.video_path.text, self.last_video_error), 0)

class LiveAuthApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    LiveAuthApp().run()
