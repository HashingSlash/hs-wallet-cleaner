# hs-wallet-cleaner
Algorand wallet cleaner.

Trades out of held assets with adjustable maximum price.

No fees beyond standard network and direct AMM swap fees.

download and open project folder in VS Code. 
create project environment in VS code, use requirements.txt when prompted. 
paste the mnemonic for the wallet you wish to clean into the .env file. 
OPTIONAL: If wallet is rekeyed, paste signing key mnemonic into .env file also. 
open the main.py file. 
OPTIONAL: within the main.py file the function 'clean_wallets' is called. The final argument (number 1 by default) is the maximum amount to empty an assets holdings via trading.  Quoted Above that limit, assets will be ignored. 
Run the main.py script (often F5). 
script will work iterate through held assets. 
Post run: Edit the .env file to remove wallet private keys. 