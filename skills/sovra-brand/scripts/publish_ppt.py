"""发布字节稳定的灵能涌现 PPTX。

退出码：0 视觉放行；2 结构稳定但未放行；1 失败，不得交付。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pptx

from build import build
from check_ppt_language import problems
from probe_env import missing_fonts, soffice_path
from stabilize import stabilize_pptx

PPTX_VERSION = "1.0.2"
PDF_FONTS = (
    "PingFangSC-Regular",
    "PingFangSC-Light",
    "ArialMT",
    "HelveticaNeue-Thin",
    "HelveticaNeue-Light",
)
SKILL = Path(__file__).resolve().parents[1]


def content_hash(data):
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def assert_media_passthrough(deck: Path, source: Path, data: dict):
    cover = (SKILL / "assets" / "cover.png").read_bytes()
    expected = [cover]
    for section in data["sections"]:
        for page in section["pages"]:
            if page.get("type") == "visual":
                asset = source.parent / page["asset"]
                blob = asset.read_bytes()
                if not blob.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError(f"visual 素材必须是 PNG，且发布时原字节嵌入：{page['asset']}")
                expected.append(blob)
    with zipfile.ZipFile(deck) as package:
        media = [
            package.read(name)
            for name in sorted(n for n in package.namelist() if n.startswith("ppt/media/"))
        ]
    if media != expected:
        raise RuntimeError("嵌入图片与源文件字节不一致。拒绝交付被改写的图。")


def pdf_fonts(blob: bytes):
    return sorted({
        item.decode(errors="replace").split("+")[-1]
        for item in re.findall(rb"/BaseFont\s*/([^/\s]+)", blob)
    })


def export_pdf(deck: Path, work: Path):
    office = soffice_path()
    if not office:
        return None, ["未找到 LibreOffice。安装后设置 SOFFICE，再重新发布。"]
    subprocess.run(
        [
            office,
            "-env:UserInstallation=" + (work / "lo-profile").resolve().as_uri(),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(work),
            str(deck),
        ],
        check=True,
        cwd=work,
    )
    found = list(work.glob("*.pdf"))
    if not found:
        return None, ["LibreOffice 没有写出 PDF。"]
    blob = found[0].read_bytes()
    actual = pdf_fonts(blob)
    missing = [name for name in PDF_FONTS if name not in actual]
    if missing:
        return None, ["PDF 未嵌入规定字体: " + ", ".join(missing) + "。不要改用其他字体顶替。"]
    return blob, []


def publish(source: Path, out: Path, force: bool = False):
    if pptx.__version__ != PPTX_VERSION:
        raise RuntimeError(f"python-pptx {pptx.__version__} != {PPTX_VERSION}。按 requirements.txt 安装，避免版式字节漂移。")
    if not __debug__:
        raise RuntimeError("请用普通模式运行 Python，不要加 -O。")
    source = source.resolve()
    out = out.resolve()
    if out == SKILL or SKILL in out.parents:
        raise RuntimeError("输出目录不能放在技能目录里。")
    data = json.loads(source.read_text(encoding="utf-8"))
    found = problems(data)
    if found:
        raise RuntimeError("语言检查未通过\n" + "\n".join("- " + item for item in found))
    digest = content_hash(data)
    marker = out / "验收.json"
    if marker.exists() and not force:
        old = json.loads(marker.read_text(encoding="utf-8"))
        if old.get("content_sha256") not in (None, digest):
            raise RuntimeError("输出目录已有另一份内容的验收记录。换新目录，或显式传入 --force。")

    work = Path(tempfile.mkdtemp(prefix="sovra-ppt-"))
    try:
        first = work / "1.pptx"
        second = work / "2.pptx"
        build(source, first)
        left = stabilize_pptx(first)
        build(source, second)
        right = stabilize_pptx(second)
        if left != right:
            raise RuntimeError("两次构建字节不一致，拒绝交付。")
        assert_media_passthrough(first, source, data)
        page_count = len(pptx.Presentation(str(first)).slides)
        pdf_dir = work / "pdf"
        pdf_dir.mkdir()
        try:
            pdf_blob, pdf_reasons = export_pdf(first, pdf_dir)
        except Exception as exc:
            pdf_blob, pdf_reasons = None, ["PDF 导出失败: " + str(exc)]
    finally:
        shutil.rmtree(work, ignore_errors=True)

    reasons = [f"缺少字体: {name}" for name in missing_fonts()]
    reasons.extend(pdf_reasons)
    released = not reasons and pdf_blob is not None
    out.mkdir(parents=True, exist_ok=True)
    (out / "演示稿.pptx").write_bytes(left)
    pdf_path = out / "演示稿.pdf"
    if released:
        pdf_path.write_bytes(pdf_blob)
    elif pdf_path.exists():
        pdf_path.unlink()
    report = {
        "媒介": "ppt",
        "python_pptx": PPTX_VERSION,
        "content_sha256": digest,
        "pptx_sha256": hashlib.sha256(left).hexdigest(),
        "页数": page_count,
        "两次构建一致": True,
        "语言检查": "通过",
        "封面原图未改写": True,
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
    args = parser.parse_args()
    try:
        report = publish(args.content, args.out, args.force)
    except Exception as exc:
        print("RESULT FAIL")
        print(exc)
        return 1
    print("RESULT", "RELEASED" if report["视觉放行"] else "UNRELEASED")
    print("PPTX", report["pptx_sha256"])
    print("PAGES", report["页数"])
    if report["未放行原因"]:
        print("WHY")
        for item in report["未放行原因"]:
            print("-", item)
    return 0 if report["视觉放行"] else 2


if __name__ == "__main__":
    sys.exit(main())
