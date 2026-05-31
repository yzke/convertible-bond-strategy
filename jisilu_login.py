"""
集思录登录模块 — 自动 Cookie 管理
用法:
    from jisilu_login import get_valid_cookie, login, load_cookies
    
    # 自动刷新
    cookie_str = get_valid_cookie()
    
    # 手动刷新
    cookie_str = login()
"""
import json
import os
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# === 配置 ===
AES_KEY = "397151C04723421F"
LOGIN_URL = "https://www.jisilu.cn/webapi/account/login_process/"
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jisilu_cookies.json")

# 从环境变量读账号密码（不设兜底默认值，提交 git 安全）
JISILU_USER = os.environ.get("JISILU_USER", "")
JISILU_PASS = os.environ.get("JISILU_PASS", "")

# 运行时校验
def _check_credentials():
    if not JISILU_USER or not JISILU_PASS:
        raise RuntimeError(
            "集思录账号未配置。请设置环境变量:\n"
            "  export JISILU_USER='your_phone_or_email'\n"
            "  export JISILU_PASS='your_password'"
        )


def jslencode(text: str, aes_key: str = AES_KEY) -> str:
    """复制集思录的 jslencode: AES-128-CBC, zero IV, hex 输出"""
    key = aes_key.encode('utf-8')
    iv = b'\x00' * 16
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(text.encode('utf-8'), AES.block_size)
    return cipher.encrypt(padded).hex()


def login() -> str:
    """
    登录集思录，返回 cookie 字符串。
    成功时保存到 COOKIE_FILE。
    """
    _check_credentials()

    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0',
        'Origin': 'https://www.jisilu.cn',
        'Referer': 'https://www.jisilu.cn/login',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    })

    # GET 拿 session
    s.get('https://www.jisilu.cn/login')

    # 加密登录
    data = {
        'aes': '1',
        'user_name': jslencode(JISILU_USER),
        'password': jslencode(JISILU_PASS),
        'auto_login': '1',
        'return_url': 'https://www.jisilu.cn/',
    }
    r = s.post(LOGIN_URL, data=data)

    if r.status_code != 200:
        raise RuntimeError(f"登录请求失败: {r.status_code}")

    result = r.json()
    if result.get('code') != 200:
        raise RuntimeError(f"登录失败: {result.get('msg', '未知错误')}")

    # 跟随跳转
    redirect_url = result['data']['url']
    s.get(redirect_url, allow_redirects=True)

    # 保存 cookie
    cookies = dict(s.cookies)
    with open(COOKIE_FILE, 'w') as f:
        json.dump(cookies, f, indent=2)

    cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
    return cookie_str


def load_cookies() -> str:
    """从文件加载 cookie 字符串"""
    if not os.path.exists(COOKIE_FILE):
        raise FileNotFoundError(f"Cookie 文件不存在: {COOKIE_FILE}")

    with open(COOKIE_FILE) as f:
        cookies = json.load(f)

    return '; '.join(f'{k}={v}' for k, v in cookies.items())


def get_valid_cookie() -> str:
    """
    获取有效 cookie（自动处理刷新）。
    策略：先加载 → 如果加载失败或需要刷新 → 重新登录。
    """
    try:
        return load_cookies()
    except (FileNotFoundError, json.JSONDecodeError):
        return login()


def refresh_cookie() -> str:
    """强制刷新 cookie"""
    return login()


if __name__ == '__main__':
    # 测试
    try:
        cookie = get_valid_cookie()
        print(f"[✓] Cookie 获取成功，长度: {len(cookie)}")
    except Exception as e:
        print(f"[✗] 失败: {e}")
