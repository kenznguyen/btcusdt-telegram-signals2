# Archived GitHub Actions definitions

These YAML files are historical references, outside `.github/workflows` and not
executed by GitHub. Active build/test and manual task definitions now live in
[`codemagic.yaml`](../../../codemagic.yaml). See
[`docs/CODEMAGIC_SETUP.md`](../../../docs/CODEMAGIC_SETUP.md) before deployment.

GitHub stores source, branches and PRs. Codemagic runs the jobs and retains build
artifacts. Moving these files does not configure the Codemagic account, transfer
secrets, recover scanner state or deploy the Render bridge automatically.
