#!/usr/bin/env python3

from getpass import getpass
from pathlib import Path
from eth_account import Account

from dfk.quest import foraging, fishing # will expand into mining/gardening later
from dfk.quest.quest import Quest
from dfk.quest.utils import utils as quest_utils

import json

RPC_SERVER = "https://api.fuzz.fi"
KEYFILE_LOCATION = "config/keystore.json"
GAS_GWEI = 35

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
  print(Account.decrypt(encrypted_key, p))
#  quest = Quest(RPC_SERVER)
#  quest.start_quest(foraging.QUEST_CONTRACT_ADDRESS, hero_id, 1, 

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Grinder. Enter hero ID')
  parser.add_argument('--hero', help='input hero id', required=True)
  args = vars(parser.parse_args())
  main(args['hero'])
