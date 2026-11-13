# 字体与导出

PPT 写入的字体名是 PingFang SC、PingFang SC Light、Helvetica Neue Thin、Helvetica Neue Light、Arial。这些名字锁在 `assets/role-styles.json`。文件本身不嵌入字体，所以换一台没有这些字体的电脑打开，画面会变，哈希不会变。

不要把商业字体文件放进仓库。

## 视觉放行需要

1. 安装有使用权限的 PingFang SC Regular、PingFang SC Light、Helvetica Neue Thin、Helvetica Neue Light、Arial Regular。
2. 安装 LibreOffice Impress。可执行文件在 PATH 里叫 `soffice`，或用环境变量 `SOFFICE` 指向它。
3. 再跑一次 `python scripts/publish_ppt.py 内容.json 新目录`。退出码 0 且 `验收.json` 里 `视觉放行` 为 true，才算放行。

`python scripts/probe_env.py` 只报告缺什么，不生产文件。

A4 的 HTML 使用同一套字体栈，并允许回退到 Microsoft YaHei。回退会改变断行。所以 A4 的视觉放行不看 HTML 源码，看 `--pdf` 的浏览器测量。Node 可用时：

`python scripts/publish_a4.py 内容.json 输出目录 --pdf`

测量脚本是 `scripts/render_a4_pdf.mjs`，需要本机 Playwright 或 `CHROME_PATH`。越界就失败。这时加页或改写，不缩小字号。

## 本机没有放行环境时

仍然交付 PPTX 或 HTML，并在回复里写退出码 2 和 `未放行原因`。不要声称 PDF 已核对，也不要另做一份视觉近似的文件充数。
