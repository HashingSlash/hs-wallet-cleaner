import algokit_utils
import algosdk.transaction as Transactions
from tinyman.v2.client import TinymanV2MainnetClient
from tinyman.assets import AssetAmount
import other_functions
import pactsdk
import requests
import json

def sign_and_send_transaction(TransactionToSend, Sending_Wallet, Auth_Wallet):
    Algod_Client = algokit_utils.get_algod_client()
    Sending_Wallet_Info = Algod_Client.account_info(Sending_Wallet.address)
    if 'auth-addr' in Sending_Wallet_Info and (Auth_Wallet == None or Auth_Wallet.address != Sending_Wallet_Info['auth-addr']):
        raise TypeError("Target wallet is rekeyed. Incorrect or no Signing wallet provided")
    Signed_Txn = TransactionToSend.sign(Auth_Wallet.private_key)
    Txid = Algod_Client.send_transaction(Signed_Txn)
    print(f"Transaction successful. Txid: {Txid}")

def clean_wallet(Target_Wallet, Signing_Wallet=None, Trade_Ceiling=1, Note="Hashingslash was 'ere"):
    if Signing_Wallet == None: Signing_Wallet = Target_Wallet
    
    for i in [1,2]:
        Algod_Client = algokit_utils.get_algod_client()
        Target_Wallet_Info = Algod_Client.account_info(Target_Wallet.address)
        Wallet_Asset_List = Target_Wallet_Info['assets']
        for Asset_Entry in Wallet_Asset_List:
            print('working...')
            Asset_Details = Algod_Client.asset_info(Asset_Entry['asset-id'])
            if Asset_Details['params']['creator'] != Target_Wallet.address:

                if i == 1 and Asset_Entry['amount'] != 0:
                    Sell_Quote = TradeQuote(Asset_Entry['amount'], Asset_Entry['asset-id'], 0, Target_Wallet.address)
                    if Sell_Quote.best_quote_amount_converted > 0 and Sell_Quote.best_quote_amount_converted < Trade_Ceiling:
                        TradeQuote.prepare_and_send_quote(Sell_Quote.best_platform, Sell_Quote.best_quote, Sell_Quote.best_pool, 
                                                          Target_Wallet, Signing_Wallet)

                if i == 2 and Asset_Entry['amount'] == 0:
                    print('Opting out of: ' + str(Asset_Details['params']['name']))
                    Opt_Out_Txn = Transactions.AssetTransferTxn(
                        sender=Target_Wallet.address,
                        receiver=Asset_Details['params']['creator'],
                        close_assets_to=Asset_Details['params']['creator'],
                        index=Asset_Entry['asset-id'],
                        amt=0,
                        sp=Algod_Client.suggested_params(),
                        note=Note)
                    sign_and_send_transaction(Opt_Out_Txn, Target_Wallet, Signing_Wallet)
        use_quote_to_force_short_wait = TradeQuote(1000000,0,31566704,Target_Wallet.address)


def return_asset_params(Asset_ID):
    ALGO_params = {'decimals':6,'name':'Algorand','unit-name':'ALGO'}

    Algod_Client = algokit_utils.get_algod_client()
    if Asset_ID != 0:
        Asset_Params = Algod_Client.asset_info(Asset_ID)['params']
    else: Asset_Params = ALGO_params
    return Asset_Params

class TradeQuote:

    def __init__(self, sell_amount, sell_asset_id, buy_asset_id, trading_wallet_address):
        
        self.sell_asset_id = sell_asset_id
        self.sell_asset_info = return_asset_params(sell_asset_id)
        self.buy_asset_id = buy_asset_id
        self.buy_asset_info = return_asset_params(buy_asset_id)
        self.best_quote_amount = 0
        self.best_quote = None
        self.best_pool = None
        self.best_platform = None
        
        algod_client = algokit_utils.get_algod_client()
        tinyman_client = TinymanV2MainnetClient(algod_client, trading_wallet_address)
        pact_client = pactsdk.PactClient(algod_client)


        #Tinyman Quote
        try:
            TINY_ASSET_A = tinyman_client.fetch_asset(sell_asset_id)
            TINY_ASSET_B = tinyman_client.fetch_asset(buy_asset_id)
            tinyman_pool = tinyman_client.fetch_pool(TINY_ASSET_A, TINY_ASSET_B)
            #print(tinyman_pool.asset_1.id)
            if tinyman_pool.asset_1.id == sell_asset_id:
                amount_in = AssetAmount(tinyman_pool.asset_1, sell_amount)
            elif tinyman_pool.asset_2.id == sell_asset_id:
                amount_in = AssetAmount(tinyman_pool.asset_2, sell_amount)
            tinyman_quote = tinyman_pool.fetch_fixed_input_swap_quote(amount_in=amount_in,)
            #print('\nTinyman\nInput: ' + str(other_functions.quantity_as_float(sell_asset_id, sell_amount)) +
            #    ' ' + self.sell_asset_info['name'] + '. ' + 
            #        'Output: ' + str(other_functions.quantity_as_float(buy_asset_id, tinyman_quote.amount_out.amount)) +
            #    ' ' + self.buy_asset_info['name'])
            if tinyman_quote.amount_out.amount > self.best_quote_amount:
                self.best_quote_amount = tinyman_quote.amount_out.amount
                self.best_quote = tinyman_quote
                self.best_pool = tinyman_pool
                self.best_platform = 'Tinyman'
        except Exception as error:pass#print('Tinyman quote failed: ' + str(error.__class__))



        #Pact Quote
        PACT_ASSET_A = pact_client.fetch_asset(sell_asset_id)
        PACT_ASSET_B = pact_client.fetch_asset(buy_asset_id)

        pact_pool_list = pact_client.fetch_pools_by_assets(PACT_ASSET_A, PACT_ASSET_B)
        for pact_pool in pact_pool_list:
            try:
                if pact_pool.version == 201: pact_pool_version = '2'
                else: pact_pool_version = '1'
                pact_swap_quote = pact_pool.prepare_swap(asset=PACT_ASSET_A,amount=sell_amount,slippage_pct=2)
                #print('\nPact v' + pact_pool_version + ' ' + str(pact_pool.fee_bps/100) + 'pct fee\n' + 
                #    'Input: ' + str(other_functions.quantity_as_float(sell_asset_id, sell_amount)) +
                #    ' ' + self.sell_asset_info['name'] + '. ' + 
                #        'Output: ' + str(other_functions.quantity_as_float(buy_asset_id, pact_swap_quote.effect.amount_received)) +
                #    ' ' + self.buy_asset_info['name'])
                if pact_swap_quote.effect.amount_received > self.best_quote_amount:
                    self.best_quote_amount = pact_swap_quote.effect.amount_received
                    self.best_quote = pact_swap_quote
                    self.best_pool = pact_pool
                    self.best_platform = 'Pact'
            except Exception as error:pass#print('Pact quote failed: ' + str(error.__class__))


        self.best_quote_amount_converted = other_functions.quantity_as_float(buy_asset_id, self.best_quote_amount)

        


    def prepare_and_send_quote(Platform, Quote_To_Use, Pool_To_Use, Target_Wallet, Signing_Wallet = None):
        Algod_Client = algokit_utils.get_algod_client()
        if Signing_Wallet == None: Signing_Wallet = Target_Wallet
        if Platform == 'Tinyman':
            Txn_Group = Pool_To_Use.prepare_swap_transactions_from_quote(quote=Quote_To_Use)
            Txn_Group.sign_with_private_key(Target_Wallet.address, Signing_Wallet.private_key)
            Txn_Info = Txn_Group.submit(Algod_Client)
        elif Platform == 'Pact':
            Txn_Group = Quote_To_Use.prepare_tx_group(Target_Wallet.address)
            Signed_Txn_Group = Txn_Group.sign(Signing_Wallet.private_key)
            Txn_Info = Algod_Client.send_transactions(Signed_Txn_Group)
            

        print('Trade sent')
        return Txn_Info


        

        
