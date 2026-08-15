package dev.mniz.zyznotify

import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.concurrent.Executors

data class ForwardedNotice(
    val pkg: String,
    val app: String,
    val title: String,
    val text: String,
    val kind: String = "message",
)

object NtfySender {
    private val io = Executors.newSingleThreadExecutor()

    fun sendAsync(prefs: Prefs, notice: ForwardedNotice, onDone: (Result<Unit>) -> Unit = {}) {
        io.execute {
            val result = runCatching { send(prefs, notice) }
            prefs.lastStatus = result.fold(
                onSuccess = { "Sent ${notice.app}: ${notice.title.ifBlank { notice.text }.take(48)}" },
                onFailure = { "Send failed: ${it.message ?: it.javaClass.simpleName}" },
            )
            onDone(result)
        }
    }

    fun send(prefs: Prefs, notice: ForwardedNotice) {
        val url = prefs.url
        val topic = prefs.topic
        val token = prefs.token
        require(url.isNotBlank()) { "ntfy URL missing" }
        require(topic.isNotBlank()) { "topic missing" }
        require(token.isNotBlank()) { "token missing" }

        val body = JSONObject()
            .put("v", 1)
            .put("pkg", notice.pkg)
            .put("app", notice.app)
            .put("title", notice.title)
            .put("text", notice.text)
            .put("kind", notice.kind)
            .toString()

        val heading = listOf(notice.app, notice.title).filter { it.isNotBlank() }.joinToString(": ")
        val endpoint = URL("$url/${topic.trim('/')}")
        val conn = (endpoint.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 10_000
            readTimeout = 10_000
            doOutput = true
            setRequestProperty("Authorization", "Bearer $token")
            setRequestProperty("Title", heading.take(120).ifBlank { notice.app })
            setRequestProperty("Tags", notice.pkg)
            setRequestProperty("TTL", prefs.ttlSeconds.toString())
            setRequestProperty("Content-Type", "text/plain; charset=utf-8")
        }
        try {
            OutputStreamWriter(conn.outputStream, StandardCharsets.UTF_8).use { it.write(body) }
            val code = conn.responseCode
            if (code !in 200..299) {
                val err = (conn.errorStream ?: conn.inputStream)?.bufferedReader()?.readText().orEmpty()
                throw IllegalStateException("HTTP $code ${err.take(180)}")
            }
        } finally {
            conn.disconnect()
        }
    }
}
