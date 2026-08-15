package dev.mniz.zyznotify

import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build

data class InstalledApp(
    val label: String,
    val pkg: String,
)

data class SuggestedApp(
    val label: String,
    val packages: List<String>,
)

object AppCatalog {
    val suggested = listOf(
        SuggestedApp(
            "Discord",
            listOf("com.discord", "com.discord.mobile"),
        ),
        SuggestedApp(
            "WhatsApp",
            listOf("com.whatsapp", "com.whatsapp.w4b"),
        ),
        SuggestedApp(
            "Messages",
            listOf(
                "com.google.android.apps.messaging",
                "com.samsung.android.messaging",
            ),
        ),
        SuggestedApp(
            "Messenger",
            listOf("com.facebook.orca", "com.facebook.mlite"),
        ),
        SuggestedApp(
            "Phone",
            listOf(
                "com.samsung.android.incallui",
                "com.samsung.android.dialer",
                "com.google.android.dialer",
                "com.android.dialer",
                "com.android.server.telecom",
            ),
        ),
        SuggestedApp("Signal", listOf("org.thoughtcrime.securesms")),
        SuggestedApp("Telegram", listOf("org.telegram.messenger")),
        SuggestedApp("Instagram", listOf("com.instagram.android")),
        SuggestedApp("Gmail", listOf("com.google.android.gm")),
    )

    val defaultEnabled = setOf(
        "com.discord",
        "com.whatsapp",
        "com.google.android.apps.messaging",
        "com.samsung.android.messaging",
        "com.facebook.orca",
        "com.samsung.android.incallui",
        "com.samsung.android.dialer",
        "com.google.android.dialer",
    )

    val labelsByPackage: Map<String, String> = buildMap {
        suggested.forEach { app ->
            app.packages.forEach { pkg -> put(pkg, app.label) }
        }
    }

    val catalogPackages: Set<String> = suggested.flatMap { it.packages }.toSet()

    fun installed(pm: PackageManager, selfPackage: String): List<InstalledApp> {
        val seen = LinkedHashMap<String, InstalledApp>()

        fun add(pkg: String, label: String? = null) {
            if (pkg.isBlank() || pkg == selfPackage || pkg in seen) return
            val resolved = label ?: runCatching {
                pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString()
            }.getOrNull().orEmpty().ifBlank { pkg }
            seen[pkg] = InstalledApp(label = resolved, pkg = pkg)
        }

        installedApplications(pm).forEach { info ->
            if (!info.enabled) return@forEach
            add(info.packageName, pm.getApplicationLabel(info).toString())
        }

        val launch = android.content.Intent(android.content.Intent.ACTION_MAIN)
            .addCategory(android.content.Intent.CATEGORY_LAUNCHER)
        pm.queryIntentActivities(launch, 0).forEach { add(it.activityInfo.packageName) }
        catalogPackages.forEach { pkg ->
            if (runCatching { pm.getApplicationInfo(pkg, 0) }.isSuccess) add(pkg, labelsByPackage[pkg])
        }

        return seen.values.sortedWith(compareBy(String.CASE_INSENSITIVE_ORDER) { it.label })
    }

    private fun installedApplications(pm: PackageManager): List<ApplicationInfo> {
        return if (Build.VERSION.SDK_INT >= 33) {
            pm.getInstalledApplications(PackageManager.ApplicationInfoFlags.of(0))
        } else {
            @Suppress("DEPRECATION")
            pm.getInstalledApplications(0)
        }
    }
}
