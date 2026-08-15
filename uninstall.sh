#!/bin/bash
set -euo pipefail
if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run with: sudo ./uninstall.sh" >&2
    exit 1
fi

systemctl disable --now zyzdisplay-kiosk.service uxplay.service miracle-watch.service miracle-sink.service miracle-wifid.service go-librespot.service zyzdisplay-dashboard.service zyz-bluetooth.service zyz-disc.service 2>/dev/null || true
rm -f /etc/systemd/system/zyzdisplay-kiosk.service \
      /etc/systemd/system/uxplay.service \
      /etc/systemd/system/miracle-sink.service \
      /etc/systemd/system/miracle-wifid.service \
      /etc/systemd/system/miracle-watch.service \
      /etc/systemd/system/go-librespot.service \
      /etc/systemd/system/zyzdisplay-dashboard.service \
      /etc/systemd/system/zyz-bluetooth.service \
      /etc/systemd/system/zyz-disc.service
rm -rf /etc/systemd/system/bluealsa.service.d /etc/systemd/system/bluealsa-aplay.service.d
rm -f /etc/udev/rules.d/99-zyz-bt500.rules /etc/udev/rules.d/99-zyz-disc.rules
rm -f /usr/local/libexec/zyz-kiosk \
      /usr/local/libexec/zyz-miracle-wifid \
      /usr/local/libexec/zyz-miracle-sink \
      /usr/local/libexec/zyz-miracast-controller \
      /usr/local/libexec/zyz-miracle-player \
      /usr/local/libexec/zyz-display-take \
      /usr/local/libexec/zyz-miracle-watch \
      /usr/local/libexec/zyz-uxplay \
      /usr/local/libexec/zyz-bluetooth \
      /usr/local/libexec/zyz-disc \
      /usr/local/bin/zyz-health
rm -rf /opt/zyzdisplay
rm -f /etc/NetworkManager/conf.d/99-zyzdisplay-miracast.conf
systemctl daemon-reload

echo "ZyzDisplay services removed."
echo "Preserved: /etc/zyzdisplay, go-librespot config/state, MiracleCast installation, UxPlay package, Avahi config, wallpaper cache."
