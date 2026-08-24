# Submitting `ecosmart` to Home Assistant core

Everything needed to open the three pull requests, in the order they have to happen.
Read it start to finish before opening anything: the three PRs go up **the same day** and
reference each other, so a half-finished sequence is worse than not starting.

## 0. Before the day

| Blocker | Who | Why it blocks |
|---|---|---|
| GitHub organisation `ecosmart-nz` exists, with `ecosmart-homeassistant` public | Daryn | The issue-tracker and release URLs in this repo point at it |
| ~~Personal GitHub handle decided, placeholder swapped everywhere~~ **DONE** — the codeowner is `@Daryn-L` | Daryn | `codeowners` must be a real account; hassfest checks the shape, reviewers check the person |
| `aioecosmart` 0.1.0 published to PyPI | Daryn (release → Trusted Publishing) | Core CI installs `requirements`; an unpublished library fails every job |
| Home Assistant CLA signed | Daryn | The core PR is blocked by a bot until it is |
| Beta evidence collected | Daryn | The PR body cites real users; see the draft below |

Only one new-integration PR per author may be open at a time. Do not queue the follow-up
PRs (windows/TOU sensors, reauth, binary sensors, diagnostics) behind this one.

## 1. Swap the codeowner handle — **DONE (25 Aug 2026): the codeowner is `@Daryn-L`**

Kept here because the same three-places-plus-one rule applies to any future handle change
(a transfer to an org account, or adding a second codeowner).

The handle appears in **three places in the core checkout**:

1. `homeassistant/components/ecosmart/manifest.json` — the `codeowners` array
2. `CODEOWNERS` — the `/homeassistant/components/ecosmart/` line
3. `CODEOWNERS` — the `/tests/components/ecosmart/` line

`CODEOWNERS` is generated, so change the manifest first and then regenerate rather than
editing the two lines by hand:

```bash
python -m script.hassfest
```

Re-run hassfest after any swap and confirm it reports 0 invalid — that is the check that
the two `CODEOWNERS` lines actually picked the new handle up. On the 25 Aug swap it
reported 1486 integrations, 0 invalid, and regenerated both lines to `@Daryn-L`.

It also appears in this repo, in `docs/ecosmart.markdown` (`ha_codeowners`), which is the
working copy of the docs page — swap it there in the same sitting — and in the synced
`custom_components/ecosmart/manifest.json`, which is not hand-edited: re-run
`scripts/sync-from-core.sh 0.1.0` and it picks the new handle up from core.

## 2. Pre-flight gates

All of these run in the WSL core checkout. Every command is foreground; none of them may
be detached (WSL unmounts the distro when the attaching process exits).

```bash
wsl -d Ubuntu-24.04 -u root --cd /root/src/ha-core -- bash -lc "source .venv/bin/activate; <command>"
```

Run in this order:

| # | Command | What it proves |
|---|---|---|
| 1 | `uv pip install /mnt/c/synergy/homeassistant/aioecosmart` | The library is importable. Drop this step once `aioecosmart` is on PyPI and `uv pip install "aioecosmart==0.1.0"` works instead. |
| 2 | `python -m script.translations develop --integration ecosmart` | Regenerates `translations/en.json`. It is gitignored in core but the tests need it, and a fresh checkout will not have it. |
| 3 | `python -m pytest tests/components/ecosmart --cov=homeassistant.components.ecosmart --cov-report=term-missing` | 25 tests + 4 snapshots pass, and coverage is 100 % on every file — config flow coverage at 100 % is a Bronze requirement, not a nicety. |
| 4 | `python -m script.hassfest` | Manifest, strings, icons, quality scale and brands references all well-formed. Expect "0 invalid". |
| 5 | `prek run --all-files` | Core's lint. It is `prek`, not `pre-commit` — pre-commit is gone from core. |
| 6 | `python -m script.gen_requirements_all` | `requirements_all.txt` picks up `aioecosmart==0.1.0`. Commit whatever it changes. |

Then confirm the branch is rebased on current `dev` and the diff contains **only**
`homeassistant/components/ecosmart/`, `tests/components/ecosmart/`, `CODEOWNERS` and the
generated requirements files.

## 3. The three pull requests, same day

Open them in this order, then go back and cross-link.

### PR 1 — `home-assistant/brands`

Path `core_integrations/ecosmart/`, files from this repo's `brand/`:

- `icon.png` (256 × 256)
- `icon@2x.png` (512 × 512)
- `logo.png` (640 × 128)

Provenance and the one open dimension question are in `brand/README.md`. Title:
`Add Ecosmart brand images`. Body: one line saying it accompanies the core PR, with the
link added once PR 3 exists.

### PR 2 — `home-assistant/home-assistant.io`

File `source/_integrations/ecosmart.markdown`, from this repo's `docs/ecosmart.markdown`.
Target the **next** branch, not `current` — docs for an unreleased integration go to
`next`. Leave `ha_release: "XXXX.XX"` as the placeholder; the release manager fills it.
Title: `Add Ecosmart integration`.

### PR 3 — `home-assistant/core`

Branch `ecosmart-integration`. Title: `Add Ecosmart integration`. Use the
new-integration template and the draft below.

Once all three are open, edit each body to link the other two.

## 4. Core PR description — draft

> ## Proposed change
>
> Adds a new integration for **Ecosmart**, a New Zealand electricity retailer that passes
> the half-hourly wholesale (spot) price of electricity through to its customers. The
> integration exposes that price and the published forward curve, so New Zealand users
> can shift consumption — hot water, EV charging, home batteries — into the cheap half
> hours.
>
> It is deliberately a minimum first integration: **one platform (sensor), two entities
> per connection point, no services, no diagnostics, no options flow.** Follow-ups are
> planned and will be small.
>
> - **Spot price** — the current wholesale price in c/kWh including GST, polled every
>   5 minutes. Unavailable when the published price is stale or has no value: a price
>   more than about fifteen minutes old must never be what tells a battery to charge.
> - **Forecast price** — the forecast for the half hour in progress, polled every
>   30 minutes, with the whole published curve as an unrecorded attribute.
>
> One service device per ICP (the fifteen-character identifier of a New Zealand
> electricity connection). Two coordinators fetch per distinct grid exit point rather
> than per ICP, so several connections behind the same substation share one request —
> roughly 14 requests an hour per grid exit point against a 60-per-minute key limit.
>
> **Library:** all protocol code lives in
> [`aioecosmart`](https://github.com/ecosmart-nz/aioecosmart) (MIT, on PyPI, 100 % test
> coverage, ruff + mypy --strict, published by GitHub Trusted Publishing). This PR pins
> `aioecosmart==0.1.0`.
>
> **Quality scale:** `bronze`. `quality_scale.yaml` marks all Bronze rules done or
> exempt; `reauthentication-flow` is the first Silver item and the next follow-up.
>
> **Tests:** config flow at 100 % including every error-to-recovery path and the
> duplicate-account abort; setup load / auth-failure / retry / unload; sensor snapshots
> plus stale, null, empty and negative-price cases. Fixtures are **live recordings from
> the production API, redacted** (account reference, ICP and key label replaced); the
> four edge-case variants are derived from those recordings rather than written from
> scratch.
>
> **Beta:** running in production on real customer accounts since [date] — [N] users, no
> data-integrity issues reported. [Quote a beta user here, with permission.]
>
> ## Type of change
>
> - [x] New integration (thank you!)
>
> ## Additional information
>
> - Brands PR: [link]
> - Documentation PR: [link]
>
> ## Checklist
>
> (tick the template's boxes — tests added, docs added, `gen_requirements_all` run,
> library on PyPI, CLA signed)

Fill in `[date]`, `[N]` and the beta quote from what the soak actually produced. If the
tally is small, say the small number — an honest "4 households since 28 August" reads
better than a vague claim, and reviewers check.

## 5. While in review

- **Reply within 24 hours**, every time, even if the reply is "looking at this, will push
  a fix tomorrow". A stalled conversation moves the PR to the back of the queue, and the
  queue is measured in months.
- **Cut, do not argue.** If a reviewer wants something removed, remove it and offer it as
  a follow-up. Scope arguments are the single biggest cause of a slow first integration.
  Reviewers close bloated first PRs.
- **Stay rebased** on `dev`. Rebase, do not merge.
- Agents draft the replies; they go out under Daryn's name.
- Realistic timeline: weeks at best, months at the tail. Electric Kiwi — the other New
  Zealand retailer integration — took about eight months. The beta channel in this repo
  serves customers the whole time, so a slow queue costs marketing timing, not product.

## 6. After it merges

1. Cut a final release of this repo whose README tells beta users to upgrade Home
   Assistant and delete `custom_components/ecosmart/`.
2. Update the website's `/electricity/api/home-assistant/` page to lead with the
   integration, keeping the YAML template as the power-user fallback.
3. Start the follow-up series, one small PR at a time: windows/TOU sensors →
   reauth + reconfigure → cheap/dear window binary sensors → diagnostics → options flow →
   Silver sweep.
