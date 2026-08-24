# Submitting `ecosmart` to Home Assistant core — runbook

Three pull requests go up **the same day** and cross-reference each other, so read this
start to finish before opening anything. Everything a machine could prepare is prepared:
all three branches exist, are committed, and have a `fork` remote wired. What is left is
push, open, tick, sign.

Prepared 25 August 2026. Branch state at that date:

| Repo | Local checkout | Branch | Commit | Based on |
|---|---|---|---|---|
| core | `/root/src/ha-core` (WSL `Ubuntu-24.04`, user `root`) | `ecosmart-integration` | `3cdd11bc40` | `dev` |
| brands | `C:\synergy\homeassistant\submission\brands` | `add-ecosmart` | `a3c9860f` | `master` @ `012785e2` |
| docs | `C:\synergy\homeassistant\submission\home-assistant.io` | `add-ecosmart-docs` | `eb989bf` | `next` @ `6260832` |

The three forks (`Daryn-L/core`, `Daryn-L/brands`, `Daryn-L/home-assistant.io`) exist. The
`fork` remote is already added to each checkout; nothing has been pushed to any of them.

---

## 1. Pre-flight gates — all green 25 August 2026

Nothing below needs re-running unless core `dev` has moved and the branch has been rebased.
Every command runs in the WSL core checkout, in the foreground (WSL unmounts the distro if
the attaching process exits):

```bash
wsl -d Ubuntu-24.04 -u root --cd /root/src/ha-core -- bash -lc "source .venv/bin/activate; <command>"
```

| # | Command | Last result |
|---|---|---|
| 1 | `uv pip install "aioecosmart==0.1.0"` | Installed **from PyPI**, not from the local path (`direct_url: none`). The published wheel is what the tests import. |
| 2 | `python -m script.translations develop --integration ecosmart` | `translations/en.json` present. Core gitignores it, the tests need it, a fresh checkout will not have it. |
| 3 | `python -m pytest tests/components/ecosmart -q` | **25 passed, 4 snapshots**, 1.2 s, 0 failures. |
| 4 | `python -m script.hassfest` | **1486 integrations, 0 invalid.** |
| 5 | `prek run --all-files` | Clean. It is `prek`, not `pre-commit` — pre-commit is gone from core. |
| 6 | `python -m script.gen_requirements_all` | `requirements_all.txt` carries `aioecosmart==0.1.0`. |

Also green on 25 August, in this repo: `python scripts/validate.py` (11 files, byte-identical
to core apart from the three custom-component manifest keys) and `python scripts/test_validate.py`
(1 control + 7 refusal cases).

Confirm before pushing that the core branch is rebased on current `dev` and the diff contains
**only** `homeassistant/components/ecosmart/`, `tests/components/ecosmart/`, `CODEOWNERS` and
the generated requirements files.

---

## 2. Push the three branches

Nothing has been pushed. Run these in order; each one is a single command.

**Core** (from Windows PowerShell or Git Bash — the checkout lives inside WSL):

```bash
wsl -d Ubuntu-24.04 -u root --cd /root/src/ha-core -- bash -lc "git push -u fork ecosmart-integration"
```

**Brands:**

```bash
git -C /c/synergy/homeassistant/submission/brands push -u fork add-ecosmart
```

**Docs:**

```bash
git -C /c/synergy/homeassistant/submission/home-assistant.io push -u fork add-ecosmart-docs
```

> The brands and docs checkouts are **shallow** (`--depth 1`, later deepened a little). A
> shallow push normally succeeds against a GitHub fork because the fork shares its object
> store with upstream. If either push is rejected with `shallow update not allowed`, run
> `git fetch --unshallow origin` in that checkout and push again. The core checkout is
> blobless, not shallow, so it has no such problem.

---

## 3. Open the pull requests

Open in this order — brands and docs first, so their URLs exist when the core PR body is
written. Each link opens a pre-filled compare page on the fork:

| # | PR | Compare URL | Title |
|---|---|---|---|
| 1 | brands | `https://github.com/home-assistant/brands/compare/master...Daryn-L:brands:add-ecosmart?expand=1` | `Add Ecosmart brand images` |
| 2 | docs | `https://github.com/home-assistant/home-assistant.io/compare/next...Daryn-L:home-assistant.io:add-ecosmart-docs?expand=1` | `Add Ecosmart integration docs` |
| 3 | core | `https://github.com/home-assistant/core/compare/dev...Daryn-L:core:ecosmart-integration?expand=1` | `Add Ecosmart integration` |

The docs PR must target **`next`**, not `current` — the compare URL above already does. Docs
for an unreleased integration go to `next`, which is what becomes the next monthly release.

Once all three are open, go back and edit each body so it links the other two.

### Brands PR body

The brands repo has its own template. Fill it in like this:

- **Proposed change**: `Brand images for the new core integration ecosmart, a New Zealand
  electricity retailer. Accompanies the core PR <CORE_PR_URL> and the documentation PR
  <DOCS_PR_URL>.`
- **Type of change**: tick only **Add a new logo or icon for a new core integration**.
- **Additional information**: leave `fixes #` empty; put the core PR URL in
  *Link to code base pull request* and the docs PR URL in *Link to documentation pull request*.
- **Checklist**: tick PNG, icon 256×256, hDPI icon 512×512, and logo shortest side within
  128–256 px. **Do not tick the hDPI logo line** — there is no `logo@2x.png`. That is normal:
  87 existing core integrations ship `logo.png` with no hDPI variant, and the repository's own
  validator only requires `logo.png` to exist when `logo@2x.png` does, never the other way
  round.

### Docs PR body

One or two sentences: documentation page for the new `ecosmart` integration, plus the core PR
link. `ha_release` is set to `"2026.9"`, the same value the two most recently added new
integrations (`tonewinner`, `flow_it`) carry on `next`. If the core review runs past that
release, a reviewer or the release manager moves it — say so in the PR body so nobody thinks
it is a claim about the merge date.

---

## 4. Core PR description — final text, ready to paste

Replace `<BRANDS_PR_URL>`, `<DOCS_PR_URL>` and `<SOAK_EVIDENCE>`. Everything else is final.
Keep the template's section headings; the HA bot and the reviewers both key off them.

<!-- BEGIN PASTE -->

## Breaking change

<!-- Not a breaking change: delete this section before submitting. -->

## Proposed change

Adds a new integration for **Ecosmart**, a New Zealand electricity retailer that passes the
half-hourly wholesale (spot) price of electricity through to its customers. The integration
exposes that price and the published forward curve, so New Zealand users can move consumption
— hot water, EV charging, home batteries — into the cheap half hours.

It is deliberately a minimum first integration: **one platform (sensor), two entities per
connection point, no actions, no diagnostics, no options flow.** Follow-ups are planned and
will each be small.

- **Spot price** — the current wholesale price in c/kWh including GST, polled every 5 minutes.
  Unavailable when the published price is stale or carries no value: a price more than about
  fifteen minutes old must never be what tells a battery to charge.
- **Forecast price** — the forecast for the half hour in progress, polled every 30 minutes,
  with the whole published curve as an unrecorded attribute.

One service device per ICP (the fifteen-character identifier of a New Zealand electricity
connection). Two coordinators fetch per distinct grid exit point rather than per ICP, so
several connections behind the same substation share one request — roughly 14 requests an
hour per grid exit point against a 60-per-minute key limit.

**Library:** all protocol code lives in
[`aioecosmart`](https://github.com/ecosmart-nz/aioecosmart)
([PyPI](https://pypi.org/project/aioecosmart/)) — MIT, 100% test coverage enforced in CI,
ruff and `mypy --strict` clean, tested on Python 3.13 and 3.14, published to PyPI by GitHub
Trusted Publishing. This PR pins `aioecosmart==0.1.0`, the library's first release, so there
is no previous version to diff against.

**Quality scale:** `bronze`. `quality_scale.yaml` marks every Bronze rule done or exempt.
Silver rules are marked honestly: six are already done, and `reauthentication-flow` is the
real outstanding one and the next follow-up PR.

**Tests:** config flow at 100% including every error-to-recovery path and the duplicate-account
abort; setup load / auth-failure / retry / unload; sensor snapshots plus stale, null, empty and
negative-price cases. Fixtures are live recordings from the production API with the account
reference, ICP and key label redacted; the edge-case variants are derived from those recordings
rather than written from scratch.

**Real-world testing:** <SOAK_EVIDENCE>

## Type of change

- [x] New integration (thank you!)

## Additional information

- This PR fixes or closes issue: n/a
- Brands PR: <BRANDS_PR_URL>
- Link to documentation pull request: <DOCS_PR_URL>
- Link to developer documentation pull request: n/a
- Link to frontend pull request: n/a

## Checklist

- [ ] I understand the code I am submitting and can explain how it works.
- [x] The code change is tested and works locally.
- [x] Local tests pass. **Your PR cannot be merged unless tests pass**
- [x] There is no commented out code in this PR.
- [x] I have followed the [development checklist][dev-checklist]
- [x] I have followed the [perfect PR recommendations][perfect-pr]
- [x] The code has been formatted using Ruff (`ruff format homeassistant tests`)
- [x] Tests have been added to verify that the new code works.
- [ ] Any generated code has been carefully reviewed for correctness and compliance with project standards.

If user exposed functionality or configuration variables are added/changed:

- [x] Documentation added/updated for [www.home-assistant.io][docs-repository]

If the code communicates with devices, web services, or third-party tools:

- [x] The [manifest file][manifest-docs] has all fields filled out correctly.
- [x] New or updated dependencies have been added to `requirements_all.txt`.
- [x] For the updated dependencies a diff between library versions and ideally a link to the changelog/release notes is added to the PR description.

To help with the load of incoming pull requests:

- [ ] I have reviewed two other [open pull requests][prs] in this repository.

<!-- END PASTE -->

### The three unticked boxes

They are unticked on purpose, and each is a Daryn action, not a code action:

- **"I understand the code I am submitting and can explain how it works"** and **"Any
  generated code has been carefully reviewed"** — these are the Home Assistant
  [AI policy](https://developers.home-assistant.io/docs/ai_policy) boxes. The integration was
  written by an agent under Daryn's direction. Read `homeassistant/components/ecosmart/` end
  to end (about 450 lines outside tests) before ticking them. Ticking them without reading is
  the one thing in this whole submission that would be dishonest.
- **"I have reviewed two other open pull requests"** — actually review two, then tick. The
  linked query filters to PRs nobody has reviewed yet.

Everything else above is ticked because it is true and was measured: see the gate table in §1.

---

## 5. Sign the CLA

The CLA bot comments on the first pull request with a link; signing is a single click with the
GitHub account, and it covers every Home Assistant repository afterwards. Sign it as soon as
the bot asks — an unsigned CLA blocks the merge and nothing else in the review can finish.

---

## 6. While in review

- **Reply within 24 hours**, every time, even if the reply is only "looking at this, will push
  a fix tomorrow". A stalled conversation moves the PR to the back of a queue measured in
  months. Agents draft the replies; they go out under Daryn's name.
- **Cut, do not argue.** If a reviewer wants something removed, remove it and offer it as a
  follow-up. Scope arguments are the single biggest cause of a slow first integration, and
  reviewers close bloated first PRs.
- **Stay rebased** on `dev`. Rebase, do not merge.
- Only one new-integration PR per author may be open at a time. Do not queue the follow-ups
  (windows/TOU sensors, reauth, binary sensors, diagnostics) behind this one.
- Realistic timeline: weeks at best, months at the tail. Electric Kiwi — the other New Zealand
  retailer integration — took about eight months. The beta channel in this repository serves
  customers the whole time, so a slow queue costs marketing timing, not product.

---

## 7. After it merges

1. Cut a final release of this repository whose README tells beta users to upgrade Home
   Assistant and delete `custom_components/ecosmart/`.
2. Update the website's `/electricity/api/home-assistant/` page to lead with the integration,
   keeping the YAML template as the power-user fallback.
3. Start the follow-up series, one small PR at a time: windows/TOU sensors → reauth and
   reconfigure → cheap/dear window binary sensors → diagnostics → options flow → Silver sweep.

---

## Appendix: what is in each branch

**brands** — one commit, three files, nothing else:

```
core_integrations/ecosmart/icon.png       256 x 256
core_integrations/ecosmart/icon@2x.png    512 x 512
core_integrations/ecosmart/logo.png       640 x 128   (shortest side 128, inside the 128-256 rule)
```

**docs** — one commit, one new file, `source/_integrations/ecosmart.markdown`. Written against
the repository's own `_integration_docs_template.markdown` and its `.claude/skills` writing
rules, and checked with the repository's own linters (`remark --frail` and `textlint`, both
clean). Section order matches the current template: prerequisites, config-flow include,
`configuration_basic`, supported functionality, data updates, known limitations,
troubleshooting, removal.

**core** — the branch is unchanged from wave 4a. Files under
`homeassistant/components/ecosmart/` and `tests/components/ecosmart/`, plus the generated
`CODEOWNERS` and requirements lines.

## Appendix: the codeowner handle

The codeowner is `@Daryn-L`, set 25 August 2026. It appears in three places in the core
checkout, and `CODEOWNERS` is generated rather than hand-edited — change the manifest, then
run `python -m script.hassfest` and confirm 0 invalid:

1. `homeassistant/components/ecosmart/manifest.json` — the `codeowners` array
2. `CODEOWNERS` — the `/homeassistant/components/ecosmart/` line
3. `CODEOWNERS` — the `/tests/components/ecosmart/` line

It also appears in this repository in `docs/ecosmart.markdown` (`ha_codeowners`), which is
hand-edited, and in `custom_components/ecosmart/manifest.json`, which is not — re-run
`scripts/sync-from-core.sh 0.1.0` and it picks the handle up from core.
