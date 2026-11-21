# ecosmart for Home Assistant - ARCHIVED

**This repository is archived and no longer maintained.** The Ecosmart integration now ships with Home Assistant
itself, from version 2026.11 (released 4 November 2026). There is nothing left to install from here.

## What to do

If you're still on the beta copy from this repo, remove it **before, or right away after, you upgrade** to Home
Assistant 2026.11 or later:

1. **Manual install**: delete `<config>/custom_components/ecosmart/` from your Home Assistant configuration
   directory.
   **HACS install**: remove "ecosmart" from HACS instead, then restart.
2. Restart Home Assistant.
3. Go to **Settings -> Devices & services**. Your existing setup should carry on, because the beta used the same
   `ecosmart` domain. If the Ecosmart entry shows an error after the restart, delete it and add the integration
   again with your API key.

**Why this matters:** a custom component and a built-in integration can't both use the domain `ecosmart` at the
same time. Home Assistant always loads the custom copy when both are present, so if you leave this old code in
place after upgrading, you stay on the frozen beta version instead of getting the built-in one (Home Assistant
only mentions it as a warning in the log).

If you haven't upgraded yet: delete the custom copy and restart first, then upgrade whenever you're ready. Home
Assistant will offer the integration from **Settings -> Devices & services -> Add integration** as soon as you're
on 2026.11 or later.

## Where to go instead

- The integration's own page: <https://www.home-assistant.io/integrations/ecosmart/>
- Ecosmart's setup walkthrough: <https://www.ecosmart.co.nz/electricity/api/home-assistant/>
- Questions or issues about the integration itself now belong on Home Assistant's own channels, not here.

## What it did, briefly

The integration published your wholesale (spot) electricity price from Ecosmart as a Home Assistant sensor, plus
an action returning the published price forecast. It publishes prices; it does not switch or control anything -
your own automations decide what to do with the number. Wholesale prices change every half hour and can spike,
sometimes for weeks, so plan automations with that in mind.

An Ecosmart electricity account is required to create the API key the integration uses - it's for Ecosmart
customers, not a public price feed.

## Licence

Apache-2.0 - see [LICENSE](LICENSE). The `aioecosmart` client library it depended on is MIT.

---

This README replaces the beta-channel install instructions that lived here while the integration went through
Home Assistant's core review queue. Thanks to everyone who tried the beta.
