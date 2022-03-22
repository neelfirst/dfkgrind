#!/usr/bin/env python3

from getpass import getpass
from pathlib import Path
from eth_account import Account
from web3 import Web3

from dfk.quest import foraging, fishing, mining
from dfk.quest.quest import Quest
from dfk.quest.utils import utils as quest_utils

import json, argparse, sys, time

import logging
LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
LOGGER = logging.getLogger("DFK-quest")
LOGGER.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=sys.stdout)

DEFAULT_KEYFILE_LOCATION = "config/keystore.json"
DEFAULT_RPC_SERVER = "https://api.fuzz.fi"
DEFAULT_QUEST_ATTEMPTS = 5 # fi/fo only

def make_new_keyfile(path_obj):
  x = getpass(prompt='Paste private key: ')
  y = getpass(prompt='Enter passphrase: ')
  z = Account.encrypt(x,y)
  with path_obj.open('w') as f:
    f.write(json.dumps(z))
  LOGGER.info('wrote encrypted keystore to ' + str(path_obj))
  return z

def manage_keyfile(keyfile_path):
  key = Path(keyfile_path)
  if key.exists():
    LOGGER.info('encrypted keystore file found, loading...')
    with key.open() as f:
      encrypted_key = json.loads(f.read())
  else:
    LOGGER.info('keystore not found, making new key. get your MM private key...')
    encrypted_key = make_new_keyfile(key)
  return encrypted_key

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

def run_quest():
  w3 = Web3(Web3.HTTPProvider(RPC_ADDRESS))
  quest = Quest(rpc_address=RPC_ADDRESS, logger=LOGGER)
  quest.start_quest(quest_address=quest_address, \
                    hero_ids=[hero_id], \
                    attempts=DEFAULT_QUEST_ATTEMPTS, \
                    private_key=(Account.decrypt(encrypted_key, p)), \
                    nonce=w3.eth.getTransactionCount(account_address), \
                    gas_price_gwei=35, \
                    tx_timeout_seconds=30)

  quest_info = quest_utils.human_readable_quest(quest.get_hero_quest(hero_id))

  time.sleep(DEFAULT_QUEST_ATTEMPTS * 35) # fudge value: complete time is unreliable

  tx_receipt = quest.complete_quest(hero_id=hero_id, \
                                    private_key=(Account.decrypt(encrypted_key, p)), \
                                    nonce=w3.eth.getTransactionCount(account_address), \
                                    gas_price_gwei=35, \
                                    tx_timeout_seconds=30)
  quest_result = quest.parse_complete_quest_receipt(tx_receipt)
  LOGGER.info("Rewards: " + str(quest_result))
  return

def main(hero_id, quest_type, keyfile_path=DEFAULT_KEYFILE_LOCATION, rpc=DEFAULT_RPC_SERVER):
  encrypted_key = manage_keyfile(keyfile_path)
  LOGGER.info('loaded encrypted key')

  p = getpass(prompt='Enter passphrase to decrypt and use: ')
  account_address = None
  try:
    account_address = w3.eth.account.privateKeyToAccount(Account.decrypt(encrypted_key, p)).address
  except:
    LOGGER.error("Bad passphrase. Bailing out.")
    sys.exit(1)
  if not account_address:
    LOGGER.error("Could not decode checksum-enabled account address. Bailing out.")
    sys.exit(1)

  quest_address = get_quest_address(quest_type)
  if not quest_address:
    LOGGER.error("Unrecognized quest type " + quest_type + " : Bailing out.")
    sys.exit(1)

  run_quest()
  use_item()

  return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Grinder. Enter hero ID')
  parser.add_argument('--hero', help='input (exactly one) hero id', required=True)
  parser.add_argument('--quest', help='choose one: [fishing, foraging]', required=True)
  parser.add_argument('--keyfile', help='relative path to keyfile (default: config/keystore.json)', required=False)
  parser.add_argument('--rpc', help='RPC server to use for calls (default: https://api.fuzz.fi)', required=False)
  args = vars(parser.parse_args())
  main(int(args['hero']), args['quest'], args['keyfile'], args['rpc'])
