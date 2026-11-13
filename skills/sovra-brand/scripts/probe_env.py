"""报告字体和 LibreOffice，不生产文件。退出码始终为 0。"""
import json
import os
import shutil
import sys
from pathlib import Path

REQUIRED = ("PingFang SC", "Helvetica Neue", "Arial")


def _windows_font_names():
    import winreg

    found = set()
    keys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
    )
    for hive, path in keys:
        try:
            with winreg.OpenKey(hive, path) as key:
                index = 0
                while True:
                    try:
                        name, _, _ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    found.add(name)
                    index += 1
        except FileNotFoundError:
            continue
    return found


def _font_blob():
    names = set()
    if os.name == "nt":
        names.update(_windows_font_names())
    roots = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
        Path.home() / "Library" / "Fonts",
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path("/usr/share/fonts"),
        Path.home() / ".local" / "share" / "fonts",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                names.add(path.name)
    fc = shutil.which("fc-list")
    if fc:
        import subprocess

        out = subprocess.run([fc], capture_output=True, text=True, check=False).stdout
        names.update(out.splitlines())
    return "\n".join(names)


def missing_fonts():
    blob = _font_blob()
    return [name for name in REQUIRED if name not in blob]


def soffice_path():
    return os.environ.get("SOFFICE") or shutil.which("soffice") or shutil.which("libreoffice")


def report():
    missing = missing_fonts()
    office = soffice_path()
    reasons = [f"缺少字体: {name}" for name in missing]
    if not office:
        reasons.append("未找到 LibreOffice。安装后把可执行文件放到 PATH，或设置 SOFFICE。")
    return {
        "缺少字体": missing,
        "LibreOffice": office or "",
        "可以尝试视觉放行": not reasons,
        "未放行原因": reasons,
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    json.dump(report(), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
