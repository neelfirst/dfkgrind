#!/usr/bin/env python3

from getpass import getpass
from pathlib import Path
from eth_account import Account
from web3 import Web3

import json, sys

# consumeItem contract address
CONTRACT_ADDRESS = '0x38e76972bd173901b5e5e43ba5cb464293b80c31'

# dfkstmnptn item contract address - checksum enabled
ITEM_CONTRACT_ADDRESS = '0x959ba19508827d1ed2333B1b503Bd5ab006C710e'

# MellowGreenGiant copypasta
ABI = '''
      [
        {
           "inputs":[
                      {
                        "internalType":"address",
                        "name":"_address",
                        "type":"address"
                      },
                      {
                        "internalType":"uint256",
                        "name":"heroId",
                        "type":"uint256"
                      }
                    ],
           "name":"consumeItem",
           "outputs":[],
           "stateMutability":"view",
           "type":"function"
         }
      ]
      '''
KEYFILE_LOCATION = "config/keystore.json"

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

def use_item(hero_id, private_key, gas_price_gwei=35, tx_timeout_seconds=30, rpc_address='https://api.fuzz.fi'):
  w3 = Web3(Web3.HTTPProvider(rpc_address))
  account = w3.eth.account.privateKeyToAccount(private_key)
  w3.eth.default_account = account.address
  nonce = w3.eth.getTransactionCount(account.address)

  contract_address = Web3.toChecksumAddress(CONTRACT_ADDRESS)
  contract = w3.eth.contract(contract_address, abi=ABI)

  tx = contract.functions.consumeItem(ITEM_CONTRACT_ADDRESS, hero_id).buildTransaction(
    {'gasPrice': w3.toWei(gas_price_gwei, 'gwei'), 'nonce': nonce})

  print("Signing transaction")
  signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
  print("Sending transaction " + str(tx))
  ret = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  print("Transaction successfully sent !")
  print(
    "Waiting for transaction " + block_explorer_link(signed_tx.hash.hex()) + " to be mined")

  tx_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash=signed_tx.hash, timeout=tx_timeout_seconds,
                                                     poll_latency=3)
  print("Transaction mined !")

  return tx_receipt

def main(hero_id=134738):
  encrypted_key = manage_keyfile()
  print('loaded encrypted key')

  p = getpass(prompt='Enter passphrase to decrypt and use: ')
  account_address = None
  try:
    w3 = Web3(Web3.HTTPProvider('https://api.fuzz.fi'))
    account_address = w3.eth.account.privateKeyToAccount(Account.decrypt(encrypted_key, p)).address
  except Exception as e:
    print(e)
    print("Bad passphrase. Bailing out.")
    sys.exit(1)

  if not account_address:
    print("Could not decode checksum-enabled account address. Bailing out.")
    sys.exit(1)

if __name__ == '__main__':
  main()
