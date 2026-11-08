# T0 Candle API — Domain and DNS Selection Criteria

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Baseline branch HEAD: `e653a9e20d6a65b7c992c4795e9e4f8aae98a3e4`
- Status: **DECISION CRITERIA ONLY — NO DOMAIN PURCHASE OR DNS CHANGE AUTHORIZED**

## 1. Decision objective

Choose a stable, low-maintenance hostname for the T0 Candle API without introducing unnecessary recurring cost or coupling the canonical data service to a domain vendor.

The hostname is only an HTTPS identity for the read-only T0 Candle Contract v1. It is not a public product, dashboard, or general-purpose website.

## 2. Preferred ownership model

Evaluate in this order:

1. **Use a subdomain of an existing domain already controlled by the owner**, if its renewal cost, account security, DNS control, and long-term ownership are acceptable. This is normally the lowest incremental-cost option.
2. If no suitable existing domain is available, compare registration of a new domain using total first-year and renewal cost, not promotional introductory price.
3. Do not use a disposable/free hostname or dynamic-DNS name as the production identity for the T0 API. A temporary private test hostname is not an approved substitute for the production TLS identity.

A dedicated hostname should be used, for example `t0-api.<owner-controlled-domain>`. This is a naming pattern only; no actual hostname is selected.

## 3. Registrar requirements

A candidate registrar must provide:

- Clear, published renewal pricing and transfer-out terms.
- Account MFA and recovery controls.
- Domain lock / transfer protection where supported.
- Reliable ownership and renewal notifications.
- Access to the domain's authoritative DNS settings.
- No requirement to publish personal contact details beyond applicable registry rules; privacy protection should be evaluated where legally and technically available.
- A documented recovery path if the registrar account is inaccessible.

Reject a candidate if ownership recovery is unclear, renewal pricing is opaque, or the owner cannot independently export/transfer the domain.

## 4. DNS provider requirements

Registrar and authoritative DNS hosting may be the same provider or separate providers. The DNS provider must support:

- Authoritative A records and, only when deliberately configured, AAAA records.
- CAA records to constrain certificate authorities.
- DNSSEC support where the registrar/zone configuration can be operated correctly.
- Short TTL during a controlled cutover and the ability to change it later.
- MFA and scoped API tokens; any future automation token must be restricted to the required zone and record operations.
- Audit history or change visibility and a documented account recovery process.

Do not create an AAAA record unless IPv6 routing, cloud firewall, host firewall, proxy listener, and external reachability are all verified. A broken AAAA record can cause intermittent client failures.

For initial deployment, prefer DNS-only resolution directly to the approved VPS address. Do not add CDN proxying, WAF transformations, or third-party HTTP proxy behavior until the T2 client's TLS, authorization-header handling, caching, response-size, and timeout behavior have been independently validated.

## 5. Cost and reliability comparison

Compare candidates using this scorecard before purchase:

| Criterion | Required evidence | Decision rule |
|---|---|---|
| Existing domain availability | Owner confirms domain and DNS control | Prefer reuse if secure and stable |
| First-year cost | Checkout price including mandatory fees | Record actual total |
| Renewal cost | Published standard renewal price | Use renewal price for long-term comparison |
| Transfer cost/lock-in | Transfer policy and authorization-code process | Reject opaque or restrictive terms |
| DNS reliability | Provider status history and service documentation | Must be suitable for a stable API hostname |
| DNS controls | A/AAAA, CAA, DNSSEC, TTL support | Required capabilities must be present |
| Account security | MFA, recovery, scoped API tokens | MFA and recoverable ownership required |
| Privacy | Applicable registration privacy options | Prefer minimized public personal data |
| Operational independence | Export/transfer and independent DNS control | Avoid unnecessary vendor lock-in |

Do not rank providers based only on marketing claims or introductory discounts. No registrar or DNS provider is selected by this document.

## 6. Naming rules

- Use a dedicated, descriptive subdomain such as `t0-api.<domain>`.
- Keep the hostname stable even if the VPS provider or IP changes later.
- Do not encode a VPS IP, region, provider name, or temporary instance label in the hostname.
- Do not reuse a hostname for unrelated services.
- Avoid publishing internal environment names, usernames, or implementation details in DNS labels.

## 7. D1 approval checklist

D1 may begin only after the owner explicitly confirms:

- [ ] Exact fully qualified hostname.
- [ ] Existing domain reuse or new domain registration decision.
- [ ] Registrar and authoritative DNS provider.
- [ ] Account ownership and MFA/recovery are controlled by the owner.
- [ ] Domain purchase budget and recurring renewal budget, if a new registration is needed.
- [ ] Exact VPS public IPv4 address, confirmed by the operator at deployment time.
- [ ] Whether IPv6 is intentionally supported; otherwise no AAAA record.
- [ ] Explicit approval for the proposed DNS records and change window.

This checklist does not authorize domain purchase, DNS changes, or disclosure of the VPS public address.

## 8. Current status and constraints

| Item | Status |
|---|---|
| Domain/subdomain selected | **NOT SELECTED** |
| Existing owner-controlled domain confirmed | NOT PROVIDED |
| Registrar selected | NOT SELECTED |
| DNS provider selected | NOT SELECTED |
| VPS public address confirmed for DNS | NOT PROVIDED |
| DNS records | NOT CREATED |
| TLS certificate | NOT ISSUED |
| HTTPS reverse proxy | NOT DEPLOYED |
| T0 API service | NOT ESTABLISHED |
| Live endpoint probe | NOT RUN |
| T2 runtime | NOT ACTIVATED |

No domain purchase, registrar login, DNS lookup/change, VPS inspection, firewall change, proxy installation, API startup, Feeder/database modification, secret handling, or T2 activation is included in this increment.

## 9. Next action

Owner identifies whether an existing domain is already available for reuse. If yes, confirm only the domain name and that DNS control exists; do not share account credentials or API tokens. If no, compare candidate registrars using the scorecard above and obtain explicit approval before any purchase.

Until D1 is approved, remain at D0 design. All later stages (D2 deployment plan, D3 VPS deployment, D4 live probe, D5 T2 connection) require separate approvals.
