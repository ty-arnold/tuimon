# TODO

- modify multiplier calculation for second typing
- modify stab calculation for second typing
- add handling for flat percentage changes to stats from things like paralysis
- finish fleshing out status moves
- set correct values for status moves
- flesh out move application
  - moves like confusion
  - [x] add turn sensitive status moves
  - add moves that trigger multiple times (ex: bullet seed)
  - [x] order of operations for applying stats + dealing damage
  - [x] allow application of moves to both attacker and defender
  - logic for moves like fly and substitute
- get player name/selected pokemon
- flesh out item system
  - add item class
  - logic to apply an item and skip move phase
- add tui
  - textual?
- add scraper or method to get stats of selected pokemon
- add scraper or method to dynamically get stats of moves of selected pokemon

## Completed

- [x] implement stat changes as stages (instead of fixed +/- values it increments or deincrements a staged amount)
- [x] add logic for multiple pokemon per trainer
  - [x] swap to next pokemon when active one dies
  - [x] check all pokemon of specific trainer when checking for winner
- [x] add battle menu
  - [x] moves
  - [x] items
  - [x] swap pokemon
- [x] add physical/special split
