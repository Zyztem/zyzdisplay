package dev.mniz.zyznotify

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Teal = Color(0xFF7DD3C0)
private val Ink = Color(0xFF111216)
private val Panel = Color(0xFF1B1E27)

@Composable
fun ZyzNotifyTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Teal,
            onPrimary = Ink,
            background = Ink,
            surface = Panel,
            onBackground = Color(0xFFE8EAED),
            onSurface = Color(0xFFE8EAED),
            secondary = Color(0xFF9AA4B2),
        ),
        content = content,
    )
}
