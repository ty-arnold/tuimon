from logger import logger

def dump_pokemon(pokemon):
    logger.debug(f"--- {pokemon.name} ---")
    logger.debug(f"  HP:           {pokemon.hp}/{pokemon.max_hp}")
    logger.debug(f"  Level:        {pokemon.lvl}")
    logger.debug(f"  Type:         {pokemon.type}")
    logger.debug(f"  Attack:       {pokemon.stat_attk} (stage: {pokemon.stage_attk})")
    logger.debug(f"  Defense:      {pokemon.stat_def} (stage: {pokemon.stage_def})")
    logger.debug(f"  Sp. Attack:   {pokemon.stat_sp_attk} (stage: {pokemon.stage_sp_attk})")
    logger.debug(f"  Sp. Defense:  {pokemon.stat_sp_def} (stage: {pokemon.stage_sp_def})")
    logger.debug(f"  Speed:        {pokemon.stat_spd} (stage: {pokemon.stage_spd})")
    logger.debug(f"  Accuracy:     {pokemon.stat_acc} (stage: {pokemon.stage_acc})")
    logger.debug(f"  Evasion:      {pokemon.stat_eva} (stage: {pokemon.stage_eva})")
    logger.debug(f"  Major Status: {pokemon.major_status}")
    logger.debug(f"  Minor Status: {[e.name for e in pokemon.minor_status]}")
    logger.debug(f"  Moveset:      {[m.name for m in pokemon.moveset]}")

def dump_trainer(trainer):
    logger.debug(f"=== {trainer.name} ===")
    logger.debug(f"  Selected Mon:       {trainer.selected_mon}")
    logger.debug(f"  Locked Move:        {trainer.locked_move.name if trainer.locked_move else None}")
    logger.debug(f"  Locked Turns:       {trainer.locked_turns}")
    logger.debug(f"  Invulnerable State: {trainer.invulnerable_state}")
    logger.debug(f"  Party:")
    for pokemon in trainer.party:
        dump_pokemon(pokemon)

def dump_move(move):
    logger.debug(f"--- Move: {move.name} ---")
    logger.debug(f"  Type:              {move.type}")
    logger.debug(f"  Category:          {move.category}")
    logger.debug(f"  Power:             {move.power}")
    logger.debug(f"  Accuracy:          {move.acc}")
    logger.debug(f"  PP:                {move.pp}")
    logger.debug(f"  Recoil:            {move.recoil}")
    logger.debug(f"  Lifesteal:         {move.lifesteal}")
    logger.debug(f"  Heal:              {move.heal}")
    logger.debug(f"  Crit Rate:         {move.crit_rate}")
    logger.debug(f"  Flinch Chance:     {move.flinch_chance}")
    logger.debug(f"  Priority:          {move.priority}")
    logger.debug(f"  Stat Changes:      {move.stat_change}")
    logger.debug(f"  Stat Change Chance {move.stat_change_chance}")
    logger.debug(f"  Hits Invulnerable: {move.hits_invulnerable}")
    logger.debug(f"  Status Effect:     {move.status_effect.name if move.status_effect else None}")

    if move.multi_turn is not None:
        logger.debug(f"  Multi Turn:")
        for key, value in move.multi_turn.items():
            logger.debug(f"    {key:<22} {value}")
    else:
        logger.debug(f"  Multi Turn:        None")

def dump_battle_state(player, npc, turn=None):
    if turn:
        logger.debug(f"{'='*40}")
        logger.debug(f"TURN {turn}")
        logger.debug(f"{'='*40}")
    dump_trainer(player)
    dump_trainer(npc)