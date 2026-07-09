#!/usr/bin/env bash
set -euo pipefail

target_repo="${APTV_SYNC_REPO:-git@github.com:279458179/APTV-dingyue.git}"
target_branch="${APTV_SYNC_BRANCH:-main}"
epg_url="${APTV_EPG_URL:-https://raw.githubusercontent.com/279458179/APTV-dingyue/main/epg.gz}"

if [[ ! -f output/user_result.m3u ]]; then
  echo "Missing output/user_result.m3u; run the IPTV update before syncing." >&2
  exit 1
fi

if [[ ! -f output/user_result.txt ]]; then
  echo "Missing output/user_result.txt; run the IPTV update before syncing." >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git clone --depth 1 --branch "$target_branch" "$target_repo" "$tmp_dir/repo"

python - "$tmp_dir/repo" "$epg_url" <<'PY'
from pathlib import Path
import re
import shutil
import sys

target = Path(sys.argv[1])
epg_url = sys.argv[2]

m3u = Path("output/user_result.m3u").read_text(encoding="utf-8")
if m3u.startswith("#EXTM3U"):
    m3u = re.sub(r'^#EXTM3U[^\n]*', f'#EXTM3U x-tvg-url="{epg_url}"', m3u, count=1)

(target / "cctv_full.txt").write_text(m3u, encoding="utf-8", newline="\n")
shutil.copyfile("output/user_result.txt", target / "iptv_api.txt")

epg = Path("output/epg/epg.gz")
if epg.exists():
    shutil.copyfile(epg, target / "epg.gz")

readme = """# APTV Dingyue

This repository is automatically synced from `279458179/iptv-api` after each successful IPTV build.

## Subscription URLs

M3U:

```text
https://raw.githubusercontent.com/279458179/APTV-dingyue/main/cctv_full.txt
```

TXT:

```text
https://raw.githubusercontent.com/279458179/APTV-dingyue/main/iptv_api.txt
```

EPG:

```text
https://raw.githubusercontent.com/279458179/APTV-dingyue/main/epg.gz
```
"""
(target / "README.md").write_text(readme, encoding="utf-8", newline="\n")
PY

cd "$tmp_dir/repo"
git config user.email "github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"
git add README.md cctv_full.txt iptv_api.txt epg.gz

if git diff --staged --quiet; then
  echo "APTV-dingyue already up to date."
  exit 0
fi

git commit -m "Sync IPTV API output"
git push origin "HEAD:$target_branch"
