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
DEFAULT_QUEST_ATTEMPTS = 5 # fi/fo only
DEFAULT_GAS_PRICE = 100 # gwei

RPC_SERVERS = [ \
                "https://api.fuzz.fi", \
                "https://rpc.hermesdefi.io", \
                "https://api.s0.t.hmny.io", \
                "https://harmony-0-rpc.gateway.pokt.network", \
                "https://api.harmony.one", \
              ]
CURRENT_RPC = 0

# rotate through RPCs in times of crisis
def switch_rpc():
  CURRENT_RPC = (CURRENT_RPC + 1) % 5
  return

def warn_sleep_reset(t, log):
  switch_rpc()
  rpc = RPC_SERVERS[CURRENT_RPC]
  LOGGER.warn("Failed {log}. Switch to {rpc}, sleep {t} sec and retry.".format(log=log,rpc=rpc,t=t))
  time.sleep(t)
  return None

def get_stamina(hero_id):
  h = None
  while h is None:
    try:
      rpc = RPC_SERVERS[CURRENT_RPC]
      h = heroes.human_readable_hero(heroes.get_hero(hero_id,rpc))
    except:
      h = warn_sleep_reset("get hero stamina", 1)
      continue

  time_to_full = h['state']['staminaFullAt'] - int(time.time())
  missing_stamina = time_to_full / ( 60 * 20 ) # 20 min / 1200 sec
  max_stamina = h['stats']['stamina']
  return max_stamina - missing_stamina

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

def run_quest(quest_address, quest_type, hero_id, private_key, addr):
  success = None
  while success is None:
    try:
      w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
      quest = Quest(rpc_address=RPC_SERVERS[CURRENT_RPC], logger=LOGGER)

      quest.start_quest(quest_address=quest_address, \
                        hero_ids=[hero_id], \
                        attempts=DEFAULT_QUEST_ATTEMPTS, \
                        private_key=private_key, \
                        nonce=w3.eth.getTransactionCount(addr), \
                        gas_price_gwei=DEFAULT_GAS_PRICE, \
                        tx_timeout_seconds=30)
      success = True
    except:
      success = warn_sleep_reset("starting quest", 1)
      continue

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
      w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
      tx_receipt = quest.complete_quest(hero_id=hero_id, \
                                        private_key=private_key, \
                                        nonce=w3.eth.getTransactionCount(addr), \
                                        gas_price_gwei=DEFAULT_GAS_PRICE, \
                                        tx_timeout_seconds=30, \
                                        rpc_address=RPC_SERVERS[CURRENT_RPC]) # needs PR to 0rtis/dfk!
      quest_result = quest.parse_complete_quest_receipt(tx_receipt)
      LOGGER.info("Rewards: " + str(quest_result))
    except:
      quest_result = warn_sleep_reset("completing quest", 1)
      continue

  del private_key
  return tx_receipt

def use_item(hero_id, private_key, gas_price_gwei=DEFAULT_GAS_PRICE, tx_timeout_seconds=30):
  w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC_SERVERS[CURRENT_RPC]))
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
      w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC_SERVERS[CURRENT_RPC]))
      LOGGER.info("Signing transaction")
      signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

      LOGGER.info("Sending transaction " + str(tx))
      ret = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
      LOGGER.info("Transaction successfully sent !")
    except:
      ret = warn_sleep_reset("potion usage tx", 1)
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
      tx_receipt = warn_sleep_reset("potion confirmation", 1)
      continue

  del private_key
  return tx_receipt

def main(hero_id, quest_type, key_path=DEFAULT_KEYFILE_LOCATION):
  w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
  private_key = None # paste in your private key here for competitive autoquesting

  if private_key is None:
    encrypted_key = keys.manage_keyfile(key_path)
    p = keys.get_password(w3, encrypted_key)
    private_key = Account.decrypt(encrypted_key, p)
    LOGGER.info('loaded key')

  addr = keys.get_address(w3, private_key)
  if not addr:
    LOGGER.error("Invalid checksum-enabled account address. Bailing out.")
    exit(1)

  quest_address = get_quest_address(quest_type)
  if not quest_address:
    LOGGER.error("Unrecognized quest type " + quest_type + " : Bailing out.")
    exit(1)

  while True:
    run_quest(quest_address, quest_type, hero_id, private_key, addr)
    # fix for double chugging until L20
    if get_stamina(hero_id) < 10:
      use_item(hero_id, private_key)

  del private_key
  return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Welcome to the grinder...')
  parser.add_argument('--hero', help='input (exactly one) hero id', required=True)
  parser.add_argument('--quest', help='choose one: [mining, fishing, foraging]', required=True)
  parser.add_argument('--keyfile', help='relative path to keyfile (default: config/keystore.json)', required=False)
  args = vars(parser.parse_args())
  if (args['keyfile']):
    main(int(args['hero']), args['quest'], args['keyfile'])
  else:
    main(int(args['hero']), args['quest'])

