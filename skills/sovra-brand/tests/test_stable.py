"""证明示例成品字节稳定。不需要字体，也不需要 LibreOffice。"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[1]
PY = sys.executable
GOLDEN = json.loads((SKILL / "tests" / "golden.json").read_text(encoding="utf-8"))


def run(script, *args):
    completed = subprocess.run(
        [PY, str(SKILL / "scripts" / script), *args],
        cwd=SKILL,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    return completed.returncode, completed.stdout + completed.stderr


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish_twice(script, source, suffix):
    hashes = []
    codes = []
    for _ in range(2):
        out = Path(tempfile.mkdtemp(prefix="sovra-test-"))
        code, output = run(script, str(source), str(out / suffix))
        codes.append(code)
        if code not in (0, 2):
            raise SystemExit(f"{script} failed ({code})\n{output}")
        report = json.loads((out / suffix / "验收.json").read_text(encoding="utf-8"))
        if report["两次构建一致"] is not True:
            raise SystemExit("稳定性标志不为 true")
        target = "演示稿.pptx" if script == "publish_ppt.py" else "文档.html"
        hashes.append(sha256(out / suffix / target))
    if hashes[0] != hashes[1]:
        raise SystemExit(f"{script} 两次发布哈希不同")
    if codes[0] != codes[1]:
        raise SystemExit(f"{script} 两次退出码不同: {codes}")
    return hashes[0], codes[0]


def main():
    ppt_hash, ppt_code = publish_twice("publish_ppt.py", SKILL / "examples" / "ppt" / "content.json", "ppt")
    html_hash, html_code = publish_twice("publish_a4.py", SKILL / "examples" / "a4" / "proposal.json", "a4")
    if ppt_hash != GOLDEN["example_pptx_sha256"]:
        raise SystemExit(f"PPTX 哈希偏离锁定值\n实际 {ppt_hash}\n锁定 {GOLDEN['example_pptx_sha256']}")
    if html_hash != GOLDEN["example_html_sha256"]:
        raise SystemExit(f"HTML 哈希偏离锁定值\n实际 {html_hash}\n锁定 {GOLDEN['example_html_sha256']}")

    mutated = json.loads((SKILL / "examples" / "ppt" / "content.json").read_text(encoding="utf-8"))
    mutated["title"] = mutated["title"] + "改"
    mut_path = Path(tempfile.mkdtemp()) / "mut.json"
    mut_path.write_text(json.dumps(mutated, ensure_ascii=False), encoding="utf-8")
    mut_out = Path(tempfile.mkdtemp()) / "mut"
    code, output = run("publish_ppt.py", str(mut_path), str(mut_out))
    if code not in (0, 2):
        raise SystemExit(f"改一个字后的发布失败 ({code})\n{output}")
    if sha256(mut_out / "演示稿.pptx") == ppt_hash:
        raise SystemExit("标题变了，PPTX 哈希却没变")

    bad = Path(tempfile.mkdtemp()) / "bad.json"
    payload = {
        "audience": "门店值班同事，不要求会做账",
        "event": "测试",
        "title": "这是一行故意写得很长的标题用来触发超宽门禁不应该被排进页面",
        "short_title": "超宽",
        "subtitle": "让值班同事看清记录",
        "speaker": "测试",
        "credentials": ["测试"],
        "goal": "看清记录",
        "sections": [{
            "title": "核对记录",
            "summary": "值班同事要能核对当班记录",
            "pages": [{
                "type": "cards",
                "title": "谁来核对记录？",
                "items": [["清点", "交班人核对设备编号。"], ["签收", "接班人核对记录并签名。"]],
                "notes": "请学员说出负责人。",
            }],
        }],
    }
    bad.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    code, output = run("publish_ppt.py", str(bad), str(Path(tempfile.mkdtemp()) / "bad-out"))
    if code != 1 or "超宽" not in output:
        raise SystemExit(f"超宽标题应当失败，实际 {code}\n{output}")

    jargon = Path(tempfile.mkdtemp()) / "jargon.json"
    jargon.write_text(json.dumps({
        "audience": "企业老板，不懂内部方法名",
        "event": "测试",
        "title": "短标题",
        "short_title": "短",
        "subtitle": "让老板看清少算错的那一笔",
        "speaker": "测试",
        "credentials": ["测试"],
        "goal": "看清记录",
        "sections": [{
            "title": "导入闭环",
            "summary": "导入我们的FDE闭环体系",
            "pages": [{
                "type": "cards",
                "title": "赋能业务",
                "items": [["抓手", "赋能"], ["对齐", "拉通部门"]],
                "notes": "讲闭环",
            }],
        }],
    }, ensure_ascii=False), encoding="utf-8")
    jargon_out = Path(tempfile.mkdtemp()) / "jargon-out"
    code, output = run("publish_ppt.py", str(jargon), str(jargon_out))
    if code != 1 or "语言检查未通过" not in output:
        raise SystemExit(f"术语稿应当被语言检查拒绝，实际 {code}\n{output}")
    if (jargon_out / "演示稿.pptx").exists():
        raise SystemExit("语言检查失败时不应写出 PPTX")
    if "缺主语" not in output and "卖方法" not in output and "专业腔" not in output:
        raise SystemExit(f"语言检查没有指出术语或缺主语\n{output}")

    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    description = text.split('description: "')[1].split('"')[0]
    if not description.startswith("Use when"):
        raise SystemExit("description 没有触发词")
    if len(description) > 60:
        raise SystemExit(f"description 超过 60 字: {len(description)}")
    print("PASS")
    print("pptx", ppt_hash)
    print("html", html_hash)
    return 0


if __name__ == "__main__":
    sys.exit(main())
