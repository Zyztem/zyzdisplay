package dev.mniz.zyznotify

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ZyzNotifyTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    HomeScreen(
                        onOpenListenerSettings = {
                            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
                        },
                        onOpenBatterySettings = {
                            val uri = Uri.parse("package:$packageName")
                            val direct = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).setData(uri)
                            val fallback = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                            startActivity(if (direct.resolveActivity(packageManager) != null) direct else fallback)
                        },
                    )
                }
            }
        }
    }
}

fun notificationAccessGranted(activity: ComponentActivity): Boolean {
    val enabled = Settings.Secure.getString(
        activity.contentResolver,
        "enabled_notification_listeners",
    ) ?: return false
    val expected = NotifyListener.component(activity).flattenToString()
    return enabled.split(':').any { it.equals(expected, ignoreCase = true) || it.startsWith(activity.packageName) }
}

fun batteryUnrestricted(activity: ComponentActivity): Boolean {
    val pm = activity.getSystemService(PowerManager::class.java)
    return pm.isIgnoringBatteryOptimizations(activity.packageName)
}
