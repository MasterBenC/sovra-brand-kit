"""发布字节稳定的灵能涌现 A4 HTML。

退出码：0 已用浏览器测过布局并导出 PDF；2 HTML 稳定但未视觉放行；1 失败。
"""
import argparse
import hashlib
import html
import json
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
A4 = SKILL / "assets" / "a4"


def content_hash(data):
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def text_width(value):
    return sum(1 if unicodedata.east_asian_width(char) in ("W", "F") else 0.5 for char in value)


def generate(data):
    for key in ("document_type", "category", "file_type", "cover", "pages"):
        if key not in data:
            raise ValueError("缺少字段: " + key)
    if data["document_type"] not in ("proposal", "meeting_minutes"):
        raise ValueError("document_type 只能是 proposal 或 meeting_minutes")
    cover = data["cover"]
    title_lines = cover["title_lines"]
    if not 2 <= len(title_lines) <= 4:
        raise ValueError("封面标题需要 2 到 4 行")
    for line in title_lines[1:]:
        if text_width(line) > 8:
            raise ValueError("封面标题后续行超过 8 个全角字位: " + line)
    if len(cover["statements"]) > 2:
        raise ValueError("封面主张最多两行")
    if not data["pages"]:
        raise ValueError("至少一页正文")

    def esc(value):
        return html.escape(str(value))

    category = esc(data["category"] + " / " + data["file_type"])
    statements = "<br>".join(esc(item.rstrip("。．.")) for item in cover["statements"])
    footer_en = "meeting notes" if data["document_type"] == "meeting_minutes" else "cooperation proposal"
    parts = [
        '<article class="page cover"><div class="head"><div class="brand-name brand-inline">灵能涌现 · the emergent company</div><span class="cover-tec">t.e.c</span></div><div class="tag">'
        + category
        + "</div><h1>"
        + "".join("<span>" + esc(line) + "</span>" for line in title_lines)
        + '</h1><p class="statement">'
        + statements
        + '</p><p class="meeting-note">'
        + esc(cover["meeting_note"])
        + "</p><footer><span>看清方向 / 学会方法 / 落到业务</span><span>"
        + footer_en
        + "</span></footer></article>"
    ]
    count = len(data["pages"])
    for number, page in enumerate(data["pages"], 1):
        sections = []
        for index, section in enumerate(page["sections"], 1):
            paragraphs = "".join("<p>" + esc(text) + "</p>" for text in section["paragraphs"])
            bullets = ""
            if section.get("bullets"):
                bullets = '<ul class="plain-list">' + "".join("<li>" + esc(item) + "</li>" for item in section["bullets"]) + "</ul>"
            sections.append(
                "<section><h2><span>"
                + f"{index:02}"
                + "</span>"
                + esc(section["title"])
                + '</h2><div class="body-copy">'
                + paragraphs
                + "</div>"
                + bullets
                + "</section>"
            )
        note = '<p class="execution-note">' + esc(page["note"]) + "</p>" if page.get("note") else ""
        parts.append(
            '<article class="page"><div class="head"><span class="doc-label">'
            + category
            + '</span><span class="doc-tec">t.e.c</span></div><h1>'
            + esc(page["title"])
            + '</h1><div class="lead">'
            + esc(page["lead"])
            + "</div>"
            + "".join(sections)
            + note
            + "<footer><span>灵能涌现 · the emergent company</span><span>"
            + f"{number:02} / {count:02}"
            + "</span></footer></article>"
        )
    template = (A4 / "templates" / "document.html").read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    css = (A4 / "templates" / "theme.css").read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    page = (
        template.replace("{{TITLE}}", esc(title_lines[0] + "｜" + data["file_type"]))
        .replace("{{CSS}}", css)
        .replace("{{PAGES}}", "".join(parts))
    )
    if not page.endswith("\n"):
        page += "\n"
    return page


def render_pdf(html_path: Path, pdf_path: Path):
    node = shutil.which("node")
    script = SKILL / "scripts" / "render_a4_pdf.mjs"
    if not node:
        raise RuntimeError("未找到 Node，不能做 A4 视觉放行。")
    subprocess.run(
        [node, str(script), str(html_path), "--pdf", str(pdf_path)],
        check=True,
        cwd=SKILL,
    )


def publish(source: Path, out: Path, force: bool = False, want_pdf: bool = False):
    source = source.resolve()
    out = out.resolve()
    if out == SKILL or SKILL in out.parents:
        raise RuntimeError("输出目录不能放在技能目录里。")
    data = json.loads(source.read_text(encoding="utf-8"))
    digest = content_hash(data)
    marker = out / "验收.json"
    if marker.exists() and not force:
        old = json.loads(marker.read_text(encoding="utf-8"))
        if old.get("content_sha256") not in (None, digest):
            raise RuntimeError("输出目录已有另一份内容的验收记录。换新目录，或显式传入 --force。")
    left = generate(data)
    right = generate(data)
    if left != right:
        raise RuntimeError("两次生成的 HTML 不一致，拒绝交付。")
    reasons = []
    released = False
    out.mkdir(parents=True, exist_ok=True)
    html_path = out / "文档.html"
    html_path.write_text(left, encoding="utf-8", newline="\n")
    pdf_path = out / "文档.pdf"
    if want_pdf:
        try:
            render_pdf(html_path, pdf_path)
            released = pdf_path.exists()
            if not released:
                reasons.append("浏览器导出没有写出 PDF。")
        except subprocess.CalledProcessError as exc:
            reasons.append("布局检查或 PDF 导出失败，退出码 " + str(exc.returncode) + "。缩短内容或加页，不要缩小字号。")
            if pdf_path.exists():
                pdf_path.unlink()
        except RuntimeError as exc:
            reasons.append(str(exc))
    else:
        reasons.append("未加 --pdf，正文是否压页脚尚未用浏览器测量。")
        if pdf_path.exists():
            pdf_path.unlink()
    report = {
        "媒介": "a4",
        "content_sha256": digest,
        "html_sha256": hashlib.sha256(left.encode("utf-8")).hexdigest(),
        "页数": 1 + len(data["pages"]),
        "两次构建一致": True,
        "视觉放行": released,
        "未放行原因": reasons,
    }
    (out / "验收.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("content", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--pdf", action="store_true")
    args = parser.parse_args()
    try:
        report = publish(args.content, args.out, args.force, args.pdf)
    except Exception as exc:
        print("RESULT FAIL")
        print(exc)
        return 1
    print("RESULT", "RELEASED" if report["视觉放行"] else "UNRELEASED")
    print("HTML", report["html_sha256"])
    print("PAGES", report["页数"])
    if report["未放行原因"]:
        print("WHY")
        for item in report["未放行原因"]:
            print("-", item)
    return 0 if report["视觉放行"] else 2


if __name__ == "__main__":
    sys.exit(main())
