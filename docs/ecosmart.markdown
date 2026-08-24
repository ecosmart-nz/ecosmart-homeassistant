---
title: Ecosmart
description: Instructions on how to integrate Ecosmart wholesale electricity prices into Home Assistant.
ha_category:
  - Energy
ha_release: "XXXX.XX"
ha_iot_class: Cloud Polling
ha_config_flow: true
ha_domain: ecosmart
ha_platforms:
  - sensor
ha_integration_type: service
ha_quality_scale: bronze
ha_codeowners:
  - '@Daryn-L'
---

[Ecosmart](https://www.ecosmart.co.nz/) is a **New Zealand electricity retailer** that
passes the half-hourly wholesale (spot) price of electricity straight through to its
customers. The **Ecosmart** {% term integration %} brings that price, and the published
forward curve, into Home Assistant so you can shift consumption to the cheap half hours.

Ecosmart publishes the price signal; it never controls your inverter, battery or charger.

{% include integrations/config_flow.md %}

## Prerequisites

You need an Ecosmart electricity account with at least one connected property, and an API
key that you create yourself.

Create a key in the Ecosmart app under **More** > **Settings** > **Advanced** >
**API keys**.

<div class='note warning'>

Creating a new key disables the previous one. If you already use your Ecosmart API key
somewhere else, minting a key for Home Assistant will stop that other tool working — and
minting a key elsewhere later will stop Home Assistant working until you remove and
re-add the integration with the new key.

</div>

If your switch to Ecosmart has not completed yet, a key can already exist while no
connection point is attached to it. Setup then reports that the key has no connection
points; try again once the property is live.

{% configuration_basic %}
API key:
  description: "The API key created in the Ecosmart app under **More** > **Settings** > **Advanced** > **API keys**."
{% endconfiguration_basic %}

## Supported devices

The integration creates one service device for every ICP the API key can reach. An ICP —
Installation Control Point — is the fifteen-character number that identifies a New
Zealand electricity connection; it appears on your bill. A customer with several
properties gets several devices, each named by its ICP and modelled by its grid exit
point (the substation where the local network draws power off the national grid).

## Sensors

Each device carries two sensors. Both report cents per kWh **including GST**, the unit
New Zealand power bills are written in.

### Spot price

The wholesale price at your grid exit point right now, republished by the market roughly
every five minutes and polled on the same cadence.

| Attribute | Description |
| --------- | ----------- |
| `price_cents_per_kwh_excl_gst` | The same price excluding GST. |
| `price_dollars_per_mwh` | The same price in dollars per megawatt hour, the unit the wholesale market itself quotes. |
| `observed_at` | When the market published this price, in UTC. |
| `gst_rate_percent` | The GST rate applied. |

### Forecast price

The forecast price for the half hour now in progress, taken from the published forward
schedules. Polled every 30 minutes.

| Attribute | Description |
| --------- | ----------- |
| `points` | The whole published curve, up to 48 hours ahead. Each point carries `starts_at`, `trading_date`, `trading_period`, `schedule`, and the price including GST, excluding GST, and in dollars per megawatt hour. |
| `covered_hours` | How far the curve actually reaches. This is usually well short of 48 hours and is the number to trust — do not assume the requested horizon. |
| `published_at` | When the schedule behind the forecast was published, in UTC. |

The `points` attribute is excluded from the recorder. It is up to 96 entries republished
every half hour, and once superseded it has no value worth storing.

## Unavailable is a normal state

Neither sensor guesses. When it does not have something it can stand behind, it reports
`unavailable`, and your automations should handle that.

- **Spot price** is unavailable when the most recent published price is stale, or carries
  no value. A price more than about fifteen minutes old must never be what tells a
  battery to charge.
- **Forecast price** is unavailable when the market has published nothing reaching this
  far ahead.
- Both are unavailable while the Ecosmart API cannot be reached, and recover on the next
  successful poll.

Prices can be negative when the market is oversupplied. That is genuine, and the sensors
pass it straight through.

If the API key is rejected — which normally means a newer key has replaced it — Home
Assistant raises a re-authentication notification for the entry. Until re-authentication
is supported, remove the integration and add it again with the current key. Entity IDs
are derived from the ICP, so they come back identical and your automations keep working.

## Removing the integration

This integration follows standard integration removal. No extra steps are required.

{% include integrations/remove_device_service.md %}

Removing the integration does not touch the API key itself. To revoke it, mint a new key
in the Ecosmart app, which disables the old one.
