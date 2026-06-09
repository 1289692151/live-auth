# -*- coding: utf-8 -*-
import os
import threading, json, time, gzip, uuid, base64, random
import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

# ========== 字体注册 ==========
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path, resource_find
if os.path.exists('font.ttf'):
    font_path = 'font.ttf'
else:
    font_path = resource_find('fonts/DroidSansFallback.ttf')
    if not font_path:
        font_path = 'font.ttf'
LabelBase.register(name='Roboto', fn_regular=font_path)

# ========== Kivy 模块 ==========
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.utils import platform
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore

# 平台相关导入
HAS_AS4K = False
if platform == 'android':
    try:
        from androidstorage4kivy import Chooser, SharedStorage
        HAS_AS4K = True
    except Exception as e:
        Logger.warning(f"androidstorage4kivy 未安装: {e}")

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Rectangle, RoundedRectangle

# ========== 常量 ==========
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCuQue3tJHQi+wm0vDThx/YUgSE
+IVlJ7K2aHtmzbflmZDP1ruVZlRxBvxzT2aw0savKRNOCc/brHqv2xEoMRRM39NF
LuDvtshM0gA8pCfUypukml1dye6sDrUbMprndaAEgsPaSBQOOkzpHvLq3wsTr3jy
DUUYn9oyokXmuCUT5wIDAQAB
-----END PUBLIC KEY-----"""
APP_KEY = "aeQqc6Pm"
BUNDLE_ID = "com.eipp.cuya.mallex.app"
HOTFIX_VERSION = "93"
LANGUAGE = "zh-CN"
OS = "Android"
VERSION = "1.4.1"
SIGN_VERSION = "2"
FIXED_SIGN = "b87766420f91cbfcfde1c0d232de5b99"
URL_AUTH_TOKEN = "https://api.mallex.io/gateway/user/realNameToken"
URL_IMAGE = "https://wsapi.253.com/identity_auth/faceAlive/v3/imageVerify"
URL_ACTIONS = "https://wsapi.253.com/identity_auth/faceAlive/v3/actions"
URL_VIDEO = "https://wsapi.253.com/identity_auth/faceAlive/v3/videoVerify"
URL_SUBMIT_REAL = "https://api.mallex.io/gateway/user/submitRealName"
URL_FIND_ACCOUNT = "https://api.mallex.io/gateway/realnameReview/createUserRealNameReviewForFind"
ACTION_MAP = {"0": "闭眼", "5": "点头", "6": "张口", "7": "左右摇头"}

# 颜色
COLOR_BG = (0.96, 0.96, 0.98, 1)
COLOR_CARD = (1, 1, 1, 1)
COLOR_PRIMARY = (0.2, 0.6, 0.86, 1)
COLOR_SUCCESS = (0.2, 0.78, 0.35, 1)
COLOR_DANGER = (0.94, 0.30, 0.30, 1)
COLOR_WARN = (0.96, 0.62, 0.20, 1)
COLOR_TEXT = (0.2, 0.2, 0.2, 1)
COLOR_TEXT_LIGHT = (0.5, 0.5, 0.5, 1)
COLOR_INPUT_BG = (0.97, 0.97, 0.99, 1)
COLOR_LOG_BG = (0.12, 0.12, 0.14, 1)
COLOR_LOG_TEXT = (0.95, 0.95, 0.95, 1)

DEFAULT_PROXY_API = 'http://api.zhiliandaili.cn/traffic/getip?linePoolIndex=1&packid=12&qty=1&time=11&port=1&format=txt&ss=1&dt=0&isp=0&ct=1&uid=51919&usertype=17&accessName=15372328495&accessPassword=01c8fef2b09e2bc25039f1470b730129'


# ========== Android URI 复制工具 ==========
def android_copy_uri_to_local(uri_str):
    if not uri_str or uri_str.startswith('/'):
        return uri_str
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        FileOutputStream = autoclass('java.io.FileOutputStream')
        BufferedInputStream = autoclass('java.io.BufferedInputStream')
        BufferedOutputStream = autoclass('java.io.BufferedOutputStream')
        Uri = autoclass('android.net.Uri')
        OpenableColumns = autoclass('android.provider.OpenableColumns')

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        parsed_uri = Uri.parse(uri_str)

        file_name = f"upload_{int(time.time() * 1000)}.bin"
        try:
            cursor = resolver.query(parsed_uri, None, None, None, None)
            if cursor and cursor.moveToFirst():
                idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if idx >= 0:
                    n = cursor.getString(idx)
                    if n:
                        file_name = n
            if cursor:
                cursor.close()
        except Exception:
            pass

        cache_dir = activity.getCacheDir().getAbsolutePath()
        dest_path = os.path.join(cache_dir, f"up_{int(time.time()*1000)}_{file_name}")

        istream = resolver.openInputStream(parsed_uri)
        bis = BufferedInputStream(istream)
        fos = FileOutputStream(dest_path)
        bos = BufferedOutputStream(fos)

        buf = bytearray(8192)
        while True:
            n = bis.read(buf)
            if n <= 0:
                break
            bos.write(buf, 0, n)
        bos.flush()
        bos.close()
        fos.close()
        bis.close()
        istream.close()
        return dest_path
    except Exception as e:
        Logger.error(f"URI 复制失败: {e}")
        return None


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
        "bundleid": BUNDLE_ID, "hotfixversion": HOTFIX_VERSION,
        "language": LANGUAGE, "os": OS, "version": VERSION,
        "sign-version": SIGN_VERSION, "sign": FIXED_SIGN,
        "sign-time": gen_sign_time(), "sign-timestamp": gen_sign_timestamp(),
        "requestid": gen_request_id(), "token": token,
        "Accept-Encoding": "gzip", "Connection": "Keep-Alive"
    }

def rsa_encrypt(data: bytes) -> str:
    pub = RSA.import_key(RSA_PUBLIC_KEY)
    return PKCS1_v1_5.new(pub).encrypt(data).hex().upper()

def aes_encrypt(plain, key, iv):
    return AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8")).encrypt(
        pad(plain, AES.block_size))

def encrypt_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    with open(file_path, "rb") as f:
        raw = f.read()
    uid = uuid.uuid4().hex
    key, iv = uid[:16], uid[16:]
    compressed = gzip.compress(raw)
    enc = aes_encrypt(compressed, key, iv)
    b64 = base64.b64encode(enc).decode()
    dk = "0" + rsa_encrypt(uid.encode("utf-8"))
    return b64, dk, uid

def fetch_proxy(api_url):
    """从API获取代理IP"""
    try:
        r = requests.get(api_url, timeout=15)
        if r.status_code == 200:
            text = r.text.strip()
            if ':' in text and len(text) < 50:
                return text
    except:
        pass
    return None

def test_proxy(proxy_addr):
    """测试代理可用性 - 只测连接速度，毫秒级返回"""
    proxies = {
        "http": f"http://{proxy_addr}",
        "https": f"http://{proxy_addr}"
    }
    # ★ 用 HEAD 请求（不下载内容）+ 轻量接口
    test_urls = [
        "http://www.baidu.com",
        "http://www.qq.com",
    ]
    for url in test_urls:
        try:
            # ★ 关键：用 stream=True + 立即关闭，只测连接和响应头
            resp = requests.get(
                url, proxies=proxies, timeout=4,
                headers={"User-Agent": "Mozilla/5.0",
                         "Connection": "close"},  # 关键：不保持连接
                allow_redirects=False,
                stream=True
            )
            # 拿到响应码立即关闭
            status_ok = resp.status_code in (200, 301, 302)
            resp.close()
            if status_ok:
                return True
        except:
            continue
    return False


def safe_request(method, url, log, proxy_api=None, use_proxy=True, timeout=30, **kwargs):
    """代理请求 - 支持多次重试和自动剔除失败IP"""
    if use_proxy and proxy_api:
        for attempt in range(3):
            proxy = fetch_proxy(proxy_api)
            if not proxy:
                log(f"  [代理] 第{attempt+1}次获取IP失败")
                time.sleep(1)
                continue
            log(f"  [代理] 第{attempt+1}次测试 {proxy} ...")
            if test_proxy(proxy):
                kwargs['proxies'] = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                log(f"  [代理] ✅ 使用代理 {proxy}")
                break
            else:
                log(f"  [代理] ❌ {proxy} 不可用，重新获取")
                time.sleep(0.5)
        else:
            log("  [代理] 多次获取均失败，尝试直连")

    try:
        return requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.RequestException as e:
        if use_proxy and proxy_api and 'proxies' in kwargs:
            log(f"  [代理] 请求失败，尝试更换IP...")
            new_proxy = fetch_proxy(proxy_api)
            if new_proxy and test_proxy(new_proxy):
                kwargs['proxies'] = {"http": f"http://{new_proxy}", "https": f"http://{new_proxy}"}
                log(f"  [代理] 换用 {new_proxy} 重试")
                try:
                    return requests.request(method, url, timeout=timeout, **kwargs)
                except:
                    pass
        raise e



# ========== 业务函数 ==========
def step1_get_auth_token(log, token, proxy_api=None, use_proxy=False):
    log("⏳ 正在获取活体检测授权...")
    try:
        resp = safe_request('GET', URL_AUTH_TOKEN, log, proxy_api, use_proxy,
                            headers=build_mallex_headers(token), timeout=15, verify=False)
        data = resp.json()
        if data.get("code") != "OK":
            log(f"❌ 授权失败：{data.get('msg')}")
            return None
        log("✅ 授权成功")
        return data["data"]
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return None

def step2_upload_image(log, img_path, auth_token):
    log("⏳ 正在上传人脸图片...")
    try:
        b64, dk, _ = encrypt_file(img_path)
    except Exception as e:
        log(f"❌ 图片处理失败：{e}")
        return False
    headers = {"Content-Type": "application/json", "Content-Encoding": "gzip",
               "Data-Key": dk, "User-Agent": "Dalvik/2.1.0"}
    payload = {"images": [{"image": b64, "face_field": "quality", "image_type": "BASE64"}],
               "app_key": APP_KEY, "platform_type": 2, "auth_token": auth_token}
    try:
        resp = requests.post(URL_IMAGE, headers=headers, json=payload, timeout=30, verify=False)
        result = resp.json()
        if result.get("code") == "000000":
            score = result.get("data", {}).get("face_liveness", "未知")
            log(f"✅ 图片上传成功（活体分数：{score}）")
            return True
        else:
            log(f"❌ 图片上传失败：{result.get('msg')}")
            return False
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False

def step3_get_session_id(log, auth_token, proxy_api=None, use_proxy=False):
    log("⏳ 正在获取视频检测指令...")
    payload = {"app_key": APP_KEY, "actions_count": "1", "auth_token": auth_token,
               "platform_type": 2, "security_level": 1}
    try:
        resp = safe_request('POST', URL_ACTIONS, log, proxy_api, use_proxy,
                            json=payload, timeout=15, verify=False)
        data = resp.json()
        if data.get("code") != "000000":
            log(f"❌ 获取检测指令失败：{data}")
            return None, None
        session_id = data["data"]["session_id"]
        actions = data["data"].get("actions", [])
        log(f"✅ 本次需要做的动作：{', '.join([ACTION_MAP.get(a, a) for a in actions])}")
        return session_id, actions
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return None, None

def step4_upload_video(log, vid_path, auth_token, session_id):
    log("⏳ 正在上传视频...")
    try:
        b64, dk, _ = encrypt_file(vid_path)
    except Exception as e:
        log(f"❌ 视频处理失败：{e}")
        return False, None, str(e)
    headers = {"Content-Type": "application/json", "Content-Encoding": "gzip",
               "Data-Key": dk, "User-Agent": "Dalvik/2.1.0"}
    payload = {"app_key": APP_KEY, "platform_type": 2, "session_id": session_id,
               "auth_token": auth_token, "video": b64, "video_type": "BASE64"}
    try:
        resp = requests.post(URL_VIDEO, headers=headers, json=payload, timeout=60, verify=False)
        result = resp.json()
        if result.get("code") == "000000":
            av = result.get("data", {}).get("action_verify", "")
            score = result.get("data", {}).get("score", 0)
            if av == "pass":
                log(f"✅ 视频验证通过（动作完成度：{score}）")
                return True, av, ""
            else:
                log(f"⚠️ 视频中动作未通过。动作完成度 {score} 过低")
                return True, av, f"动作完成度 {score} 过低"
        else:
            log(f"❌ 视频上传失败：{result.get('msg')}")
            return False, None, result.get('msg', '')
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False, None, str(e)

def step5_submit_real_name(log, login_token, id_card, real_name, proxy_api=None, use_proxy=False):
    log("⏳ 正在提交实名认证...")
    headers = build_mallex_headers(login_token)
    headers["Content-Type"] = "application/json"
    payload = {"idCard": id_card, "realName": real_name}
    try:
        resp = safe_request('POST', URL_SUBMIT_REAL, log, proxy_api, use_proxy,
                            headers=headers, json=payload, timeout=15, verify=False)
        result = resp.json()
        code = result.get("code")
        if code == "OK" and result.get("data", {}).get("status") == "pass":
            log("✅ 实名认证通过！")
            return True, False
        elif code == "REAL_NAME_AUTH_OTHER":
            log("⚠️ 该身份证已被其他账号绑定，需要找回")
            return False, True
        else:
            log(f"❌ 实名认证失败：{result.get('msg')}")
            return False, False
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False, False

def step6_find_account(log, login_token, id_card, proxy_api=None, use_proxy=False):
    log("⏳ 正在申请找回身份证...")
    headers = build_mallex_headers(login_token)
    headers["Content-Type"] = "application/json"
    payload = {"idCard": id_card, "liveAuthPassed": 1, "defineCondition": "createNew", "defined": "yes"}
    try:
        resp = safe_request('POST', URL_FIND_ACCOUNT, log, proxy_api, use_proxy,
                            headers=headers, json=payload, timeout=15, verify=False)
        result = resp.json()
        if result.get("code") == "OK" and result.get("data") == True:
            log("✅ 找回成功！")
            return True
        else:
            log(f"❌ 找回失败：{result.get('msg')}")
            return False
    except Exception as e:
        log(f"❌ 网络错误：{e}")
        return False


# ========== 自定义组件 ==========
class RoundedButton(Button):
    def __init__(self, bg_color=COLOR_PRIMARY, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = dp(14)
        self.bold = True
        self._bg_color = bg_color
        with self.canvas.before:
            self._color = Color(*bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._update_rect, size=self._update_rect, state=self._update_state)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_state(self, *args):
        if self.state == 'down':
            self._color.rgb = (self._bg_color[0]*0.8, self._bg_color[1]*0.8, self._bg_color[2]*0.8)
        else:
            self._color.rgb = self._bg_color


class CardLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*COLOR_CARD)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


# ========== 主界面 ==========
class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.continue_event = threading.Event()
        self.user_confirmed = False
        self.new_video_path = ""
        self.last_video_error = ""
        self.proxy_addr = None
        self.current_file_type = None
        self._video_popup = None
        self._waiting_for_video_change = False
        self._pending_video_action = ""
        self._pending_video_error = ""
        # ★ 新增：找回确认弹窗相关
        self._find_event = threading.Event()
        self._find_agreed = False
        self._find_popup = None

        self._init_storage()

        with self.canvas.before:
            Color(*COLOR_BG)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.build_ui()

    def _init_storage(self):
        try:
            if platform == 'android':
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                app_dir = PythonActivity.mActivity.getFilesDir().getAbsolutePath()
            else:
                app_dir = App.get_running_app().user_data_dir
            store_path = os.path.join(app_dir, 'app_settings.json')
            self.store = JsonStore(store_path)
            Logger.info(f"存储路径: {store_path}")
        except Exception as e:
            Logger.error(f"存储初始化失败: {e}")
            self.store = JsonStore('app_settings.json')

    def _save_proxy_api(self, api_url):
        try:
            self.store.put('proxy_api', url=api_url)
            self.log(f"💾 已保存代理API配置")
        except Exception as e:
            Logger.error(f"保存代理API失败: {e}")

    def _load_proxy_api(self):
        try:
            if self.store.exists('proxy_api'):
                return self.store.get('proxy_api').get('url', DEFAULT_PROXY_API)
        except Exception as e:
            Logger.error(f"加载代理API失败: {e}")
        return DEFAULT_PROXY_API

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def build_ui(self):
        self._build_header()
        self._build_body()
        self._build_log_area()

    def _build_header(self):
        header = BoxLayout(orientation='vertical',
                          size_hint_y=None, height=dp(56),
                          padding=[dp(16), dp(8), dp(16), dp(8)])
        with header.canvas.before:
            Color(*COLOR_PRIMARY)
            self._header_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._update_header_rect, size=self._update_header_rect)

        title = Label(text='活体认证助手',
                     font_size=dp(20), bold=True,
                     color=(1, 1, 1, 1),
                     halign='center', valign='middle')
        title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        header.add_widget(title)
        self.add_widget(header)

    def _update_header_rect(self, *args):
        if hasattr(self, '_header_rect') and self.children:
            try:
                self._header_rect.pos = self.children[-1].pos
                self._header_rect.size = self.children[-1].size
            except:
                pass

    def _build_body(self):
        body_scroll = ScrollView(size_hint=(1, 0.55), do_scroll_x=False, bar_width=dp(4))
        body = BoxLayout(orientation='vertical',
                        size_hint_y=None, padding=[dp(10), dp(8)], spacing=dp(8))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(self._build_user_card())
        body.add_widget(self._build_file_card())
        body.add_widget(self._build_proxy_card())
        body.add_widget(self._build_action_area())

        body_scroll.add_widget(body)
        self.add_widget(body_scroll)

    def _make_field_label(self, text):
        lbl = Label(
            text=text, color=COLOR_TEXT, font_size=dp(13), bold=True,
            size_hint_y=None, height=dp(20),
            halign='left', valign='middle'
        )
        lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        return lbl

    def _build_user_card(self):
        card = CardLayout(orientation='vertical',
                         size_hint_y=None, height=dp(250),
                         padding=[dp(12), dp(10), dp(12), dp(10)], spacing=dp(8))
        title = Label(text='📋 认证信息',
                     font_size=dp(15), bold=True,
                     color=COLOR_PRIMARY, size_hint_y=None, height=dp(28),
                     halign='left', valign='middle')
        title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        card.add_widget(title)

        card.add_widget(self._make_field_label('登录Token'))
        self.token_input = TextInput(
            hint_text='请输入登录Token', multiline=False,
            size_hint_y=None, height=dp(40), font_size=dp(14),
            background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT,
            hint_text_color=COLOR_TEXT_LIGHT, cursor_color=COLOR_PRIMARY,
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        card.add_widget(self.token_input)

        card.add_widget(self._make_field_label('身份证号'))
        self.id_card_input = TextInput(
            hint_text='请输入身份证号', multiline=False,
            size_hint_y=None, height=dp(40), font_size=dp(14),
            background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT,
            hint_text_color=COLOR_TEXT_LIGHT, cursor_color=COLOR_PRIMARY,
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        card.add_widget(self.id_card_input)

        card.add_widget(self._make_field_label('姓名'))
        self.name_input = TextInput(
            hint_text='请输入姓名', multiline=False,
            size_hint_y=None, height=dp(40), font_size=dp(14),
            background_color=COLOR_INPUT_BG, foreground_color=COLOR_TEXT,
            hint_text_color=COLOR_TEXT_LIGHT, cursor_color=COLOR_PRIMARY,
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        card.add_widget(self.name_input)
        return card

    def _build_file_card(self):
        card = CardLayout(orientation='vertical',
                         size_hint_y=None, height=dp(180),
                         padding=[dp(12), dp(10), dp(12), dp(10)], spacing=dp(8))
        title = Label(text='📁 文件选择',
                     font_size=dp(15), bold=True,
                     color=COLOR_PRIMARY, size_hint_y=None, height=dp(28),
                     halign='left', valign='middle')
        title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        card.add_widget(title)

        card.add_widget(self._make_field_label('人脸图片'))
        img_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self.image_path = TextInput(
            hint_text='未选择', multiline=False, readonly=True,
            font_size=dp(13), background_color=COLOR_INPUT_BG,
            foreground_color=COLOR_TEXT,
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        img_row.add_widget(self.image_path)
        btn_img = RoundedButton(text='选择', size_hint_x=None, width=dp(80))
        btn_img.bind(on_press=lambda x: self.pick_file('image'))
        img_row.add_widget(btn_img)
        card.add_widget(img_row)

        card.add_widget(self._make_field_label('动作视频'))
        vid_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self.video_path = TextInput(
            hint_text='未选择', multiline=False, readonly=True,
            font_size=dp(13), background_color=COLOR_INPUT_BG,
            foreground_color=COLOR_TEXT,
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )
        vid_row.add_widget(self.video_path)
        btn_vid = RoundedButton(text='选择', size_hint_x=None, width=dp(80))
        btn_vid.bind(on_press=lambda x: self.pick_file('video'))
        vid_row.add_widget(btn_vid)
        card.add_widget(vid_row)
        return card

    def _build_proxy_card(self):
        card = CardLayout(orientation='vertical',
                         size_hint_y=None, height=dp(210),
                         padding=[dp(12), dp(10), dp(12), dp(10)], spacing=dp(8))
        title = Label(text='🌐 代理设置（可选）',
                     font_size=dp(15), bold=True,
                     color=COLOR_PRIMARY, size_hint_y=None, height=dp(28),
                     halign='left', valign='middle')
        title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        card.add_widget(title)

        card.add_widget(self._make_field_label('代理API地址'))

        saved_proxy = self._load_proxy_api()
        self.proxy_api_input = TextInput(
            text=saved_proxy,
            multiline=True, size_hint_y=None, height=dp(70),
            font_size=dp(11), background_color=COLOR_INPUT_BG,
            foreground_color=COLOR_TEXT,
            padding=[dp(10), dp(8), dp(10), dp(8)]
        )
        self.proxy_api_input.bind(text=self._on_proxy_api_changed)
        card.add_widget(self.proxy_api_input)

        self.btn_get_proxy = RoundedButton(
            text='🔄 获取代理IP', bg_color=COLOR_WARN,
            size_hint_y=None, height=dp(36)
        )
        self.btn_get_proxy.bind(on_press=self.on_get_proxy)
        card.add_widget(self.btn_get_proxy)

        status_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        self.proxy_status_label = Label(
            text='未获取代理', color=COLOR_TEXT_LIGHT, font_size=dp(12),
            halign='left', valign='middle', size_hint_x=0.7
        )
        self.proxy_status_label.bind(size=lambda i, v: setattr(i, 'text_size', v))
        status_row.add_widget(self.proxy_status_label)
        self.use_proxy_check = CheckBox(
            active=True, size_hint_x=None, width=dp(30),
            color=COLOR_PRIMARY
        )
        status_row.add_widget(self.use_proxy_check)
        status_row.add_widget(Label(
            text='启用', color=COLOR_TEXT, font_size=dp(12),
            size_hint_x=None, width=dp(35)
        ))
        card.add_widget(status_row)
        return card

    def _on_proxy_api_changed(self, instance, value):
        if hasattr(self, '_save_proxy_event') and self._save_proxy_event:
            self._save_proxy_event.cancel()
        self._save_proxy_event = Clock.schedule_once(
            lambda dt: self._save_proxy_api(value), 0.5)

    def _build_action_area(self):
        container = BoxLayout(orientation='vertical', size_hint_y=None,
                            height=dp(70), spacing=dp(6))
        self.status_label = Label(
            text='● 状态：准备就绪', color=COLOR_SUCCESS,
            font_size=dp(13), bold=True, size_hint_y=None, height=dp(24),
            halign='left', valign='middle'
        )
        self.status_label.bind(size=lambda i, v: setattr(i, 'text_size', v))
        container.add_widget(self.status_label)

        self.btn_start = RoundedButton(
            text='🚀 开始认证', bg_color=COLOR_SUCCESS,
            size_hint_y=None, height=dp(44), font_size=dp(16)
        )
        self.btn_start.bind(on_press=self.start_auth)
        container.add_widget(self.btn_start)
        return container

    def _build_log_area(self):
        log_container = BoxLayout(orientation='vertical',
                                 size_hint=(1, 0.45),
                                 padding=[dp(10), dp(4), dp(10), dp(10)])
        log_title = Label(text='📜 认证日志',
                         font_size=dp(13), bold=True,
                         color=COLOR_TEXT, size_hint_y=None, height=dp(24),
                         halign='left', valign='middle')
        log_title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        log_container.add_widget(log_title)

        self.log_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
        with self.log_scroll.canvas.before:
            Color(*COLOR_LOG_BG)
            self._log_rect = RoundedRectangle(pos=self.log_scroll.pos,
                                              size=self.log_scroll.size,
                                              radius=[dp(6)])
        self.log_scroll.bind(pos=self._update_log_rect, size=self._update_log_rect)

        self.log_content = Label(text='',
                                size_hint_y=None,
                                halign='left', valign='top',
                                color=COLOR_LOG_TEXT,
                                font_size=dp(12),
                                padding=[dp(10), dp(8), dp(10), dp(8)])
        self.log_content.bind(texture_size=self.log_content.setter('size'),
                             width=self._update_log_text_size)
        self.log_scroll.add_widget(self.log_content)
        log_container.add_widget(self.log_scroll)
        self.add_widget(log_container)

    def _update_log_rect(self, *args):
        if hasattr(self, '_log_rect'):
            try:
                self._log_rect.pos = self.log_scroll.pos
                self._log_rect.size = self.log_scroll.size
            except:
                pass

    def _update_log_text_size(self, instance, value):
        instance.text_size = (value, None)

    # ========== 文件选择 ==========
    def pick_file(self, file_type):
        self.current_file_type = file_type
        self.log(f"⏳ 正在打开{('图片' if file_type == 'image' else '视频')}选择器...")
        if platform == 'android':
            self._android_pick_file(file_type)
        else:
            self._kivy_pick_file(file_type)

    def _android_pick_file(self, file_type):
        try:
            if HAS_AS4K:
                chooser = Chooser(self._handle_chooser_result)
                if file_type == 'image':
                    chooser.choose_content("image/*")
                else:
                    chooser.choose_content("video/*")
            else:
                self.log("❌ 未安装 androidstorage4kivy")
                self._show_manual_input(file_type)
        except Exception as e:
            self.log(f"❌ 打开文件选择器失败: {e}")
            self._show_manual_input(file_type)

    def _handle_chooser_result(self, uri_list):
        if not uri_list:
            self.log("❌ 未选择文件")
            return
        uri = uri_list[0] if isinstance(uri_list, list) else uri_list
        self.log("⏳ 正在复制文件到本地...")

        def _do_copy():
            try:
                if HAS_AS4K:
                    try:
                        ss = SharedStorage()
                        local_path = ss.copy_from_shared(uri)
                    except Exception:
                        local_path = android_copy_uri_to_local(uri)
                else:
                    local_path = android_copy_uri_to_local(uri)

                Clock.schedule_once(lambda dt: self._on_file_ready(local_path), 0)
            except Exception as e:
                err = str(e)
                Clock.schedule_once(lambda dt: self._on_file_error(err), 0)

        threading.Thread(target=_do_copy, daemon=True).start()

    @mainthread
    def _on_file_ready(self, local_path):
        if not local_path or not os.path.exists(local_path):
            self.log("❌ 文件复制失败")
            self._reset_video_change_state()
            return
        try:
            file_size = os.path.getsize(local_path) / 1024
        except:
            file_size = 0
        if self.current_file_type == 'image':
            self.image_path.text = local_path
            self.log(f"✅ 图片就绪 ({file_size:.1f}KB)")
        else:
            self.video_path.text = local_path
            self.log(f"✅ 视频就绪 ({file_size/1024:.1f}MB)")

        if self._waiting_for_video_change and self.current_file_type == 'video':
            self._waiting_for_video_change = False
            Clock.schedule_once(
                lambda dt: self._show_video_popup(
                    self._pending_video_action,
                    local_path,
                    self._pending_video_error
                ), 0.3
            )

    @mainthread
    def _on_file_error(self, err):
        self.log(f"❌ 文件错误: {err}")
        self._reset_video_change_state()

    def _reset_video_change_state(self):
        self._waiting_for_video_change = False
        if self.continue_event and not self.continue_event.is_set():
            self.user_confirmed = False
            self.continue_event.set()

    def _kivy_pick_file(self, file_type):
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        default_path = os.path.expanduser('~')
        filechooser = FileChooserListView(path=default_path, dirselect=False)
        if file_type == 'image':
            filechooser.filters = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']
        else:
            filechooser.filters = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.3gp', '*.flv']
        filechooser.size_hint_y = 0.85
        content.add_widget(filechooser)

        btn_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title=f"选择{('图片' if file_type == 'image' else '视频')}",
                     content=content, size_hint=(0.95, 0.9))

        def on_select(instance):
            if filechooser.selection:
                self._handle_file_selection(filechooser.selection)
            popup.dismiss()

        btn_cancel = RoundedButton(text='取消', bg_color=COLOR_TEXT_LIGHT)
        btn_cancel.bind(on_press=popup.dismiss)
        btn_ok = RoundedButton(text='确定', bg_color=COLOR_PRIMARY)
        btn_ok.bind(on_press=on_select)
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_ok)
        content.add_widget(btn_box)
        popup.open()

    def _handle_file_selection(self, selection):
        if not selection:
            return
        path = selection[0] if isinstance(selection, list) else selection
        if isinstance(path, tuple):
            path = path[0]
        if self.current_file_type == 'image':
            self.image_path.text = path
            self.log(f"✅ 已选择图片: {os.path.basename(path)}")
        else:
            self.video_path.text = path
            self.log(f"✅ 已选择视频: {os.path.basename(path)}")

        if self._waiting_for_video_change and self.current_file_type == 'video':
            self._waiting_for_video_change = False
            Clock.schedule_once(
                lambda dt: self._show_video_popup(
                    self._pending_video_action,
                    path,
                    self._pending_video_error
                ), 0.2
            )

    def _show_manual_input(self, file_type):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text=f"请输入{('图片' if file_type == 'image' else '视频')}完整路径:",
                                size_hint_y=None, height=dp(30)))
        path_input = TextInput(hint_text='/sdcard/...', multiline=False,
                              size_hint_y=None, height=dp(40), font_size=dp(13))
        content.add_widget(path_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title='手动输入路径', content=content,
                     size_hint=(0.9, None), height=dp(180))

        def on_confirm(instance):
            if path_input.text.strip():
                self._handle_file_selection([path_input.text.strip()])
            popup.dismiss()

        btn_cancel = RoundedButton(text='取消', bg_color=COLOR_TEXT_LIGHT)
        btn_cancel.bind(on_press=popup.dismiss)
        btn_ok = RoundedButton(text='确定', bg_color=COLOR_PRIMARY)
        btn_ok.bind(on_press=on_confirm)
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_ok)
        content.add_widget(btn_box)
        popup.open()

    # ========== 日志和状态 ==========
    def log(self, msg):
        def _update(dt):
            self.log_content.text += msg + "\n"
            self.log_scroll.scroll_y = 0
        Clock.schedule_once(_update, 0)

    @mainthread
    def set_status(self, text, color=COLOR_SUCCESS):
        self.status_label.text = '● 状态：' + text
        self.status_label.color = color

    @mainthread
    def set_proxy_status(self, text, color=COLOR_TEXT_LIGHT):
        self.proxy_status_label.text = text
        self.proxy_status_label.color = color

    # ========== 代理获取 ==========
    def on_get_proxy(self, instance):
        api_url = self.proxy_api_input.text.strip()
        if not api_url:
            self.log("❌ 请输入代理API地址")
            return
        self._save_proxy_api(api_url)
        self.log("⏳ 正在获取代理IP...")
        self.btn_get_proxy.disabled = True

        def _get():
            proxy = fetch_proxy(api_url)
            if proxy:
                if test_proxy(proxy):
                    self.proxy_addr = proxy
                    self.set_proxy_status(f"✅ {proxy}", COLOR_SUCCESS)
                    self.log(f"✅ 获取代理成功：{proxy}")
                else:
                    self.proxy_addr = None
                    self.set_proxy_status("❌ 代理无效", COLOR_DANGER)
                    self.log("❌ 代理无效，请更换API")
            else:
                self.proxy_addr = None
                self.set_proxy_status("❌ 获取失败", COLOR_DANGER)
                self.log("❌ 获取代理失败")
            self.btn_get_proxy.disabled = False

        threading.Thread(target=_get, daemon=True).start()

    # ========== 认证流程 ==========
    def start_auth(self, instance):
        self._save_proxy_api(self.proxy_api_input.text.strip())

        token = self.token_input.text.strip()
        img = self.image_path.text.strip()
        vid = self.video_path.text.strip()
        idcard = self.id_card_input.text.strip()
        name = self.name_input.text.strip()

        if not all([token, img, vid, idcard, name]):
            self.log("❌ 请填写所有信息并选择文件")
            self.set_status("信息不完整", COLOR_DANGER)
            return

        if not os.path.exists(img):
            self.log(f"❌ 图片文件不存在: {img}")
            return
        if not os.path.exists(vid):
            self.log(f"❌ 视频文件不存在: {vid}")
            return

        use_proxy = self.use_proxy_check.active
        proxy_api = self.proxy_api_input.text.strip() if use_proxy else None
        self.btn_start.disabled = True
        self.log("\n========== 开始认证流程 ==========")
        self.set_status("正在认证...", COLOR_WARN)
        threading.Thread(target=self.run_auth,
                        args=(token, img, vid, idcard, name, use_proxy, proxy_api),
                        daemon=True).start()

    def run_auth(self, token, img, vid, idcard, name, use_proxy, proxy_api):
        try:
            auth_token = step1_get_auth_token(self.log, token, proxy_api, use_proxy)
            if not auth_token:
                self.set_status("授权失败", COLOR_DANGER)
                return
            if not step2_upload_image(self.log, img, auth_token):
                self.set_status("图片上传失败", COLOR_DANGER)
                return

            while True:
                session_id, actions = step3_get_session_id(self.log, auth_token, proxy_api, use_proxy)
                if not session_id:
                    self.set_status("获取指令失败", COLOR_DANGER)
                    return
                action_desc = [ACTION_MAP.get(a, a) for a in actions] if actions else []
                action_str = ', '.join(action_desc) if action_desc else "无特定动作"
                self.log(f"📢 视频需包含动作：{action_str}")

                confirmed, new_vid = self.ask_user_for_video(action_str, vid, self.last_video_error)
                if not confirmed:
                    self.set_status("已取消", COLOR_DANGER)
                    return
                if new_vid:
                    vid = new_vid
                    self.video_path.text = vid

                ok, action_verify, err_msg = step4_upload_video(self.log, vid, auth_token, session_id)
                if not ok:
                    self.set_status("视频上传失败", COLOR_DANGER)
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
                self.set_status("✅ 实名认证通过", COLOR_SUCCESS)
                self.log("🎉 恭喜！实名认证全部完成")
            elif need_find:
                # ★ 修改：先弹确认框让用户选择
                agreed = self.ask_user_for_find(idcard)
                if not agreed:
                    self.set_status("已取消找回", COLOR_WARN)
                    self.log("⚠️ 用户取消找回身份证")
                    return
                # 同意后才执行找回
                if step6_find_account(self.log, token, idcard, proxy_api, use_proxy):
                    self.set_status("✅ 找回成功", COLOR_SUCCESS)
                    self.log("🎉 找回并认证成功！")
                else:
                    self.set_status("❌ 找回失败", COLOR_DANGER)
                    self.log("⚠️ 请稍后重试找回步骤")
            else:
                self.set_status("❌ 实名认证失败", COLOR_DANGER)
                self.log("❌ 认证失败，请检查日志")
        except Exception as e:
            self.log(f"❌ 程序异常：{e}")
            self.set_status("程序异常", COLOR_DANGER)
        finally:
            self.btn_start.disabled = False
            self.log("========== 流程结束 ==========\n")

    # ========== 视频确认弹窗 ==========
    def ask_user_for_video(self, action_str, current_video, error_msg=""):
        self.continue_event.clear()
        self.user_confirmed = False
        self.new_video_path = ""
        Clock.schedule_once(lambda dt: self._show_video_popup(action_str, current_video, error_msg), 0)
        self.continue_event.wait()
        return self.user_confirmed, self.new_video_path

    @mainthread
    def _show_video_popup(self, action_str, current_video, error_msg=""):
        if self._video_popup:
            try:
                self._video_popup.dismiss(force=True)
            except:
                pass
            self._video_popup = None

        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        info = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), spacing=dp(4))
        lbl1 = Label(text=f"当前视频：{os.path.basename(current_video)}",
                    color=COLOR_TEXT, font_size=dp(13),
                    halign='left', valign='middle')
        lbl1.bind(size=lambda i, v: setattr(i, 'text_size', v))
        info.add_widget(lbl1)
        lbl2 = Label(text=f"要求动作：{action_str}",
                    color=COLOR_PRIMARY, font_size=dp(14), bold=True,
                    halign='left', valign='middle')
        lbl2.bind(size=lambda i, v: setattr(i, 'text_size', v))
        info.add_widget(lbl2)
        content.add_widget(info)

        if error_msg:
            err = Label(text=f"⚠️ 上次失败：{error_msg}",
                       color=COLOR_DANGER, font_size=dp(12),
                       size_hint_y=None, height=dp(30),
                       halign='left', valign='middle')
            err.bind(size=lambda i, v: setattr(i, 'text_size', v))
            content.add_widget(err)

        btn_box = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        popup = Popup(title='确认视频文件', content=content,
                     size_hint=(0.9, None), height=dp(230), auto_dismiss=False)
        self._video_popup = popup

        def on_continue(instance):
            self.user_confirmed = True
            self.new_video_path = self.video_path.text
            self._video_popup = None
            popup.dismiss()
            self.continue_event.set()

        def on_change(instance):
            self._video_popup = None
            popup.dismiss(force=True)
            self._waiting_for_video_change = True
            self._pending_video_action = action_str
            self._pending_video_error = error_msg
            self.current_file_type = 'video'
            Clock.schedule_once(lambda dt: self.pick_file('video'), 0.1)

        def on_cancel(instance):
            self.user_confirmed = False
            self._video_popup = None
            popup.dismiss()
            self.continue_event.set()

        btn_cancel = RoundedButton(text='取消', bg_color=COLOR_TEXT_LIGHT)
        btn_cancel.bind(on_press=on_cancel)
        btn_change = RoundedButton(text='更换视频', bg_color=COLOR_WARN)
        btn_change.bind(on_press=on_change)
        btn_continue = RoundedButton(text='使用当前', bg_color=COLOR_SUCCESS)
        btn_continue.bind(on_press=on_continue)
        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_change)
        btn_box.add_widget(btn_continue)
        content.add_widget(btn_box)
        popup.open()

    # ★ 新增：找回身份证确认弹窗
    def ask_user_for_find(self, id_card):
        """弹窗询问用户是否同意找回身份证，同意返回 True"""
        self._find_event.clear()
        self._find_agreed = False
        Clock.schedule_once(lambda dt: self._show_find_popup(id_card), 0)
        self._find_event.wait()
        return self._find_agreed

    @mainthread
    def _show_find_popup(self, id_card):
        # 防止重复弹窗
        if self._find_popup:
            try:
                self._find_popup.dismiss(force=True)
            except:
                pass
            self._find_popup = None

        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # 标题
        title = Label(
            text="⚠️ 身份证已被占用",
            color=COLOR_WARN, font_size=dp(16), bold=True,
            size_hint_y=None, height=dp(30),
            halign='center', valign='middle'
        )
        title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        content.add_widget(title)

        # 提示信息
        masked_id = id_card[:6] + "********" + id_card[-4:] if len(id_card) >= 10 else id_card
        info_text = (
            f"身份证号 {masked_id} 已被其他账号绑定。\n\n"
            f"是否同意申请将该身份证找回并绑定到当前账号？\n\n"
            f"• 同意：系统将提交找回申请\n"
            f"• 不同意：取消本次操作"
        )
        info = Label(
            text=info_text,
            color=COLOR_TEXT, font_size=dp(13),
            halign='left', valign='top'
        )
        info.bind(size=lambda i, v: setattr(i, 'text_size', v))
        content.add_widget(info)

        # 按钮
        btn_box = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(12))
        popup = Popup(
            title='找回身份证确认',
            content=content,
            size_hint=(0.9, None), height=dp(320),
            auto_dismiss=False
        )
        self._find_popup = popup

        def on_agree(instance):
            self._find_agreed = True
            self._find_popup = None
            popup.dismiss()
            self._find_event.set()

        def on_disagree(instance):
            self._find_agreed = False
            self._find_popup = None
            popup.dismiss()
            self._find_event.set()

        btn_disagree = RoundedButton(text='不同意', bg_color=COLOR_TEXT_LIGHT)
        btn_disagree.bind(on_press=on_disagree)
        btn_agree = RoundedButton(text='同意', bg_color=COLOR_SUCCESS)
        btn_agree.bind(on_press=on_agree)
        btn_box.add_widget(btn_disagree)
        btn_box.add_widget(btn_agree)
        content.add_widget(btn_box)

        popup.open()


# ========== APP ==========
class LiveAuthApp(App):
    def build(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_MEDIA_IMAGES,
                    Permission.READ_MEDIA_VIDEO,
                ])
            except Exception as e:
                Logger.warning(f"权限申请失败: {e}")
        return MainScreen()


if __name__ == '__main__':
    try:
        LiveAuthApp().run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        Logger.error(f"App 启动失败: {e}")
