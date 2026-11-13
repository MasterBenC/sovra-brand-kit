# A4 执行参数

成品是 A4 竖版。HTML 设计尺寸 794 × 1123 CSS px。上 48、左右 52、下 66。有效内容宽 690。这些是 CSS 像素，不是 PowerPoint 的磅。

最终生效的是 `assets/a4/templates/theme.css` 里后出现的规则。封面主标题上距以后一条 `margin-top:102px` 为准。不要按旧说明改模板，也不要只摘第一条声明。

## 颜色与字体

封面底 #080912，封面字 #EDEAE6，结构 #5145FF，强调 #FF925C，正文标题 #171717，正文 #444550。字体栈是 Helvetica Neue / Arial / PingFang SC / Microsoft YaHei。不随包分发字体文件。

| 角色 | 规则 |
|---|---|
| 封面品牌 | 左「灵能涌现 · the emergent company」16px；右 t.e.c 18px。不恢复 24px |
| 封面分类 | 13.2px，橙色，字距 2px |
| 封面主标题 | 51px，字重 300，行高 1.42。第一行是合作方正式名称。后续每行最多 8 个全角字位 |
| 封面主张 | 23px，最多两行，去掉句末句号 |
| 正文页标题 | 34px，一页一个 |
| 说明条 | 15px，左 3px 蓝紫线 |
| 小节标题 | 17px，字重 500 |
| 正文 | 14px，行高 1.9，不首行缩进 |
| 页脚 | 10px。左完整品牌，右正文页码。封面不计入页码 |

## 输入

`document_type` 只能是 `proposal` 或 `meeting_minutes`。课程指南用 proposal。页脚英文因此是 `cooperation proposal` 或 `meeting notes`，不要在 HTML 里改。

必填：`category`、`file_type`、`cover.title_lines`、`cover.statements`、`cover.meeting_note`、`pages`。每页有 `title`、`lead`、`sections`。每个小节有 `title`、`paragraphs`，可选 `bullets`。

客户成品不写制作日期、v1.0、内部讨论版。真实会议日期可以写在 `meeting_note`。

## 内容

先写读者要解决的问题和能得到什么，再写路径、交付和安排。已确认、计划、待确认三种状态用词必须能分开。不编造数字、案例、身份和免费权益。

连续内容跨页时，标题写明「（续）」和 1/2、2/2。装不下就加页。禁止缩小正文、压行距、裁切或隐藏文字。

## 和 PPT 的边界

A4 的 t.e.c 页眉、从 1 计数的正文页码、51px 封面标题，都不迁移到 PPT。PPT 的 21pt 标题和从 02 开始的页码，也不迁移到 A4。
