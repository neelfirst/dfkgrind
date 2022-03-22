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

def use_item(w3, hero_id, private_key, gas_price_gwei=35, tx_timeout_seconds=30, rpc_address='https://api.fuzz.fi'):
  account = w3.eth.account.privateKeyToAccount(private_key)
  w3.eth.default_account = account.address
  nonce = w3.eth.getTransactionCount(account.address)

  contract_address = Web3.toChecksumAddress(CONTRACT_ADDRESS)
  contract = w3.eth.contract(contract_address, abi=ABI)

  tx = contract.functions.consumeItem(ITEM_CONTRACT_ADDRESS, hero_id).buildTransaction(
    {'gasPrice': w3.toWei(gas_price_gwei, 'gwei'), 'nonce': nonce})

  logger = logging.getLogger('dfkgrind')
  logger.info("Signing transaction")
  signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
  logger.info("Sending transaction " + str(tx))
  ret = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logger.info("Transaction successfully sent !")
  logger.info("Waiting for transaction " + block_explorer_link(signed_tx.hash.hex()) + " to be mined")

  tx_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash=signed_tx.hash, timeout=tx_timeout_seconds,
                                                     poll_latency=3)
  logger.info("Transaction mined !")
  return tx_receipt
