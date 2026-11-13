# 给 Agent 的安装说明

仓库：`MasterBenC/sovra-brand-kit`，公开。装之前不要改仓库里的内容。

## 第 0 步：确定目标目录

| 你的运行环境 | 目标目录 |
|---|---|
| Hermes Agent | `~/.hermes/skills/productivity/sovra-brand/` |
| Claude Code | `~/.claude/skills/sovra-brand/` |
| 其他能读 SKILL.md 的 Agent | 该环境 skills 目录下的 `sovra-brand/` |

Windows 上 Hermes 的家目录是 `%LOCALAPPDATA%\hermes`，不是用户名以外的另一条路径。`~/.hermes/` 和 `~/.claude/` 都存在时，优先 Hermes，并在回报里说明。

## 第 1 步：下载

```bash
TMP=$(mktemp -d)
curl -fL --retry 3 -o "$TMP/pkg.tar.gz" \
  https://codeload.github.com/MasterBenC/sovra-brand-kit/tar.gz/refs/heads/main
tar xzf "$TMP/pkg.tar.gz" -C "$TMP"
SRC="$TMP/sovra-brand-kit-main/skills/sovra-brand"
test -f "$SRC/SKILL.md" && test -f "$SRC/assets/cover.png"
```

GitHub 慢或连不上时，把上面的 URL 换成镜像：

```text
https://gh-proxy.com/https://github.com/MasterBenC/sovra-brand-kit/archive/refs/heads/main.tar.gz
https://ghfast.top/https://github.com/MasterBenC/sovra-brand-kit/archive/refs/heads/main.tar.gz
```

三个都失败就 `gh repo clone MasterBenC/sovra-brand-kit`。全失败就停手，把报错原文告诉用户，不要凭记忆编造文件。

## 第 2 步：复制

```bash
DEST=~/.hermes/skills/productivity/sovra-brand
mkdir -p "$(dirname "$DEST")"
if [ -e "$DEST" ]; then
  echo "SKIP (已存在): $DEST"
else
  cp -a "$SRC" "$DEST"
  echo "OK: $DEST"
fi
```

默认不覆盖。用户明确说更新时，先删掉旧目录再复制。必须带上 `assets/cover.png` 和 `scripts/`。只复制 SKILL.md 不能生产。

扁平 skills 目录（没有 `productivity/` 这一层）时，直接放到 `$DEST/sovra-brand/`。

## 第 3 步：依赖

```bash
python -m pip install -r "$DEST/requirements.txt"
```

锁定 `python-pptx==1.0.2`。版本不同，发布脚本会拒绝产出。系统 Python 有 PEP 668 限制时用虚拟环境，不要 `--break-system-packages`。

## 第 4 步：验证

```bash
python "$DEST/tests/test_stable.py"
python "$DEST/scripts/probe_env.py"
```

`test_stable.py` 必须打印 `PASS`。失败就把原文回报，不要改测试或版式脚本来凑绿。缺字体不是安装失败。

## 第 5 步：回报

1. 装到哪个目录，是新装还是因已存在而跳过
2. `test_stable.py` 是否 PASS
3. `probe_env.py` 列出的缺项
4. 一句话：做灵能涌现 PPT 或 A4 时先读这个技能，只写 JSON，用发布脚本出文件
