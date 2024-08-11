import algokit_utils
import os
import wallet_functions


target_wallet = algokit_utils.get_account_from_mnemonic(os.getenv("TARGET_WALLET_KEY"))
try:
    signing_wallet = algokit_utils.get_account_from_mnemonic(os.getenv("SIGNING_WALLET_KEY"))
except:
    signing_wallet = None


wallet_functions.clean_wallet(target_wallet, signing_wallet, 1)



