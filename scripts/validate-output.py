from pathlib import Path
import re
import sys


MIN_CHANNELS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
URL_PATTERN = re.compile(r"^(https?|rtmp|rtsp)://", re.IGNORECASE)


def count_txt_channels(path: Path) -> int:
    if not path.exists():
        raise FileNotFoundError(path)

    count = 0
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or "#genre#" in line:
            continue
        name, sep, value = line.partition(",")
        if sep and name != "🕘️更新时间" and URL_PATTERN.match(value.strip()):
            count += 1
    return count


def count_m3u_channels(path: Path) -> int:
    if not path.exists():
        raise FileNotFoundError(path)

    count = 0
    pending_extinf = None
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("#EXTINF"):
            pending_extinf = line
            continue
        if pending_extinf and URL_PATTERN.match(line):
            if "group-title=\"🕘️更新时间\"" not in pending_extinf:
                count += 1
            pending_extinf = None
    return count


txt_count = count_txt_channels(Path("output/user_result.txt"))
m3u_count = count_m3u_channels(Path("output/user_result.m3u"))

print(f"Validated output channels: txt={txt_count}, m3u={m3u_count}, minimum={MIN_CHANNELS}")

if txt_count < MIN_CHANNELS or m3u_count < MIN_CHANNELS:
    raise SystemExit(
        f"Generated output is too small. Refusing to commit or sync empty/invalid IPTV results."
    )
