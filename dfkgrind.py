#!/usr/bin/env python3

import getpass, eth_account, json, pathlib

def make_new_keyfile(path_obj):
  x = getpass.getpass(prompt='Paste private key: ')
  y = getpass.getpass(prompt='Enter passphrase: ')
  z = eth_account.account.Account.encrypt(x,y)
  with path_obj.open('w') as f:
    f.write(json.dumps(z))
  print('wrote encrypted keystore to config/keystore.json')
  return z

def manage_keyfile():
  key = pathlib.Path('config/keystore.json')
  if key.exists():
    print('encrypted keystore file found, loading...')
    with key.open() as f:
      encrypted_key = json.loads(f.read())
  else:
    print('keystore not found, making new key. get your MM creds ready')
    encrypted_key = make_new_keyfile(key)
  return encrypted_key

def main():
  encrypted_key = manage_keyfile()

if __name__ == '__main__':
  main()
