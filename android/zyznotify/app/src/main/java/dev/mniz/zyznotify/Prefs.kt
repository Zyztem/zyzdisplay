package dev.mniz.zyznotify

import android.content.Context
import android.content.SharedPreferences

class Prefs(context: Context) {
    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences("zyznotify", Context.MODE_PRIVATE)

    var url: String
        get() = prefs.getString(KEY_URL, DEFAULT_URL).orEmpty().trim().trimEnd('/')
        set(value) = prefs.edit().putString(KEY_URL, value.trim().trimEnd('/')).apply()

    var topic: String
        get() = prefs.getString(KEY_TOPIC, DEFAULT_TOPIC).orEmpty().trim()
        set(value) = prefs.edit().putString(KEY_TOPIC, value.trim()).apply()

    var token: String
        get() = prefs.getString(KEY_TOKEN, "").orEmpty().trim()
        set(value) = prefs.edit().putString(KEY_TOKEN, value.trim()).apply()

    var ttlSeconds: Int
        get() = prefs.getInt(KEY_TTL, DEFAULT_TTL).coerceIn(60, 12 * 3600)
        set(value) = prefs.edit().putInt(KEY_TTL, value.coerceIn(60, 12 * 3600)).apply()

    var forwardingEnabled: Boolean
        get() = prefs.getBoolean(KEY_ENABLED, true)
        set(value) = prefs.edit().putBoolean(KEY_ENABLED, value).apply()

    var allowedPackages: Set<String>
        get() {
            val stored = prefs.getStringSet(KEY_ALLOWED, null)
            return stored?.toSet() ?: AppCatalog.defaultEnabled
        }
        set(value) = prefs.edit().putStringSet(KEY_ALLOWED, value).apply()

    var lastStatus: String
        get() = prefs.getString(KEY_STATUS, "").orEmpty()
        set(value) = prefs.edit().putString(KEY_STATUS, value).apply()

    fun allows(packageName: String): Boolean = packageName in allowedPackages

    fun togglePackage(packageName: String, enabled: Boolean) {
        val next = allowedPackages.toMutableSet()
        if (enabled) next += packageName else next -= packageName
        allowedPackages = next
    }

    fun readyToSend(): Boolean = forwardingEnabled && url.isNotBlank() && topic.isNotBlank() && token.isNotBlank()

    companion object {
        const val DEFAULT_URL = "https://ntfy.mniz.dev"
        const val DEFAULT_TOPIC = "BLll6HGzJA0P9U4U"
        const val DEFAULT_TTL = 900
        private const val KEY_URL = "url"
        private const val KEY_TOPIC = "topic"
        private const val KEY_TOKEN = "token"
        private const val KEY_TTL = "ttl"
        private const val KEY_ENABLED = "enabled"
        private const val KEY_ALLOWED = "allowed"
        private const val KEY_STATUS = "status"
    }
}
