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
  logger = logging.getLogger('dfkgrind')
  logger.info('wrote encrypted keystore to ' + str(path_obj))
  return z

def manage_keyfile(keyfile_path):
  key = Path(keyfile_path)
  logger = logging.getLogger('dfkgrind')
  if key.exists():
    logger.info('encrypted keystore file found, loading...')
    with key.open() as f:
      encrypted_key = json.loads(f.read())
  else:
    logger.info('keystore not found, making new key. get your MM private key...')
    encrypted_key = make_new_keyfile(key)
  return encrypted_key

def get_password(w3, encrypted_key):
  p = getpass(prompt='Enter passphrase to decrypt and use: ')
  try:
    account_address = w3.eth.account.privateKeyToAccount(Account.decrypt(encrypted_key, p)).address
  except:
    logger.exception("Bad passphrase. Bailing out.")
  return p

def get_address(w3, encrypted_key, p):
  account_address = None
  try:
    account_address = w3.eth.account.privateKeyToAccount(Account.decrypt(encrypted_key, p)).address
  except:
    logger.exception("Bad passphrase. Bailing out.")
  if not account_address:
    logger.exception("Could not decode checksum-enabled account address. Bailing out.")
  del p
  return account_address

