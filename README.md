# Web安全渗透测试 - SSRF攻击链实验

## 文件说明

| 文件 | 说明 |
|------|------|
| `class_notes.md` | 课堂笔记（手写整理） |
| `attack_analysis.md` | 攻击链分析文档（AI生成，含流程图） |
| `ssrf_attack.py` | 攻击脚本实现 |
| `private/` | 废弃文件，无需关注 |

## 攻击链

```
SSRF → Redis利用 → Session伪造 → Pickle RCE → MCP攻击
```
