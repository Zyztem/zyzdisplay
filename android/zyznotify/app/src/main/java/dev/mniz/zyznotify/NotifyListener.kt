package dev.mniz.zyznotify

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.ComponentName
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

class NotifyListener : NotificationListenerService() {
    private lateinit var prefs: Prefs
    private val recent = LinkedHashMap<String, Long>()

    override fun onCreate() {
        super.onCreate()
        prefs = Prefs(this)
        ensureChannel()
    }

    override fun onListenerConnected() {
        super.onListenerConnected()
        val notification = statusNotification()
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(STATUS_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(STATUS_ID, notification)
        }
        prefs.lastStatus = "Listener connected"
    }

    override fun onListenerDisconnected() {
        prefs.lastStatus = "Listener disconnected"
        super.onListenerDisconnected()
    }

    override fun onBind(intent: Intent?): IBinder? = super.onBind(intent)

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        val note = sbn ?: return
        if (!prefs.readyToSend()) return
        if (note.packageName == packageName) return
        if (!prefs.allows(note.packageName)) return
        if (note.isOngoing) return
        val notification = note.notification ?: return
        if (notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) return
        if (notification.category == Notification.CATEGORY_SERVICE ||
            notification.category == Notification.CATEGORY_TRANSPORT
        ) {
            return
        }

        val extras = notification.extras
        val title = extras.charSeq(Notification.EXTRA_TITLE)
            .ifBlank { extras.charSeq(Notification.EXTRA_CONVERSATION_TITLE) }
        val text = extras.charSeq(Notification.EXTRA_BIG_TEXT)
            .ifBlank { extras.charSeq(Notification.EXTRA_TEXT) }
            .ifBlank { extras.charSeq(Notification.EXTRA_SUB_TEXT) }
        if (title.isBlank() && text.isBlank()) return

        val key = "${note.packageName}|$title|$text"
        val now = System.currentTimeMillis()
        synchronized(recent) {
            val last = recent[key]
            if (last != null && now - last < 2_500) return
            recent[key] = now
            val stale = recent.entries.filter { now - it.value > 30_000 }.map { it.key }
            stale.forEach { recent.remove(it) }
        }

        val app = AppCatalog.labelsByPackage[note.packageName] ?: runCatching {
            packageManager.getApplicationLabel(packageManager.getApplicationInfo(note.packageName, 0)).toString()
        }.getOrDefault(note.packageName)
        val kind = when {
            notification.category == Notification.CATEGORY_MISSED_CALL -> "missed"
            "missed" in title.lowercase() || "missed" in text.lowercase() -> "missed"
            else -> "message"
        }
        NtfySender.sendAsync(
            prefs,
            ForwardedNotice(
                pkg = note.packageName,
                app = app,
                title = title,
                text = text,
                kind = kind,
            ),
        )
    }

    private fun statusNotification(): Notification {
        val launch = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_notify)
            .setContentTitle(getString(R.string.status_title))
            .setContentText(getString(R.string.status_text))
            .setContentIntent(launch)
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build()
    }

    private fun ensureChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, getString(R.string.status_channel), NotificationManager.IMPORTANCE_LOW),
        )
    }

    companion object {
        private const val CHANNEL_ID = "zyznotify-forward"
        private const val STATUS_ID = 7

        fun component(context: android.content.Context) =
            ComponentName(context, NotifyListener::class.java)
    }
}

private fun android.os.Bundle.charSeq(key: String): String =
    getCharSequence(key)?.toString()?.trim().orEmpty()
