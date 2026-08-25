# ecosmart for Home Assistant

Live New Zealand wholesale electricity prices in Home Assistant, for ecosmart customers.

ecosmart is a New Zealand electricity retailer that passes the half-hourly wholesale
(spot) price straight through to customers. This integration puts that price, and the
published forward curve, into Home Assistant as sensors you can automate against — run
the dishwasher when power is cheap, charge the battery before a price spike, whatever
your setup can do.

**ecosmart publishes the price signal; it never controls your inverter, battery or
charger.** What you do with the price is entirely yours, and so is the outcome.

> **Beta.** This is the public beta channel while the integration goes through Home
> Assistant's core review queue. The code here is the exact code submitted to core —
> only repackaged so you can install it by hand today. Report anything odd at
> <https://github.com/ecosmart-nz/ecosmart-homeassistant/issues>.

## What you get

Two sensors for every connection point (ICP — the fifteen-character Installation Control
Point number that identifies a New Zealand electricity connection) your API key can see,
grouped into one device per ICP.

| Sensor | Entity ID | What it is | Updates |
|---|---|---|---|
| Spot price | `sensor.<icp>_spot_price` | The wholesale price right now, cents per kWh **including GST**, at your grid exit point | every 5 minutes |
| Forecast price | `sensor.<icp>_forecast_price` | The forecast price for the half-hour now in progress, same units | every 30 minutes |

**Spot price attributes:** `price_cents_per_kwh_excl_gst`, `price_dollars_per_mwh`,
`observed_at`, `gst_rate_percent`.

**Forecast price attributes:** `points` — the whole published forward curve, up to 48
hours ahead, each point carrying `starts_at`, `trading_date`, `trading_period`,
`schedule` and the price in all three units — plus `covered_hours` (how far the curve
actually reaches, which is usually less than 48 hours) and `published_at`.

The `points` curve is deliberately kept out of Home Assistant's recorder database. It is
up to 96 entries republished every half hour and none of it is worth keeping once it has
been superseded.

**When a sensor goes unavailable, that is the design, not a fault.** The spot sensor
reports unavailable whenever the price it has is stale or has no value — a price more
than about fifteen minutes old must never be the thing that tells a battery to charge.
The forecast sensor reports unavailable when the market has published nothing that
reaches this far ahead. Write your automations to tolerate `unavailable`.

Prices can be negative. That is real, it happens, and the sensors pass it through.

## Before you start

You need:

- An **ecosmart electricity account** with at least one connected property. If your
  switch to ecosmart has not completed yet, the integration will tell you the key has no
  connection points — try again once the property is live.
- An **API key**, which you create yourself in the ecosmart app:

  > Create a key in the ecosmart app under More > Settings > Advanced > API keys.
  > Creating a new key disables the previous one, so if you use your key somewhere else
  > already, that other tool will stop working.

  That warning matters. There is one key per account. If you later mint a fresh key for
  something else, this integration stops working until you delete and re-add it with the
  new key. (A proper re-authentication prompt is the next thing on the list.)

- A **recent Home Assistant**. This is the code submitted to Home Assistant core, written
  against the current development branch, and it uses modern helper APIs —
  `ConfigEntry.runtime_data`, `AddConfigEntryEntitiesCallback`, translated coordinator
  errors — along with Python 3.12+ syntax. The exact oldest release it works on has not
  been pinned down yet; the beta will establish it. If your Home Assistant is too old it
  will refuse to load the component and say so in the log, rather than misbehave quietly.
  If you hit that, please open an issue with your version — that is useful information.

Nobody at ecosmart will ever send you a key or ask you for one. You mint it, you hold it.

## Install

**Manual installation only.** This integration is not distributed through HACS and there
is nothing to add to HACS.

1. Download the latest release from the
   [Releases page](https://github.com/ecosmart-nz/ecosmart-homeassistant/releases), or
   clone this repository.
2. Copy the folder `custom_components/ecosmart/` into your Home Assistant configuration
   directory so that you end up with `<config>/custom_components/ecosmart/`. On a
   standard Home Assistant OS install, `<config>` is the folder holding
   `configuration.yaml`.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, search for **ecosmart**,
   and paste your API key.

The integration checks the key before it creates anything, so if it accepts the key you
are done — devices and sensors appear immediately.

## When this lands in Home Assistant core

Once `ecosmart` ships inside Home Assistant itself, this custom copy becomes redundant
and should go:

1. Upgrade Home Assistant to the release that includes the integration.
2. Delete `<config>/custom_components/ecosmart/`.
3. Restart Home Assistant.

**Do not remove the integration from the UI first.** Delete the folder only. Your config
entry, devices and entity IDs all survive — the built-in integration picks them up
exactly as they are, so every automation, dashboard card and long-term statistic keeps
working. Leaving the custom folder in place after the upgrade is the thing that causes
trouble: a custom component always overrides the built-in one, so you would silently
stay on this frozen copy.

## Reporting problems

Issues and questions: <https://github.com/ecosmart-nz/ecosmart-homeassistant/issues>

When reporting, please say which Home Assistant version you are on, what the sensors show
(including `unavailable`), and anything in the log mentioning `ecosmart`. Never paste
your API key into an issue — redact it.

## For maintainers

`custom_components/ecosmart/` is **generated, never hand-edited.** The integration is
written and tested in the `home-assistant/core` fork; this repo republishes it with the
two manifest keys a custom component requires and core forbids (`version`,
`issue_tracker`), plus the `translations/en.json` that core generates but does not
commit.

```bash
scripts/sync-from-core.sh 0.1.0     # regenerate from the core checkout, then validate
python scripts/validate.py          # check the generated copy on its own
python scripts/test_validate.py     # check that the validator refuses broken copies
```

To edit the integration, edit it in core and re-run the sync. See
`docs/core-pr-checklist.md` for the submission sequence and
`docs/ecosmart.markdown` for the working copy of the home-assistant.io page.

## Licence

Apache-2.0 — see [LICENSE](LICENSE). The `aioecosmart` client library it depends on is
MIT.
