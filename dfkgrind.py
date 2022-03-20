#!/usr/bin/env python3

from getpass import getpass
from pathlib import Path
from eth_account import Account
from web3 import Web3

from dfk.quest import foraging, fishing # will expand into mining/gardening later
from dfk.quest.quest import Quest
from dfk.quest.utils import utils as quest_utils

import json, argparse, sys, time, logging

KEYFILE_LOCATION = "config/keystore.json"
RPC_ADDRESS = "https://api.fuzz.fi"

w3 = Web3(Web3.HTTPProvider(RPC_ADDRESS))

log_format = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
logger = logging.getLogger("DFK-quest")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)

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
  print('loaded encrypted key')

  p = getpass(prompt='Enter passphrase to decrypt and use: ')
  account_address = None
  try:
    account_address = w3.eth.account.privateKeyToAccount(Account.decrypt(encrypted_key, p)).address
  except:
    print("Bad passphrase. Bailing out.")
    sys.exit(1)

  if not account_address:
    print("Could not decode checksum-enabled account address. Bailing out.")
    sys.exit(1)

  quest = Quest(rpc_address=RPC_ADDRESS, logger=logger)
  quest.start_quest(quest_address=fishing.QUEST_CONTRACT_ADDRESS, \
                    hero_ids=hero_id, \
                    attempts=1, \
                    private_key=str(Account.decrypt(encrypted_key, p)), \
                    nonce=w3.eth.getTransactionCount(account_address), \
                    gas_price_gwei=35, \
                    tx_timeout=30, \
                    rpc_address=RPC_ADDRESS)

  quest_info = quest_utils.human_readable_quest(quest.get_hero_quest(hero_id))

  print("Waiting " + str(quest_info['completeAtTime'] - time.time()) + " secs to complete quest " + str(quest_info))
  while time.time() < quest_info['completeAtTime']:
    time.sleep(2)

  tx_receipt = quest.complete_quest(hero_ids=hero_id, \
                                    private_key=str(Account.decrypt(encrypted_key, p)), \
                                    nonce=w3.eth.getTransactionCount(account_address), \
                                    gas_price_gwei=35, \
                                    tx_timeout=30, \
                                    rpc_address=RPC_ADDRESS)
  quest_result = quest.parse_complete_quest_receipt(tx_receipt)
  print("Rewards: " + str(quest_result))

  return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Grinder. Enter hero ID')
  parser.add_argument('--hero', help='input hero id', required=True)
  args = vars(parser.parse_args())
  main(args['hero'])
