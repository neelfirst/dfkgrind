#!/usr/bin/env python3
# usage: use_item(hero_id, Account.decrypt(encrypted_key, p))

from web3 import Web3
import logging

# consumeItem contract address
CONTRACT_ADDRESS = '0x38e76972bd173901b5e5e43ba5cb464293b80c31'

# dfkstmnptn item contract address - checksum enabled
DFKSTMNPTN_ADDRESS = '0x959ba19508827d1ed2333B1b503Bd5ab006C710e'

# MellowGreenGiant copypasta
ABI = \
'''
[
  {
    "inputs":
      [
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

def block_explorer_link(txid):
  return 'https://explorer.harmony.one/tx/' + str(txid)

def use_item(hero_id, private_key, gas_price_gwei=50, tx_timeout_seconds=30. rpc='https://api.fuzz.fi'):
  LOGGER.info("using potion")
  w3 = Web3(Web3.HTTPProvider(rpc)
  account = w3.eth.account.privateKeyToAccount(private_key)
  w3.eth.default_account = account.address
  nonce = w3.eth.getTransactionCount(account.address)

  contract_address = Web3.toChecksumAddress(CONTRACT_ADDRESS)
  contract = w3.eth.contract(contract_address, abi=item.ABI)

  try:
    tx = contract.functions.consumeItem(DFKSTMNPTN_ADDRESS, hero_id).buildTransaction(
      {'gasPrice': w3.toWei(gas_price_gwei, 'gwei'), 'nonce': nonce})
  except:
    raise

  ret = None
  while ret is None:
    try:
      w3 = Web3(Web3.HTTPProvider(rpc)
      LOGGER.info("Signing transaction")
      signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

      LOGGER.info("Sending transaction " + str(tx))
      ret = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
      LOGGER.info("Transaction successfully sent !")
    except Exception as e:
      LOGGER.exception(str(ex))
      continue

  tx_receipt = None
  while tx_receipt is None:
    try:
      LOGGER.info("Waiting for transaction " + str(signed_tx.hash.hex()) + " to be mined")
      tx_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash=signed_tx.hash, \
                                                       timeout=tx_timeout_seconds, \
                                                       poll_latency=3)
      LOGGER.info("Transaction mined !")
    except:
      continue

  del private_key
  return tx_receipt
