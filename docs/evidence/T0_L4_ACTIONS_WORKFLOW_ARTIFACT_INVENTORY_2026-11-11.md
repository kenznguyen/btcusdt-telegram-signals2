# T0 L4-Minimum — Workflow Run and Artifact Inventory

Date: 2026-11-11
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Workflow: `.github/workflows/t0-l4-minimum-validation.yml`
Workflow ID: `413351263`
Allowlist blob: `d481ca0baaca9605cfda1e3ebb79e423b17ac876`
Inventory method: GitHub Actions repository workflow-run listing, ordered newest-first, plus per-run artifact metadata endpoint.

## 1. Discovery boundary and completeness

Repository Actions API reported 4,442 total workflow runs. Page 1 returned 100 runs covering `2026-11-10T07:37:23Z` through `2026-11-10T22:37:35Z`. It contained 32 runs for workflow ID `413351263`. Page 2 covered `2026-11-08T07:23:51Z` through `2026-11-10T07:23:51Z` and contained zero runs for workflow ID `413351263`. Because page 2's newest run predates the earliest target-workflow run, and the repository list is reverse chronological, the observed 32-run set is exhaustive for this workflow at the time of query. This conclusion is limited to the repository Actions API result and current accessible history; it is not an inventory of every workflow in the repository.

## 2. Workflow run inventory

| Run ID | Exact source SHA | Conclusion | Created UTC | Artifacts |
|---:|---|---|---|---:|
| 42916283963 | `946e2b0d1da4ec35046ef3b37f4408f438dff27f` | SUCCESS | 22:37:35 | 3 |
| 42915451341 | `258c971d06baa9818980ebcf3d1db046b412beb7` | SUCCESS | 22:32:10 | 3 |
| 42915177432 | `0e496d251af825b0ba7ba7fbbc1837578aa210f3` | SUCCESS | 22:30:27 | 3 |
| 42914799884 | `9442386151f3ff7ce7c699e00e617b8f4033aa3c` | SUCCESS | 22:27:57 | 3 |
| 42914214815 | `da0dc7bce6d3130a718a7ff7a504d8b4c06451cb` | SUCCESS | 22:24:08 | 3 |
| 42914049188 | `b2abc8e8014b5ae0c48f7c67736712bf1a7cd9db` | SUCCESS | 22:23:03 | 3 |
| 42913556801 | `97b01031778b68d791d9d43543cfd445a11d49aa` | SUCCESS | 22:19:57 | 3 |
| 42913380578 | `7d6cbb10f903625f2051db7d5322e0648ae7727d` | SUCCESS | 22:18:48 | 3 |
| 42913229506 | `bf2483a61714356d6fce45896ee25b8ea5a3abd1` | FAILURE | 22:17:51 | 2 |
| 42912784110 | `57898ea1dd0d812f2aa39575b90d957cbbb6d2d9` | SUCCESS | 22:15:02 | 3 |
| 42912485814 | `b584cc218833bfa6f5d0345b55639c0448961a8e` | FAILURE | 22:13:09 | 2 |
| 42838428048 | `640911d1c242c483e327b955293487517f50e29a` | SUCCESS | 14:51:55 | 2 |
| 42838231181 | `fa6d317cd43d4ce4bc1091cdd50c2d5f0e8c62b7` | SUCCESS | 14:50:43 | 2 |
| 42838019140 | `42b97bcd252537a75119b93b5eb6f55b56e98e11` | FAILURE | 14:49:30 | 1 |
| 42837579509 | `5c9941112f24edb213c129a5962187461d8f4308` | SUCCESS | 14:46:58 | 2 |
| 42836600413 | `f02ab102bd75beafe45eeae9203b3a126c8815d5` | SUCCESS | 14:41:14 | 2 |
| 42836094887 | `b3a975e151241ba5d5116f49a8d00a056adf9fa4` | SUCCESS | 14:38:11 | 1 |
| 42835910100 | `e64ab3a2623689dc42f112205e5d76054fd00508` | FAILURE | 14:37:06 | 1 |
| 42835562035 | `66df47d4df49899f709e92a799082a9e6feb63aa` | FAILURE | 14:35:05 | 1 |
| 42834966105 | `db01cbe7750b75fcaafd4576d646d04c5b029c4b` | SUCCESS | 14:31:37 | 2 |
| 42834714404 | `c6e42de3bcb78f9b57790747aa536a830dd39319` | FAILURE | 14:30:11 | 1 |
| 42833692280 | `d6550315521c3d0660a57afbe1c2e4bbdd3dff65` | SUCCESS | 14:24:04 | 2 |
| 42833036316 | `90822744621882b2d9d13509eaa2d73eb32df7b9` | SUCCESS | 14:20:12 | 2 |
| 42832488512 | `e4f5ede7ffa5c555ecffc3e19ef7460c9568987d` | FAILURE | 14:16:56 | 1 |
| 42832269030 | `acb1defbe611ef1fad54d29a6f197ae8de58d8c1` | FAILURE | 14:15:37 | 1 |
| 42832023416 | `7318a43d35e0a31f1ea77cda9080258d02a65442` | FAILURE | 14:14:10 | 1 |
| 42831240089 | `27aea002a3f404792d4c1a3dc56eff77c2163840` | SUCCESS | 14:09:24 | 1 |
| 42830696970 | `5dc935aa4663bf3b2ccf6075b704189896e45e63` | SUCCESS | 14:06:03 | 1 |
| 42830499889 | `5b24397773eb957a7efeb0694773b1c0ff446c06` | FAILURE | 14:04:54 | 1 |
| 42829518609 | `0c00055b816e96378ada614236cc05b79e9ef3f5` | SUCCESS | 13:58:50 | 1 |
| 42829483832 | `d60be930c5b35254fd336de4777ce8058187ed01` | SUCCESS | 13:58:37 | 1 |
| 42829414892 | `ed82a1cf7bc12429ccc3ddb3c0ab6896f3f854e7` | FAILURE | 13:58:10 | 1 |

All 32 runs are on `feature/t0-centralized-data-feeder-p1-20261101`, event `push`. Aggregate: 21 SUCCESS, 11 FAILURE.

## 3. Artifact inventory by output class

All entries below are generated outputs of the L4 Minimum workflow. The GitHub API digest is the upload-time ZIP digest; it is not an independent payload readback unless explicitly stated in a separate verification record.

### 3.1 Lineage bundles — 32

| Run ID | Artifact ID | Size | Expiry UTC | GitHub ZIP SHA-256 |
|---:|---:|---:|---|---|
| 42916283963 | 13810400590 | 1,151 | 2026-11-17 22:37:35 | `3a77cdcd09328e5bfc54050110ddf7d2a2793d169f602a0f64f5ccc1b250f158` |
| 42915451341 | 13809780354 | 1,151 | 2026-11-17 22:32:10 | `9377722a00dcabe80dbb9749f86e131ffd0ac25ce3662775941591d70e7fcf42` |
| 42915177432 | 13809830236 | 1,151 | 2026-11-17 22:30:27 | `e2bbc948f67e0698214888fa2968b066103267a138fd58b9fd755173af84ea9e` |
| 42914799884 | 13807883936 | 1,152 | 2026-11-17 22:27:57 | `21f3d7ac0bd9c784e097f1d2e5f20bced382c11cea6f04f1e7f19f06081006aa` |
| 42914214815 | 13807869163 | 1,152 | 2026-11-17 22:24:09 | `a85b42d823e962e8bfce994044cbc22006a16ec6605a5e5996531e3f0f3f6772` |
| 42914049188 | 13807734153 | 1,152 | 2026-11-17 22:23:03 | `6536d1a57f306f275c4bcba59d763d54867916dc3c8598457a6fe5e421dac2aa` |
| 42913556801 | 13807479120 | 1,151 | 2026-11-17 22:19:57 | `14d7e3a3721728e4dc43f3a641b04726ed07b8ac77df2f7a57b3db66838dfec1` |
| 42913380578 | 13808342278 | 1,151 | 2026-11-17 22:18:48 | `f0758bacb52e1243d4e93e2a0f8c741be83b95e9989f140c05e91a2c4875d8c6` |
| 42913229506 | 13807278659 | 1,151 | 2026-11-17 22:17:51 | `f2f8ebda2e5c98cfbd63a8a10618c8fa2fc89fa0436412915d53c1d5a30a54fa` |
| 42912784110 | 13807977459 | 1,152 | 2026-11-17 22:15:02 | `fe6df73a03c98ec79c3bb84f9a23a331c6bbb54c378822eff2de289107c977e8` |
| 42912485814 | 13806724879 | 1,152 | 2026-11-17 22:13:09 | `c83b8ce84a584340973110b340fe7049cabf8996fa8ab2d6e488eea7a0d0da73` |
| 42838428048 | 13773424397 | 1,151 | 2026-11-17 14:51:55 | `8354ce82574c09f2cfb36792ed5d0628100fdb7e5dade6a79375e423fb8eb87a` |
| 42838231181 | 13774367642 | 1,151 | 2026-11-17 14:50:44 | `565dfca4b34cdb967ba49e475acfa3a0824f26df9928aaa9879651f2297f7c91` |
| 42838019140 | 13775075609 | 1,218 | 2026-11-17 14:49:30 | `f899d35ace2cde4a73706484a57668be16980560d94b18b8ced6a54e2c27afc5` |
| 42837579509 | 13772649665 | 1,151 | 2026-11-17 14:46:58 | `9c4c7fabdf076abb1f719d32e28edf47b2bfaec91fa5528531d178c91a51bfc4` |
| 42836600413 | 13774805871 | 1,152 | 2026-11-17 14:41:14 | `04724a6fd3013db3c075328da90b9710c6fa93afa499199f8a67727981714910` |
| 42836094887 | 13774031418 | 1,151 | 2026-11-17 14:38:12 | `801bbc22e1979b3e5260371a22db305d37ddd2bc6837aae3c00c99d60595abcf` |
| 42835910100 | 13773856706 | 1,218 | 2026-11-17 14:37:06 | `cb9f75037327a55348a7f96cc2ad95b16b08da48477a887841e883bea77d1152` |
| 42835562035 | 13774190649 | 1,189 | 2026-11-17 14:35:05 | `54a4c9d7086dde62c579627cda54687f38898d8382039d191840fd94dc98a135` |
| 42834966105 | 13772852186 | 1,124 | 2026-11-17 14:31:38 | `242705761a816a60c816ca485b1ff28570318738fae56b28bf02093815881c12` |
| 42834714404 | 13773266040 | 1,124 | 2026-11-17 14:30:11 | `273960b478390c3a556c1cc711c4390739cfb4af8b87469170a9f84b8fd7e99c` |
| 42833692280 | 13772721991 | 1,123 | 2026-11-17 14:24:04 | `f577a43665f971853ce3dc58c623f3aa76d110d6965d78011d68d558d2fdbc14` |
| 42833036316 | 13771089305 | 1,124 | 2026-11-17 14:20:12 | `7b543edb61a07fefabfd5b03b451571afeadc6b471852de433dd195e35b2f363` |
| 42832488512 | 13771473430 | 1,124 | 2026-11-17 14:16:56 | `74f556f4fecf1c961cafed5bc93b052305b5e409da0efa85a789f8413109c830` |
| 42832269030 | 13771682934 | 1,124 | 2026-11-17 14:15:37 | `2bd5070bdc84ff10db559e2b65cb4619f4d193d8ba3e4771a02d0e4beff485da` |
| 42832023416 | 13771417968 | 1,126 | 2026-11-17 14:14:10 | `2d80e758d9644eb79fd54c54b792c22a5eb7203935f967071ce4c2929bca75ab` |
| 42831240089 | 13771662067 | 1,125 | 2026-11-17 14:09:25 | `50991097fb0febf8f38398c656c6edf600f8a079bccd2dbf23a36873931bba68` |
| 42830696970 | 13771616562 | 1,124 | 2026-11-17 14:06:04 | `e71871a8872a78d18b3092c087c0de3394d2fe77bb84d732219ed976fac5690e` |
| 42830499889 | 13772080387 | 1,191 | 2026-11-17 14:04:54 | `077f19676b3bb75ce665ce660697622cb452758b7f4e900e5ed9282bed914275` |
| 42829518609 | 13769829104 | 1,010 | 2026-11-17 13:58:51 | `d54dac06554901e6edec95db66608807fc3aea824d88a277b35a41f9db7fb9d4` |
| 42829483832 | 13770317206 | 1,010 | 2026-11-17 13:58:37 | `a176c0a75595571a0ef77ca557318041ffe5d4afb47a102ead691d5d6503d75f` |
| 42829414892 | 13770158775 | 6,002 | 2026-11-17 13:58:10 | `707dabe90a3050eb81fc9c43e3452dc0e87b1b12853fde54ad9ae70122d978c9` |

### 3.2 Manifest bundles — 18

| Run ID | Artifact ID | Size | Expiry UTC | GitHub ZIP SHA-256 |
|---:|---:|---:|---|---|
| 42916283963 | 13809057870 | 3,037 | 2026-11-17 22:37:35 | `360554820e48d6a0fbe9d772e75fa37bc6582c0728a112217f9a6e4ab8caa9f0` |
| 42915451341 | 13809910243 | 3,037 | 2026-11-17 22:32:10 | `3914efd3be41a8c92580835826f5c472b752d58a38d2fdaab123dd15e8bc19ef` |
| 42915177432 | 13809460570 | 3,040 | 2026-11-17 22:30:27 | `d4b9d2db86ebe8b3f9508fc352ec4172e2e7ac86e7b46e09f257682a6db7f2b3` |
| 42914799884 | 13809042009 | 3,038 | 2026-11-17 22:27:57 | `5fef6eb79efde8de9734716a997c57b83cccd57e3e7c7c76cef217ac0bc1fa60` |
| 42914214815 | 13808956100 | 3,037 | 2026-11-17 22:24:09 | `73aac8f5688dc7ce362cd0932df1950920b38be0612adde9df80aeebcd60f889` |
| 42914049188 | 13808093579 | 3,036 | 2026-11-17 22:23:03 | `4e610534835b0e6fd6a5ae2a2b892c041a36eb92581f75affc62e47c4f109b26` |
| 42913556801 | 13807163772 | 3,038 | 2026-11-17 22:19:57 | `d4899c0935b386381623c7150e8c3109c65a60a8e7701fb3b663e2ddbc0d7ec3` |
| 42913380578 | 13809050350 | 3,038 | 2026-11-17 22:18:48 | `a5f3dd50e26a8bf719411806c61181401232b94ba2940f133e552be83247a3b1` |
| 42913229506 | 13807013792 | 3,039 | 2026-11-17 22:17:51 | `cb1f51fda1b37e8d07b662422b503ad7a5de841aa602bc983ada66f977209797` |
| 42912784110 | 13807163151 | 3,038 | 2026-11-17 22:15:02 | `56c239dd8cf27f81ed8e7cd361db2bfc1a43eedd2ea1c5082164eba48b083731` |
| 42912485814 | 13806324895 | 3,037 | 2026-11-17 22:13:09 | `82730745a218c96b4cbf8efed1da01bca814e99e29dfb414379cf66592689ebb` |
| 42838428048 | 13773544544 | 3,038 | 2026-11-17 14:51:55 | `7f746a0bef3ae5892c97a048e2f87ddcfd14de9587e609e12f2c97169b4c9d75` |
| 42838231181 | 13773284504 | 3,036 | 2026-11-17 14:50:44 | `add93d2d2bf18ee4f66338a28b4a6c6f98dfa15ac224539fed46d947fcff5609` |
| 42837579509 | 13774501896 | 3,038 | 2026-11-17 14:46:58 | `6f121108e6e3f98b84327251bbc965c9d6a9a849f40b2bba6d6efb8b4eff88ba` |
| 42836600413 | 13773777447 | 2,881 | 2026-11-17 14:41:14 | `3c072dd8a4599de9c4d683efcc1b8e72687938f61f9cc55276ec8b8224b5ab62` |
| 42834966105 | 13772792245 | 2,877 | 2026-11-17 14:31:38 | `a361eae206bffc312e1e1c04cd86aa9f9b75c8eb748900b6f663955efa08e9e4` |
| 42833692280 | 13773015826 | 1,109 | 2026-11-17 14:24:04 | `db7b5723020473e84af69314552b69a81b46c1144e9716e5d6c8e5a33451a387` |
| 42833036316 | 13771294248 | 1,110 | 2026-11-17 14:20:12 | `451afff6d551758a2eacf8bd4e41fffd9ffcf2be4da8c7b2c4357090931cee48` |

### 3.3 Repository-file inventory bundles — 9

| Run ID | Artifact ID | Size | Expiry UTC | GitHub ZIP SHA-256 |
|---:|---:|---:|---|---|
| 42916283963 | 13809381785 | 4,490 | 2026-11-17 22:37:35 | `eb3c2adb7b6ee87bc5cadd913439e201e105c88c9d710f34605ac9cea882a884` |
| 42915451341 | 13810135011 | 4,489 | 2026-11-17 22:32:10 | `76642680304c7c35ae9daf3f28e4e0f80e615036001e708a0d5223afda5f6926` |
| 42915177432 | 13809286004 | 4,489 | 2026-11-17 22:30:27 | `0035ac3c264efa094307b74349797711488d1e1b01b721ee3ede2bb737de400e` |
| 42914799884 | 13807289589 | 4,477 | 2026-11-17 22:27:57 | `40ec49a9ac0e0f3caa2883c6808cdf150151a0586f46b41901a37b4377fdf6f3` |
| 42914214815 | 13807169340 | 4,101 | 2026-11-17 22:24:09 | `0bb9a774e3b9fc6718feb6e636d1f43183623dde7b69f3736c41954b655ab3bc` |
| 42914049188 | 13806969533 | 4,100 | 2026-11-17 22:23:03 | `0b7b5588330d4070e13db361ff28931b86e4a08584b7ba9e65f2e1bb1fe6fb5a` |
| 42913556801 | 13807773179 | 3,748 | 2026-11-17 22:19:57 | `efe18625c23c099917e935f7ae5fa09bd120418f3f439cf7cf371d4af494475c` |
| 42913380578 | 13807208514 | 3,750 | 2026-11-17 22:18:48 | `f77ed0a0480134e5f7d9f386e900acc6547177033130b35ff0e1ab6cfd5cc3f6` |
| 42912784110 | 13808276963 | 3,271 | 2026-11-17 22:15:02 | `b9635c842ca3df2c1f8e19d7f4403e6c01c5be94db91092cf68747e877d78f59` |

## 4. Classification and source allowlist disposition

The 59 records are all generated by this L4 workflow:
- 32 lineage bundles: CI lineage-test outputs.
- 18 manifest bundles: current-run manifest collector outputs.
- 9 repository inventory bundles: exact-commit repository inventory outputs.

The current allowlist contains two lineage outputs from this workflow (runs `42831240089` and `42836094887`) plus two synthetic evidence artifacts from P1.8.14 run `42304505004`. These are deliberately selected inputs to the current manifest, not owner-originated custody evidence. The remaining 30 lineage bundles and all 27 manifest/repository-inventory bundles remain historical workflow outputs; they are not automatically eligible to be added as source evidence. The two P1.8.14 artifacts remain a separate workflow/evidence class and were previously byte-verified.

The current run's own outputs must never be included in its own input manifest. Generated outputs are not equivalent to original source evidence, owner-held copies, independent attestations, or offline recovery proof.

## 5. Result and limitations

| Gate | Result |
|---|---|
| All repository Actions run pages needed to bracket target workflow history | PASS |
| 32/32 target workflow runs identified and exact source SHAs recorded | PASS |
| Per-run artifact metadata for all 32 runs | PASS |
| 59 artifact outputs classified by type | PASS |
| Complete repository-wide artifact inventory across all workflows | NOT IN SCOPE / NOT VERIFIED |
| Independent payload re-hash of all 59 historical artifacts | NOT PERFORMED |
| Eligibility of historical CI outputs as L4 owner evidence | NOT ESTABLISHED |

This completes the discovery inventory, not independent payload verification for every historical output. GitHub-reported upload digests are recorded as metadata and must not be described as independently recomputed digests.

Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. No control is promoted by this inventory.

## 6. Next permitted action

Review whether any of the 30 non-allowlisted lineage bundles are needed as historical CI provenance, and whether the current four-item allowlist's selection rationale is adequate. If a historical lineage bundle is selected for additional use, download that exact artifact and independently verify archive bytes and member hashes before changing the allowlist. Keep manifest and repository-inventory artifacts as generated outputs, not self-authenticating source evidence.

No key generation/signing, trust-root change, offline verification, VPS/SQLite access, artifact deletion, retention changes, cleanup, or destructive action is authorized. Option C — No Destructive Authority remains ACTIVE.
