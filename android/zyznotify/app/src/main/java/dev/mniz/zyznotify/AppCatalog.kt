package dev.mniz.zyznotify

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
}
