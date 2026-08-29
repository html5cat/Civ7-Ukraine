# Ukraine: Historical Continuity

A Civilization VII mod that adds a historically grounded Ukrainian all-age path:

| Age | Civilization | Ability | Unique Unit |
| --- | --- | --- | --- |
| Antiquity | **Pontic Scythia** | Riders of the Pontic Steppe | Saka Horse Archer |
| Exploration | **Kyivan Rus'** | Route from the Varangians | Druzhina |
| Modern | **Ukraine** | Breadbasket and Bastion | Sich Riflemen |

## Historical Framing

The mod does **not** claim that modern Ukraine existed in Antiquity. It uses an age-appropriate continuity chain tied to lands and institutions of the Ukrainian historical region:

- **Pontic Scythia** — Iranian-speaking steppe peoples of the Pontic-Caspian steppe (including southern Ukraine); horse warfare, kurgan culture, Black Sea trade.
- **Kyivan Rus'** — medieval polity centered on Kyiv; river trade (“from the Varangians to the Greeks”), Orthodox conversion (988), princely law and diplomacy.
- **Ukraine** — modern nation; chernozem agriculture, Cossack traditions of self-rule, civic resilience, defensive sovereignty.

Unique units avoid colliding with Russia’s Cossacks by using **Sich Riflemen** (Sichovi Striltsi) for Modern Ukraine.

## Abilities

### Pontic Scythia — Riders of the Pontic Steppe
- Cavalry: +1 Movement, +3 Combat Strength
- Capital: +2 Gold

### Kyivan Rus' — Route from the Varangians
- Settlements on navigable rivers: +2 Gold, +1 Culture
- Capital: +1 Influence (Diplomacy yield)

### Ukraine — Breadbasket and Bastion
- All settlements: +2 Food, +1 Gold
- +3 War Support in wars you did not start

## Unique Units

- **Saka Horse Archer** — replaces Chariot / Horseman; bonus Combat Strength on flat terrain
- **Druzhina** — replaces Courser / Knight / Lancer; bonus Combat Strength in friendly territory
- **Sich Riflemen** — replaces Line Infantry / Rifleman / Infantry Company; bonus Combat Strength in friendly territory

## Install

Copy this folder into your Civ VII Mods directory:

```text
# macOS
~/Library/Application Support/Civilization VII/Mods/ukraine-historical-continuity/

# Windows
%USERPROFILE%\AppData\Local\Firaxis Games\Sid Meier's Civilization VII\Mods\ukraine-historical-continuity\

# Linux (Proton / native paths may vary)
~/.local/share/Civilization VII/Mods/ukraine-historical-continuity/
```

Restart Civilization VII, enable **Ukraine: Historical Continuity**, then check:

```text
Logs/mods.log
Logs/database.log
```

You should see the three civilizations in the matching age setup menus without database errors.

## Validate (offline)

Civilization VII is required for a full in-game load test. Offline structural checks:

```bash
python3 scripts/validate_mod.py
python3 scripts/test_mod_offline.py
```

These catch crash-class issues (bad VisualRemaps loading, reversed donor direction, missing files, dangling modifiers, LOC gaps). They cannot replace checking `Modding.log` / `Database.log` after enabling the mod in-game.

## Leader pairings (setup highlights)

| Leader | Civ | Reason |
| --- | --- | --- |
| Xerxes | Pontic Scythia | Strategic — imperial frontier / steppe cavalry |
| Charlemagne | Kyivan Rus' | Historical — medieval Christian polity |
| Lafayette | Ukraine | Strategic — civic liberty / defensive struggle |

Any leader can still lead any civilization; these are recommended pairings only.
