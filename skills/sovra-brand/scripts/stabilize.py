"""把 python-pptx 写出的 PPTX 收成跨机器可重复的字节。

库会把当前时间写进 ZIP 条目头。Deflate 的压缩结果还会随 zlib 版本变化。
这里改为不压缩、固定时间戳、按文件名排序，使哈希只取决于 OOXML 内容。
"""
import io
import zipfile
from pathlib import Path

FIXED = (2026, 11, 5, 0, 0, 0)


def stabilize_pptx(path: Path) -> bytes:
    raw = Path(path).read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as src:
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as dst:
            for info in sorted(src.infolist(), key=lambda item: item.filename):
                blob = src.read(info.filename)
                ni = zipfile.ZipInfo(filename=info.filename, date_time=FIXED)
                ni.compress_type = zipfile.ZIP_STORED
                ni.create_system = 0
                ni.external_attr = 0
                dst.writestr(ni, blob)
    data = out.getvalue()
    Path(path).write_bytes(data)
    return data
