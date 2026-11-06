"""Policy checks for GitHub CLI-verified Sigstore artifact attestations.

Cryptographic signature, trusted-root, repository/workflow identity and source
ref checks are performed by gh attestation verify before this JSON is read.
This module enforces the additional subject-digest and transparency-timestamp
policy on the CLI's successful verification output.
"""
import re

_SHA64 = re.compile(r"^[0-9a-f]{64}$")


def verify_attestation_result(result, *, expected_subject_sha256):
    if not isinstance(expected_subject_sha256, str) or not _SHA64.fullmatch(expected_subject_sha256):
        raise ValueError("invalid expected subject digest")
    if not isinstance(result, list) or not result:
        raise ValueError("no verified attestations")

    saw_statement = False
    saw_predicate = False
    saw_certificate = False
    saw_timestamp = False
    saw_subject = False

    for item in result:
        if not isinstance(item, dict):
            continue
        verification = item.get("verificationResult")
        if not isinstance(verification, dict):
            continue
        statement = verification.get("statement")
        if not isinstance(statement, dict):
            continue
        saw_statement = True
        if statement.get("predicateType") != "https://slsa.dev/provenance/v1":
            continue
        saw_predicate = True

        signature = verification.get("signature")
        certificate = signature.get("certificate") if isinstance(signature, dict) else None
        if not isinstance(certificate, dict) or not certificate:
            continue
        saw_certificate = True

        timestamps = verification.get("verifiedTimestamps")
        if not isinstance(timestamps, list) or not timestamps:
            continue
        saw_timestamp = True

        subjects = statement.get("subject")
        if not isinstance(subjects, list):
            continue
        for subject in subjects:
            digest = subject.get("digest") if isinstance(subject, dict) else None
            if isinstance(digest, dict) and digest.get("sha256") == expected_subject_sha256:
                saw_subject = True
                return True

    if not saw_statement:
        raise ValueError("verification result has no statement")
    if not saw_predicate:
        raise ValueError("unsupported predicate type")
    if not saw_certificate:
        raise ValueError("verification result has no signing certificate")
    if not saw_timestamp:
        raise ValueError("missing verified transparency timestamp")
    if not saw_subject:
        raise ValueError("subject digest mismatch")
    raise ValueError("attestation policy verification failed")
