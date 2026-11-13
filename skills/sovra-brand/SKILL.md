---
name: sovra-brand
description: "Use when 做灵能涌现PPT或A4，且要求成品字节稳定。"
version: 1.0.0
author: MasterBenC, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sovra, brand, pptx, a4, stable-output]
---

# 灵能涌现品牌生产

把新材料做成灵能涌现的 PPT 或 A4。坐标、颜色、字号和页码由脚本写入，不由模型现场排。同一份内容源连续发布两次，PPTX 或 HTML 必须字节相同。做不到就不得交付。

不改已经打开的成品，不把 A4 规则套进 PPT，也不把 PPT 规则套进 A4。

## When to Use

- 新的课程、企业分享、业务演示，要可编辑 PPTX
- 新的提案、会议纪要、课程指南，要 A4 HTML，确认后再出 PDF
- 同一份材料再出一版，版式不能漂

不要用于：其他品牌；在 WPS 或 PowerPoint 里改一个字当交付；让模型自由画母版；用生图充当页标题或页码。

## 稳定合同

完成只看 `验收.json`，不看口头判断。

| 退出码 | 含义 | 能不能交付 |
|---|---|---|
| 1 | 失败 | 不能。没有成品 |
| 2 | 结构稳定，未视觉放行 | 可以交源文件，必须写明未放行和原因 |
| 0 | 视觉放行 | 可以交源文件和本次脚本导出的 PDF |

PPT 的锚点是 `演示稿.pptx`：不压缩 ZIP、时间戳固定为 2026-11-05、封面 PNG 原字节嵌入。A4 的锚点是 `文档.html`。PDF 不承诺字节相同，而且必须由本次发布从该锚点导出。另做一份排版不同的 PDF，视为失败。

模型只写 JSON。不手改 pptx、html、`assets/a4/templates/theme.css`、`assets/role-styles.json`、`scripts/build.py`。

## Procedure

1. 先定媒介。课程、分享、演示走 PPT，读 `references/ppt-vi.md`。提案、纪要、课程指南走 A4，读 `references/a4-vi.md`。两份都读 `references/stability.md`。完成标准：媒介只有一个，没有混用字号、页码或品牌位置。
2. 把材料写成 JSON。PPT 对照 `examples/ppt/content.json`。A4 对照 `assets/a4/document.schema.json` 和 `examples/a4/`。姓名、身份、数字、价格、承诺没有出处就标待确认，或停下来问。不把示例客户、示例讲师和历史项目事实抄进新稿。完成标准：JSON 能被发布脚本读入，没有空的必填字段。
3. 图只用已经保存的 PNG，并写 `provenance`。发布过程中不生图。已确认的图不重新生成。没有图就不要用 visual。完成标准：每个 visual 页都有 PNG 和 provenance。
4. 在技能目录发布。输出目录必须在技能目录之外。
   - PPT：`python scripts/publish_ppt.py 内容.json 输出目录`
   - A4：`python scripts/publish_a4.py 内容.json 输出目录`
   - A4 要测分页并出 PDF 时加 `--pdf`
   环境不清楚时先跑 `python scripts/probe_env.py`。完成标准：命令退出码是 0 或 2，输出目录里有 `验收.json`。
5. 读 `验收.json`。`两次构建一致` 不是 true 就停止，不得换一条手工排版路径。退出码 2 时列出 `未放行原因`。缺苹方、Helvetica Neue 或 LibreOffice 时，不要把字体改成微软雅黑再发布。完成标准：回复里写明退出码、哈希、页数、是否放行。
6. 交付对应文件。PPT 交 `演示稿.pptx` 和 `验收.json`；只有退出码 0 才加 `演示稿.pdf`。A4 交 `文档.html` 和 `验收.json`；只有退出码 0 才加 `文档.pdf`。完成标准：目录里没有上一次运行留下的、本次没有重新导出的 PDF。

## 页型

PPT 正文只允许 flow、cards、table、case、data、visual。封面、目录、章首由脚本按章节生成。没有单独的茶歇或结尾母版；用章首加 cards 或 flow，不要新画一页。

A4 的 `document_type` 只有 `proposal` 和 `meeting_minutes`。课程指南用 proposal。页脚英文由脚本写死。

## Pitfalls

- 没有苹方或 Helvetica Neue 时，PPTX 仍然字节稳定，但打开会换字体。这不是放行。
- 用 WPS 或 PowerPoint 另存会破坏字节锚点。要改字就改 JSON，再发布。
- `python -O` 会丢掉版式断言。发布脚本拒绝这个模式。
- 直接运行 `scripts/build.py` 不能交付。它已改为直接拒绝。
- 文字超宽、超高、案例页缺来源、visual 缺 provenance、封面后续行超过 8 个全角字位，都是内容问题。改 JSON，不改坐标。
- 客户实例里的协会名、讲师、数字不是新稿的默认事实。本仓库不含那些成品。

## Verification

发布后核对这四项，缺一不可：

- 退出码是 0 或 2，且与 `视觉放行` 一致
- `pptx_sha256` 或 `html_sha256` 连续两次相同
- 示例回归通过：`python tests/test_stable.py`
- 回复里写了哈希、页数、未放行原因。没有这些，就还没做完
