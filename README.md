# ZyzDisplay Production Stack

A Raspberry Pi OS Lite appliance stack, proven on:

- Raspberry Pi 3
- Raspberry Pi 5

Common hardware:

- onboard `wlan0` dedicated to Miracast
- USB Wi-Fi adapter for normal Wi-Fi (TP-Link Archer on the tested Pi 3 unit)
- HDMI-A-1 at 1920x1080 (30Hz when the display offers it)
- HDMI audio through ALSA, matched to whichever HDMI port is actually driving
  the display (`plughw:1,0` on the Pi 3 unit; Pi 5 has two HDMI ports/cards)
- MiracleCast
- UxPlay (AirPlay)
- go-librespot
- Cog/WPE rendering directly to DRM/KMS

## Raspberry Pi 5 notes

Pi 5 (BCM2712) dropped the `bcm2835-codec` V4L2 M2M block that Pi 3/4 use for
hardware H.264 decode; its only hardware video decoder is HEVC-only
(`rpi-hevc-dec`), which Miracast and AirPlay don't use. The installer detects
this at install time (`v4l2-ctl --list-devices`) and records the right
GStreamer decoder/converter in `/etc/zyzdisplay/zyzdisplay.env`:

```text
H264_DECODER=avdec_h264      # v4l2h264dec on Pi 3/4
H264_CONVERTER=videoconvert  # v4l2convert on Pi 3/4
```

Software H.264 decode runs on the CPU; `zyz-miracle-player` and `zyz-uxplay`
switch the CPU governor to `performance` while a software-decoded stream is
active and restore it afterward. Pi 5's four Cortex-A76 cores handle 1080p30
H.264 comfortably this way.

### USB Wi-Fi dongle note (Realtek RTL8852BU / rtw89_8852bu)

The USB adapter used for `NETWORK_IFACE` on the bring-up unit is a Realtek
RTL8852BU (`rtw89_8852bu` driver). Its mainline Linux support is quite new and
has a scanning bug: a plain passive scan finds nearby APs fine, but a
*directed* active scan (`iw dev <if> scan ssid "<ssid>"`, which is what
wpa_supplicant issues) returns nothing. Against a WPA2/WPA3-transition AP,
NetworkManager needs that directed scan to pull the full RSN info required to
negotiate SAE, so every connection attempt fails with "the Wi-Fi network
could not be found" even though the network is clearly visible.

Workaround: force the connection profile to plain WPA2-PSK, which only needs
the info already present in a passive scan:

```bash
sudo nmcli connection add type wifi ifname wlan1 con-name "wlan1-<ssid>" \
  ssid "<ssid>" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "<password>"
```

If this dongle is swapped for another unit, or a fresh Pi 5 is being
provisioned, check for this symptom first before assuming a bad config: a
raw `sudo iw dev <if> scan` finds the SSID, but `nmcli connection up` fails
with `ssid-not-found`.

## Exiting to a terminal

The kiosk owns DRM/KMS directly with no window manager, so there's normally no
keyboard path back to a console. `zyz-kiosk-escape.service` runs independently
of Cog and the dashboard (so it still works if either is hung) and watches for
**Ctrl+Alt+Esc**: it stops `zyzdisplay-kiosk.service` and prints a message to
the physical console. Resume the display with:

```bash
sudo systemctl start zyzdisplay-kiosk
```

or reboot.

## Production behavior

At boot, systemd owns everything:

1. `zyzdisplay-dashboard.service` starts the local dashboard/API backend.
2. `go-librespot.service` exposes ZyzDisplay as a Spotify Connect speaker.
3. `uxplay.service` advertises ZyzDisplay as an AirPlay receiver.
4. `miracle-wifid.service` owns onboard Wi-Fi for Wi-Fi Direct.
5. `miracle-sink.service` starts `miracle-sinkctl` and binds the sink on `wlan0`.
6. `miracle-watch.service` keeps P2P scanning and the ZyzDisplay name alive after disconnects.
7. `zyzdisplay-kiosk.service` shows the idle dashboard directly on DRM/KMS.

When a Miracast or AirPlay stream starts, the stack:

- stops the Cog kiosk so DRM is free;
- stops go-librespot so HDMI ALSA is free;
- plays video through `v4l2h264dec` into `kmssink`;
- plays audio to the configured ALSA HDMI device;
- restores Spotify, AirPlay advertising, and Cog when the stream exits.

No desktop, X11, Wayland compositor, or Chromium is required.

## Dashboard

The dashboard is intentionally self-contained: static HTML/CSS/JS with no
runtime Tailwind compiler or icon-webfont dependency. This avoids a blank or
unstyled appliance screen when external CDNs are unavailable.

Idle mode shows:

- a large clock, date, and greeting;
- current weather with feels-like, hourly, and a 3-day forecast;
- the next calendar events, when an ICS feed is configured;
- compact Miracast / AirPlay / Spotify / Bluetooth / Disc readiness;
- normal-Wi-Fi SSID and IP address;
- Wallhaven wallpaper background.

Spotify / CD mode shows:

- album artwork and ambient artwork background;
- track, artists, album;
- playback state;
- smooth progress;
- volume, with weather and network in the footer.

## Calendar

The idle agenda reads a Google Calendar (or any ICS) URL. No OAuth is required.

In Google Calendar: **Settings → the calendar → Integrate calendar → Secret
address in iCal format**. Put that URL in:

`/etc/zyzdisplay/zyzdisplay.env`

```text
CALENDAR_ICS_URL=https://calendar.google.com/calendar/ical/.../private-.../basic.ics
CALENDAR_REFRESH=900
```

Multiple feeds can be comma-separated. The installer preserves an existing
`CALENDAR_ICS_URL` across reinstalls. Leave it empty to hide the agenda card.

The backend caches the next 7 days in `/var/lib/zyzdisplay/calendar.json` and
shows the next 3 events, including recurring ones (`RRULE`).

## Weather

Weather comes from [Open-Meteo](https://open-meteo.com/) (no API key) and is
cached in `/var/lib/zyzdisplay/weather.json`. The place name is geocoded once,
then the forecast API supplies current conditions, hourly slots, and a 3-day
outlook.

```text
WEATHER_ENABLED=1
WEATHER_LOCATION="Newberry, Florida"
WEATHER_UNITS=u
WEATHER_REFRESH=900
```

Optional `WEATHER_LAT` / `WEATHER_LON` skip geocoding. `WEATHER_UNITS=u` is °F;
`m` is °C.

## Wallhaven

The backend requests SFW, general-category, random, 16:9 wallpapers at exactly
1920x1080. One API response provides a batch, which is cached in
`/var/lib/zyzdisplay/wallhaven.json` and rotated locally every 5 minutes.
The default batch refresh is every 2 hours. Non-1080 downloads are scaled to
1920x1080 JPEG before the kiosk uses them.

If Wallhaven or WAN is unavailable, the current cached wallpaper remains. If
there is no cache yet, the dashboard falls back to its dark gradient.

Change filters in:

`/etc/zyzdisplay/zyzdisplay.env`

Important settings:

```text
WALLHAVEN_INTERVAL=300
WALLHAVEN_BATCH_REFRESH=7200
WALLHAVEN_CATEGORIES=100
WALLHAVEN_PURITY=100
WALLHAVEN_RESOLUTION=1920x1080
WALLHAVEN_RATIOS=16x9
WALLHAVEN_QUERY="wildlife -cgi -3d -fantasy,nature landscape -cgi -3d,forest mountains -cgi,castle palace -fantasy -cgi,temple pyramid ruins -cgi"
```

## Install

The current MiracleCast and go-librespot binaries must already be installed.
UxPlay is installed from Debian. The installer preserves the existing
go-librespot configuration with a backup, then merges the settings required
by the dashboard.

```bash
unzip zyzdisplay-production.zip
cd zyzdisplay-production
sudo ./install.sh
```

The installer automatically detects the connected HDMI DRM connector and tries
to detect the HDMI ALSA card/device. The proven values remain the fallback.
`DRM_MODE=1920x1080@30` prefers 1080p30; Cog falls back to 1080p60 if the
display does not advertise a 30Hz mode.

```text
DRM_CONNECTOR_ID=35
DRM_MODE=1920x1080@30
AUDIO_DEVICE=plughw:1,0
```

It deliberately does **not** restart NetworkManager during installation. It
marks `wlan0` unmanaged immediately and installs the persistent NetworkManager
policy for the next boot.

A reboot after installation is recommended.

## MiracleCast

`miracle-sink.service` is not a stock MiracleCast unit. It starts
`/usr/local/libexec/zyz-miracle-sink`, which waits for:

- the `org.freedesktop.miracle.wifi` D-Bus name;
- `wlan0`;
- the MiracleCast wpa_supplicant sockets under `/run/miracle/wifi`
  (`wlan0` and `p2p-dev-wlan0`);
- the D-Bus link object to become managed;

sets the P2P friendly name to **ZyzDisplay**, then runs:

```bash
miracle-sinkctl --audio 1 --external-player /usr/local/libexec/zyz-miracle-player bind wlan0
```

`bind` is used instead of `run` so scanning comes back after wpa_supplicant
HUPs when a P2P group is torn down.

Starting `miracle-sinkctl` before P2P is ready makes scan fail with
`supplicant: invalid arguments (p2p_start_scan)` and the receiver never
advertises. MiracleCast also needs periodic `P2P_FIND` while idle; that is
why `miracle-watch.service` re-enables `P2PScanning` and restores the name
after a session ends.

`miracle-wifid` is started with `--go-intent 15` so the Pi is the P2P group
owner. Being a client of a phone GO is the path that left scanning dead
after disconnect.

## AirPlay / UxPlay

UxPlay is installed from Debian (`uxplay`) and advertised over Avahi on
`wlan1` as **ZyzDisplay**. It uses the same HDMI `kmssink` + ALSA path as
Miracast, using whichever H.264 decode path the installer detected (see
[Raspberry Pi 5 notes](#raspberry-pi-5-notes)) and `-bt709`.

Avahi is shared with go-librespot (`zeroconf_backend: avahi`) so Spotify
Connect and AirPlay do not fight over mDNS port 5353. Avahi is restricted to
the normal Wi-Fi interface and excluded from the MiracleCast radio.

## MiracleCast local workaround

Do not lose the Samsung peer workaround that was required during bring-up.
See:

`tools/MIRACLECAST_SAMSUNG_PATCH.md`

If MiracleCast is rebuilt from upstream later, re-apply that local change
unless the upstream behavior has been fixed and retested with the Samsung
phone.

## Operations

Status summary:

```bash
zyz-health
```

Dashboard/backend health:

```bash
curl -s http://127.0.0.1:8080/api/health | python3 -m json.tool
```

Service status:

```bash
systemctl status \
  zyzdisplay-dashboard \
  zyzdisplay-kiosk \
  zyz-kiosk-escape \
  go-librespot \
  uxplay \
  miracle-wifid \
  miracle-sink \
  miracle-watch
```

Logs:

```bash
journalctl -u zyzdisplay-dashboard -f
journalctl -u zyzdisplay-kiosk -f
journalctl -u go-librespot -f
journalctl -u uxplay -f
journalctl -u miracle-wifid -f
journalctl -u miracle-sink -f
journalctl -u miracle-watch -f
journalctl -t miracle-sinkctl-gst -f
```

Restart the full stack:

```bash
sudo systemctl restart \
  zyzdisplay-dashboard \
  go-librespot \
  uxplay \
  miracle-wifid \
  miracle-sink \
  miracle-watch \
  zyzdisplay-kiosk
```

## Configuration

Primary appliance config:

`/etc/zyzdisplay/zyzdisplay.env`

go-librespot config:

`~/.config/go-librespot/config.yml`

UxPlay options:

`/etc/zyzdisplay/uxplayrc`

Normal networking remains managed by NetworkManager on `wlan1`. The persistent
Miracast exclusion is:

`/etc/NetworkManager/conf.d/99-zyzdisplay-miracast.conf`

## Uninstall

```bash
sudo ./uninstall.sh
```

The uninstaller removes ZyzDisplay services and application files but preserves
MiracleCast, go-librespot, their user state/configuration, `/etc/zyzdisplay`,
and the wallpaper cache.
