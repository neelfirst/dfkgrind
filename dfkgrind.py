#!/usr/bin/env python3

from eth_account import Account
from web3 import Web3

import json, argparse, logging, time
from sys import exit, stdout

from dfk.quest import foraging, fishing, mining
from dfk.quest.quest import Quest
from dfk.quest.utils import utils as quest_utils
import dfk.hero.hero as heroes

import keys, item

LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
LOGGER = logging.getLogger('dfkgrind')
LOGGER.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=stdout)

DEFAULT_KEYFILE_LOCATION = "config/keystore.json"
DEFAULT_RPC_SERVER = "https://api.fuzz.fi"
DEFAULT_QUEST_ATTEMPTS = 5 # fi/fo only
DEFAULT_GAS_PRICE = 100 # gwei

def check_stamina(hero_id, rpc=DEFAULT_RPC_SERVER):
  h = None
  while h is None:
    try:
      h = heroes.human_readable_hero(heroes.get_hero(hero_id,rpc))
    except:
      LOGGER.warn("couldn't get hero stamina. sleeping and retrying")
      time.sleep(1)
      h = None

  time_to_full = h['state']['staminaFullAt'] - int(time.time())
  if time_to_full > 60 * 60 * 7: # 7 hours: 21 stamina from max
    return True
  else:
    return False

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

def run_quest(w3, quest_address, quest_type, hero_id, encrypted_key, p, addr):
  private_key = Account.decrypt(encrypted_key, p)
  quest = Quest(rpc_address=DEFAULT_RPC_SERVER, logger=LOGGER)
  success = False
  while success is False:
    try:
      quest.start_quest(quest_address=quest_address, \
                        hero_ids=[hero_id], \
                        attempts=DEFAULT_QUEST_ATTEMPTS, \
                        private_key=private_key, \
                        nonce=w3.eth.getTransactionCount(addr), \
                        gas_price_gwei=DEFAULT_GAS_PRICE, \
                        tx_timeout_seconds=30)
      success = True
    except:
      LOGGER.warn("Starting quest failed! Hero is inactive. Retrying in 3 seconds.")
      time.sleep(3)
      success = False

  if quest_type == 'mining':
    LOGGER.info("sleeping for 250 minutes")
    time.sleep(25 * 10 * 60)
  else: # quest_type == 'fishing' or 'foraging'
    sleep_time = DEFAULT_QUEST_ATTEMPTS * 35 # some overage built in
    LOGGER.info("sleeping for " + sleep_time + " seconds")
    time.sleep(sleep_time)

  quest_result = None
  while quest_result is None:
    try:
      tx_receipt = quest.complete_quest(hero_id=hero_id, \
                                        private_key=private_key, \
                                        nonce=w3.eth.getTransactionCount(addr), \
                                        gas_price_gwei=DEFAULT_GAS_PRICE, \
                                        tx_timeout_seconds=30)
      quest_result = quest.parse_complete_quest_receipt(tx_receipt)
      LOGGER.info("Rewards: " + str(quest_result))
    except:
      LOGGER.warn("Completing quest failed! Hero is stuck. Retrying in 3 seconds.")
      time.sleep(3)
      quest_result = None
  del p, private_key
  return tx_receipt

def use_item(w3, hero_id, encrypted_key, p, \
            gas_price_gwei=DEFAULT_GAS_PRICE, \
            tx_timeout_seconds=30, \
            rpc_address=DEFAULT_RPC_SERVER):
  private_key = Account.decrypt(encrypted_key, p)
  account = w3.eth.account.privateKeyToAccount(private_key)
  w3.eth.default_account = account.address
  nonce = w3.eth.getTransactionCount(account.address)

  contract_address = Web3.toChecksumAddress(item.CONTRACT_ADDRESS)
  contract = w3.eth.contract(contract_address, abi=item.ABI)

  tx = contract.functions.consumeItem(item.DFKSTMNPTN_ADDRESS, hero_id).buildTransaction(
    {'gasPrice': w3.toWei(gas_price_gwei, 'gwei'), 'nonce': nonce})

  ret = None
  while ret is None:
    try:
      LOGGER.info("Signing transaction")
      signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

      LOGGER.info("Sending transaction " + str(tx))
      ret = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
      LOGGER.info("Transaction successfully sent !")
    except:
      LOGGER.warn("Failed to send dfkstmnptn usage tx. Retrying in 3 seconds")
      time.sleep(3)
      ret = None

  tx_receipt = None
  while tx_receipt is None:
    try:
      LOGGER.info("Waiting for transaction " + str(signed_tx.hash.hex()) + " to be mined")
      tx_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash=signed_tx.hash, \
                                                       timeout=tx_timeout_seconds, \
                                                       poll_latency=3)
      LOGGER.info("Transaction mined !")
    except:
      LOGGER.warn("Failed to confirm dfkstmnptn usage. Retrying in 3 seconds.")
      time.sleep(3)
      tx_receipt = None

  del p, private_key
  return tx_receipt

def main(hero_id, quest_type, key_path=DEFAULT_KEYFILE_LOCATION, rpc=DEFAULT_RPC_SERVER):
  w3 = Web3(Web3.HTTPProvider(rpc))

  encrypted_key = keys.manage_keyfile(key_path)
  LOGGER.info('loaded encrypted key')

  p = keys.get_password(w3, encrypted_key)

  addr = keys.get_address(w3, encrypted_key, p)
  if not addr:
    LOGGER.error("Invalid checksum-enabled account address. Bailing out.")
    exit(1)

  quest_address = get_quest_address(quest_type)
  if not quest_address:
    LOGGER.error("Unrecognized quest type " + quest_type + " : Bailing out.")
    exit(1)

  while True:
    run_quest(w3, quest_address, quest_type, hero_id, encrypted_key, p, addr)
    if check_stamina(hero_id, rpc):
      use_item(w3, hero_id, encrypted_key, p)
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

