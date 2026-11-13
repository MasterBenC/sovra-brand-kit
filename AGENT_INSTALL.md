# 给 Agent 的安装说明

仓库私有。先确认 `gh auth status` 已登录，再克隆。不要用未授权的公开下载链接，那会 404。

```bash
gh repo clone MasterBenC/sovra-brand-kit
```

## 装到哪里

| 环境 | 目录 |
|---|---|
| Hermes Agent | `~/.hermes/skills/productivity/sovra-brand/` |
| Claude Code | `~/.claude/skills/sovra-brand/` |
| 其他能读 SKILL.md 的 Agent | 该环境的 skills 目录下的 `sovra-brand/` |

Windows 上 Hermes 的家目录通常是 `%LOCALAPPDATA%\hermes`。不要猜另一条路径。

已有同名目录时不要覆盖，除非用户明确说更新。更新时先删掉旧目录再复制。

复制 `skills/sovra-brand/` 的全部内容，包括 `assets/cover.png`。只复制 SKILL.md 不能生产。

## 依赖

```bash
python -m pip install -r skills/sovra-brand/requirements.txt
```

锁定 `python-pptx==1.0.2`。版本不同就拒绝发布，避免版式字节漂移。

## 验证

在技能目录执行：

```bash
python tests/test_stable.py
```

必须打印 `PASS`。失败就把原文回报，不要改测试或改版式脚本来凑绿。

再执行：

```bash
python scripts/probe_env.py
```

把缺少的字体和 LibreOffice 如实告诉用户。缺字体不是安装失败。

## 回报

1. 装到哪个目录
2. `test_stable.py` 是否 PASS
3. `probe_env.py` 列出的缺项
4. 一句话：之后做灵能涌现 PPT 或 A4 时先读这个技能，只写 JSON，用发布脚本出文件
