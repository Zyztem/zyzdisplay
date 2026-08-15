#!/usr/bin/env python3

import base64
import json
import os
import random
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from icalendar import Calendar as ICalendar
    from dateutil.rrule import rrulestr
    CALENDAR_LIBS = True
except ImportError:
    ICalendar = None
    rrulestr = None
    CALENDAR_LIBS = False

APP_VERSION = "1.0.0"
WEB_ROOT = Path(os.environ.get("ZYZ_WEB_ROOT", "/opt/zyzdisplay/web")).resolve()
STATE_DIR = Path(os.environ.get("ZYZ_STATE_DIR", "/var/lib/zyzdisplay")).resolve()
NETWORK_IFACE = os.environ.get("NETWORK_IFACE", "wlan1")
SPOTIFY_STATUS_URL = os.environ.get("SPOTIFY_STATUS_URL", "http://127.0.0.1:3678/status")
WALLHAVEN_ENABLED = os.environ.get("WALLHAVEN_ENABLED", "1") not in ("0", "false", "False", "no")
WALLHAVEN_INTERVAL = max(60, int(os.environ.get("WALLHAVEN_INTERVAL", "300")))
WALLHAVEN_BATCH_REFRESH = max(600, int(os.environ.get("WALLHAVEN_BATCH_REFRESH", "7200")))
WALLHAVEN_QUERY = os.environ.get("WALLHAVEN_QUERY", "wildlife -cgi -3d -fantasy,nature landscape -cgi -3d,forest mountains -cgi,castle palace -fantasy -cgi,temple pyramid ruins -cgi")
WALLHAVEN_CATEGORIES = os.environ.get("WALLHAVEN_CATEGORIES", "100")
WALLHAVEN_PURITY = os.environ.get("WALLHAVEN_PURITY", "100")
WALLHAVEN_RESOLUTION = os.environ.get("WALLHAVEN_RESOLUTION", os.environ.get("WALLHAVEN_ATLEAST", "1920x1080"))
WALLHAVEN_RATIOS = os.environ.get("WALLHAVEN_RATIOS", "16x9")
WALLHAVEN_API = "https://wallhaven.cc/api/v1/search"
WALLHAVEN_DEFAULT_QUERIES = "wildlife -cgi -3d -fantasy,nature landscape -cgi -3d,forest mountains -cgi,castle palace -fantasy -cgi,temple pyramid ruins -cgi"
WEATHER_ENABLED = os.environ.get("WEATHER_ENABLED", "1") not in ("0", "false", "False", "no")
WEATHER_LOCATION = os.environ.get("WEATHER_LOCATION", "Newberry, Florida")
WEATHER_UNITS = os.environ.get("WEATHER_UNITS", "u")  # u = USCS °F, m = metric °C
WEATHER_REFRESH = max(300, int(os.environ.get("WEATHER_REFRESH", "900")))
WEATHER_LAT = os.environ.get("WEATHER_LAT", "").strip()
WEATHER_LON = os.environ.get("WEATHER_LON", "").strip()
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/gfs"
OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_AIR = "https://air-quality-api.open-meteo.com/v1/air-quality"
NWS_ALERTS = "https://api.weather.gov/alerts/active"
NWS_USER_AGENT = f"ZyzDisplay/{APP_VERSION} (home kiosk)"
CALENDAR_ICS_URL = os.environ.get("CALENDAR_ICS_URL", "")
CALENDAR_REFRESH = max(300, int(os.environ.get("CALENDAR_REFRESH", "900")))
CALENDAR_WINDOW_DAYS = 7
CALENDAR_LIMIT = 3
NTFY_ENABLED = os.environ.get("NTFY_ENABLED", "1") not in ("0", "false", "False", "no")
NTFY_URL = os.environ.get("NTFY_URL", "").strip().rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "").strip()
NTFY_USER = os.environ.get("NTFY_USER", "").strip()
NTFY_PASSWORD = os.environ.get("NTFY_PASSWORD", "").strip()
NTFY_LIMIT = 3
NTFY_MAX_AGE = 6 * 3600
NTFY_SINCE = os.environ.get("NTFY_SINCE", "1h").strip() or "1h"
NTFY_APP_NAMES = {
    "com.whatsapp": "WhatsApp",
    "com.whatsapp.w4b": "WhatsApp",
    "com.discord": "Discord",
    "com.discord.mobile": "Discord",
    "com.google.android.apps.messaging": "Messages",
    "com.samsung.android.messaging": "Messages",
    "com.facebook.orca": "Messenger",
    "com.facebook.mlite": "Messenger",
    "com.instagram.android": "Instagram",
    "com.samsung.android.dialer": "Phone",
    "com.samsung.android.incallui": "Phone",
    "com.google.android.dialer": "Phone",
    "com.android.dialer": "Phone",
    "com.android.server.telecom": "Phone",
    "com.google.android.gm": "Gmail",
    "org.thoughtcrime.securesms": "Signal",
    "org.telegram.messenger": "Telegram",
}


def run_command(*cmd):
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip()
    except Exception:
        return ""


_NET_CACHE = {"at": 0.0, "data": None}
_SPOTIFY_CACHE = {"at": 0.0, "data": None, "ok": False}
_SERVICE_CACHE = {"at": 0.0, "data": None}
_STATIC_CACHE = {}


def receiver_status():
    now = time.time()
    if _SERVICE_CACHE["data"] is not None and (now - _SERVICE_CACHE["at"]) < 15:
        return _SERVICE_CACHE["data"]

    def active(unit):
        # systemd maintains these markers only while a unit has an active
        # invocation. Unlike systemctl, they remain readable in our locked-down
        # DynamicUser sandbox and do not require D-Bus access.
        return os.path.lexists(f"/run/systemd/units/invocation:{unit}")

    data = {
        "miracast": all(active(unit) for unit in (
            "miracle-wifid.service", "miracle-sink.service", "miracle-watch.service"
        )),
        "airplay": active("uxplay.service"),
        "spotify": active("go-librespot.service"),
        "bluetooth": active("zyz-bluetooth.service"),
        "disc": active("zyz-disc.service"),
    }
    _SERVICE_CACHE["at"] = now
    _SERVICE_CACHE["data"] = data
    return data


def network_info():
    now = time.time()
    cached = _NET_CACHE["data"]
    if cached is not None and (now - _NET_CACHE["at"]) < 8:
        return cached

    iw = run_command("iw", "dev", NETWORK_IFACE, "link")
    ssid = None
    match = re.search(r"^\s*SSID:\s*(.+)$", iw, re.MULTILINE)
    if match:
        ssid = match.group(1).strip()

    ip_text = run_command("ip", "-4", "-o", "addr", "show", "dev", NETWORK_IFACE)
    ip = None
    match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/", ip_text)
    if match:
        ip = match.group(1)

    data = {
        "hostname": socket.gethostname(),
        "interface": NETWORK_IFACE,
        "ssid": ssid,
        "ip": ip,
    }
    _NET_CACHE["at"] = now
    _NET_CACHE["data"] = data
    return data


def fetch_bluetooth_status():
    path = Path("/run/zyzdisplay/bluetooth.json")
    try:
        if not path.is_file():
            return {"connected": False, "name": ""}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {"connected": False, "name": ""}
        name = str(payload.get("name") or "").strip()[:40]
        connected = bool(payload.get("connected")) and bool(name)
        return {"connected": connected, "name": name if connected else ""}
    except Exception:
        return {"connected": False, "name": ""}


def fetch_disc_status():
    path = Path("/run/zyzdisplay/nowplaying.json")
    try:
        if not path.is_file():
            return None
        age = time.time() - path.stat().st_mtime
        if age > 15:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not payload.get("track"):
            return None
        return payload
    except Exception:
        return None


def fetch_now_playing(timeout=0.8):
    disc = fetch_disc_status()
    if disc:
        return disc
    return fetch_spotify_status(timeout=timeout)


def fetch_spotify_status(timeout=0.8):
    now = time.time()
    if _SPOTIFY_CACHE["ok"] and (now - _SPOTIFY_CACHE["at"]) < 0.4:
        return _SPOTIFY_CACHE["data"]

    req = urllib.request.Request(
        SPOTIFY_STATUS_URL,
        headers={"Accept": "application/json", "User-Agent": f"ZyzDisplay/{APP_VERSION}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status == 204:
                payload = None
            else:
                payload = json.loads(res.read().decode("utf-8"))
        _SPOTIFY_CACHE["at"] = time.time()
        _SPOTIFY_CACHE["data"] = payload
        _SPOTIFY_CACHE["ok"] = True
        return payload
    except urllib.error.HTTPError as exc:
        if exc.code == 204:
            _SPOTIFY_CACHE["at"] = time.time()
            _SPOTIFY_CACHE["data"] = None
            _SPOTIFY_CACHE["ok"] = True
            return None
        raise
    except Exception:
        if _SPOTIFY_CACHE["ok"] and (now - _SPOTIFY_CACHE["at"]) < 5:
            return _SPOTIFY_CACHE["data"]
        raise


def wallhaven_queries():
    raw = (WALLHAVEN_QUERY or WALLHAVEN_DEFAULT_QUERIES).strip()
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return parts or [part.strip() for part in WALLHAVEN_DEFAULT_QUERIES.split(",")]


class WallpaperManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.items = []
        self.fetched_at = 0.0
        self.stop_event = threading.Event()
        self.cache_path = STATE_DIR / "wallhaven.json"
        self.fetching = set()
        self._load_cache()

    def _load_cache(self):
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            items = payload.get("items", [])
            fetched_at = float(payload.get("fetched_at", 0))
            cached_queries = payload.get("queries")
            cached_resolution = payload.get("resolution")
            if cached_queries != wallhaven_queries() or cached_resolution != WALLHAVEN_RESOLUTION:
                return
            if isinstance(items, list):
                self.items = [item for item in items if isinstance(item, dict) and item.get("url")]
                self.fetched_at = fetched_at
        except Exception:
            pass

    def _save_cache(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        temp = self.cache_path.with_suffix(".tmp")
        payload = {
            "fetched_at": self.fetched_at,
            "queries": wallhaven_queries(),
            "resolution": WALLHAVEN_RESOLUTION,
            "items": self.items,
        }
        temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.cache_path)

    def _build_url(self, query):
        params = {
            "sorting": "random",
            "categories": WALLHAVEN_CATEGORIES,
            "purity": WALLHAVEN_PURITY,
            "resolutions": WALLHAVEN_RESOLUTION,
            "ratios": WALLHAVEN_RATIOS,
        }
        if query:
            params["q"] = query
        return WALLHAVEN_API + "?" + urllib.parse.urlencode(params)

    def _fetch_query(self, query):
        req = urllib.request.Request(
            self._build_url(query),
            headers={
                "Accept": "application/json",
                "User-Agent": f"ZyzDisplay/{APP_VERSION} personal-display",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as res:
            payload = json.loads(res.read().decode("utf-8"))

        parsed = []
        for item in payload.get("data", []):
            if not isinstance(item, dict):
                continue
            url = item.get("path")
            page = item.get("url")
            if not url:
                continue
            parsed.append({
                "id": item.get("id"),
                "url": url,
                "page": page,
                "resolution": item.get("resolution"),
                "file_type": item.get("file_type"),
                "file_size": item.get("file_size") or 0,
                "category": item.get("category"),
                "purity": item.get("purity"),
                "query": query,
            })
        return parsed

    def refresh(self, force=False):
        if not WALLHAVEN_ENABLED:
            return False

        with self.lock:
            if not force and self.items and (time.time() - self.fetched_at) < WALLHAVEN_BATCH_REFRESH:
                return True

        seen = set()
        parsed = []
        try:
            for query in wallhaven_queries():
                try:
                    for item in self._fetch_query(query):
                        item_id = item.get("id") or item.get("url")
                        if item_id in seen or not self._is_wanted_resolution(item):
                            continue
                        seen.add(item_id)
                        parsed.append(item)
                except Exception as exc:
                    print(f"wallhaven query {query!r} failed: {exc}", flush=True)
                time.sleep(0.4)

            if not parsed:
                return False

            random.SystemRandom().shuffle(parsed)
            with self.lock:
                self.items = parsed
                self.fetched_at = time.time()
                self._save_cache()
            return True
        except Exception as exc:
            print(f"wallhaven refresh failed: {exc}", flush=True)
            return False

    def _wanted_resolution(self):
        return str(WALLHAVEN_RESOLUTION or "1920x1080").lower().replace(" ", "")

    def _parse_wh(self):
        try:
            width, height = self._wanted_resolution().split("x", 1)
            return int(width), int(height)
        except Exception:
            return 1920, 1080

    def _is_wanted_resolution(self, item):
        return str(item.get("resolution") or "").lower().replace(" ", "") == self._wanted_resolution()

    def _wallpaper_dir(self):
        path = STATE_DIR / "wallpapers"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _transcode_1080(self, src, dest):
        width, height = self._parse_wh()
        out_tmp = Path(str(dest) + ".enc")
        pipelines = (
            [
                "gst-launch-1.0", "-q",
                "filesrc", f"location={src}",
                "!", "jpegdec",
                "!", "videoconvert",
                "!", "videoscale", "method=1",
                "!", f"video/x-raw,width={width},height={height}",
                "!", "jpegenc", "quality=78",
                "!", "filesink", f"location={out_tmp}",
            ],
            [
                "gst-launch-1.0", "-q",
                "filesrc", f"location={src}",
                "!", "decodebin",
                "!", "videoconvert",
                "!", "videoscale", "method=1",
                "!", f"video/x-raw,width={width},height={height}",
                "!", "jpegenc", "quality=78",
                "!", "filesink", f"location={out_tmp}",
            ],
        )
        try:
            for cmd in pipelines:
                try:
                    result = subprocess.run(cmd, check=False, capture_output=True, timeout=90)
                except Exception as exc:
                    print(f"wallpaper transcode failed: {exc}", flush=True)
                    continue
                if result.returncode == 0 and out_tmp.is_file() and out_tmp.stat().st_size > 4096:
                    out_tmp.replace(dest)
                    return True
                err = (result.stderr or b"").decode("utf-8", errors="replace").strip()
                if err:
                    print(f"wallpaper transcode failed: {err}", flush=True)
            return False
        finally:
            try:
                out_tmp.unlink()
            except OSError:
                pass

    def _item_id(self, item):
        return str(item.get("id") or "current").replace("/", "_")

    def local_path(self, item):
        return self.path_for_id(self._item_id(item))

    def path_for_id(self, item_id):
        safe = str(item_id or "").replace("/", "_")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", safe):
            return None
        return self._wallpaper_dir() / f"{safe}.jpg"

    def public_url(self, item):
        return f"/wallpaper?id={urllib.parse.quote(self._item_id(item), safe='')}"

    def _ready_url(self, item):
        local = self.local_path(item)
        if local is not None and local.is_file() and local.stat().st_size > 4096:
            return self.public_url(item)
        return None

    def _queue_fetch(self, item):
        pending = dict(item)
        threading.Thread(target=self.ensure_local, args=(pending,), name="wallpaper-fetch", daemon=True).start()

    def ensure_local(self, item):
        dest = self.local_path(item)
        if dest is None:
            return None
        if dest.is_file() and dest.stat().st_size > 4096:
            return dest
        item_id = self._item_id(item)
        with self.lock:
            if item_id in self.fetching:
                return None
            self.fetching.add(item_id)
        url = item.get("url")
        if not url:
            with self.lock:
                self.fetching.discard(item_id)
            return None
        tmp = dest.with_suffix(".tmp")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"ZyzDisplay/{APP_VERSION} personal-display"},
            )
            with urllib.request.urlopen(req, timeout=20) as res:
                data = res.read()
            if len(data) < 4096:
                return None
            tmp.write_bytes(data)
            file_type = str(item.get("file_type") or "").lower()
            is_jpeg = file_type in ("jpg", "jpeg", "image/jpeg", "image/jpg") or data[:3] == b"\xff\xd8\xff"
            if self._is_wanted_resolution(item) and is_jpeg and tmp.stat().st_size <= 380_000:
                tmp.replace(dest)
            else:
                ok = self._transcode_1080(tmp, dest)
                try:
                    tmp.unlink()
                except OSError:
                    pass
                if not ok:
                    return None
            self._prune_wallpapers()
            return dest
        except Exception as exc:
            print(f"wallpaper download failed: {exc}", flush=True)
            try:
                tmp.unlink()
            except OSError:
                pass
            return None
        finally:
            with self.lock:
                self.fetching.discard(item_id)

    def _prune_wallpapers(self, keep=8):
        files = sorted(self._wallpaper_dir().glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        for stale in files[keep:]:
            try:
                stale.unlink()
            except OSError:
                pass

    def current(self):
        pending = []
        with self.lock:
            if not self.items:
                return None
            slot = int(time.time() // WALLHAVEN_INTERVAL)
            index = slot % len(self.items)
            next_index = (index + 1) % len(self.items)
            item = dict(self.items[index])
            nxt = dict(self.items[next_index])
            item["next_change_epoch"] = (slot + 1) * WALLHAVEN_INTERVAL
            item["local"] = self._ready_url(item)
            item["next_local"] = self._ready_url(nxt) if next_index != index else item["local"]
            if item["local"] is None:
                pending.append(item)
            if next_index != index and item["next_local"] is None:
                pending.append(nxt)
        for entry in pending:
            self._queue_fetch(entry)
        return item

    def cache_status(self):
        with self.lock:
            return {
                "enabled": WALLHAVEN_ENABLED,
                "count": len(self.items),
                "age_seconds": None if not self.fetched_at else int(time.time() - self.fetched_at),
                "interval_seconds": WALLHAVEN_INTERVAL,
                "queries": wallhaven_queries(),
                "resolution": WALLHAVEN_RESOLUTION,
            }

    def loop(self):
        while not self.stop_event.is_set():
            try:
                self.refresh(force=False)
            except Exception as exc:
                print(f"wallpaper loop error: {exc}", flush=True)
            self.stop_event.wait(60)

    def start(self):
        thread = threading.Thread(target=self.loop, name="wallhaven-refresh", daemon=True)
        thread.start()


WALLPAPERS = WallpaperManager()


def parse_sun_minutes(value):
    if not value:
        return None
    text = " ".join(str(value).strip().split())
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            parsed = time.strptime(text, fmt)
            return parsed.tm_hour * 60 + parsed.tm_min
        except ValueError:
            continue
    return None


def night_from_sun(sunrise, sunset):
    now = time.localtime()
    now_m = now.tm_hour * 60 + now.tm_min
    rise = parse_sun_minutes(sunrise)
    sett = parse_sun_minutes(sunset)
    if rise is None or sett is None:
        return now.tm_hour < 7 or now.tm_hour >= 20
    if rise <= sett:
        return now_m < rise or now_m >= sett
    return sett <= now_m < rise


def weather_icon(code, is_night=False):
    try:
        code = int(code)
    except (TypeError, ValueError):
        code = 0
    if code in (95, 96, 99):
        return "storm"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (45, 48):
        return "fog"
    if code == 3:
        return "cloud"
    if code in (1, 2):
        return "partly-night" if is_night else "partly"
    if code == 0 and is_night:
        return "moon"
    return "sun"


WEATHER_DESC = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}


def _as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _weather_code_for_precip(code, precip_mm):
    try:
        code = int(code)
    except (TypeError, ValueError):
        code = 0
    if code in RAIN_WEATHER_CODES or code in (71, 73, 75, 77, 85, 86, 95, 96, 99):
        return code
    if precip_mm >= 2:
        return 63
    if precip_mm >= 0.2:
        return 61
    if precip_mm > 0:
        return 51
    return code


def weather_desc(code):
    try:
        code = int(code)
    except (TypeError, ValueError):
        return ""
    return WEATHER_DESC.get(code, "Cloudy" if code else "Clear")


def _as_int(value, default=0):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _wind_compass(degrees):
    try:
        heading = float(degrees)
    except (TypeError, ValueError):
        return ""
    points = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
    return points[int((heading + 11.25) / 22.5) % 16]


def _hour_label(minutes):
    hours = max(0, int(minutes) // 60) % 24
    suffix = "AM" if hours < 12 else "PM"
    display = hours % 12
    if display == 0:
        display = 12
    return f"{display} {suffix}"


def _day_label(date_str, index):
    if index == 0:
        return "Today"
    if index == 1:
        return "Tomorrow"
    try:
        year, month, day = [int(part) for part in str(date_str).split("-")[:3]]
        return time.strftime("%a", datetime(year, month, day).timetuple())
    except Exception:
        return str(date_str or "")


def _parse_iso_local(value):
    text = str(value or "").strip().replace("Z", "")
    if "." in text:
        text = text.split(".", 1)[0]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _format_sun(value):
    parsed = _parse_iso_local(value)
    if parsed is None:
        return str(value or "").strip()
    return parsed.strftime("%-I:%M %p")


def _upcoming_hourly(hours):
    now = time.time()
    out = []
    for hour in hours or []:
        if float(hour.get("epoch") or 0) + 1800 < now:
            continue
        out.append({
            "label": hour.get("label") or "",
            "temp": hour.get("temp"),
            "icon": hour.get("icon") or "sun",
            "rain": hour.get("rain") or 0,
        })
        if len(out) >= 5:
            break
    return out


RAIN_WEATHER_CODES = {
    51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99,
}


def _rain_alert(hours, current_code):
    try:
        code = int(current_code)
    except (TypeError, ValueError):
        code = 0
    if code in RAIN_WEATHER_CODES:
        return None
    now = time.time()
    for hour in hours or []:
        epoch = float(hour.get("epoch") or 0)
        if epoch < now + 20 * 60:
            continue
        if epoch > now + 18 * 3600:
            break
        if (hour.get("rain") or 0) >= 50:
            return f"Rain {hour.get('label') or ''}".strip()
    return None


class WeatherManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.payload = None
        self.geo = None
        self.fetched_at = 0.0
        self.stop_event = threading.Event()
        self.cache_path = STATE_DIR / "weather.json"
        self._load_cache()

    def _load_cache(self):
        try:
            stored = json.loads(self.cache_path.read_text(encoding="utf-8"))
            payload = stored.get("payload")
            fetched_at = float(stored.get("fetched_at", 0))
            geo = stored.get("geo")
            if isinstance(payload, dict) and payload.get("source") in ("open-meteo-nbm", "open-meteo-gfs"):
                self.payload = payload
                self.fetched_at = fetched_at
            if isinstance(geo, dict) and geo.get("lat") is not None:
                self.geo = geo
        except Exception:
            pass

    def _save_cache(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        temp = self.cache_path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {"fetched_at": self.fetched_at, "payload": self.payload, "geo": self.geo},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        temp.replace(self.cache_path)

    def _pick_geo(self, results):
        needle = WEATHER_LOCATION.lower()
        parts = [part.strip().lower() for part in WEATHER_LOCATION.split(",") if part.strip()]
        for item in results:
            blob = " ".join([
                str(item.get("name") or ""),
                str(item.get("admin1") or ""),
                str(item.get("admin2") or ""),
                str(item.get("country") or ""),
                str(item.get("country_code") or ""),
            ]).lower()
            if all(part in blob for part in parts):
                return item
            if "florida" in needle and "florida" in blob:
                return item
        return results[0] if results else None

    def _geocode(self):
        if WEATHER_LAT and WEATHER_LON:
            return {
                "lat": float(WEATHER_LAT),
                "lon": float(WEATHER_LON),
                "name": WEATHER_LOCATION.split(",")[0].strip() or "Home",
                "region": (WEATHER_LOCATION.split(",")[1].strip() if "," in WEATHER_LOCATION else ""),
                "query": WEATHER_LOCATION,
            }
        with self.lock:
            cached = dict(self.geo) if self.geo else None
        if cached and cached.get("query") == WEATHER_LOCATION:
            return cached

        name = WEATHER_LOCATION.split(",")[0].strip() or WEATHER_LOCATION
        url = OPEN_METEO_GEOCODE + "?" + urllib.parse.urlencode({
            "name": name,
            "count": 10,
            "language": "en",
            "format": "json",
        })
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": f"ZyzDisplay/{APP_VERSION} (open-meteo kiosk)",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as res:
            data = json.loads(res.read().decode("utf-8"))
        item = self._pick_geo(data.get("results") or [])
        if not item:
            raise RuntimeError(f"no geocode result for {WEATHER_LOCATION!r}")
        geo = {
            "lat": float(item["latitude"]),
            "lon": float(item["longitude"]),
            "name": item.get("name") or name,
            "region": item.get("admin1") or "",
            "query": WEATHER_LOCATION,
        }
        with self.lock:
            self.geo = geo
        return geo

    def _open_meteo_json(self, url, timeout=12):
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": f"ZyzDisplay/{APP_VERSION} (open-meteo kiosk)",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))

    def _forecast_params(self, geo, models=None):
        units_f = WEATHER_UNITS != "m"
        params = {
            "latitude": f"{geo['lat']:.4f}",
            "longitude": f"{geo['lon']:.4f}",
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,is_day,precipitation,rain,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,weather_code,precipitation_probability,is_day,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max,uv_index_max",
            "temperature_unit": "fahrenheit" if units_f else "celsius",
            "wind_speed_unit": "mph" if units_f else "kmh",
            "timezone": "auto",
            "forecast_days": 3,
        }
        if models:
            params["models"] = models
        return params

    def _fetch_forecast(self, geo, models=None):
        url = OPEN_METEO_FORECAST + "?" + urllib.parse.urlencode(self._forecast_params(geo, models))
        return self._open_meteo_json(url)

    def _fetch_uv(self, geo):
        try:
            url = OPEN_METEO_FORECAST + "?" + urllib.parse.urlencode({
                "latitude": f"{geo['lat']:.4f}",
                "longitude": f"{geo['lon']:.4f}",
                "daily": "uv_index_max",
                "timezone": "auto",
                "forecast_days": 1,
            })
            data = self._open_meteo_json(url, timeout=10)
            values = (data.get("daily") or {}).get("uv_index_max") or []
            if not values or values[0] is None:
                return None
            uv = round(float(values[0]), 1)
            return int(uv) if uv == int(uv) else uv
        except Exception as exc:
            print(f"uv refresh failed: {exc}", flush=True)
            return None

    def _fetch_aqi(self, geo):
        try:
            url = OPEN_METEO_AIR + "?" + urllib.parse.urlencode({
                "latitude": f"{geo['lat']:.4f}",
                "longitude": f"{geo['lon']:.4f}",
                "current": "us_aqi",
                "timezone": "auto",
            })
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": f"ZyzDisplay/{APP_VERSION} (open-meteo kiosk)",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
            value = (data.get("current") or {}).get("us_aqi")
            if value is None:
                return None
            return _as_int(value)
        except Exception as exc:
            print(f"air quality refresh failed: {exc}", flush=True)
            return None

    def _parse(self, data, geo):
        units_f = WEATHER_UNITS != "m"
        current = data.get("current") or {}
        daily = data.get("daily") or {}
        hourly = data.get("hourly") or {}
        code = _weather_code_for_precip(
            current.get("weather_code"),
            max(_as_float(current.get("precipitation")), _as_float(current.get("rain"))),
        )
        is_day = current.get("is_day", 1)
        is_night = not bool(is_day)
        dates = daily.get("time") or []
        highs = daily.get("temperature_2m_max") or []
        lows = daily.get("temperature_2m_min") or []
        day_codes = daily.get("weather_code") or []
        day_rain = daily.get("precipitation_probability_max") or []
        sunrises = daily.get("sunrise") or []
        sunsets = daily.get("sunset") or []
        sunrise = _format_sun(sunrises[0] if sunrises else "")
        sunset = _format_sun(sunsets[0] if sunsets else "")
        uv_max = daily.get("uv_index_max") or []
        uv = None
        if uv_max:
            try:
                uv = round(float(uv_max[0]), 1)
                if uv == int(uv):
                    uv = int(uv)
            except (TypeError, ValueError):
                uv = None

        hours = []
        times = hourly.get("time") or []
        temps = hourly.get("temperature_2m") or []
        codes = hourly.get("weather_code") or []
        rains = hourly.get("precipitation_probability") or []
        amounts = hourly.get("precipitation") or []
        is_days = hourly.get("is_day") or []
        for index, stamp in enumerate(times):
            parsed = _parse_iso_local(stamp)
            if parsed is None:
                continue
            minutes = parsed.hour * 60 + parsed.minute
            night = not bool(is_days[index]) if index < len(is_days) else minutes < 7 * 60 or minutes >= 20 * 60
            hour_code = _weather_code_for_precip(
                codes[index] if index < len(codes) else 0,
                _as_float(amounts[index] if index < len(amounts) else 0),
            )
            hours.append({
                "epoch": parsed.timestamp(),
                "minute": minutes,
                "label": _hour_label(minutes),
                "temp": _as_int(temps[index] if index < len(temps) else 0),
                "rain": _as_int(rains[index] if index < len(rains) else 0),
                "icon": weather_icon(hour_code, night),
            })

        days = []
        for index, date_str in enumerate(dates[:3]):
            days.append({
                "date": date_str,
                "label": _day_label(date_str, index),
                "high": _as_int(highs[index] if index < len(highs) else 0),
                "low": _as_int(lows[index] if index < len(lows) else 0),
                "rain": _as_int(day_rain[index] if index < len(day_rain) else 0),
                "icon": weather_icon(day_codes[index] if index < len(day_codes) else 0, False),
            })

        return {
            "ok": True,
            "source": "open-meteo-nbm",
            "location": geo.get("name") or WEATHER_LOCATION.split(",")[0],
            "region": geo.get("region") or "",
            "units": "F" if units_f else "C",
            "temp": _as_int(current.get("temperature_2m")),
            "feels": _as_int(current.get("apparent_temperature")),
            "high": days[0]["high"] if days else _as_int(current.get("temperature_2m")),
            "low": days[0]["low"] if days else _as_int(current.get("temperature_2m")),
            "humidity": _as_int(current.get("relative_humidity_2m")),
            "wind": _as_int(current.get("wind_speed_10m")),
            "wind_dir": _wind_compass(current.get("wind_direction_10m")),
            "desc": weather_desc(code),
            "code": code,
            "sunrise": sunrise,
            "sunset": sunset,
            "is_night": is_night,
            "theme": "dark" if is_night else "light",
            "icon": weather_icon(code, is_night),
            "uv": uv,
            "aqi": None,
            "hours": hours,
            "days": days,
        }

    def refresh(self, force=False):
        if not WEATHER_ENABLED:
            return False
        with self.lock:
            if (
                not force
                and self.payload
                and self.payload.get("source") == "open-meteo-nbm"
                and self.payload.get("days")
                and self.payload.get("uv") is not None
                and self.payload.get("wind") is not None
                and (time.time() - self.fetched_at) < WEATHER_REFRESH
            ):
                return True

        try:
            geo = self._geocode()
            source = "open-meteo-nbm"
            try:
                raw = self._fetch_forecast(geo, models="ncep_nbm_conus")
            except Exception as exc:
                print(f"NBM forecast failed, falling back to GFS/HRRR: {exc}", flush=True)
                raw = self._fetch_forecast(geo)
                source = "open-meteo-gfs"
            parsed = self._parse(raw, geo)
            parsed["source"] = source
            if parsed.get("uv") is None:
                parsed["uv"] = self._fetch_uv(geo)
            parsed["aqi"] = self._fetch_aqi(geo)
            with self.lock:
                self.payload = parsed
                self.fetched_at = time.time()
                self._save_cache()
            return True
        except Exception as exc:
            print(f"weather refresh failed: {exc}", flush=True)
            return False

    def current(self):
        with self.lock:
            if not self.payload:
                return None
            item = dict(self.payload)
            is_night = night_from_sun(item.get("sunrise"), item.get("sunset"))
            item["is_night"] = is_night
            item["theme"] = "dark" if is_night else "light"
            item["icon"] = weather_icon(item.get("code"), is_night)
            item["hourly"] = _upcoming_hourly(item.get("hours") or [])
            item["alert"] = _rain_alert(item.get("hours") or [], item.get("code"))
            item.pop("hours", None)
            item["age_seconds"] = None if not self.fetched_at else int(time.time() - self.fetched_at)
            return item

    def loop(self):
        while not self.stop_event.is_set():
            try:
                self.refresh(force=False)
            except Exception as exc:
                print(f"weather loop error: {exc}", flush=True)
            self.stop_event.wait(60)

    def start(self):
        thread = threading.Thread(target=self.loop, name="weather-refresh", daemon=True)
        thread.start()


WEATHER = WeatherManager()


def calendar_urls():
    raw = (CALENDAR_ICS_URL or "").strip()
    if not raw:
        return []
    parts = [part.strip().strip('"').strip("'") for part in re.split(r"[,\s]+", raw) if part.strip()]
    return [part for part in parts if part.startswith("http://") or part.startswith("https://")]


def _local_tz():
    return datetime.now().astimezone().tzinfo


def _as_local_datetime(value):
    tzinfo = _local_tz()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tzinfo)
        return value.astimezone(tzinfo)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=tzinfo)
    return None


def _naive(value):
    if isinstance(value, datetime):
        local = _as_local_datetime(value)
        return local.replace(tzinfo=None, microsecond=0) if local else None
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return None


def _event_duration(start, end, all_day):
    if end is None:
        return timedelta(days=1) if all_day else timedelta(hours=1)
    delta = end - start
    if delta <= timedelta(0):
        return timedelta(days=1) if all_day else timedelta(hours=1)
    return delta


def _format_when(start, all_day, now, end=None):
    day = start.date()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    if all_day:
        still_today = end is None or end.date() > today
        if day <= today and still_today:
            return "All day"
        if day == tomorrow:
            return "Tomorrow"
        return start.strftime("%a")
    if end is not None and start <= now < end:
        return "Now"
    minutes = int((start - now).total_seconds() // 60)
    if 0 <= minutes < 90:
        if minutes < 1:
            return "Now"
        return f"in {minutes} min"
    if 90 <= minutes < 12 * 60 and day == today:
        hours = max(1, int(round(minutes / 60)))
        return f"in {hours} hr"
    clock = start.strftime("%-I:%M %p")
    if day == today:
        return clock
    if day == tomorrow:
        return f"Tomorrow · {clock}"
    return f"{start.strftime('%a')} · {clock}"


def _exdates(component):
    values = component.get("exdate")
    if values is None:
        items = []
    elif isinstance(values, list):
        items = values
    else:
        items = [values]
    seen = set()
    for item in items:
        dts = getattr(item, "dts", None) or []
        for stamp in dts:
            naive = _naive(getattr(stamp, "dt", None))
            if naive is not None:
                seen.add(naive)
    return seen


def _rrule_text(component, start):
    field = component.get("rrule")
    if field is None:
        return ""
    text = field.to_ical().decode("utf-8")
    match = re.search(r"UNTIL=(\d{8}(?:T\d{6})?)(Z)?", text)
    if not match or match.group(2) == "Z" or start.tzinfo is None:
        return text
    stamp = match.group(1)
    fmt = "%Y%m%dT%H%M%S" if "T" in stamp else "%Y%m%d"
    until = datetime.strptime(stamp, fmt).replace(tzinfo=start.tzinfo).astimezone(timezone.utc)
    return re.sub(r"UNTIL=\d{8}(?:T\d{6})?Z?", until.strftime("UNTIL=%Y%m%dT%H%M%SZ"), text, count=1)


def _expand_vevent(component, now, window_end):
    status = str(component.get("status") or "").upper()
    if status == "CANCELLED":
        return []
    dtstart_field = component.get("dtstart")
    if dtstart_field is None:
        return []
    raw_start = dtstart_field.dt
    all_day = isinstance(raw_start, date) and not isinstance(raw_start, datetime)
    start = _as_local_datetime(raw_start)
    if start is None:
        return []
    dtend_field = component.get("dtend")
    duration_field = component.get("duration")
    if dtend_field is not None:
        raw_end = dtend_field.dt
        if all_day and isinstance(raw_end, date) and not isinstance(raw_end, datetime):
            end = _as_local_datetime(raw_end)
        else:
            end = _as_local_datetime(raw_end)
    elif duration_field is not None:
        try:
            end = start + duration_field.dt
        except Exception:
            end = None
    else:
        end = None
    duration = _event_duration(start, end, all_day)
    title = str(component.get("summary") or "Busy").strip() or "Busy"
    rrule_field = component.get("rrule")
    if rrule_field is not None and rrulestr is not None:
        try:
            rule = rrulestr(_rrule_text(component, start), dtstart=start)
            skipped = _exdates(component)
            found = []
            for occ in rule.between(now - timedelta(days=1), window_end, inc=True):
                if occ.tzinfo is None:
                    local_start = occ.replace(tzinfo=start.tzinfo, microsecond=0)
                else:
                    local_start = occ.astimezone(start.tzinfo).replace(microsecond=0)
                if _naive(local_start) in skipped:
                    continue
                local_end = local_start + duration
                if local_end > now and local_start < window_end:
                    found.append((local_start, local_end, all_day, title))
            return found
        except Exception as exc:
            print(f"calendar rrule skipped: {exc}", flush=True)
    event_end = start + duration
    if event_end > now and start < window_end:
        return [(start, event_end, all_day, title)]
    return []


class CalendarManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.events = []
        self.fetched_at = 0.0
        self.stop_event = threading.Event()
        self.cache_path = STATE_DIR / "calendar.json"
        self._warned_libs = False
        self._load_cache()

    def _load_cache(self):
        try:
            stored = json.loads(self.cache_path.read_text(encoding="utf-8"))
            events = stored.get("events")
            fetched_at = float(stored.get("fetched_at", 0))
            if isinstance(events, list):
                self.events = [item for item in events if isinstance(item, dict)]
                self.fetched_at = fetched_at
        except Exception:
            pass

    def _save_cache(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        temp = self.cache_path.with_suffix(".tmp")
        temp.write_text(
            json.dumps({"fetched_at": self.fetched_at, "events": self.events}, ensure_ascii=False),
            encoding="utf-8",
        )
        temp.replace(self.cache_path)

    def _parse_ics(self, body, now, window_end):
        if not CALENDAR_LIBS:
            return []
        calendar = ICalendar.from_ical(body)
        found = []
        for component in calendar.walk("VEVENT"):
            found.extend(_expand_vevent(component, now, window_end))
        return found

    def _fetch_url(self, url):
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "text/calendar, text/plain, */*",
                "User-Agent": f"ZyzDisplay/{APP_VERSION} calendar",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.read()

    def refresh(self, force=False):
        urls = calendar_urls()
        if not urls:
            with self.lock:
                self.events = []
                self.fetched_at = time.time()
            return False
        if not CALENDAR_LIBS:
            if not self._warned_libs:
                print("calendar disabled: python3-icalendar and python3-dateutil are required", flush=True)
                self._warned_libs = True
            return False
        with self.lock:
            if not force and self.fetched_at and (time.time() - self.fetched_at) < CALENDAR_REFRESH:
                return True

        now = datetime.now().astimezone()
        window_end = now + timedelta(days=CALENDAR_WINDOW_DAYS)
        merged = []
        ok = False
        for index, url in enumerate(urls):
            try:
                body = self._fetch_url(url)
                merged.extend(self._parse_ics(body, now, window_end))
                ok = True
            except Exception as exc:
                print(f"calendar feed {index + 1} failed: {exc}", flush=True)
        if not ok:
            return False

        merged.sort(key=lambda item: item[0])
        seen = set()
        events = []
        for start, end, all_day, title in merged:
            key = (start.isoformat(), title)
            if key in seen:
                continue
            seen.add(key)
            events.append({
                "title": title[:120],
                "start": start.isoformat(),
                "end": end.isoformat(),
                "all_day": all_day,
                "when": _format_when(start, all_day, now, end),
            })
            if len(events) >= CALENDAR_LIMIT:
                break
        with self.lock:
            self.events = events
            self.fetched_at = time.time()
            self._save_cache()
        return True

    def current(self):
        now = datetime.now().astimezone()
        with self.lock:
            live = []
            for item in self.events:
                try:
                    end = datetime.fromisoformat(item.get("end") or "")
                    start = datetime.fromisoformat(item.get("start") or "")
                except (TypeError, ValueError):
                    continue
                if end.tzinfo is None:
                    end = end.replace(tzinfo=now.tzinfo)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=now.tzinfo)
                if end <= now:
                    continue
                live.append({
                    "title": item.get("title") or "Busy",
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "all_day": bool(item.get("all_day")),
                    "when": _format_when(start, bool(item.get("all_day")), now, end),
                })
                if len(live) >= CALENDAR_LIMIT:
                    break
            return {
                "ok": bool(calendar_urls()) and CALENDAR_LIBS,
                "events": live,
            }

    def status(self):
        with self.lock:
            return {
                "enabled": bool(calendar_urls()),
                "libs": CALENDAR_LIBS,
                "feeds": len(calendar_urls()),
                "event_count": len(self.events),
                "age_seconds": None if not self.fetched_at else int(time.time() - self.fetched_at),
            }

    def loop(self):
        while not self.stop_event.is_set():
            try:
                self.refresh(force=False)
            except Exception as exc:
                print(f"calendar loop error: {exc}", flush=True)
            self.stop_event.wait(60)

    def start(self):
        thread = threading.Thread(target=self.loop, name="calendar-refresh", daemon=True)
        thread.start()


CALENDAR = CalendarManager()


ALERT_SKIP = (
    "advisory",
    "statement",
    "outlook",
    "marine",
    "beach",
    "coastal",
    "rip current",
    "air quality",
    "frost",
    "freeze",
    "fog",
    "wind chill",
    "lake wind",
)

ALERT_URGENT = (
    "tornado warning",
    "extreme wind warning",
    "hurricane warning",
    "tsunami warning",
    "storm surge warning",
    "flash flood warning",
)


def _alert_keep(event, severity):
    text = (event or "").lower()
    if any(skip in text for skip in ALERT_SKIP):
        return False
    if "warning" in text or "watch" in text:
        return True
    return severity in ("Extreme", "Severe")


def _alert_rank(item):
    event = item.get("event", "").lower()
    if any(name in event for name in ALERT_URGENT):
        return 0
    if "warning" in event:
        return 1
    if "tornado watch" in event:
        return 2
    if "watch" in event:
        return 3
    if item.get("severity") == "Extreme":
        return 1
    return 4


def _alert_until(props):
    for key in ("ends", "expires"):
        raw = props.get(key)
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone()
        except Exception:
            continue
        return parsed.strftime("%-I:%M %p")
    return ""


def _alert_detail(event, until, instruction, headline):
    text = (event or "").lower()
    if "tornado warning" in text:
        line = "Take shelter now"
    elif instruction:
        line = str(instruction).split(".")[0].strip()
        if len(line) > 90:
            line = line[:87].rsplit(" ", 1)[0] + "…"
    elif headline:
        line = str(headline).split(" issued ")[0].strip()
    else:
        line = ""
    if until:
        line = f"{line} · until {until}" if line else f"Until {until}"
    return line


class AlertManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.alerts = []
        self.fetched_at = 0.0
        self.stop_event = threading.Event()

    def _fetch(self, geo):
        url = NWS_ALERTS + "?" + urllib.parse.urlencode({
            "status": "actual",
            "message_type": "alert,update",
            "point": f"{geo['lat']:.4f},{geo['lon']:.4f}",
        })
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/geo+json",
                "User-Agent": NWS_USER_AGENT,
            },
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
        items = []
        for feature in data.get("features") or []:
            props = feature.get("properties") or {}
            event = str(props.get("event") or "").strip()
            severity = str(props.get("severity") or "")
            if not event or not _alert_keep(event, severity):
                continue
            until = _alert_until(props)
            level = "warning" if "warning" in event.lower() or severity == "Extreme" else "watch"
            urgent = any(name in event.lower() for name in ALERT_URGENT)
            items.append({
                "event": event,
                "severity": severity,
                "level": level,
                "urgent": urgent,
                "until": until,
                "detail": _alert_detail(event, until, props.get("instruction"), props.get("headline")),
            })
        items.sort(key=_alert_rank)
        return items[:3]

    def refresh(self, force=False):
        with self.lock:
            if not force and self.fetched_at and (time.time() - self.fetched_at) < 30:
                return True
        try:
            geo = WEATHER._geocode()
            items = self._fetch(geo)
            with self.lock:
                self.alerts = items
                self.fetched_at = time.time()
            return True
        except Exception as exc:
            print(f"weather alert refresh failed: {exc}", flush=True)
            return False

    def current(self):
        with self.lock:
            items = list(self.alerts)
            age = None if not self.fetched_at else int(time.time() - self.fetched_at)
        primary = items[0] if items else None
        return {
            "primary": primary,
            "count": len(items),
            "age_seconds": age,
        }

    def loop(self):
        while not self.stop_event.is_set():
            try:
                self.refresh(force=False)
            except Exception as exc:
                print(f"weather alert loop error: {exc}", flush=True)
            self.stop_event.wait(30)

    def start(self):
        thread = threading.Thread(target=self.loop, name="weather-alerts", daemon=True)
        thread.start()


ALERTS = AlertManager()


_NTFY_SKIP_TAGS = {
    "go-rocks",
    "jack_o_lantern",
    "mouse",
    "de-server-1",
    "phils-automation",
}
_NTFY_SKIP_SNIPPETS = (
    "what do you use it for",
    "titles are optional",
    "it's interesting to hear what people use ntfy",
)
_NTFY_BIDI = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]")


def _ntfy_clean(text):
    return _NTFY_BIDI.sub("", str(text or "")).strip()


def _ntfy_noise(app, title, body, tags):
    blob = f"{app} {title} {body}".lower()
    if any(snippet in blob for snippet in _NTFY_SKIP_SNIPPETS):
        return True
    return any(str(tag).lower() in _NTFY_SKIP_TAGS for tag in tags)


def _ntfy_tags(raw):
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    if isinstance(raw, list):
        return [str(part).strip() for part in raw if str(part).strip()]
    return []


def _ntfy_app(tags, title):
    for tag in tags:
        name = NTFY_APP_NAMES.get(tag.lower())
        if name:
            return name
        if tag.startswith("com.") or tag.startswith("org."):
            return tag.rsplit(".", 1)[-1].replace("_", " ").title()
    if ": " in (title or ""):
        return title.split(": ", 1)[0].strip()
    return ""


def _ntfy_title_body(title, message, app):
    title = str(title or "").strip()
    message = str(message or "").strip()
    if app and title.lower().startswith(app.lower() + ": "):
        title = title[len(app) + 2:].strip()
    prefix = "/".join(part for part in (app, title) if part)
    if prefix and message.lower().startswith(prefix.lower() + "/"):
        message = message[len(prefix) + 1:].strip()
    elif app and message.lower().startswith(app.lower() + "/"):
        rest = message[len(app) + 1:]
        if title and rest.lower().startswith(title.lower() + "/"):
            message = rest[len(title) + 1:].strip()
    if message.lower() == title.lower():
        message = ""
    return title[:120], message[:140]


def _ntfy_known_app(name):
    text = (name or "").strip().lower()
    if not text:
        return ""
    if text in {value.lower() for value in NTFY_APP_NAMES.values()}:
        return name.strip()
    aliases = {
        "google messages": "Messages",
        "messages": "Messages",
        "phone": "Phone",
        "call": "Phone",
        "facebook messenger": "Messenger",
    }
    return aliases.get(text, "")


def _ntfy_parse_json(message):
    raw = str(message or "").strip()
    if not raw.startswith("{"):
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if not (payload.get("v") or payload.get("pkg") or payload.get("package")):
        return None
    pkg = str(payload.get("pkg") or payload.get("package") or "").strip()
    app = str(payload.get("app") or "").strip() or _ntfy_app([pkg], "")
    heading = str(payload.get("title") or "").strip()
    body = str(payload.get("text") or payload.get("body") or payload.get("message") or "").strip()
    kind = str(payload.get("kind") or "message").strip() or "message"
    if not app:
        app = "Notification"
    if not heading:
        heading, body = (body or "Notification"), ""
    if body.lower() == heading.lower():
        body = ""
    return app[:40], heading[:120], body[:140], pkg, kind


def _ntfy_parse(title, message, tags):
    parsed = _ntfy_parse_json(message)
    if parsed:
        return parsed
    title = str(title or "").strip()
    message = str(message or "").strip()
    app = _ntfy_app(tags, title)
    lines = [line.strip() for line in message.replace("\r\n", "\n").split("\n") if line.strip()]
    if not title and lines:
        guessed = _ntfy_known_app(lines[0]) or (lines[0] if len(lines[0]) <= 24 and ":" not in lines[0] else "")
        if not app and guessed:
            app = guessed
            title = lines[1] if len(lines) > 1 else ""
            body = "\n".join(lines[2:])
        else:
            title = lines[0]
            body = "\n".join(lines[1:])
    else:
        title, body = _ntfy_title_body(title, message, app)
    if not app:
        app = "Notification"
    if not title:
        title, body = (body or "Notification"), ""
    if body.lower() == title.lower():
        body = ""
    pkg = next((tag for tag in tags if "." in tag), "")
    kind = "missed" if "missed" in f"{title} {body}".lower() or (app or "").lower() == "phone" else "message"
    return app[:40], title[:120], body[:140], pkg, kind


def _ntfy_when(ts, now=None):
    now = time.time() if now is None else now
    try:
        age = max(0, int(now - float(ts)))
    except (TypeError, ValueError):
        return ""
    if age < 45:
        return "now"
    minutes = age // 60
    if minutes < 90:
        return f"{minutes} min"
    hours = max(1, int(round(minutes / 60)))
    if hours < 24:
        return f"{hours} hr"
    try:
        return datetime.fromtimestamp(float(ts)).astimezone().strftime("%a")
    except (OSError, OverflowError, ValueError):
        return ""


class NtfyManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.items = []
        self.since = NTFY_SINCE
        self.connected = False
        self.error = ""
        self.stop_event = threading.Event()
        self._warned_auth = False

    def configured(self):
        return bool(NTFY_ENABLED and NTFY_URL and NTFY_TOPIC and (NTFY_TOKEN or (NTFY_USER and NTFY_PASSWORD)))

    def _headers(self):
        headers = {
            "Accept": "application/x-ndjson, application/json",
            "User-Agent": f"ZyzDisplay/{APP_VERSION}",
        }
        if NTFY_TOKEN:
            headers["Authorization"] = f"Bearer {NTFY_TOKEN}"
        elif NTFY_USER and NTFY_PASSWORD:
            token = base64.b64encode(f"{NTFY_USER}:{NTFY_PASSWORD}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    def _url(self):
        path = f"{NTFY_URL}/{urllib.parse.quote(NTFY_TOPIC, safe='')}/json"
        params = {"since": self.since or NTFY_SINCE}
        return path + "?" + urllib.parse.urlencode(params)

    def _ingest(self, data):
        if (data.get("event") or "message") != "message":
            return
        msg_id = str(data.get("id") or "").strip()
        title = str(data.get("title") or "").strip()
        message = str(data.get("message") or "").strip()
        if not msg_id or (not title and not message):
            return
        tags = _ntfy_tags(data.get("tags"))
        app, title, body, pkg, kind = _ntfy_parse(title, message, tags)
        app = _ntfy_clean(app)
        title = _ntfy_clean(title)
        body = _ntfy_clean(body)
        if _ntfy_noise(app, title, body, tags):
            return
        try:
            ts = int(data.get("time") or time.time())
        except (TypeError, ValueError):
            ts = int(time.time())
        item = {
            "id": msg_id,
            "app": app or "Notification",
            "title": title or body or "Notification",
            "body": body if body != title else "",
            "pkg": pkg,
            "time": ts,
            "kind": kind if kind in ("missed", "message") else "message",
        }
        fingerprint = (item["app"], item["title"], item["body"])
        with self.lock:
            self.items = [
                old for old in self.items
                if old.get("id") != msg_id and (
                    old.get("time", 0) < ts - 120
                    or (old.get("app"), old.get("title"), old.get("body")) != fingerprint
                )
            ]
            self.items.insert(0, item)
            cutoff = time.time() - NTFY_MAX_AGE
            self.items = [old for old in self.items if old.get("time", 0) >= cutoff][:12]
            self.since = msg_id
            self.connected = True
            self.error = ""

    def _stream(self):
        req = urllib.request.Request(self._url(), headers=self._headers())
        with urllib.request.urlopen(req, timeout=120) as res:
            self.connected = True
            self.error = ""
            while not self.stop_event.is_set():
                raw = res.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event = data.get("event")
                if event in ("open", "keepalive"):
                    if data.get("id"):
                        self.since = str(data.get("id"))
                    continue
                self._ingest(data)

    def loop(self):
        delay = 2
        while not self.stop_event.is_set():
            if not NTFY_ENABLED or not NTFY_URL or not NTFY_TOPIC:
                self.stop_event.wait(30)
                continue
            if not NTFY_TOKEN and not (NTFY_USER and NTFY_PASSWORD):
                if not self._warned_auth:
                    print("ntfy token missing; set NTFY_TOKEN in /etc/zyzdisplay/zyzdisplay.env", flush=True)
                    self._warned_auth = True
                with self.lock:
                    self.error = "token missing"
                    self.connected = False
                self.stop_event.wait(30)
                continue
            try:
                self._stream()
                delay = 2
            except urllib.error.HTTPError as exc:
                self.connected = False
                self.error = f"HTTP {exc.code}"
                print(f"ntfy subscribe failed: HTTP {exc.code}", flush=True)
                delay = 60 if exc.code in (401, 403) else min(60, delay * 2)
            except Exception as exc:
                self.connected = False
                self.error = str(exc)
                print(f"ntfy subscribe error: {exc}", flush=True)
                delay = min(60, delay * 2)
            self.stop_event.wait(delay)

    def current(self):
        now = time.time()
        cutoff = now - NTFY_MAX_AGE
        with self.lock:
            items = []
            for item in self.items:
                if item.get("time", 0) < cutoff:
                    continue
                items.append({
                    "id": item.get("id"),
                    "app": item.get("app") or "Notification",
                    "title": item.get("title") or "Notification",
                    "body": item.get("body") or "",
                    "when": _ntfy_when(item.get("time"), now),
                    "kind": item.get("kind") or "message",
                })
                if len(items) >= NTFY_LIMIT:
                    break
            return {
                "ok": self.configured(),
                "connected": self.connected,
                "items": items,
            }

    def status(self):
        with self.lock:
            return {
                "enabled": bool(NTFY_ENABLED and NTFY_URL and NTFY_TOPIC),
                "configured": self.configured(),
                "connected": self.connected,
                "count": len(self.items),
                "error": self.error,
            }

    def start(self):
        thread = threading.Thread(target=self.loop, name="ntfy", daemon=True)
        thread.start()


NTFY = NtfyManager()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    server_version = f"ZyzDisplay/{APP_VERSION}"

    def log_message(self, fmt, *args):
        return

    def send_bytes(self, body, content_type, status=200, cache="no-store"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_bytes(body, "application/json; charset=utf-8", status=status, cache="no-store")

    def send_empty(self, status=204):
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def serve_static(self, name, content_type, cache):
        path = (WEB_ROOT / name).resolve()
        try:
            path.relative_to(WEB_ROOT)
        except ValueError:
            self.send_empty(404)
            return
        if not path.is_file():
            self.send_empty(404)
            return
        try:
            st = path.stat()
            key = (str(path), st.st_mtime_ns, st.st_size)
            cached = _STATIC_CACHE.get(name)
            if cached and cached[0] == key:
                body = cached[1]
            else:
                body = path.read_bytes()
                _STATIC_CACHE[name] = (key, body)
        except OSError:
            self.send_empty(500)
            return
        self.send_bytes(body, content_type, cache=cache)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path in ("/", "/index.html"):
            self.serve_static("index.html", "text/html; charset=utf-8", "no-cache")
            return
        if path == "/dashboard.css":
            self.serve_static("dashboard.css", "text/css; charset=utf-8", "no-cache")
            return
        if path == "/dashboard.js":
            self.serve_static("dashboard.js", "application/javascript; charset=utf-8", "no-cache")
            return
        if path.startswith("/assets/") and path.endswith(".svg"):
            self.serve_static(path.lstrip("/"), "image/svg+xml", "public, max-age=86400")
            return
        if path == "/wallpaper":
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            item_id = (query.get("id") or [None])[0]
            if item_id:
                local = WALLPAPERS.path_for_id(item_id)
            else:
                item = WALLPAPERS.current()
                local = WALLPAPERS.local_path(item) if item else None
            if local is None or not local.is_file() or local.stat().st_size < 4096:
                self.send_empty(204)
                return
            try:
                body = local.read_bytes()
            except OSError:
                self.send_empty(500)
                return
            self.send_bytes(body, "image/jpeg", cache="public, max-age=86400")
            return

        if path == "/api/snapshot":
            self.send_json({
                "network": network_info(),
                "services": receiver_status(),
                "weather": WEATHER.current(),
                "calendar": CALENDAR.current(),
                "alerts": ALERTS.current(),
                "ntfy": NTFY.current(),
                "bluetooth": fetch_bluetooth_status(),
                "background": WALLPAPERS.current(),
            })
            return

        if path == "/api/system":
            self.send_json(network_info())
            return

        if path == "/api/weather":
            item = WEATHER.current()
            if item is None:
                self.send_empty(204)
            else:
                self.send_json(item)
            return

        if path == "/api/background":
            item = WALLPAPERS.current()
            if item is None:
                self.send_empty(204)
            else:
                self.send_json(item)
            return

        if path == "/disc-cover":
            cover = Path("/run/zyzdisplay/cover.jpg")
            try:
                body = cover.read_bytes()
            except OSError:
                self.send_empty(404)
                return
            self.send_bytes(body, "image/jpeg", cache="no-cache")
            return

        if path == "/api/spotify":
            try:
                payload = fetch_now_playing()
                if payload is None:
                    self.send_empty(204)
                else:
                    self.send_json(payload)
            except Exception:
                self.send_empty(204)
            return

        if path == "/api/health":
            try:
                spotify = fetch_spotify_status(timeout=0.75) is not None
            except Exception:
                spotify = False
            self.send_json({
                "ok": True,
                "version": APP_VERSION,
                "network": network_info(),
                "spotify_active": spotify,
                "wallhaven": WALLPAPERS.cache_status(),
                "weather": WEATHER.current(),
                "calendar": CALENDAR.status(),
                "ntfy": NTFY.status(),
            })
            return

        self.send_empty(404)


def main():
    bind = os.environ.get("ZYZ_BIND", "127.0.0.1")
    port = int(os.environ.get("ZYZ_PORT", "8080"))
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    WALLPAPERS.start()
    WEATHER.start()
    CALENDAR.start()
    ALERTS.start()
    NTFY.start()
    server = Server((bind, port), Handler)
    print(f"ZyzDisplay {APP_VERSION} listening on http://{bind}:{port}", flush=True)
    try:
        server.serve_forever(poll_interval=1.0)
    except KeyboardInterrupt:
        pass
    finally:
        WALLPAPERS.stop_event.set()
        WEATHER.stop_event.set()
        CALENDAR.stop_event.set()
        ALERTS.stop_event.set()
        NTFY.stop_event.set()
        server.server_close()


if __name__ == "__main__":
    main()
