import time
import string
import random
import secrets
import base64
import httpx
import requests
from .reply import PuzzleSolver
from .signer.sign import sign


class CaptchaSolver:
    def __init__(self, iid: str, did: str, device_type: str, device_brand: str, country: str, proxy: str = None):
        self.iid = iid
        self.did = did
        self.device_type = device_type
        self.device_brand = device_brand

        self.host = 'rc-verification-sg.tiktokv.com'
      #  self.host = 'verification-va.tiktok.com'
        self.host_region = self.host.split('-')[2].split('.')[0]
      #  self.host_region = 'va'
        self.country = country

        # Using proxies in the requests session constructor directly
        if proxy:
            self.session = requests.Session()
            self.session.proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
        else:
            self.session = requests.Session()

    def get_captcha(self):
        params = f'lang=en&app_name=musical_ly&h5_sdk_version=2.33.7&h5_sdk_use_type=cdn&sdk_version=2.3.4.i18n&iid={self.iid}&did={self.did}&device_id={self.did}&ch=googleplay&aid=1233&os_type=0&mode=slide&tmp={int(time.time())}{random.randint(111, 999)}&platform=app&webdriver=undefined&verify_host=https%3A%2F%2F{self.host_region}%2F&locale=en&channel=googleplay&app_key&vc=32.9.5&app_version=32.9.5&session_id&region={self.host_region}&use_native_report=1&use_jsb_request=1&orientation=2&resolution=720*1280&os_version=25&device_brand={self.device_brand}&device_model={self.device_type}&os_name=Android&version_code=3275&device_type={self.device_type}&device_platform=Android&type=verify&detail=&server_sdk_env=&imagex_domain&subtype=slide&challenge_code=99996&triggered_region={self.host_region}&cookie_enabled=true&screen_width=360&screen_height=640&browser_language=en&browser_platform=Linux%20i686&browser_name=Mozilla&browser_version=5.0%20%28Linux%3B%20Android%207.1.2%3B%20{self.device_type}%20Build%2FN2G48C%3B%20wv%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Version%2F4.0%20Chrome%2F86.0.4240.198%20Mobile%20Safari%2F537.36%20BytedanceWebview%2Fd8a21c6'
        sig = sign(params, '', "AadCFwpTyztA5j9L" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(9)), None, 1233)
        headers = {
            'X-Tt-Request-Tag': 'n=1;t=0',
            'X-Vc-Bdturing-Sdk-Version': '2.3.4.i18n',
            'X-Tt-Bypass-Dp': '1',
            'Content-Type': 'application/json; charset=utf-8',
            'X-Tt-Dm-Status': 'login=0;ct=0;rt=7',
            'X-Tt-Store-Region': self.country,
            'X-Tt-Store-Region-Src': 'did',
            'User-Agent': f'com.zhiliaoapp.musically/2023209050 (Linux; U; Android 7.1.2; en_{self.country.upper()}; {self.device_type}; Build/N2G48C;tt-ok/3.12.13.4-tiktok)',
            "x-ss-req-ticket": sig["x-ss-req-ticket"],
            "x-ss-stub": sig["x-ss-stub"],
            "X-Gorgon": sig["x-gorgon"],
            "X-Khronos": str(sig["x-khronos"]),
            "X-Ladon": sig["x-ladon"],
            "X-Argus": sig["x-argus"]
        }

        response = self.session.get(
            f'https://{self.host}/captcha/get?{params}',
            headers=headers
        ).json()

        return response

    def verify_captcha(self, data):
        params = f'lang=en&app_name=musical_ly&h5_sdk_version=2.33.7&h5_sdk_use_type=cdn&sdk_version=2.3.4.i18n&iid={self.iid}&did={self.did}&device_id={self.did}&ch=googleplay&aid=1233&os_type=0&mode=slide&tmp={int(time.time())}{random.randint(111, 999)}&platform=app&webdriver=undefined&verify_host=https%3A%2F%2F{self.host}%2F&locale=en&channel=googleplay&app_key&vc=32.9.5&app_version=32.9.5&session_id&region={self.host_region}&use_native_report=1&use_jsb_request=1&orientation=2&resolution=720*1280&os_version=25&device_brand={self.device_brand}&device_model={self.device_type}&os_name=Android&version_code=3275&device_type={self.device_type}&device_platform=Android&type=verify&detail=&server_sdk_env=&imagex_domain&subtype=slide&challenge_code=99996&triggered_region={self.host_region}&cookie_enabled=true&screen_width=360&screen_height=640&browser_language=en&browser_platform=Linux%20i686&browser_name=Mozilla&browser_version=5.0%20%28Linux%3B%20Android%207.1.2%3B%20{self.device_type}%20Build%2FN2G48C%3B%20wv%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Version%2F4.0%20Chrome%2F86.0.4240.198%20Mobile%20Safari%2F537.36%20BytedanceWebview%2Fd8a21c6'
        sig = sign(params, '', "AadCFwpTyztA5j9L" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(9)), None, 1233)
        headers = {
            'X-Tt-Request-Tag': 'n=1;t=0',
            'X-Vc-Bdturing-Sdk-Version': '2.3.4.i18n',
            'X-Tt-Bypass-Dp': '1',
            'Content-Type': 'application/json; charset=utf-8',
            'X-Tt-Dm-Status': 'login=0;ct=0;rt=7',
            'X-Tt-Store-Region': self.country,
            'X-Tt-Store-Region-Src': 'did',
            'User-Agent': f'com.zhiliaoapp.musically/2023209050 (Linux; U; Android 7.1.2; en_{self.country.upper()}; {self.device_type}; Build/N2G48C;tt-ok/3.12.13.4-tiktok)',
            "x-ss-req-ticket": sig["x-ss-req-ticket"],
            "x-ss-stub": sig["x-ss-stub"],
            "X-Gorgon": sig["x-gorgon"],
            "X-Khronos": str(sig["x-khronos"]),
            "X-Ladon": sig["x-ladon"],
            "X-Argus": sig["x-argus"]
        }

        response = self.session.post(
            f'https://{self.host}/captcha/verify?{params}',
            headers=headers,
            json=data
        ).json()

        return response

    def start(self) -> None:
        try:
            _captcha = self.get_captcha()

            captcha_data = _captcha["data"]["challenges"][0]

            captcha_id = captcha_data["id"]
            verify_id = _captcha["data"]["verify_id"]

            puzzle_img = self.session.get(captcha_data["question"]["url1"]).content
            piece_img = self.session.get(captcha_data["question"]["url2"]).content

            puzzle_b64 = base64.b64encode(puzzle_img)
            piece_b64 = base64.b64encode(piece_img)

            solver = PuzzleSolver(puzzle_b64, piece_b64)
            max_loc = solver.get_position()

            rand_length = random.randint(50, 100)
            movements = []

            for i in range(rand_length):
                progress = (i + 1) / rand_length
                x_pos = round(max_loc * progress)

                y_offset = random.randint(-2, 2) if i > 0 and i < rand_length - 1 else 0
                y_pos = captcha_data["question"]["tip_y"] + y_offset

                movements.append({
                    "relative_time": i * rand_length + random.randint(-5, 5),
                    "x": x_pos,
                    "y": y_pos
                })

            verify_payload = {
                "modified_img_width": 552,
                "id": captcha_id,
                "mode": "slide",
                "reply": movements,
                "verify_id": verify_id
            }

            return self.verify_captcha(verify_payload)
        except Exception as e:
            pass

def send(device: str.split, proxy: str):
    return CaptchaSolver(device[0], device[1], device[2], device[3], device[4], proxy).start()



