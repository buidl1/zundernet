# zundernet
_Python3 wallet GUI for [Pirate Chain](https://pirate.black/)_

Zundernet is new proof of concept wallet, with features not available in other wallets.  
[NEW] Decentralized on-chain in-wallet forum over private blockchain is there!

It works with Pirate (komodod or pirated) .

**Why Pirate Chain?** Two reasons:
1. Proven double spend protection & 51% attack prevention via Komodo Platform's dPoW (delayed Proof of Work) tech
2. Forced private blockchain, using ZEC tech but with forced p2p tx (biggest anon set among private chains).

NOTE: when using zundernet do not run Pirate at the same time with different wallets.

## List of features:

Big:
1. Decentralized on-chain in-wallet forum
3. address book
4. messeging arbitrary length message with signatures (recognizing sender - allows for chat threading)
5. transaction history stored in DB (possible to view sent transactions details without wallet syncing)
6. initial loading of wallet in view mode without running blockchain (e.g. if you only need to copy address no need to wait to sync)
7. handling multiple wallets in data directory
8. wallet and database encryption on closing

Small:
1. amounts rounding
2. handling many addresses - filtering addresses by category
3. creating new wallet by default with random name - to not touch the default one
4. easy merging - z_mergetoaddress
5. able to send many tx in a single one (z_sendmany)
6. easy maintenance - export, import options in gui layer

It is an experimental software. Expect changes and updates as we progress through the development.

It should work on Windows and Linux as long as user has python3 installed with following libraries: `pyside2, pycryptodome` and some other standard libraries.

## Requirements

- Python version >=3.7 (make sure you are using the right version of Python by issuing `python3 --version` in Linux terminal)
- To use the app you also need Komodo/Pirate deamon
- zcash params (Zcash params for Windows and Linux may be downloaded using attached scripts (komodo-win, komodo-lin) containing also komodo deamons)
- For database you can sync fresh from the network or use bootstrap
- USB flash drive to keep backup of encrypted wallet.dat file

**Important: Before you start - backup your wallet.dat file just in case.**

## Dependencies
Install the following dependencies to run Zundernet properly:
```shell
sudo apt-get install python3-pip qt5-default
pip3 install pycryptodome
pip3 install pyside2
pip3 install psutil
pip3 install ssd
```
## Run Zundernet
When all above conditions are met you should run:

1. Windows, cmd:
```shell
python zundernet.py
```
2. Linux, terminal:
```shell
python3 zundernet.py
```
Then you point the app to komodo-cli and wallet file (if you are running custom data dir) to be able to use it.
