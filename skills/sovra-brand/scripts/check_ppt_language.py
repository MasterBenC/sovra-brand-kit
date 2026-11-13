"""PPT 语言门禁。发布前必须通过，否则不写 PPTX。

查两件事：
1. 专业词不能单独当卖点。听众先要看到谁在做什么、做成什么。
2. 正文和备注不能省掉主语谓语。后一页要接上前一页，不能另起一个没头的话题。
"""
import argparse
import json
import re
import sys
from pathlib import Path

BUZZ = (
    "赋能", "抓手", "闭环", "颗粒度", "组合拳", "底层逻辑", "顶层设计",
    "打法", "心智", "赛道", "护城河", "拉通", "穿透", "解构", "对齐",
    "沉淀", "中台", "方法论",
)
OUTCOME = ("能", "可以", "少", "避免", "看清", "说清", "交出", "确认", "完成", "知道", "减少", "跟上", "核对", "登记", "帮助", "让")
ACTORS = (
    "人", "员", "师", "同事", "主管", "学员", "老板", "财务", "客户", "门店", "公司",
    "值班", "接班", "交班", "双方", "两人", "大家", "我们", "他们", "讲师", "维修",
    "税务", "部门", "学员", "读者",
)
PREDS = (
    "是", "为", "有", "要", "能", "会", "把", "被", "让", "做", "用", "写", "看",
    "确认", "核对", "完成", "发现", "需要", "可以", "应该", "交给", "留下", "跟进",
    "复核", "登记", "通知", "安排", "说明", "区分", "比较", "找到", "说出", "说清",
    "看清", "避免", "减少", "帮助", "试扫", "复测", "更换", "换上", "签名", "留存",
    "记下", "移交", "来自", "用于", "重新", "对应",
)
CONNECTIVES = ("接着", "然后", "所以", "因此", "这时", "此后", "完成后", "上一", "接下来", "对应", "同样", "如果", "再", "还", "已经", "对此", "基于", "当")
ACRONYM = re.compile(r"[A-Z]{2,}|[A-Za-z]{3,}")
ACRONYM_ALLOW = {"AI", "PPT", "PDF", "OK"}
METHOD_SELL = re.compile(r"(导入|上线|落地|推广|赋能).{0,16}(体系|模型|框架|方法论|中台|闭环)")


def _sentences(text):
    parts = re.split(r"[。！？\n；;]", text or "")
    return [part.strip() for part in parts if part.strip()]


def _has_actor(text):
    return any(word in text for word in ACTORS)


def _has_pred(text):
    return any(word in text for word in PREDS)


def _words(text):
    found = set()
    for run in re.findall(r"[\u4e00-\u9fff]+", text or ""):
        for index in range(len(run) - 1):
            found.add(run[index:index + 2])
    return found


def _page_text(page):
    chunks = [page.get("title", ""), page.get("lead", ""), page.get("takeaway", ""), page.get("notes", "")]
    for label, desc in page.get("items") or []:
        chunks.extend((label, desc))
    chunks.extend(page.get("columns") or [])
    for row in page.get("rows") or []:
        chunks.extend(row)
    return "\n".join(chunks)


def _need_sentence(text, where, errors):
    flat = (text or "").replace("\n", "")
    if not flat:
        errors.append(f"{where} 是空的。写清谁在做什么。")
        return
    if not _has_pred(flat) or not _has_actor(flat):
        errors.append(f"{where} 缺主语或谓语，不能只丢术语或动作：{flat}")


def _buzz(text, where, errors):
    for sentence in _sentences(text):
        if METHOD_SELL.search(sentence) and not any(word in sentence for word in ("让", "帮助", "以便", "从而", "少", "能", "看清", "避免")):
            errors.append(f"{where} 在卖方法名，没有听众能核对的结果：{sentence}")
        hits = [word for word in BUZZ if word in sentence]
        if hits and not any(word in sentence for word in OUTCOME):
            errors.append(f"{where} 用了专业腔「{'、'.join(hits)}」，同句没有听众结果：{sentence}")


def _acronyms(text, where, errors):
    for term in ACRONYM.findall(text or ""):
        if term in ACRONYM_ALLOW:
            continue
        window = text[text.find(term):text.find(term) + len(term) + 18]
        if "（" not in window and "是指" not in text and "也就是" not in text:
            errors.append(f"{where} 的 {term} 没有当页解释。先写听众能看见的事，再括号解释术语。")


def problems(data):
    errors = []
    audience = (data.get("audience") or "").strip()
    if len(audience) < 6 or not any(word in audience for word in ("不", "懂", "会", "同事", "老板", "学员", "财务", "客户", "门店")):
        errors.append("缺少 audience。写清谁在听，以及他们不熟悉什么。例如：门店值班同事，不要求会做账。")
    for section_index, section in enumerate(data.get("sections") or [], 1):
        title = section.get("title") or ""
        summary = section.get("summary") or ""
        where = f"第{section_index}章"
        _need_sentence(summary, where + " 摘要", errors)
        _buzz(summary, where + " 摘要", errors)
        if not (_words(title) & _words(summary)):
            errors.append(f"{where} 摘要没有接上章名「{title}」。摘要里要重复这章正在讲的人或事。")
        pages = section.get("pages") or []
        previous = ""
        for page_index, page in enumerate(pages, 1):
            place = f"{where}第{page_index}页"
            page_title = page.get("title") or ""
            if "？" not in page_title and not _has_pred(page_title):
                errors.append(f"{place} 标题「{page_title}」既不是问题，也没有动作。听众不知道这页要判断什么。")
            for field, label in (("lead", "导语"), ("takeaway", "结论"), ("notes", "备注")):
                value = page.get(field) or ""
                if not value:
                    continue
                _need_sentence(value, f"{place} {label}", errors)
                _buzz(value, f"{place} {label}", errors)
                if field == "notes" and not value.endswith(("。", "？", "！")):
                    errors.append(f"{place} 备注不是完整句：{value}")
            if page_index > 1:
                notes = page.get("notes") or ""
                if not any(word in notes for word in CONNECTIVES):
                    errors.append(f"{place} 备注没有承接上一页。写明接着、因此、这时要做什么，不要另起一个没头的话题。")
                if not (_words(_page_text(page)) & _words(previous)):
                    errors.append(f"{place} 和上一页没有共同的人或事。把上一页的对象写进这一页的标题、导语或说明。")
            for item_index, item in enumerate(page.get("items") or [], 1):
                if len(item) < 2:
                    continue
                desc = item[1]
                _need_sentence(desc, f"{place} 第{item_index}条说明", errors)
                _buzz(desc, f"{place} 第{item_index}条说明", errors)
                _acronyms(desc, f"{place} 第{item_index}条说明", errors)
            for row_index, row in enumerate(page.get("rows") or [], 1):
                for cell in row:
                    chinese = re.findall(r"[\u4e00-\u9fff]", cell or "")
                    if len(chinese) <= 8 and "，" not in (cell or "") and "。" not in (cell or ""):
                        continue
                    _need_sentence(cell, f"{place} 表格第{row_index}行", errors)
                    _buzz(cell, f"{place} 表格第{row_index}行", errors)
                    _acronyms(cell, f"{place} 表格第{row_index}行", errors)
            blob = _page_text(page)
            _acronyms(blob, place, errors)
            _buzz(page_title, place + " 标题", errors)
            previous = blob
    return errors


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("content", type=Path)
    args = parser.parse_args()
    found = problems(json.loads(args.content.read_text(encoding="utf-8")))
    if found:
        print("语言检查未通过")
        for item in found:
            print("-", item)
        return 1
    print("语言检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
