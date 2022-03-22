#!/usr/bin/env python3

from eth_account import Account
from web3 import Web3

import json, argparse, logging
from time import sleep
from sys import exit, stdout

from dfk.quest import foraging, fishing, mining
from dfk.quest.quest import Quest
from dfk.quest.utils import utils as quest_utils

LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
LOGGER = logging.getLogger('dfkgrind')
LOGGER.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=stdout)

DEFAULT_KEYFILE_LOCATION = "config/keystore.json"
DEFAULT_RPC_SERVER = "https://api.fuzz.fi"
DEFAULT_QUEST_ATTEMPTS = 5 # fi/fo only

def get_quest_address(quest_type):
  if quest_type == 'fishing':
    quest_address = fishing.QUEST_CONTRACT_ADDRESS
  elif quest_type == 'foraging':
    quest_address = foraging.QUEST_CONTRACT_ADDRESS
  elif quest_type == 'mining':
    quest_address = mining.GOLD_QUEST_CONTRACT_ADDRESS
  else:
    quest_address = None
  return quest_address

def run_quest(w3, quest_address, hero_id, encrypted_key, p, account_address):
  w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC_SERVER))
  quest = Quest(rpc_address=DEFAULT_RPC_SERVER, logger=LOGGER)
  quest.start_quest(quest_address=quest_address, \
                    hero_ids=[hero_id], \
                    attempts=DEFAULT_QUEST_ATTEMPTS, \
                    private_key=(Account.decrypt(encrypted_key, p)), \
                    nonce=w3.eth.getTransactionCount(account_address), \
                    gas_price_gwei=35, \
                    tx_timeout_seconds=30)

  quest_info = quest_utils.human_readable_quest(quest.get_hero_quest(hero_id))

  sleep(DEFAULT_QUEST_ATTEMPTS * 35) # fudge value: complete time is unreliable

  tx_receipt = quest.complete_quest(hero_id=hero_id, \
                                    private_key=(Account.decrypt(encrypted_key, p)), \
                                    nonce=w3.eth.getTransactionCount(account_address), \
                                    gas_price_gwei=35, \
                                    tx_timeout_seconds=30)
  quest_result = quest.parse_complete_quest_receipt(tx_receipt)
  LOGGER.info("Rewards: " + str(quest_result))
  return

def main(hero_id, quest_type, keyfile_path=DEFAULT_KEYFILE_LOCATION, rpc=DEFAULT_RPC_SERVER):
  w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC_SERVER))

  from keys import manage_keyfile
  encrypted_key = manage_keyfile(keyfile_path)
  LOGGER.info('loaded encrypted key')

  from keys import get_address
  account_address, p = get_address(encrypted_key, w3)
  if not account_address:
    LOGGER.error("Could not decode checksum-enabled account address. Bailing out.")
    exit(1)

  quest_address = get_quest_address(quest_type)
  if not quest_address:
    LOGGER.error("Unrecognized quest type " + quest_type + " : Bailing out.")
    exit(1)

#  run_quest()
#  use_item()

  return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Welcome to the grinder...')
  parser.add_argument('--hero', help='input (exactly one) hero id', required=True)
  parser.add_argument('--quest', help='choose one: [fishing, foraging]', required=True)
  parser.add_argument('--keyfile', help='relative path to keyfile (default: config/keystore.json)', required=False)
  parser.add_argument('--rpc', help='RPC server to use for calls (default: https://api.fuzz.fi)', required=False)
  args = vars(parser.parse_args())
  if (args['keyfile']):
    if (args['rpc']):
      main(int(args['hero']), args['quest'], args['keyfile'], args['rpc'])
    else:
      main(int(args['hero']), args['quest'], args['keyfile'])
  else:
    if (args['rpc']):
      main(int(args['hero']), args['quest'], rpc=args['rpc'])
    else:
      main(int(args['hero']), args['quest'])
