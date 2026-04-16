"""RSSフィードを一括取得し、正規化した JSON として data/raw_YYYY-MM-DD.json に保存する。

使い方:
    python scripts/fetch_feeds.py

feeds.yaml を読み、各フィードを並列に取得。直近 lookback_hours 以内のエントリだけ抽出し、
URL 重複を除去して data/raw_<today>.json に書き出す。1フィードが失敗しても全体は継続する。
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser  # type: ignore
import yaml  # type: ignore


JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "feeds.yaml"
DATA_DIR = ROOT / "data"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def entry_timestamp(entry) -> datetime | None:
    """feedparser entry から published/updated を datetime(UTC) で返す。取れなければ None。"""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def strip_html(text: str, limit: int = 400) -> str:
    """HTML タグを雑に剥がして先頭 limit 文字に切り詰める。要約生成用の入力として使う。"""
    import re

    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def fetch_one(feed_cfg: dict, cutoff: datetime, timeout: int) -> tuple[str, list[dict], str | None]:
    """1フィードを取得。(feed名, items, エラー文字列) を返す。"""
    name = feed_cfg["name"]
    url = feed_cfg["url"]
    category = feed_cfg.get("category", "community")
    try:
        # feedparser は内部で urllib を使うため、socket.setdefaulttimeout で制御する
        import socket

        socket.setdefaulttimeout(timeout)
        parsed = feedparser.parse(url)
        if parsed.bozo and not parsed.entries:
            return name, [], f"parse error: {parsed.bozo_exception!r}"

        items: list[dict] = []
        for e in parsed.entries:
            ts = entry_timestamp(e)
            if ts is None or ts < cutoff:
                continue
            items.append(
                {
                    "source": name,
                    "category": category,
                    "title": (e.get("title") or "").strip(),
                    "url": e.get("link") or "",
                    "published_at": ts.astimezone(JST).isoformat(),
                    "summary": strip_html(e.get("summary") or e.get("description") or ""),
                    "tags": [t.get("term", "") for t in e.get("tags", []) if t.get("term")],
                }
            )
        return name, items, None
    except Exception as ex:  # noqa: BLE001 - フィード側の事情はなんでも起こりうる
        return name, [], f"{type(ex).__name__}: {ex}"


def main() -> int:
    cfg = load_config()
    feeds = cfg.get("feeds", [])
    settings = cfg.get("settings", {})

    now_jst = datetime.now(JST)
    weekday = now_jst.weekday()  # 月曜=0
    lookback = (
        settings.get("lookback_hours_monday", 66)
        if weekday == 0
        else settings.get("lookback_hours_weekday", 30)
    )
    cutoff = (now_jst - timedelta(hours=lookback)).astimezone(timezone.utc)
    timeout = int(settings.get("fetch_timeout", 10))
    max_workers = int(settings.get("max_workers", 8))

    print(f"[fetch] now_jst={now_jst.isoformat()}  lookback={lookback}h  feeds={len(feeds)}", flush=True)

    all_items: list[dict] = []
    errors: list[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_one, f, cutoff, timeout): f for f in feeds}
        for fut in as_completed(futures):
            name, items, err = fut.result()
            if err:
                print(f"[warn ] {name}: {err}", flush=True)
                errors.append({"feed": name, "error": err})
            else:
                print(f"[ok   ] {name}: {len(items)} items", flush=True)
                all_items.extend(items)

    # URL重複除去（最初に現れたものを残す）
    seen: set[str] = set()
    deduped: list[dict] = []
    for it in all_items:
        key = it["url"]
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    # 新しい順に並べる
    deduped.sort(key=lambda x: x["published_at"], reverse=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"raw_{now_jst.strftime('%Y-%m-%d')}.json"
    payload = {
        "generated_at": now_jst.isoformat(),
        "lookback_hours": lookback,
        "feed_count": len(feeds),
        "item_count": len(deduped),
        "errors": errors,
        "items": deduped,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[done ] wrote {out_path}  items={len(deduped)}  errors={len(errors)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
