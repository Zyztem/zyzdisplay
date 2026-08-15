MiracleCast Samsung / modern P2P peer workaround

This ZyzDisplay was proven to need a local MiracleCast workaround with the
current Samsung devices and Wi-Fi stack.

Symptom before the workaround:

P2P-DEVICE-FOUND ... name='Galaxy ...'

MiracleCast immediately requests detailed peer data with P2P_PEER <MAC>

the child wpa_supplicant exits / the control socket HUPs

The working local change is in:

src/wifi/wifid-supplicant.c

Replace the body of supplicant_event_p2p_device_found() so it parses the
already-complete P2P-DEVICE-FOUND event and does not issue the follow-up
P2P_PEER request:

static void supplicant_event_p2p_device_found(struct supplicant *s,
                                              struct wpas_message *ev)
{
    const char *mac;
    int r;

    r = wpas_message_dict_read(ev, "p2p_dev_addr", 's', &mac);
    if (r < 0) {
        log_debug("no p2p_dev_addr in P2P-DEVICE-FOUND: %s",
                  wpas_message_get_raw(ev));
        return;
    }

    supplicant_parse_peer(s, ev);

    log_debug("using P2P-DEVICE-FOUND data directly for peer %s", mac);
}

Then rebuild/install MiracleCast from its existing build directory:

cd ~/miraclecast/build
make -j2
sudo make install

Additional production fixes in the same tree:

- Parse `p2p_dev_addr` when a peer event has no positional MAC
- Apply a DHCP lease to the only peer on the GO if the lease MAC is unknown
- Bind that peer to the GO group and emit D-Bus `Connected`/`RemoteAddress`
  after the lease (Wi-Fi Display RTSP cannot start without this)
- sinkctl treats peers on a WFD-enabled link as Miracast sinks even when
  `WfdSubelements` is missing, and retries RTSP for ~45s after GO negotiation

The production installer checks the installed miracle-wifid for the custom
log string as a best-effort reminder. It does not modify MiracleCast source
automatically.