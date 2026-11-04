package com.kenznguyen.btclivealerts

import java.io.IOException
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.nio.file.StandardOpenOption

/**
 * Durable file adapter for the identity pin.
 *
 * The caller supplies an already-existing private directory (production wiring is deliberately
 * out of scope). Reads never create or repair data. Writes use a same-directory temporary file,
 * force file contents, then require an atomic replacement; unsupported atomic moves fail closed.
 */
class IdentityPinFileStore(private val directory: Path) {
    private val target: Path = directory.resolve(FILE_NAME)

    fun read(): IdentityPinParseResult {
        validateDirectory()
        if (!Files.exists(target, LinkOption.NOFOLLOW_LINKS)) return IdentityPinParseResult.Missing
        if (Files.isSymbolicLink(target) ||
            !Files.isRegularFile(target, LinkOption.NOFOLLOW_LINKS)
        ) {
            throw IOException("Identity pin target is not a regular file")
        }
        val size = Files.size(target)
        if (size > MAX_PIN_BYTES) return IdentityPinParseResult.Malformed
        val bytes = Files.readAllBytes(target)
        val decoded = try {
            StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(bytes))
                .toString()
        } catch (_: Exception) {
            return IdentityPinParseResult.Malformed
        }
        return CanonicalIdentityPinCodec.parse(decoded)
    }

    @Throws(IOException::class)
    fun writeAtomic(pin: CanonicalDatabaseIdentityPin) {
        validateDirectory()
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS) && Files.isSymbolicLink(target)) {
            throw IOException("Refusing symbolic-link identity pin target")
        }
        if (Files.exists(target, LinkOption.NOFOLLOW_LINKS) &&
            !Files.isRegularFile(target, LinkOption.NOFOLLOW_LINKS)
        ) {
            throw IOException("Identity pin target is not a regular file")
        }

        val bytes = CanonicalIdentityPinCodec.encode(pin).toByteArray(StandardCharsets.UTF_8)
        require(bytes.size <= MAX_PIN_BYTES) { "Identity pin exceeds size limit" }
        val temporary = Files.createTempFile(directory, TEMP_PREFIX, TEMP_SUFFIX)
        try {
            FileChannel.open(temporary, StandardOpenOption.WRITE).use { channel ->
                var buffer = ByteBuffer.wrap(bytes)
                while (buffer.hasRemaining()) channel.write(buffer)
                channel.force(true)
            }
            try {
                Files.move(
                    temporary,
                    target,
                    StandardCopyOption.ATOMIC_MOVE,
                    StandardCopyOption.REPLACE_EXISTING,
                )
            } catch (error: AtomicMoveNotSupportedException) {
                throw IOException("Atomic identity pin replacement is unavailable", error)
            }
        } finally {
            Files.deleteIfExists(temporary)
        }
    }

    private fun validateDirectory() {
        if (Files.isSymbolicLink(directory) ||
            !Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)
        ) {
            throw IOException("Identity pin directory must already exist and not be a symlink")
        }
    }

    companion object {
        const val FILE_NAME = "canonical-database.identity-pin"
        private const val MAX_PIN_BYTES = 4096
        private const val TEMP_PREFIX = ".identity-pin-"
        private const val TEMP_SUFFIX = ".tmp"
    }
}
