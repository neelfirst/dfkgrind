#!/usr/bin/env python3

from getpass import getpass
from pathlib import Path
from eth_account import Account
from web3 import Web3

from dfk.quest import foraging, fishing # will expand into mining/gardening later
from dfk.quest.quest import Quest
from dfk.quest.utils import utils as quest_utils

import json, argparse, sys, time

KEYFILE_LOCATION = "config/keystore.json"
GAS_GWEI = 35
TX_TIMEOUT = 30

RPC_SERVER = "https://api.fuzz.fi"
w3 = Web3(Web3.HTTPProvider(RPC_SERVER))

def make_new_keyfile(path_obj):
  x = getpass(prompt='Paste private key: ')
  y = getpass(prompt='Enter passphrase: ')
  z = Account.encrypt(x,y)
  with path_obj.open('w') as f:
    f.write(json.dumps(z))
  print('wrote encrypted keystore to ' + KEYFILE_LOCATION)
  return z

def manage_keyfile():
  key = Path(KEYFILE_LOCATION)
  if key.exists():
    print('encrypted keystore file found, loading...')
    with key.open() as f:
      encrypted_key = json.loads(f.read())
  else:
    print('keystore not found, making new key. get your MM creds ready')
    encrypted_key = make_new_keyfile(key)
  return encrypted_key

def main(hero_id):
  encrypted_key = manage_keyfile()
  account_address = encrypted_key['address']
  print('loaded encrypted key')

  p = getpass(prompt='Enter passphrase to decrypt and use: ')
  try:
    Account.decrypt(encrypted_key, p)
  except:
    print("Bad passphrase. Bailing out.")
    sys.exit(1)

  quest = Quest(RPC_SERVER)
  quest.start_quest(fishing.QUEST_CONTRACT_ADDRESS, \
                     hero_id, \
                     1, \
                     str(Account.decrypt(encrypted_key, p)), \
                     w3.eth.getTransactionCount(account_address), \
                     GAS_GWEI, \
                     TX_TIMEOUT)

  quest_info = quest_utils.human_readable_quest(quest.get_hero_quest(hero_id))

  print("Waiting " + str(quest_info['completeAtTime'] - time.time()) + " secs to complete quest " + str(quest_info))
  while time.time() < quest_info['completeAtTime']:
    time.sleep(2)

  tx_receipt = quest.complete_quest(hero_id, \
                                    str(Account.decrypt(encrypted_key, p)), \
                                    w3.eth.getTransactionCount(account_address), \
                                    GAS_GWEI, \
                                    TX_TIMEOUT)
  quest_result = quest.parse_complete_quest_receipt(tx_receipt)
  logger.info("Rewards: " + str(quest_result))

  return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Grinder. Enter hero ID')
  parser.add_argument('--hero', help='input hero id', required=True)
  args = vars(parser.parse_args())
  main(args['hero'])
