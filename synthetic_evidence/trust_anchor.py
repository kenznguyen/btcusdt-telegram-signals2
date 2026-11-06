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
    matched = False
    for item in result:
        if not isinstance(item, dict):
            continue
        verification = item.get("verificationResult")
        if not isinstance(verification, dict):
            continue
        statement = verification.get("statement")
        if not isinstance(statement, dict):
            continue
        if statement.get("predicateType") != "https://slsa.dev/provenance/v1":
            continue
        signature = verification.get("signature")
        certificate = signature.get("certificate") if isinstance(signature, dict) else None
        timestamps = verification.get("verifiedTimestamps")
        if not isinstance(certificate, dict) or not certificate:
            continue
        if not isinstance(timestamps, list) or not timestamps:
            continue
        subjects = statement.get("subject")
        if not isinstance(subjects, list):
            continue
        for subject in subjects:
            digest = subject.get("digest") if isinstance(subject, dict) else None
            if isinstance(digest, dict) and digest.get("sha256") == expected_subject_sha256:
                matched = True
                break
        if matched:
            break
    if not matched:
        raise ValueError("no attestation matches subject digest, SLSA predicate, certificate and transparency timestamp")
    return True
