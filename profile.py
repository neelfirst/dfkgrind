#!/usr/bin/env python3

import dfk.hero.hero_core as heroes
import dfk.hero.utils.utils as hero_utils
from dfk.quests.training import arm_wrestling, game_of_ball, dancing, darts, puzzle_solving
from dfk.quests.training import helping_the_farm, card_game, alchemist_assistance
from dfk.quests.professions import fishing, foraging, gardening, minning
from pathlib import Path
import json, logging

STAT_QUEST_MAP = {'strength' : arm_wrestling.QUEST_CONTRACT_ADDRESS, \
                 'agility' : game_of_ball.QUEST_CONTRACT_ADDRESS, \
                 'endurance' : dancing.QUEST_CONTRACT_ADDRESS, \
                 'wisdom' : puzzle_solving.QUEST_CONTRACT_ADDRESS, \
                 'dexterity' : darts.QUEST_CONTRACT_ADDRESS, \
                 'vitality' : helping_the_farm.QUEST_CONTRACT_ADDRESS, \
                 'intelligence' : alchemist_assistance.QUEST_CONTRACT_ADDRESS, \
                 'luck' : card_game.QUEST_CONTRACT_ADDRESS}

PROF_QUEST_MAP = {'mining' : minning.GOLD_QUEST_CONTRACT_ADDRESS, \
                  'gardening' : gardening.QUEST_CONTRACT_ADDRESS, \
                  'fishing' : fishing.QUEST_CONTRACT_ADDRESS_V2, \
                  'foraging' : foraging.QUEST_CONTRACT_ADDRESS_V2}

def get_max_stat_quest(hero):
  maxStatKey = None
  maxStatValue = 0
  for stat in STAT_QUEST_MAP.keys():
    if hero['stats'][stat] > maxStatValue:
      maxStatKey = stat
      maxStatValue = hero['stats'][stat]
  return STAT_QUEST_MAP[maxStatKey]

def get_quest_type_from_address(address):
  for k in STAT_QUEST_MAP:
    if address == STAT_QUEST_MAP[k]:
      return k
  for k in PROF_QUEST_MAP:
    if address == STAT_QUEST_MAP[k]:
      return k
  return None

def set_quest(hero, mode):
  if mode == "training":
    return get_max_stat_quest(hero)
  elif mode == "profession":
    profession = hero_utils.parse_stat_genes(hero['info']['statGenes'])['profession']
    return PROF_QUEST_MAP[profession]
  else:
    return input("[NOT RECOMMENDED] Manually input contract address for hero" + str(hero) + ": ")

def set_stampot(hero, mode):
  if mode == "training" or mode == "profession":
    return 0
  else:
    if 'y' in input("Use stampots for hero id " + hero['id'] + "? [y/N]"):
      return 1
    else:
      return 0

def make_new_profile(path_obj, hero_list):
  logger = logging.getLogger('dfkgrind')
  quest_config = []
  mode = None
  while mode is None:
    mode = input("Autoconfig your heroes: [training|profession|manual] ")
    if mode != 'training' and mode != 'profession' and mode != 'manual':
      mode = None
      logger.error('mode not recognized, please try again.')
  for hero in hero_list:
    quest_config.append({"hero_id" : hero["id"], "quest_address" : set_quest(hero, mode), "stampot" : set_stampot(hero, mode)})
  with open(path_obj,'w') as fp:
    fp.write(json.dumps(quest_config, indent=2))
  logger.info('wrote user config to ' + str(path_obj))
  return quest_config

def main(config_path, rpc_address, user_address):
  profile = Path(config_path)
  logger = logging.getLogger('dfkgrind')
  if profile.exists():
    logger.info('user profile found, loading...')
    with profile.open() as f:
      user_config = json.loads(f.read())
  else:
    logger.info('user profile not found. setting up...')
    hero_list = [heroes.get_hero(heroes.SERENDALE_CONTRACT_ADDRESS, h, rpc_address) \
                 for h in heroes.get_users_heroes(heroes.SERENDALE_CONTRACT_ADDRESS, user_address, rpc_address)]
    user_config = make_new_profile(profile, hero_list)
  return user_config

if __name__ == "__main__":
  f = "config/profile.json"
  c = heroes.SERENDALE_CONTRACT_ADDRESS
  r = "https://api.fuzz.fi"
  u = "0xd30798047E1801EAcd9b517001B74178FCa8a91b"
  mode = "training"
  main(f, r, u)
