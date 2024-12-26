from web3 import Web3
from eth_account.messages import encode_defunct
from loguru import logger
import json
import os
import time
import random
from utils import RPCS
from enum import Enum
import functools
from Contract import Contract
ETH = '0x0000000000000000000000000000000000000000'


USER_GAS_PRICE = 15

def is_gasL1_low():
    w3 = Web3(Web3.HTTPProvider(RPCS["eth"]["rpc"]))
    while True:
        gasPrice = Web3.fromWei(w3.eth.gasPrice, 'gwei')
        if gasPrice > USER_GAS_PRICE:
            logger.info(f'gas in ethereum to high - {gasPrice}, sleep 30s')
            time.sleep(30)
        else:
            break

class RollupChain(Enum):
    optimism = 1
    arbitrum = 2
    era = 3
    ethereum = 4

class NotEip1559(Enum):
    optimism = 1
    bsc = 2
    fantom = 3
    harmony = 4


# def load_contract(web3, abi_name, address):
#     address = web3.toChecksumAddress(address)
#     return web3.eth.contract(address=address, abi=_load_abi(abi_name))
#
# def _load_abi(name):
#         path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
#         with open(os.path.abspath(path + f"{name}.abi")) as f:
#             abi: str = json.load(f)
#         return abi

def estimateFasPrise(w3, tx):
    errors = {}

    provider = w3.provider.endpoint_uri
    for chain in RPCS:
        if RPCS[chain]['rpc'] == provider:
            native_token = RPCS[chain]["token"]

    is_prise_cost = False
    attempts = 5
    while not is_prise_cost:
        try:
            if 'gasPrice' in tx and  type(tx["gasPrice"]).__name__ == 'float':
                tx.update({'gasPrice': int(tx["gasPrice"])})
            if 'maxFeePerGas' in tx and type(tx['maxFeePerGas']).__name__ == 'float':
                tx.update({'maxFeePerGas': int(tx["maxFeePerGas"])})
            if 'maxPriorityFeePerGas' in tx and type(tx['maxPriorityFeePerGas']).__name__ == 'float':
                tx.update({'maxPriorityFeePerGas': int(tx["maxPriorityFeePerGas"])})
            gasLimit = w3.eth.estimateGas(tx)
            tx.update({'gas': int(gasLimit * 11 / 10)})
            is_prise_cost = True
        except Exception as e:
            errors = e
            logger.info(e)
            # if type(e).__name__ == 'ValueError' and 'message' in e.args[0] and e.args[0]["message"] == "insufficient funds for transfer":
            #     logger.info(f'not enough balance on wallet - {native_token}')
            #     break
            logger.info('timeout 1 sec')
            time.sleep(1)
            attempts -=1
            if attempts == 0:
                break

    return {'tx': tx, 'errors': errors}

def get_tx_type(eip1559, func_type, params, wallet, to, tx_data):
    function = params["function"]
    w3 = params["w3"]
    nonce = params["nonce"]

    if not eip1559:
        tx = {
            'chainId': w3.eth.chain_id,
            'from': Web3.toChecksumAddress(wallet.address),
            'gas': 0,
            'gasPrice': w3.eth.gasPrice,
            'nonce': nonce,
        }
    else:
        tx = {
            'chainId': w3.eth.chain_id,
            'from': Web3.toChecksumAddress(wallet.address),
            'gas': 0,
            'maxFeePerGas': int(max(w3.eth.gasPrice, w3.eth.gas_price) * 1.1),
            'maxPriorityFeePerGas': int(min(w3.eth.gasPrice, w3.eth.gas_price)),
            'nonce': nonce,
        }

    if func_type:
        tx_func = function.buildTransaction(tx)
    else:
        tx_func = tx
        tx_func.update({'to': to})
        if tx_data != None:
            tx_func.update({'data': tx_data})

    return tx_func


def is_approved(w3, address, token_spender, token, limit, type_token):
    amount = (
             Contract(w3, type_token, token).contract
            .functions.allowance(address, token_spender)
            .call()
    )
    if type(limit) != None:
        max_approval_check_int = limit
    else:
        max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
        max_approval_check_int = int(max_approval_check_hex, 16)

    if amount >= max_approval_check_int:
        return True
    else:
        return False

def approve(w3, wallet, token, token_spender, max_approval, type, chain):
    max_approval_int = int(f"0x{64 * 'f'}", 16)
    max_approval = max_approval_int if not max_approval else max_approval

    function = Contract(w3, type, token).contract.functions.approve(
        token_spender, max_approval
    )
    logger.warning(f"Approving {token}...")
    nonce = w3.eth.get_transaction_count(Web3.toChecksumAddress(wallet["wallet"].address))
    logger.info(f'nonce - {nonce}')
    log_value = [ f'\n>>> approve {chain.explorers[0].url}/', f'amount - {max_approval}']
    wallet['eip1559'] = chain.eip1559
    Transaction.build_transaction(function, w3, wallet, chain ,log_value)

def check_approval(method):
    @functools.wraps(method)
    def approved(account, *args, **kwargs):

        w3 = account.web3

        token = args[0] if args[0] != ETH else None
        token_spender = args[1] if args[1] != ETH else None
        max_approval = args[2] if type(args[2]) == int else None
        amount = args[3]
        type_token = args[4] if type(args[4]) != None else None
        chain = args[5] if args[5] != None else 'ethereum'

        _new = [_arg for idx, _arg in enumerate(args) if idx > 5]

        if token:
            _is_approved = is_approved(w3, Web3.toChecksumAddress(account.wallet["wallet"].address) ,Web3.toChecksumAddress(token_spender), token, max_approval, type_token)
            if not _is_approved:
                approve(w3, account.wallet, token, token_spender, max_approval, type_token, chain)

        return method(account.wallet, w3, token, token_spender, max_approval, amount, type_token, chain, _new)

    return approved

class Transaction:
    @staticmethod
    def build_transaction(function, w3, wallet, chain, log_value, value = 0, isTxBack = False, isTxReady = False, tx = None):

        if 'harmony' in wallet:
            harmony_address = wallet["harmony"]

        if 'eip1559' in wallet:
            eip1559 = wallet['eip1559']

        if isTxReady:
            wallet = wallet["wallet"]

        if not isTxReady:
            to_address = None
            tx_data = None
            if function == None:
                try:
                    if 'cex_address' in wallet:
                        to_address = Web3.toChecksumAddress(wallet["cex_address"])
                    else:
                        to_address = Web3.toChecksumAddress(wallet["to_address"])
                        tx_data = wallet["tx_data"]

                    wallet = wallet["wallet"]

                except Exception as e:
                    logger.error(e)
            else:
                wallet = wallet["wallet"]
                to_address = Web3.toChecksumAddress(wallet.address)

            nonce = w3.eth.get_transaction_count(wallet.address)
            rollup_chain = list(RollupChain)
            if chain == 'eth':
                is_gasL1_low()

            logger.info(f'base {w3.eth.gasPrice} --fee {w3.eth.gas_price}')
            _baseFeePrice = int(min(w3.eth.gasPrice, w3.eth.gas_price))
            _maxFeePrice = int(max(w3.eth.gasPrice, w3.eth.gas_price))

            func_type = False
            if function != None:
                func_type = True

            tx_params = {
                "gasBasePrice": _baseFeePrice,
                "gasMaxPrice": _maxFeePrice,
                "function": function,
                "w3": w3,
                "nonce": nonce
            }

            tx = get_tx_type(eip1559, func_type, tx_params, wallet, to_address, tx_data)

            if value > 0:
                tx.update({'value': value})

            tx.update({'gas': 1500000})

            isValid_tx = estimateFasPrise(w3, tx)


            # if bool(isValid_tx['errors']):
            #     if 'message' in isValid_tx['errors'].args[0] and isValid_tx['errors'].args[0]['message'] == 'intrinsic gas too low':
            #         tx.update({'gas': random.randint(1255000, 1555000)})
            #         isValid_tx['errors'] = None

            if bool(isValid_tx["errors"]):
                return {"transaction_status": False, 'errors': isValid_tx["errors"]}

            if isTxBack:
                return isValid_tx


        if not 'isValid_tx' in locals():
            isValid_tx = {'tx': tx, 'errors': []}

        signed_txn = w3.eth.account.sign_transaction(tx, private_key=wallet.privateKey)
        tx_token = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.opt(colors=True).info(f'{log_value[0]}tx/{w3.toHex(tx_token)} {log_value[1]}')
        task_timeout('_task')
        try:
            tx_log = w3.eth.wait_for_transaction_receipt(tx_token, timeout=6000)
            if tx_log['status'] == 1:
                return {"transaction_status": True, 'errors': isValid_tx["errors"]}
            else:
                return {"transaction_status": False, 'errors': isValid_tx["errors"]}
        except Exception as e:
            logger.info('timeout approve')


def task_timeout(_t = 'gl_task'):
    if _t == 'gl_task':
        t_sl = random.randint(80, 120)
    else:
        t_sl = random.randint(15, 25)

    logger.info(f'task break - {t_sl} second')
    time.sleep(t_sl)

def sign_message(web3, wallet, msg):
    msg = encode_defunct(text=msg)
    sign_msg = web3.eth.account.sign_message(msg, private_key=wallet["wallet"].privateKey)
    signature = sign_msg.signature.hex()

    return signature