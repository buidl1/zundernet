# zundernet
_Python3 wallet gui for Pirate Chain_

Zundernet is new proof of concept wallet, with features not available in other wallets.
It is an experimental software. Except changes and updates as we progress through the development.

It should work on Windows and Linux as long as user has python3 installed with following libraries: `tk, ttk, psutil, pycryptodome` and some other standard libraries.

## Requirements

- Python version >=3.7 (make sure you are using the right version of Python by issuing `python3 --version` in Linux terminal)
- To use the app you also need Komodo/Pirate deamon
- zcash params (Zcash params for Windows and Linux may be downloaded using attached scripts (komodo-win, komodo-lin) containing also komodo deamons)
- For database you can sync fresh from the network or use bootstrap

**Important: Before you start - backup your wallet.dat file just in case.**

## Dependencies
Install the following dependencies to run Zundernet properly:
```shell
sudo apt-get install python3-tk 
sudo apt-get install python3-pip
pip3 install pycryptodome
pip3 install psutil
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
