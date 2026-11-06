#!/usr/bin/env bash
# Verify a GitHub artifact attestation using only local evidence and a pinned Sigstore root.
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "usage: verify_offline.sh ARTIFACT BUNDLE TRUSTED_ROOT SOURCE_SHA SOURCE_REF" >&2
  exit 2
fi

artifact="$1"
bundle="$2"
trusted_root="$3"
source_sha="$4"
source_ref="$5"
repo="${GITHUB_REPOSITORY:-}"
if [[ -z "$repo" ]]; then
  echo "GITHUB_REPOSITORY must identify the attested repository" >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

python - "$trusted_root" <<'PY'
import sys
from pathlib import Path
from synthetic_evidence.trust_anchor import verify_trusted_root
from synthetic_evidence.trusted_root_pin import TRUSTED_ROOT_SHA256

digest = verify_trusted_root(Path(sys.argv[1]).read_bytes(), TRUSTED_ROOT_SHA256)
print(f"TRUSTED_ROOT_PIN_VERIFICATION=PASS sha256={digest}", file=sys.stderr)
PY

gh attestation verify "$artifact" \
  --bundle "$bundle" \
  --custom-trusted-root "$trusted_root" \
  --repo "$repo" \
  --signer-workflow "$repo/.github/workflows/p1-8-synthetic-evidence.yml" \
  --source-digest "$source_sha" \
  --source-ref "$source_ref" \
  --cert-oidc-issuer "https://token.actions.githubusercontent.com" \
  --deny-self-hosted-runners \
  --format json
