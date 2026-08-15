# ZyzNotify

Sideload this on the Samsung phone. It is the notification allowlist + ntfy publisher for ZyzDisplay. Not Expo: Android’s notification listener is a native service.

## Build

On a machine with Android Studio (the display Pi cannot build this well):

1. Open `android/zyznotify`.
2. Let Gradle sync.
3. Build → Build APK(s), or `./gradlew assembleDebug` after Android Studio generates the wrapper jar.
4. Copy `app/build/outputs/apk/debug/app-debug.apk` to the phone and sideload it.

If the wrapper jar is missing:

```bash
gradle wrapper --gradle-version 8.9
```

## First run on the phone

1. Open **ZyzNotify**.
2. Enable **Notification access**.
3. Set battery to **Unrestricted** (Samsung will kill it otherwise).
4. Paste the ntfy token. URL and topic default to the home server.
5. Leave TTL at 15 minutes unless you want them gone faster.
6. Toggle apps. Defaults: Discord, WhatsApp, Messages, Messenger, Phone.
7. **Send test to TV**.

Turn MacroDroid off so the same alerts are not posted twice.

The kiosk reads JSON `{v,pkg,app,title,text,kind}` from the ntfy message body.
