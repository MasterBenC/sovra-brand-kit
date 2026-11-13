# 灵能涌现品牌生产技能

PPT 和 A4 分轨。版式由脚本锁定。同一份内容源连续发布两次，PPTX 或 HTML 字节相同，才允许交付。

不含客户成品或历史课件。品牌底图可随仓库分发，不构成改标授权，见 `NOTICE.md`。

## 交给 Agent 的一句

```text
请阅读 https://raw.githubusercontent.com/MasterBenC/sovra-brand-kit/main/AGENT_INSTALL.md
按里面的步骤安装，装完跑 python tests/test_stable.py，把结果告诉我。
```

## 稳定是什么

| 媒介 | 锚点 | 两次发布必须相同 | 不承诺 |
|---|---|---|---|
| PPT | `演示稿.pptx` | SHA256 | PDF 字节 |
| A4 | `文档.html` | SHA256 | PDF 字节 |

退出码 1 是失败，包括语言检查未通过：用术语当卖点、句子缺主语、后页接不上前页，都不产出 PPTX。退出码 2 是源文件稳定但未视觉放行，通常因为缺苹方、Helvetica Neue 或 LibreOffice。退出码 0 才是视觉放行。不要把缺字体时的文件说成已核对 PDF。

## 文件

```text
skills/sovra-brand/
  SKILL.md
  scripts/publish_ppt.py
  scripts/publish_a4.py
  assets/cover.png
  assets/role-styles.json
  examples/
  tests/test_stable.py
```

技能说明在 `skills/sovra-brand/SKILL.md`。安装步骤在 `AGENT_INSTALL.md`。
