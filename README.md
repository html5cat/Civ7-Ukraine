# Ukraine: Historical Continuity

This is a Civilization VII mod scaffold for an historically grounded Ukrainian all-age path.

## Historical Framing

The mod deliberately avoids claiming that modern Ukraine existed in Antiquity. Instead, it uses an age-appropriate continuity chain:

- Antiquity: Pontic Scythia
  - Historically tied to the Pontic-Caspian steppe, including present-day southern Ukraine.
  - Theme: horse mobility, steppe trade, kurgan culture.
- Exploration: Kyivan Rus'
  - Medieval polity centered on Kyiv.
  - Theme: river trade, urban law, Orthodox culture, diplomacy.
- Modern: Ukraine
  - Modern Ukrainian nation.
  - Theme: fertile agriculture, civic resilience, rail/industrial reconstruction, defensive sovereignty.

## V0.1 Scope

This first version focuses on loadable structure:

- `.modinfo`
- shell setup entries
- three age-specific civilizations
- transition unlocks from Pontic Scythia to Kyivan Rus' to Ukraine
- city names, descriptions, traits, tags, and start biases

Custom gameplay modifiers, unique units, unique improvements, icons, and civic trees should be added after validating the shell in Civ7 logs.

## Target Mechanics

### Pontic Scythia: Riders of the Pontic Steppe

- Cavalry gains movement or combat strength on flat open terrain.
- Horse and pasture starts are favored.
- Unique improvement: Kurgan, producing Culture and Gold near pastures or open land.

### Kyivan Rus': Route from the Varangians

- River settlements and trade routes generate Gold and Culture.
- Fortified river cities gain defensive benefits.
- Unique unit: Druzhina.
- Unique building or quarter: Veche Square or Saint Sophia Quarter.

### Ukraine: Breadbasket and Bastion

- Farms on fertile flat land generate Food and Gold.
- Rail/factory infrastructure converts agricultural strength into Production or GDP.
- During defensive wars, cities gain Production toward units and repairs.
- Unique improvement: Chernozem Farm.
- Unique unit: Sich Riflemen or Cossack Host, depending on final age placement.

## Install

Copy the whole `ukraine-historical-continuity` folder to:

```text
~/Library/Application Support/Civilization VII/Mods/
```

Restart Civilization VII, enable the mod, and inspect:

```text
~/Library/Application Support/Civilization VII/Logs/mods.log
~/Library/Application Support/Civilization VII/Logs/database.log
```

The first validation target is that the three civilizations appear in the correct age setup menus without database errors.
