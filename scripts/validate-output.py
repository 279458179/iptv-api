from pathlib import Path
import re
import sys


MIN_CHANNELS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
REQUIRED_CHANNELS_PATH = Path("config/required_channels.txt")
URL_PATTERN = re.compile(r"^(https?|rtmp|rtsp)://", re.IGNORECASE)


def load_required_channels(path: Path) -> list[str]:
    if not path.exists():
        return []

    channels = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            channels.append(line)
    return channels


def parse_txt_channels(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(path)

    channels = set()
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or "#genre#" in line:
            continue
        name, sep, value = line.partition(",")
        if sep and URL_PATTERN.match(value.strip()):
            channels.add(name.strip())
    return channels


def parse_m3u_channels(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(path)

    channels = set()
    pending_name = None
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("#EXTINF"):
            pending_name = line.rsplit(",", 1)[-1].strip()
            continue
        if pending_name and URL_PATTERN.match(line):
            channels.add(pending_name)
            pending_name = None
    return channels


txt_channels = parse_txt_channels(Path("output/user_result.txt"))
m3u_channels = parse_m3u_channels(Path("output/user_result.m3u"))
required_channels = load_required_channels(REQUIRED_CHANNELS_PATH)

print(
    "Validated output channels: "
    f"txt={len(txt_channels)}, m3u={len(m3u_channels)}, minimum={MIN_CHANNELS}, "
    f"required={len(required_channels)}"
)

errors = []
if len(txt_channels) < MIN_CHANNELS or len(m3u_channels) < MIN_CHANNELS:
    errors.append("Generated output is too small.")

missing_txt = [name for name in required_channels if name not in txt_channels]
missing_m3u = [name for name in required_channels if name not in m3u_channels]

if missing_txt:
    errors.append(f"Missing required TXT channels: {', '.join(missing_txt)}")
if missing_m3u:
    errors.append(f"Missing required M3U channels: {', '.join(missing_m3u)}")

if errors:
    raise SystemExit(
        "\n".join(errors)
        + "\nRefusing to commit or sync incomplete IPTV results."
    )
