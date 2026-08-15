package dev.mniz.zyznotify

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver

@Composable
fun HomeScreen(
    onOpenListenerSettings: () -> Unit,
    onOpenBatterySettings: () -> Unit,
) {
    val context = LocalContext.current
    val activity = context as ComponentActivity
    val prefs = remember { Prefs(context) }
    var tick by remember { mutableIntStateOf(0) }
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) tick += 1
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    var enabled by remember(tick) { mutableStateOf(prefs.forwardingEnabled) }
    var url by remember(tick) { mutableStateOf(prefs.url) }
    var topic by remember(tick) { mutableStateOf(prefs.topic) }
    var token by remember(tick) { mutableStateOf(prefs.token) }
    var ttl by remember(tick) { mutableIntStateOf(prefs.ttlSeconds) }
    var allowed by remember(tick) { mutableStateOf(prefs.allowedPackages) }
    var status by remember(tick) { mutableStateOf(prefs.lastStatus) }
    var search by remember { mutableStateOf("") }
    val listenerOn = remember(tick) { notificationAccessGranted(activity) }
    val batteryOk = remember(tick) { batteryUnrestricted(activity) }
    val apps = remember(tick) { AppCatalog.installed(context.packageManager, context.packageName) }
    val installed = remember(apps) { apps.map { it.pkg }.toSet() }
    val needle = search.trim()
    val suggested = remember(apps, needle) {
        AppCatalog.suggested.filter { app ->
            val present = app.packages.any { it in installed }
            present && app.matches(needle)
        }
    }
    val others = remember(apps, needle, allowed) {
        apps.filter { app ->
            app.pkg !in AppCatalog.catalogPackages && app.matches(needle)
        }.sortedWith(
            compareByDescending<InstalledApp> { it.pkg in allowed }
                .thenBy(String.CASE_INSENSITIVE_ORDER) { it.label },
        )
    }

    fun persistAllowed(next: Set<String>) {
        allowed = next
        prefs.allowedPackages = next
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Text("ZyzNotify", style = MaterialTheme.typography.headlineMedium)
            Text(
                "Pick apps on this phone. They hit ntfy with a short TTL, then the TV glance.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.secondary,
                modifier = Modifier.padding(top = 4.dp),
            )
        }
        item {
            StatusCard(
                title = "Notification access",
                ok = listenerOn,
                detail = if (listenerOn) "Listener is on" else "Required to read Discord, WhatsApp, calls…",
                action = if (listenerOn) "Open" else "Enable",
                onClick = onOpenListenerSettings,
            )
        }
        item {
            StatusCard(
                title = "Battery unrestricted",
                ok = batteryOk,
                detail = if (batteryOk) "Samsung won’t kill the listener as quickly" else "Otherwise forwarding dies in the background",
                action = if (batteryOk) "Open" else "Allow",
                onClick = onOpenBatterySettings,
            )
        }
        item {
            Card {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Column(Modifier.weight(1f)) {
                            Text("Forward to TV", style = MaterialTheme.typography.titleMedium)
                            Text("Master switch", color = MaterialTheme.colorScheme.secondary)
                        }
                        Switch(
                            checked = enabled,
                            onCheckedChange = {
                                enabled = it
                                prefs.forwardingEnabled = it
                            },
                        )
                    }
                    OutlinedTextField(
                        value = url,
                        onValueChange = { url = it; prefs.url = it },
                        label = { Text("ntfy URL") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = topic,
                        onValueChange = { topic = it; prefs.topic = it },
                        label = { Text("Topic") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = token,
                        onValueChange = { token = it; prefs.token = it },
                        label = { Text("Token") },
                        singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Text("Expire on server after ${ttl / 60} min", color = MaterialTheme.colorScheme.secondary)
                    Slider(
                        value = ttl.toFloat(),
                        onValueChange = { ttl = it.toInt().coerceIn(60, 3600) },
                        onValueChangeFinished = { prefs.ttlSeconds = ttl },
                        valueRange = 60f..3600f,
                    )
                    Button(
                        onClick = {
                            NtfySender.sendAsync(
                                prefs,
                                ForwardedNotice(
                                    pkg = context.packageName,
                                    app = "ZyzNotify",
                                    title = "Test",
                                    text = "If this hits the TV, the token and topic are good.",
                                ),
                            ) { result ->
                                activity.runOnUiThread {
                                    status = result.fold(
                                        onSuccess = { "Test sent" },
                                        onFailure = { "Test failed: ${it.message}" },
                                    )
                                    tick += 1
                                }
                            }
                        },
                        enabled = url.isNotBlank() && topic.isNotBlank() && token.isNotBlank(),
                    ) {
                        Text("Send test to TV")
                    }
                    if (status.isNotBlank()) {
                        Text(status, color = MaterialTheme.colorScheme.secondary)
                    }
                }
            }
        }
        item {
            Text("Apps", style = MaterialTheme.typography.titleLarge)
            Text(
                "Every installed app is here. Only enabled ones are forwarded.",
                color = MaterialTheme.colorScheme.secondary,
            )
            OutlinedTextField(
                value = search,
                onValueChange = { search = it },
                label = { Text("Search apps") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            )
        }
        if (suggested.isNotEmpty()) {
            item {
                Text("Suggested", style = MaterialTheme.typography.titleMedium)
            }
            items(suggested, key = { "suggested:${it.label}" }) { app ->
                val present = app.packages.filter { it in installed }
                val on = present.any { it in allowed }
                AppToggle(
                    label = app.label,
                    detail = present.joinToString(),
                    checked = on,
                    onCheckedChange = { checked ->
                        val next = allowed.toMutableSet()
                        if (checked) next += present else next -= app.packages.toSet()
                        persistAllowed(next)
                    },
                )
            }
        }
        item {
            Text(
                if (needle.isBlank()) "All apps (${others.size})" else "Matches (${others.size})",
                style = MaterialTheme.typography.titleMedium,
            )
        }
        items(others, key = { it.pkg }) { app ->
            AppToggle(
                label = app.label,
                detail = app.pkg,
                checked = app.pkg in allowed,
                onCheckedChange = { checked ->
                    val next = allowed.toMutableSet()
                    if (checked) next += app.pkg else next -= app.pkg
                    persistAllowed(next)
                },
            )
        }
        item {
            TextButton(onClick = { persistAllowed(AppCatalog.defaultEnabled.intersect(installed)) }) {
                Text("Reset to Discord, WhatsApp, Messages, Messenger, Phone")
            }
        }
    }
}

@Composable
private fun StatusCard(
    title: String,
    ok: Boolean,
    detail: String,
    action: String,
    onClick: () -> Unit,
) {
    Card {
        Row(
            Modifier.padding(16.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Column(Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(if (ok) "Ready · $detail" else detail, color = MaterialTheme.colorScheme.secondary)
            }
            FilledTonalButton(onClick = onClick) { Text(action) }
        }
    }
}

@Composable
private fun AppToggle(
    label: String,
    detail: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Card {
        Row(
            Modifier.padding(horizontal = 16.dp, vertical = 10.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f).padding(end = 12.dp)) {
                Text(label, style = MaterialTheme.typography.titleMedium)
                Text(detail, color = MaterialTheme.colorScheme.secondary, style = MaterialTheme.typography.bodySmall)
            }
            Switch(checked = checked, onCheckedChange = onCheckedChange)
        }
    }
}

private fun SuggestedApp.matches(needle: String): Boolean {
    if (needle.isBlank()) return true
    return label.contains(needle, ignoreCase = true) ||
        packages.any { it.contains(needle, ignoreCase = true) }
}

private fun InstalledApp.matches(needle: String): Boolean {
    if (needle.isBlank()) return true
    return label.contains(needle, ignoreCase = true) || pkg.contains(needle, ignoreCase = true)
}
