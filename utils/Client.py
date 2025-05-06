import random

from curl_cffi.requests import AsyncSession


class Client:
    def __init__(self, proxy=None, timeout=15, verify=True, impersonate='safari15_3'):
        self.proxies = {"http": proxy, "https": proxy}
        self.timeout = timeout
        self.verify = verify

        self.impersonate = impersonate
        # impersonate=self.impersonate

        # self.ja3 = ""
        # self.akamai = ""
        # ja3=self.ja3, akamai=self.akamai
        proxy_auth = None
        if proxy:
            proxy_info = parse_proxy_url(proxy)
            protocol = proxy_info.get("protocol", "").lower()
            username = proxy_info.get("username")
            password = proxy_info.get("password")
            ip = proxy_info.get("ip")
            port = proxy_info.get("port")
            if username and password:
                # 假设 AsyncSession 的 proxy_auth 参数接受 (username, password) 元组
                proxy_auth = (username, password)
            elif username:
                proxy_auth = (username, "")

        self.session = AsyncSession(proxy_auth=proxy_auth if proxy_auth else None, proxies=self.proxies,
                                    timeout=self.timeout, impersonate=self.impersonate, verify=self.verify)
        self.session2 = AsyncSession(proxy_auth=proxy_auth if proxy_auth else None, proxies=self.proxies,
                                     timeout=self.timeout, impersonate=self.impersonate,
                                     verify=self.verify)

    async def post(self, *args, **kwargs):
        r = await self.session.post(*args, **kwargs)
        return r

    async def post_stream(self, *args, headers=None, cookies=None, **kwargs):
        if self.session:
            headers = headers or self.session.headers
            cookies = cookies or self.session.cookies
        r = await self.session2.post(*args, headers=headers, cookies=cookies, **kwargs)
        return r

    async def get(self, *args, **kwargs):
        r = await self.session.get(*args, **kwargs)
        return r

    async def request(self, *args, **kwargs):
        r = await self.session.request(*args, **kwargs)
        return r

    async def put(self, *args, **kwargs):
        r = await self.session.put(*args, **kwargs)
        return r

    async def close(self):
        if hasattr(self, 'session'):
            try:
                await self.session.close()
                del self.session
            except Exception:
                pass
        if hasattr(self, 'session2'):
            try:
                await self.session2.close()
                del self.session2
            except Exception:
                pass

def parse_proxy_url(proxy_url):
    """
    解析 proxy URL，提取协议、用户名、密码、IP 和端口
    """
    result = {
        "protocol": None,
        "username": None,
        "password": None,
        "ip": None,
        "port": None
    }

    if not proxy_url:
        return result

    protocol_split = proxy_url.split("://", 1)
    if len(protocol_split) == 2:
        result["protocol"] = protocol_split[0]
        remaining = protocol_split[1]
    else:
        remaining = proxy_url

    if '@' in remaining:
        auth_part, host_part = remaining.split('@', 1)
        if ':' in auth_part:
            result["username"], result["password"] = auth_part.split(':', 1)
        else:
            result["username"] = auth_part
    else:
        host_part = remaining

    if ':' in host_part:
        result["ip"], result["port"] = host_part.split(':', 1)
    else:
        result["ip"] = host_part