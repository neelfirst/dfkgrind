#!/usr/bin/env python3

import getpass, eth_account, json, pathlib

def make_new_keyfile(path_obj):
  x = getpass.getpass(prompt='Paste private key: ')
  y = getpass.getpass(prompt='Enter passphrase: ')
  z = eth_account.account.Account.encrypt(x,y)
  with path_obj.open('w') as f:
    f.write(json.dumps(z))
  print('wrote encrypted keystore to config/keystore.json')
  return

def manage_keyfile():
  key = pathlib.Path('config/keystore.json')
  if key.exists():
    print('encrypted keystore file found, loading...')
    with key.open() as f:
      encrypted_key = json.loads(f.read())
    print(encrypted_key)
  else:
    print('keystore not found, making new key. get your MM creds ready')
    make_new_keyfile(key)

def main():
  manage_keyfile()

if __name__ == '__main__':
  main()
