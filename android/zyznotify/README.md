# ZyzNotify

Sideload this on the Samsung phone. It is the notification allowlist + ntfy publisher for ZyzDisplay. Not Expo: Android’s notification listener is a native service.

## Build

The display Pi cannot build this. Use GitHub Actions:

1. Push to `main`, or run **Actions → ZyzNotify APK → Run workflow**.
2. Download the `zyznotify-debug` artifact.
3. Sideload `app-debug.apk` on the phone.
    
On a machine with Android Studio: open `android/zyznotify`, then **Build → Build APK(s)**.

## First run on the phone

1. Open **ZyzNotify**.
2. Enable **Notification access**.
3. Set battery to **Unrestricted** (Samsung will kill it otherwise).
4. Paste the ntfy token. URL and topic default to the home server.
5. Leave TTL at 15 minutes unless you want them gone faster.
6. Search the full app list and toggle anything you want. Defaults: Discord, WhatsApp, Messages, Messenger, Phone.
7. **Send test to TV**.

Turn MacroDroid off so the same alerts are not posted twice.

The kiosk reads JSON `{v,pkg,app,title,text,kind}` from the ntfy message body.
