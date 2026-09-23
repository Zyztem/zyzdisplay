# Miracast on Pi 5: root cause and recommendations (2026-09-22)

## TL;DR

Miracast on the onboard Wi-Fi chip (`wlan0`, Broadcom/Cypress BCM4345/6) is
unreliable because **the chip's own firmware crashes** during P2P
GO-Negotiation on this specific Pi 5 + kernel combination. This is not a bug
in this repo's scripts, in `miraclecast`, or in the Linux kernel driver — it's
inside Broadcom/Cypress's closed-source firmware blob, and it's a known,
currently unresolved issue affecting other Pi 5 users too (see Sources below).
It worked on the Pi 3 because that board's older, slower SDIO controller
never exercised the firmware code path that crashes on Pi 5's newer,
faster `sdhci-brcmstb` (BCM2712) SDIO controller.

No further software change on this box is likely to fix it. The path that
would actually fix it is different Wi-Fi hardware.

## What's fixed and staying (real improvements)

These are genuine bugs, found and fixed tonight, that make retries recover
fast and cleanly instead of hanging in broken states. They don't fix the
underlying firmware crash, but they're worth keeping regardless.

1. **Stale `.global` control-socket race on `wpa_supplicant` respawn.**
   `miracle-wifid` never unlinked its old `wpa_supplicant` global control
   socket (`/run/miracle/wifi/<ifname>-<ifindex>.global`) before respawning
   after a crash. `wpa_supplicant`'s own stale-socket "fixup" is unreliable
   for `AF_UNIX SOCK_DGRAM` sockets, so the leftover file reliably won the
   race and the respawn failed with `ctrl_iface exists and seems to be in
   use`. Fixed in `~/miraclecast/src/wifi/wifid-supplicant.c`,
   `supplicant_spawn()`.
2. **Same bug, second socket.** The plain per-interface control socket
   (`/run/miracle/wifi/<ifname>`, distinct from the `.global` one) had the
   identical race. Same fix, same function.
3. **`zyz-miracle-sink` hard-failed on a socket that's allowed to
   disappear.** Once `wpa_supplicant`'s P2P-Device role fully takes over the
   radio, the plain `/run/miracle/wifi/<ifname>` socket can vanish for good
   even though the one that actually matters
   (`/run/miracle/wifi/p2p-dev-<ifname>`) stays up. The sink script used to
   treat the first socket's absence as fatal; now it only requires the P2P
   socket and logs the other as informational. Fixed in `bin/zyz-miracle-sink`.
4. **Watchdog re-triggering scans on top of a known peer.**
   `zyz-miracle-watch`'s `ensure_scan()` used to fire on a blind ~12s timer
   regardless of state, colliding with an in-flight negotiation. It's now
   gated on a `has_known_peer()` check (busctl peer-object presence). Fixed
   in `bin/zyz-miracle-watch`.
5. **Proactive scan-stop on Provision Discovery.** Added a
   `supplicant_p2p_stop_scan()` call in
   `supplicant_event_p2p_prov_disc_pbc_req()` so the radio isn't mid-scan
   when a GO-Negotiation-Response needs to go out. This is what produced the
   one fully successful `GO-NEG-SUCCESS` + WPA handshake tonight. Fixed in
   `~/miraclecast/src/wifi/wifid-supplicant.c`.

**Important:** the `miraclecast` fixes (1, 2, 5) live in `~/miraclecast`, a
**separate git repo from this one**, and are currently **uncommitted local
changes** (`git status` there shows `wifid-supplicant.c` modified). If that
checkout is ever wiped or the built binaries at `/usr/local/bin/miracle-wifid`
get reinstalled from a package, these fixes disappear silently. Recommend
committing them there (with a note that they're locally-authored, not
upstream) and/or documenting the diff in this repo the way
`MIRACLECAST_SAMSUNG_PATCH.md` already documents the earlier Samsung
peer-parsing patch.

## What was tried and reverted

- **Swapping the RTL8852BU (TP-Link-branded, `rtw89_8852bu` driver) onto
  Miracast duty, onboard chip onto normal networking.** Reverted. The
  RTL8852BU driver crashes `wpa_supplicant` (`HUP`) within seconds of trying
  to start P2P, every time, and never creates a P2P-Device interface at all
  despite `iw` advertising `P2P-GO`/`P2P-client` as supported modes. Worse
  than the onboard chip's intermittent failures, not better. This chipset
  cannot do Miracast on this system, regardless of branding on the case.
- **Custom kernel `brcmfmac.ko` patch** to stop a failed
  `actframe_abort` (`BCME_IE_NOTFOUND`, errno -52) from forcing a spurious
  `escan_complete` event up to userspace mid-negotiation. Built against the
  exact matching kernel source (`linux-source-6.18`, package
  `1:6.18.50-1+rpt1`), loaded live, tested. Didn't fix the underlying issue
  — confirmed the crash is a genuine firmware halt
  (`brcmf_fw_crashed: Firmware has halted or crashed` in `dmesg`), not a
  driver-side logic bug, so no kernel-side patch can fix it. Reverted to the
  stock packaged module.
- **Armbian.** Ruled out without attempting — the firmware blob is Raspberry
  Pi hardware-specific (antenna/RF calibration data, distributed via
  Raspberry Pi Ltd's own `firmware-brcm80211` packaging), and the kernel
  driver is the same mainline code on any distro. Switching OS would carry
  real risk to the parts of this project that currently work (DRM/KMS
  kiosk display, HDMI audio) for no realistic chance of fixing this.

## Recommendations, in priority order

1. **Get a dedicated USB Wi-Fi adapter for Miracast specifically**, separate
   from the RTL8852BU/TP-Link dongle already handling `NETWORK_IFACE`. This
   is the only path found tonight with a real chance of fixing Miracast.
   When picking one, chipset matters far more than brand — look for older,
   well-trodden Linux P2P-GO chipsets rather than newer Wi-Fi 6 parts:
   - Better track record: Realtek RTL8188CUS/RTL8192CU-family, MediaTek
     MT7601U/MT7612U-family.
   - Confirm before buying if possible: search `<chipset> wifi direct group
     owner linux` or check for existing Miracast/hostapd P2P reports with
     that exact chipset — the RTL8852BU's `iw`-reported capability
     (`P2P-GO` listed as supported) turned out to mean nothing in practice.
2. **Watch for a firmware update.** Check
   `apt list --upgradable | grep -i firmware` periodically — if Broadcom/
   Cypress or Raspberry Pi Ltd ship a fixed blob, this could resolve itself
   with zero further work. As of tonight, `firmware-brcm80211` is already at
   the latest available version (`1:20260519-1~bpo13+1+rpt1`) with no known
   fix yet.
3. **If neither happens**, live with intermittent Miracast on the onboard
   chip. The fixes above make failures recover fast, and it does work
   sometimes — just not reliably enough to depend on.

## Sources (known upstream issue tracking)

- [BCM43455 firmware crash with concurrent STA+AP mode on kernel 6.12 — raspberrypi/linux#7092](https://github.com/raspberrypi/linux/issues/7092)
- [brcmfmac: BCM43455 on Raspberry Pi 5 — HT Avail timeout before firmware download after repeated wifi reload — openwrt/openwrt#23069](https://github.com/openwrt/openwrt/issues/23069)
- [wifi: brcmfmac: firmware crash when using WPA3/SAE — raspberrypi/linux#7528](https://github.com/raspberrypi/linux/issues/7528)
- [RPi4: WiFi client crashes often (brcmf_fw_crashed: Firmware has halted or crashed) — raspberrypi/linux#3849](https://github.com/raspberrypi/linux/issues/3849)

## Current system state as of tonight

- `NETWORK_IFACE=wlan1` (RTL8852BU/TP-Link dongle), `MIRACAST_IFACE=wlan0`
  (onboard BCM4345/6) — the original assignment, confirmed as the better of
  the two working options.
- `miracle-wifid.service`, `miracle-sink.service`, `miracle-watch.service`
  all active and using the patched `miracle-wifid`/`miracle-sinkctl`
  binaries from `~/miraclecast` and the updated `bin/zyz-miracle-sink` /
  `bin/zyz-miracle-watch` scripts in this repo.
- Kernel module: stock, unpatched `brcmfmac.ko` from the
  `linux-image-6.18.50+rpt-rpi-2712` package (the experimental patched
  build was tested and reverted; nothing kernel-side is modified from
  stock).
