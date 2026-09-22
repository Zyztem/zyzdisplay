#!/bin/bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run with: sudo ./install.sh" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZYZ_USER="${ZYZ_USER:-${SUDO_USER:-zyztem}}"
ZYZ_HOME="$(getent passwd "$ZYZ_USER" | cut -d: -f6)"

if [[ -z "$ZYZ_HOME" || ! -d "$ZYZ_HOME" ]]; then
    echo "Cannot resolve home directory for user: $ZYZ_USER" >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
    apt-get install -y \
    cog curl iw network-manager alsa-utils libdrm-tests v4l-utils \
    python3 python3-yaml python3-evdev \
    python3-icalendar python3-dateutil \
    gstreamer1.0-tools gstreamer1.0-alsa \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav \
    avahi-daemon uxplay bluez bluez-alsa-utils bluez-tools \
    mpv cd-discid libcdio-utils libdvdnav4 libdvdread8

for cmd in miracle-wifid miracle-sinkctl go-librespot cog gst-launch-1.0 uxplay; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $cmd" >&2
        exit 1
    fi
done

# Raspberry Pi 5 (BCM2712) dropped the bcm2835-codec V4L2 M2M block that
# provides hardware H.264 decode/convert on Pi 3/4; it only has hardware HEVC
# decode (rpi-hevc-dec), which Miracast/AirPlay do not use. Detect what is
# actually present instead of assuming hardware decode is available.
HAVE_HW_H264=0
if v4l2-ctl --list-devices 2>/dev/null | grep -qi 'bcm2835-codec'; then
    HAVE_HW_H264=1
fi
if [[ "$HAVE_HW_H264" -eq 1 ]]; then
    H264_DECODER=v4l2h264dec
    H264_CONVERTER=v4l2convert
else
    H264_DECODER=avdec_h264
    H264_CONVERTER=videoconvert
    echo "No bcm2835-codec V4L2 decoder found (expected on Raspberry Pi 5); using software H.264 decode (avdec_h264)."
fi
if ! gst-inspect-1.0 "$H264_DECODER" >/dev/null 2>&1; then
    echo "ERROR: GStreamer element $H264_DECODER is unavailable." >&2
    exit 1
fi

MIRACLE_WIFID="$(command -v miracle-wifid)"
MIRACLE_SINKCTL="$(command -v miracle-sinkctl)"
GO_LIBRESPOT="$(command -v go-librespot)"

install -d -m 0755 /opt/zyzdisplay/web /opt/zyzdisplay/web/assets/weather /opt/zyzdisplay/backend
install -m 0644 "$SCRIPT_DIR/web/index.html" "$SCRIPT_DIR/web/dashboard.css" "$SCRIPT_DIR/web/dashboard.js" /opt/zyzdisplay/web/
install -m 0644 "$SCRIPT_DIR"/web/assets/weather/* /opt/zyzdisplay/web/assets/weather/
install -m 0755 "$SCRIPT_DIR/backend/zyzdisplay_server.py" /opt/zyzdisplay/backend/
install -d -m 0755 /usr/local/libexec
install -m 0755 "$SCRIPT_DIR/bin/zyz-kiosk" /usr/local/libexec/zyz-kiosk
install -m 0755 "$SCRIPT_DIR/bin/zyz-miracle-wifid" /usr/local/libexec/zyz-miracle-wifid
install -m 0755 "$SCRIPT_DIR/bin/zyz-miracle-sink" /usr/local/libexec/zyz-miracle-sink
install -m 0755 "$SCRIPT_DIR/bin/zyz-miracast-controller" /usr/local/libexec/zyz-miracast-controller
install -m 0755 "$SCRIPT_DIR/bin/zyz-miracle-player" /usr/local/libexec/zyz-miracle-player
install -m 0755 "$SCRIPT_DIR/bin/zyz-display-take" /usr/local/libexec/zyz-display-take
install -m 0755 "$SCRIPT_DIR/bin/zyz-miracle-watch" /usr/local/libexec/zyz-miracle-watch
install -m 0755 "$SCRIPT_DIR/bin/zyz-uxplay" /usr/local/libexec/zyz-uxplay
install -m 0755 "$SCRIPT_DIR/bin/zyz-bluetooth" /usr/local/libexec/zyz-bluetooth
install -m 0755 "$SCRIPT_DIR/bin/zyz-disc" /usr/local/libexec/zyz-disc
install -m 0755 "$SCRIPT_DIR/bin/zyz-kiosk-escape" /usr/local/libexec/zyz-kiosk-escape
install -m 0755 "$SCRIPT_DIR/bin/zyz-health" /usr/local/bin/zyz-health

usermod -aG video,render,audio "$ZYZ_USER" >/dev/null 2>&1 || true

install -d -m 0755 /etc/zyzdisplay
install -m 0644 "$SCRIPT_DIR/config/uxplayrc" /etc/zyzdisplay/uxplayrc
ENV_FILE=/etc/zyzdisplay/zyzdisplay.env

existing_env_value() {
    local key="$1"
    [[ -f "$ENV_FILE" ]] || return 0
    awk -v k="$key" 'index($0, k "=") == 1 {sub("^" k "=", ""); print}' "$ENV_FILE" | tail -n1
}

wifi_interfaces() {
    iw dev 2>/dev/null | awk '$1 == "Interface" {print $2}'
}

is_usb_wifi() {
    local iface="$1" device_path
    device_path="$(readlink -f "/sys/class/net/${iface}/device" 2>/dev/null || true)"
    [[ "$device_path" == */usb* ]]
}

if [[ -z "${NETWORK_IFACE:-}" ]]; then
    NETWORK_IFACE="$(existing_env_value NETWORK_IFACE)"
fi
if [[ -z "${MIRACAST_IFACE:-}" ]]; then
    MIRACAST_IFACE="$(existing_env_value MIRACAST_IFACE)"
fi

mapfile -t WIFI_IFACES < <(wifi_interfaces)
if [[ -z "${NETWORK_IFACE:-}" ]]; then
    for iface in "${WIFI_IFACES[@]}"; do
        if is_usb_wifi "$iface"; then
            NETWORK_IFACE="$iface"
            break
        fi
    done
fi
if [[ -z "${NETWORK_IFACE:-}" && -d /sys/class/net/wlan1 ]]; then
    NETWORK_IFACE=wlan1
fi
if [[ -z "${MIRACAST_IFACE:-}" && -d /sys/class/net/wlan0 ]]; then
    MIRACAST_IFACE=wlan0
fi
if [[ -z "${MIRACAST_IFACE:-}" ]]; then
    for iface in "${WIFI_IFACES[@]}"; do
        if [[ "$iface" != "$NETWORK_IFACE" ]] && ! is_usb_wifi "$iface"; then
            MIRACAST_IFACE="$iface"
            break
        fi
    done
fi
if [[ -z "${NETWORK_IFACE:-}" || -z "${MIRACAST_IFACE:-}" || "$NETWORK_IFACE" == "$MIRACAST_IFACE" ]]; then
    echo "ERROR: could not identify separate USB network and onboard MiracleCast Wi-Fi interfaces." >&2
    echo "       Set NETWORK_IFACE and MIRACAST_IFACE explicitly and rerun." >&2
    exit 1
fi
if [[ ! -d "/sys/class/net/${NETWORK_IFACE}" || ! -d "/sys/class/net/${MIRACAST_IFACE}" ]]; then
    echo "ERROR: Wi-Fi interface is not present: network=${NETWORK_IFACE}, miracast=${MIRACAST_IFACE}" >&2
    exit 1
fi

DRM_MODE="${DRM_MODE:-1920x1080@30}"

DRM_CONNECTOR_ID="${DRM_CONNECTOR_ID:-}"
DRM_CONNECTOR_NAME=""
if [[ -z "$DRM_CONNECTOR_ID" ]]; then
    read -r DRM_CONNECTOR_ID DRM_CONNECTOR_NAME < <(modetest -c 2>/dev/null | awk '$3 == "connected" && $4 ~ /^HDMI-A/ {print $1, $4; exit}') || true
fi
DRM_CONNECTOR_ID="${DRM_CONNECTOR_ID:-35}"

# Raspberry Pi 5 has two HDMI ports (HDMI-A-1 / HDMI-A-2), each with its own
# ALSA card (vc4-hdmi-0 / vc4-hdmi-1). HDMI audio only comes out of the port
# actually driving the display, so match the ALSA card to the connector
# picked above instead of just grabbing the first HDMI card found.
AUDIO_DEVICE="${AUDIO_DEVICE:-}"
if [[ -z "$AUDIO_DEVICE" ]]; then
    AUDIO_PAIR=""
    if [[ "$DRM_CONNECTOR_NAME" =~ ^HDMI-A-([0-9]+)$ ]]; then
        HDMI_PORT_INDEX=$(( BASH_REMATCH[1] - 1 ))
        AUDIO_PAIR="$(aplay -l 2>/dev/null | sed -nE "/^card [0-9]+:.*vc4-?hdmi-?${HDMI_PORT_INDEX}\\b/ s/^card ([0-9]+):.*device ([0-9]+):.*/\\1,\\2/p" | head -n1)"
    fi
    if [[ -z "$AUDIO_PAIR" ]]; then
        AUDIO_PAIR="$(aplay -l 2>/dev/null | sed -nE '/^card [0-9]+:.*(HDMI|vc4hdmi|vc4-hdmi)/ s/^card ([0-9]+):.*device ([0-9]+):.*/\1,\2/p' | head -n1)"
    fi
    AUDIO_DEVICE="plughw:${AUDIO_PAIR:-1,0}"
fi

env_value() {
    local key="$1"
    [[ -f "$ENV_FILE" ]] || return 0
    awk -v k="$key" '
        index($0, k "=") == 1 {
            sub("^" k "=", "")
            print
        }
    ' "$ENV_FILE" | tail -n1
}

EXISTING_CALENDAR_ICS_URL=""
EXISTING_NTFY_ENABLED=""
EXISTING_NTFY_URL=""
EXISTING_NTFY_TOPIC=""
EXISTING_NTFY_TOKEN=""
if [[ -f "$ENV_FILE" ]]; then
    cp -a "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    EXISTING_CALENDAR_ICS_URL="$(env_value CALENDAR_ICS_URL)"
    EXISTING_NTFY_ENABLED="$(env_value NTFY_ENABLED)"
    EXISTING_NTFY_URL="$(env_value NTFY_URL)"
    EXISTING_NTFY_TOPIC="$(env_value NTFY_TOPIC)"
    EXISTING_NTFY_TOKEN="$(env_value NTFY_TOKEN)"
fi
NTFY_ENABLED_VALUE="${EXISTING_NTFY_ENABLED:-1}"
NTFY_URL_VALUE="${EXISTING_NTFY_URL:-https://ntfy.mniz.dev}"
NTFY_TOPIC_VALUE="${EXISTING_NTFY_TOPIC:-BLll6HGzJA0P9U4U}"
NTFY_TOKEN_VALUE="${EXISTING_NTFY_TOKEN}"

cat > "$ENV_FILE" <<EOF_ENV
ZYZ_USER=${ZYZ_USER}
NETWORK_IFACE=${NETWORK_IFACE}
MIRACAST_IFACE=${MIRACAST_IFACE}
DISPLAY_NAME=ZyzDisplay
DRM_CONNECTOR_ID=${DRM_CONNECTOR_ID}
DRM_MODE=${DRM_MODE}
AUDIO_DEVICE=${AUDIO_DEVICE}
H264_DECODER=${H264_DECODER}
H264_CONVERTER=${H264_CONVERTER}
SPOTIFY_STATUS_URL=http://127.0.0.1:3678/status
WALLHAVEN_ENABLED=1
WALLHAVEN_INTERVAL=300
WALLHAVEN_BATCH_REFRESH=7200
WALLHAVEN_QUERY="wildlife -cgi -3d -fantasy,nature landscape -cgi -3d,forest mountains -cgi,castle palace -fantasy -cgi,temple pyramid ruins -cgi"
WALLHAVEN_CATEGORIES=100
WALLHAVEN_PURITY=100
WALLHAVEN_RESOLUTION=1920x1080
WALLHAVEN_RATIOS=16x9
WEATHER_ENABLED=1
WEATHER_LOCATION="Newberry, Florida"
WEATHER_UNITS=u
WEATHER_REFRESH=900
CALENDAR_ICS_URL=${EXISTING_CALENDAR_ICS_URL}
CALENDAR_REFRESH=900
NTFY_ENABLED=${NTFY_ENABLED_VALUE}
NTFY_URL=${NTFY_URL_VALUE}
NTFY_TOPIC=${NTFY_TOPIC_VALUE}
NTFY_TOKEN=${NTFY_TOKEN_VALUE}
EOF_ENV
chown root:"$ZYZ_USER" "$ENV_FILE"
chmod 0640 "$ENV_FILE"

# Persistently reserve onboard Wi-Fi for MiracleCast. Do not restart
# NetworkManager here; that can interrupt the install/SSH session.
install -d -m 0755 /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/99-zyzdisplay-miracast.conf <<EOF_NM
[keyfile]
unmanaged-devices=interface-name:${MIRACAST_IFACE},interface-name:p2p-dev-${MIRACAST_IFACE},interface-name:p2p-dev-${NETWORK_IFACE},interface-name:p2p-${MIRACAST_IFACE}*
EOF_NM
install -m 0644 "$SCRIPT_DIR/networkmanager/99-zyzdisplay-wifi-powersave.conf" \
    /etc/NetworkManager/conf.d/99-zyzdisplay-wifi-powersave.conf
iw dev "$NETWORK_IFACE" set power_save off >/dev/null 2>&1 || true

# Merge production-required go-librespot settings while preserving credentials
# and any unrelated user settings. A timestamped backup is kept.
GL_DIR="$ZYZ_HOME/.config/go-librespot"
GL_CFG="$GL_DIR/config.yml"
install -d -o "$ZYZ_USER" -g "$ZYZ_USER" -m 0755 "$GL_DIR"
if [[ -f "$GL_CFG" ]]; then
    cp -a "$GL_CFG" "${GL_CFG}.bak.$(date +%Y%m%d%H%M%S)"
fi
python3 - "$GL_CFG" "$NETWORK_IFACE" "$AUDIO_DEVICE" <<'PY'
import sys
from pathlib import Path
import yaml

path = Path(sys.argv[1])
iface = sys.argv[2]
audio = sys.argv[3]
try:
    data = yaml.safe_load(path.read_text()) if path.exists() else {}
except Exception:
    data = {}
if not isinstance(data, dict):
    data = {}

data["device_name"] = "ZyzDisplay"
data["device_type"] = "speaker"
data["audio_backend"] = "alsa"
data["audio_device"] = audio
data["bitrate"] = 320
data.setdefault("initial_volume", 75)
data["zeroconf_enabled"] = True
data["zeroconf_backend"] = "avahi"
data["zeroconf_interfaces_to_advertise"] = [iface]

credentials = data.setdefault("credentials", {})
if not isinstance(credentials, dict):
    credentials = {}
    data["credentials"] = credentials
credentials.setdefault("type", "zeroconf")
if credentials.get("type") == "zeroconf":
    zc = credentials.setdefault("zeroconf", {})
    if not isinstance(zc, dict):
        zc = {}
        credentials["zeroconf"] = zc
    zc["persist_credentials"] = True

server = data.setdefault("server", {})
if not isinstance(server, dict):
    server = {}
    data["server"] = server
server.update({
    "enabled": True,
    "address": "127.0.0.1",
    "port": 3678,
    "image_size": "large",
})

path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
PY
chown -R "$ZYZ_USER:$ZYZ_USER" "$GL_DIR"

backup_unit() {
    local path="$1"
    if [[ -f "$path" ]]; then
        cp -a "$path" "${path}.bak.$(date +%Y%m%d%H%M%S)"
    fi
}

for unit in zyzdisplay-dashboard.service zyzdisplay-kiosk.service go-librespot.service miracle-wifid.service miracle-sink.service miracle-watch.service uxplay.service zyz-bluetooth.service zyz-kiosk-escape.service; do
    backup_unit "/etc/systemd/system/$unit"
done

install -m 0644 "$SCRIPT_DIR/systemd/zyzdisplay-dashboard.service" /etc/systemd/system/zyzdisplay-dashboard.service
sed "s/^User=zyztem$/User=${ZYZ_USER}/; s/^ExecStart=\/usr\/local\/bin\/go-librespot /ExecStart=$(printf '%s' "$GO_LIBRESPOT" | sed 's/[&/]/\\&/g') /; s#/home/zyztem#${ZYZ_HOME}#g" \
    "$SCRIPT_DIR/systemd/go-librespot.service" > /etc/systemd/system/go-librespot.service
sed "s/^User=zyztem$/User=${ZYZ_USER}/" "$SCRIPT_DIR/systemd/zyzdisplay-kiosk.service" > /etc/systemd/system/zyzdisplay-kiosk.service
install -m 0644 "$SCRIPT_DIR/systemd/miracle-wifid.service" /etc/systemd/system/miracle-wifid.service
install -m 0644 "$SCRIPT_DIR/systemd/miracle-sink.service" /etc/systemd/system/miracle-sink.service
install -m 0644 "$SCRIPT_DIR/systemd/miracle-watch.service" /etc/systemd/system/miracle-watch.service
install -m 0644 "$SCRIPT_DIR/systemd/uxplay.service" /etc/systemd/system/uxplay.service
install -m 0644 "$SCRIPT_DIR/systemd/zyz-bluetooth.service" /etc/systemd/system/zyz-bluetooth.service
install -m 0644 "$SCRIPT_DIR/systemd/zyz-disc.service" /etc/systemd/system/zyz-disc.service
install -m 0644 "$SCRIPT_DIR/systemd/zyz-kiosk-escape.service" /etc/systemd/system/zyz-kiosk-escape.service
install -d -m 0755 /etc/systemd/system/bluealsa.service.d /etc/systemd/system/bluealsa-aplay.service.d
install -m 0644 "$SCRIPT_DIR/systemd/bluealsa.service.d/zyz.conf" /etc/systemd/system/bluealsa.service.d/zyz.conf
cat > /etc/systemd/system/bluealsa-aplay.service.d/zyz.conf <<EOF_BT
[Service]
ExecStart=
ExecStart=/usr/bin/bluealsa-aplay -S --pcm=${AUDIO_DEVICE} --volume=none
EOF_BT
install -m 0644 "$SCRIPT_DIR/udev/99-zyz-bt500.rules" /etc/udev/rules.d/99-zyz-bt500.rules
install -m 0644 "$SCRIPT_DIR/udev/99-zyz-disc.rules" /etc/udev/rules.d/99-zyz-disc.rules
udevadm control --reload-rules >/dev/null 2>&1 || true
python3 - "$SCRIPT_DIR/config/bluetooth-main.conf" /etc/bluetooth/main.conf <<'PY'
from pathlib import Path
import sys
overlay = Path(sys.argv[1]).read_text(encoding="utf-8")
path = Path(sys.argv[2])
text = path.read_text(encoding="utf-8") if path.exists() else "[General]\n"
keys = {}
for line in overlay.splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = [part.strip() for part in line.split("=", 1)]
    keys[key] = value

def upsert(src: str, key: str, value: str) -> str:
    import re
    pattern = re.compile(rf"^[#[\t ]*{re.escape(key)}[ \t]*=.*$", re.M)
    replacement = f"{key} = {value}"
    if pattern.search(src):
        return pattern.sub(replacement, src, count=1)
    if "[Policy]" in src and key == "AutoEnable":
        return src.replace("[Policy]", f"[Policy]\n{replacement}", 1)
    if "[General]" in src:
        return src.replace("[General]", f"[General]\n{replacement}", 1)
    return src + f"\n[General]\n{replacement}\n"

for key, value in keys.items():
    text = upsert(text, key, value)
path.write_text(text, encoding="utf-8")
PY
systemctl enable bluealsa.service bluealsa-aplay.service >/dev/null 2>&1 || true

# Avahi is shared by UxPlay and go-librespot. Keep it off the MiracleCast radio.
AVAHI_CONF=/etc/avahi/avahi-daemon.conf
if [[ -f "$AVAHI_CONF" ]]; then
    cp -a "$AVAHI_CONF" "${AVAHI_CONF}.bak.$(date +%Y%m%d%H%M%S)"
    python3 - "$AVAHI_CONF" "$NETWORK_IFACE" "$MIRACAST_IFACE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
allow = sys.argv[2]
deny = sys.argv[3]
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
out = []
seen_allow = False
seen_deny = False
in_server = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        in_server = stripped.lower() == "[server]"
    if in_server and stripped.startswith("allow-interfaces="):
        out.append(f"allow-interfaces={allow}")
        seen_allow = True
        continue
    if in_server and stripped.startswith("deny-interfaces="):
        out.append(f"deny-interfaces={deny}")
        seen_deny = True
        continue
    out.append(line)
if not seen_allow or not seen_deny:
    rebuilt = []
    inserted = False
    for line in out:
        rebuilt.append(line)
        if not inserted and line.strip().lower() == "[server]":
            if not seen_allow:
                rebuilt.append(f"allow-interfaces={allow}")
            if not seen_deny:
                rebuilt.append(f"deny-interfaces={deny}")
            inserted = True
    out = rebuilt
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
fi

SERVICES_STOPPED=0
restore_services_on_failure() {
    local status=$?
    if [[ "$status" -ne 0 && "$SERVICES_STOPPED" -eq 1 ]]; then
        systemctl daemon-reload >/dev/null 2>&1 || true
        systemctl start zyzdisplay-dashboard.service go-librespot.service uxplay.service \
            zyz-bluetooth.service miracle-wifid.service miracle-sink.service \
            miracle-watch.service zyzdisplay-kiosk.service zyz-kiosk-escape.service >/dev/null 2>&1 || true
    fi
    exit "$status"
}
trap restore_services_on_failure EXIT

# Clear prototype/manual processes before systemd becomes the sole owner.
systemctl stop zyzdisplay-kiosk.service uxplay.service miracle-watch.service miracle-sink.service miracle-wifid.service go-librespot.service zyzdisplay-dashboard.service zyz-bluetooth.service 2>/dev/null || true
SERVICES_STOPPED=1
pkill -f '[m]iracle-sinkctl' 2>/dev/null || true
pkill -f '[m]iracle-wifid' 2>/dev/null || true
pkill -x uxplay 2>/dev/null || true
fuser -k 8080/tcp >/dev/null 2>&1 || true

systemctl daemon-reload
systemctl enable bluetooth.service avahi-daemon.service zyzdisplay-dashboard.service zyzdisplay-kiosk.service go-librespot.service uxplay.service zyz-bluetooth.service miracle-wifid.service miracle-sink.service miracle-watch.service zyz-kiosk-escape.service
systemctl restart avahi-daemon.service >/dev/null 2>&1 || systemctl start avahi-daemon.service
systemctl start bluetooth.service >/dev/null 2>&1 || true
systemctl start zyzdisplay-dashboard.service go-librespot.service uxplay.service zyz-bluetooth.service miracle-wifid.service miracle-sink.service miracle-watch.service zyzdisplay-kiosk.service
systemctl restart zyz-kiosk-escape.service >/dev/null 2>&1 || systemctl start zyz-kiosk-escape.service
SERVICES_STOPPED=0

sleep 2

echo
echo "ZyzDisplay production stack installed."
echo "  user:       $ZYZ_USER"
echo "  network:    $NETWORK_IFACE"
echo "  Miracast:   $MIRACAST_IFACE"
echo "  HDMI DRM:   connector $DRM_CONNECTOR_ID, mode $DRM_MODE"
echo "  HDMI audio: $AUDIO_DEVICE"
echo "  AirPlay:    UxPlay on $NETWORK_IFACE"
echo "  Bluetooth:  A2DP sink ZyzDisplay"
echo "  H.264:      $H264_DECODER decode, $H264_CONVERTER convert"
echo "  Escape:     Ctrl+Alt+Esc on the keyboard stops the kiosk for terminal access"
echo
/usr/local/bin/zyz-health || true

echo
if strings "$MIRACLE_WIFID" 2>/dev/null | grep -q 'using P2P-DEVICE-FOUND data directly'; then
    echo "MiracleCast Samsung peer workaround: detected."
else
    echo "WARNING: the Samsung P2P_PEER workaround was not detected in miracle-wifid."
    echo "Your current manually patched build may still be fine if symbols/log strings were stripped,"
    echo "but preserve the source patch before rebuilding MiracleCast. See README.md."
fi

echo
echo "Reboot recommended so NetworkManager picks up the persistent ${MIRACAST_IFACE} unmanaged policy cleanly."
