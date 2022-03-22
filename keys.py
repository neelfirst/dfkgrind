#!/usr/bin/env python3

from getpass import getpass
from pathlib import Path
from eth_account import Account
from web3 import Web3

import json, logging

def make_new_keyfile(path_obj):
  x = getpass(prompt='Paste private key: ')
  y = getpass(prompt='Enter passphrase: ')
  z = Account.encrypt(x,y)
  with path_obj.open('w') as f:
    f.write(json.dumps(z))

  try:
    logger = getLogger('dfkgrind')
    logger.info('wrote encrypted keystore to ' + str(path_obj))
  except:
    pass

  return z

def manage_keyfile(keyfile_path):
  key = Path(keyfile_path)
  if key.exists():
    try:
      logger = getLogger('dfkgrind')
      logger.info('encrypted keystore file found, loading...')
    except:
      pass
    with key.open() as f:
      encrypted_key = json.loads(f.read())
  else:
    try:
      logger = getLogger('dfkgrind')
      logger.info('keystore not found, making new key. get your MM private key...')
    except:
      pass
    encrypted_key = make_new_keyfile(key)
  return encrypted_key

def get_address(encrypted_key, w3):
  p = getpass(prompt='Enter passphrase to decrypt and use: ')
  account_address = None
  try:
    account_address = w3.eth.account.privateKeyToAccount(Account.decrypt(encrypted_key, p)).address
  except:
    try:
      logger = getLogger('dfkgrind')
      logger.error("Bad passphrase. Bailing out.")
    except:
      pass
  if not account_address:
    try:
      logger = getLogger('dfkgrind')
      logger.error("Could not decode checksum-enabled account address. Bailing out.")
    except:
      pass
  return account_address
