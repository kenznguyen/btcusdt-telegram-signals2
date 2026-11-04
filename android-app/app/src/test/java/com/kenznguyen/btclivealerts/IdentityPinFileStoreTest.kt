package com.kenznguyen.btclivealerts

import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.assertFalse
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class IdentityPinFileStoreTest {
    @get:Rule
    val temporaryFolder = TemporaryFolder()

    private val pin = CanonicalDatabaseIdentityPin(
        CanonicalDatabaseRoleId.canonicalT0(),
        CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440000"),
        IdentityPinLifecycleState.ACTIVE,
    )

    @Test
    fun missingPinIsReportedAndNeverCreatedByRead() {
        val directory = temporaryFolder.newFolder().toPath()
        val store = IdentityPinFileStore(directory)
        assertEquals(IdentityPinParseResult.Missing, store.read())
        assertFalse(Files.exists(directory.resolve(IdentityPinFileStore.FILE_NAME)))
    }

    @Test
    fun atomicWriteCanBeReadBackAcrossStoreInstances() {
        val directory = temporaryFolder.newFolder().toPath()
        IdentityPinFileStore(directory).writeAtomic(pin)
        assertEquals(IdentityPinParseResult.Valid(pin), IdentityPinFileStore(directory).read())
    }

    @Test
    fun malformedOrUnsupportedPinIsPreservedAndNeverRepaired() {
        val directory = temporaryFolder.newFolder().toPath()
        val target = directory.resolve(IdentityPinFileStore.FILE_NAME)
        Files.write(target, "format_version=2\n".toByteArray(Charsets.UTF_8))
        assertEquals(IdentityPinParseResult.UnsupportedVersion(2), IdentityPinFileStore(directory).read())
        assertEquals("format_version=2\n", String(Files.readAllBytes(target), Charsets.UTF_8))
    }

    @Test
    fun failedWriteToMissingDirectoryDoesNotCreateDirectoryOrPin() {
        val parent = temporaryFolder.newFolder().toPath()
        val missing = parent.resolve("not-created")
        val store = IdentityPinFileStore(missing)
        try {
            store.writeAtomic(pin)
            throw AssertionError("write should fail when its parent directory is absent")
        } catch (_: java.io.IOException) {
            assertFalse(Files.exists(missing))
        }
    }

    @Test
    fun rejectsSymbolicLinkTargetWithoutFollowingIt() {
        val directory = temporaryFolder.newFolder().toPath()
        val outside = temporaryFolder.newFile().toPath()
        Files.write(outside, "untouched".toByteArray(Charsets.UTF_8))
        Files.createSymbolicLink(directory.resolve(IdentityPinFileStore.FILE_NAME), outside)
        try {
            IdentityPinFileStore(directory).writeAtomic(pin)
            throw AssertionError("symlink target must be rejected")
        } catch (_: java.io.IOException) {
            assertEquals("untouched", String(Files.readAllBytes(outside), Charsets.UTF_8))
        }
    }
}
