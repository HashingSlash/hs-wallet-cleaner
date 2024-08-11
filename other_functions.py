import algokit_utils

def quantity_as_float(Asset_ID, Int_Amount):
    if Asset_ID == 0:
        return Int_Amount/pow(10, 6)
    else: 
        algod = algokit_utils.get_algod_client()
        return Int_Amount/pow(10,algod.asset_info(Asset_ID)['params']['decimals'])
