# Stage II — PyCA cryptography dependency candidate

**Date:** 2026-11-11  
**Status:** CANDIDATE / NOT OWNER-FROZEN / NO INSTALLATION AUTHORIZED

## 1. Proposed pin

Proposed exact release: `cryptography==50.0.2`.

Target CI wheel for the current CPython 3.12 Linux x86-64 test lane:

- Filename: `cryptography-50.0.2-cp311-abi3-manylinux_2_34_x86_64.whl`
- Compatibility tag: CPython 3.11+ stable ABI; Linux glibc 2.34+ x86-64.
- SHA-256 reported by independently published lockfile records: `9dab55f57c74c3cad24c323bacbbd04be4705ba6eb0d92e920b1fc4837ed5079`.
- Upload date: 2026-09-30.
- PyPI release page lists 50.0.2 as the current release, with release files marked as having provenance. PyPI metadata states Python >=3.9 (excluding 3.9.0/3.9.1).

PyPI source distribution reference:
- `cryptography-50.0.2.tar.gz`
- SHA-256: `7b46165bb56eb4704e2eaaf86f3c940d19154535d9b0ca7d6d590b04060e00d5`.

## 2. Fit to this project

- The current Stage I workflow used CPython 3.12.16; the proposed cp311-abi3 wheel is designed for CPython 3.11+ and therefore is a plausible fit for CPython 3.12.
- The manylinux_2_34 x86-64 wheel requires glibc 2.34 or later. The actual GitHub runner image/glibc must be recorded by the eventual build job before this wheel is frozen.
- No VPS installation is proposed. The package is for an isolated, offline-verification test lane only.
- No private key generation, signing, trust-root bootstrap, policy/anchor state or network runtime behavior is implied.

## 3. Provenance and pinning caveats

- PyPI reports Trusted Publishing and provenance for the 50.0.2 release artifacts. This is an upstream provenance signal, not a complete independent security audit of the package.
- The wheel hash above is currently corroborated by published lockfile records, not yet recomputed from a downloaded wheel in this repository. It MUST be verified against the exact PyPI artifact bytes in the eventual isolated CI supply-chain step before the lock is frozen.
- The sdist hash is reported by the PyPI release page. The source build path is not selected; the proposed target is the prebuilt manylinux wheel.
- Exact transitive dependency closure, installer version, wheel provenance attestation verification, license review, supported runtime matrix and offline installation test remain open.
- Do not use an unpinned `pip install cryptography` or resolve a floating latest version in CI.

## 4. Sources

- PyPI release metadata and supported Python versions: https://pypi.org/project/cryptography/50.0.2/
- PyCA upstream changelog: https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst
- Wheel hash corroboration in published lockfile: https://github.com/virtualenv/virtualenv/blob/main/pylock.toml

**Disposition: 50.0.2 IS A PROPOSED PIN ONLY. No dependency file, lockfile, CI, runtime or VPS was changed.**
