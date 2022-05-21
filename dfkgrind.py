#!/usr/bin/env python3

from eth_account import Account
from web3 import Web3

import json, argparse, logging, time, os, sys

from dfk.quests.professions import foraging, fishing, minning
from dfk.quests.training import arm_wrestling
from dfk.quests import quest_core_v2
import dfk.hero.hero_core as heroes

import keys, item, profile

LOG_FORMAT = '%(asctime)s|%(name)s|%(levelname)s: %(message)s'
LOGGER = logging.getLogger('dfkgrind')
LOGGER.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=sys.stdout)

DEFAULT_CONFIG_LOCATION = "config/profile.json"
DEFAULT_KEYFILE_LOCATION = "config/keystore.json"
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
  global CURRENT_RPC
  CURRENT_RPC += 1
  CURRENT_RPC %= 5
  return

def warn_sleep_reset(log, t):
  switch_rpc()
  rpc = RPC_SERVERS[CURRENT_RPC]
  LOGGER.warning("Failed {log}. Switch to {rpc}, sleep {t} sec and retry.".format(log=log,rpc=rpc,t=t))
  time.sleep(t)
  return None

def get_stamina(hero_id):
  h = None
  while h is None:
    try:
      rpc = RPC_SERVERS[CURRENT_RPC]
      h = heroes.human_readable_hero(heroes.get_hero(heroes.SERENDALE_CONTRACT_ADDRESS, hero_id,rpc))
    except Exception as e:
      LOGGER.exception(str(e))
      h = warn_sleep_reset("get hero stamina", 1)
      continue

  time_to_full = max(0, h['state']['staminaFullAt'] - int(time.time()))
  missing_stamina = time_to_full / ( 60 * 20 ) # 20 min / 1200 sec
  max_stamina = h['stats']['stamina']
  return max_stamina - missing_stamina

def sleep_for(quest_type):
  sleep_time = 0
  if quest_type == 'mining' or quest_type == 'gardening':
    sleep_time =  250 * 60
  elif quest_type == 'fishing' or quest_type == 'foraging':
    sleep_time =  140
  else: # training quests
    sleep_time =  100
  time.sleep(sleep_time)
  return

def begin_quest(quest_address, hero_id, private_key, addr):
  success = None
  while success is None:
    try:
      quest_attempts = min(5, int(get_stamina(hero_id) / 5))
      LOGGER.info('attempting to start quest')
      w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))

      quest_core_v2.start_quest(quest_address=quest_address, \
                                hero_ids=[hero_id], \
                                attempts=quest_attempts, \
                                level=1, \
                                private_key=private_key, \
                                nonce=w3.eth.getTransactionCount(addr), \
                                gas_price_gwei=DEFAULT_GAS_PRICE, \
                                tx_timeout_seconds=30, \
                                rpc_address=RPC_SERVERS[CURRENT_RPC], \
                                logger=LOGGER)
      success = True
      LOGGER.info('successfully started quest')
    except Exception as ex:
      if "already questing" in str(ex):
        break
      else:
        LOGGER.exception(ex)
        success = warn_sleep_reset("starting quest", 1)
        continue

def end_quest(quest_address, hero_id, private_key, addr):
  quest_result = None
  while quest_result is None:
    try:
      LOGGER.info('attempting to complete quest')
      w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
      tx_receipt = quest_core_v2.complete_quest(hero_id=hero_id, \
                                                private_key=private_key, \
                                                nonce=w3.eth.getTransactionCount(addr), \
                                                gas_price_gwei=DEFAULT_GAS_PRICE, \
                                                tx_timeout_seconds=30, \
                                                rpc_address=RPC_SERVERS[CURRENT_RPC], \
                                                logger=LOGGER)
      quest_result = quest_core_v2.parse_complete_quest_receipt(tx_receipt, RPC_SERVERS[CURRENT_RPC])
      LOGGER.info("Rewards: " + str(quest_result))
    except Exception as ex:
      LOGGER.exception(str(ex))
      if "no quest found" in str(ex):
        break
      else:
        quest_result = warn_sleep_reset("completing quest", 1)
        continue

  del private_key
  return tx_receipt

def use_item(hero_id, private_key, gas_price_gwei=DEFAULT_GAS_PRICE, tx_timeout_seconds=30):
  LOGGER.info("using potion")
  w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
  account = w3.eth.account.privateKeyToAccount(private_key)
  w3.eth.default_account = account.address
  nonce = w3.eth.getTransactionCount(account.address)

  contract_address = Web3.toChecksumAddress(item.CONTRACT_ADDRESS)
  contract = w3.eth.contract(contract_address, abi=item.ABI)

  try:
    tx = contract.functions.consumeItem(item.DFKSTMNPTN_ADDRESS, hero_id).buildTransaction(
      {'gasPrice': w3.toWei(gas_price_gwei, 'gwei'), 'nonce': nonce})
  except:
    raise

  ret = None
  while ret is None:
    try:
      w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
      LOGGER.info("Signing transaction")
      signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

      LOGGER.info("Sending transaction " + str(tx))
      ret = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
      LOGGER.info("Transaction successfully sent !")
    except Exception as e:
      LOGGER.exception(str(ex))
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

def main(config_path, key_path):
  private_key = None # paste in your private key here for competitive autoquesting
  addr = None # paste in your address if you want to skip using keys.py

  if private_key is None:
    w3 = Web3(Web3.HTTPProvider(RPC_SERVERS[CURRENT_RPC]))
    encrypted_key = keys.manage_keyfile(key_path)
    p = keys.get_password(w3, encrypted_key)
    private_key = Account.decrypt(encrypted_key, p)
    LOGGER.info('loaded key')

  if addr is None:
    addr = keys.get_address(w3, private_key)
    if not addr:
      LOGGER.error("Invalid checksum-enabled account address. Bailing out.")
      sys.exit(1)

  user_profile = profile.main(config_path, RPC_SERVERS[CURRENT_RPC], addr)
  for hero in user_profile:
    begin_quest(hero['quest_address'], hero['hero_id'], private_key, addr)
  input("Debug wait. Press Enter to continue with end_quest.")
  for hero in user_profile:
    end_quest(hero['quest_address'], hero['hero_id'], private_key, addr)
  '''
  while True:
    try:
      begin_quest(quest_address, hero_id, private_key, addr)
      sleep_for(quest_type)
      end_quest(quest_address, hero_id, private_key, addr)
    except Exception as ex:
      LOGGER.warning("Exception: " + str(ex) + " Restarting Bot.")
      break
  '''
  return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Welcome to the grinder...')
  parser.add_argument('--keyfile', help='relative path to keyfile (default: config/keystore.json)', required=False)
  parser.add_argument('--config', help='relative path to config file (default: config/profile.json)', required=False)
  args = vars(parser.parse_args())
  key_path = None
  config_path = None
  if not args['config']:
    config_path = DEFAULT_CONFIG_LOCATION
  else:
    config_path = args['config']
  if not args['keyfile']:
    key_path = DEFAULT_KEYFILE_LOCATION
  else:
    key_path = args['keyfile']
  main(config_path, key_path)
  os.execv(__file__, sys.argv)
