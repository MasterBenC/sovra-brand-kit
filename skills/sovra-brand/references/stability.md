# 稳定合同

## 什么叫稳定

同一份 JSON、同一版技能、`python-pptx==1.0.2`，连续两次发布得到相同的 SHA256。

- PPT 比的是规范化之后的 `演示稿.pptx`
- A4 比的是 `文档.html`
- 不比 PDF 字节。PDF 只证明它从这次的锚点导出，并且通过字体或分页门禁

规范化做三件事：ZIP 条目不压缩、时间戳写成 2026-11-05 00:00:00、条目按文件名排序。Deflate 会随 zlib 版本变化，所以不用它。PowerPoint 可以打开这种不压缩的 PPTX。

封面和 visual 素材必须原字节嵌入。脚本发现嵌入图和源 PNG 不一致就拒绝交付。

## 什么不算放行

结构稳定只说明文件可以重复生成。视觉放行还要：

- PPT：本机有 PingFang SC、Helvetica Neue、Arial，LibreOffice 导出的 PDF 嵌入 `PingFangSC-Regular`、`PingFangSC-Light`、`ArialMT`、`HelveticaNeue-Thin`、`HelveticaNeue-Light`
- A4：用 `--pdf` 跑浏览器测量，没有越界，才写出 `文档.pdf`

缺字体时不要改脚本换微软雅黑。那是另一份成品，不是这一份的稳定替代。

语言检查未通过则退出码 1，不写 PPTX。这不是视觉问题，改 JSON，不要放宽检查脚本。

## 代理不得做的事

- 手改 PPTX、HTML、CSS、`role-styles.json`、`build.py` 来“修一下溢出”
- 发布过程中调用生图。图要先落成 PNG，人工确认后再发布
- 重新生成一张已经确认过的图
- 用 WPS 或 PowerPoint 另存后的文件替换脚本输出
- 输出目录放在技能目录里面
- 往已有另一份 `content_sha256` 的目录里发布。换目录，或用户明确要求时才加 `--force`

## 回归

`tests/golden.json` 锁着示例 PPTX 和示例 HTML 的哈希。`python tests/test_stable.py` 必须通过。改版式脚本之前先改测试预期；客户任务里不改这些文件。
