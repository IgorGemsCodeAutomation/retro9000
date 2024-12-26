from web3 import Web3
from enum import Enum
import os
import json
from loguru import logger
import functools
from functools import lru_cache
import requests
from models import CAIP2ChainData
from typing import Iterable
from Chain import Chain

import traceback

class Chains(Enum):
    # ETH = 1
    # BSC = 56
    OPTIMISM = 10
    # POLYGON = 137
    ARBITRUM = 42161
    # AVAXC = 43114
    # FANTOM = 250
    # CELO = 42220
    # HARMONY = 1666600000
    # XDAI = 100
    # CORE = 1116
    # OPBNB = 204
    # ZKSYNC = 324
    # MOONRIVER = 1285
    # BASE = 8453

class Chains_testnets(Enum):
    SEPOLIA_ETH = 11155111
    SEPOLIA_BASE = 84532
    SEPOLIA_OPTIMISM = 11155420
    SEPOLIA_ARBITRUM = 421614
    SEPOLIA_LINEA = 59141
    SEPOLIA_MANTLE = 50031
    MITOSIS = 124832


RPCS = {
    'eth' : {'chain': 'ETH', 'chain_id': 1, 'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://etherscan.io/tx', 'token': 'ETH'},

    'optimism' : {'chain': 'OPTIMISM', 'chain_id': 10, 'rpc': 'https://rpc.ankr.com/optimism', 'scan': 'https://optimistic.etherscan.io/tx', 'token': 'ETH'},

    'bsc' : {'chain': 'BSC', 'chain_id': 56, 'rpc': 'https://rpc.ankr.com/bsc', 'scan': 'https://bscscan.com/tx', 'token': 'BNB'},

    'polygon' : {'chain': 'MATIC', 'chain_id': 137, 'rpc': 'https://polygon-rpc.com', 'scan': 'https://polygonscan.com/tx', 'token': 'MATIC'},

    'arbitrum' : {'chain': 'ARBITRUM', 'chain_id': 42161, 'rpc': 'https://rpc.ankr.com/arbitrum', 'scan': 'https://arbiscan.io/tx', 'token': 'ETH'},

    'avaxc' : {'chain': 'AVAXC', 'chain_id': 43114, 'rpc': 'https://rpc.ankr.com/avalanche', 'scan': 'https://snowtrace.io/tx', 'token': 'AVAX'},

    'fantom' : {'chain': 'FANTOM', 'chain_id': 250, 'rpc': 'https://rpc.ankr.com/fantom', 'scan': 'https://ftmscan.com/tx', 'token': 'FTM'},

    'celo' : {'chain': 'CELO', 'chain_id': 42220, 'rpc': 'https://rpc.ankr.com/celo', 'scan': 'https://celoscan.io/tx', 'token': 'CELO'},

    'harmony' : {'chain': 'HARMONY', 'chain_id': 1666600000, 'rpc': 'https://api.harmony.one', 'scan': 'https://explorer.harmony.one/tx', 'token': 'Harmony'},

    'xdai' : {'chain': 'xDai', 'chain_id': 100, 'rpc': 'https://rpc.ankr.com/gnosis', 'scan': 'https://blockscout.com/xdai/mainnet/tx', 'token': 'xDai'},

    'core' : {'chain': 'core', 'chain_id': 1116, 'rpc': 'https://rpc.coredao.org', 'scan': 'https://scan.coredao.org/tx', 'token': 'core'},

    'opbnb' : {'chain': 'OpBnb', 'chain_id': 204, 'rpc': 'https://1rpc.io/opbnb', 'scan': 'https://opbnbscan.com/tx', 'token': 'opBnb'},

    'sepolia-eth' : {'chain': 'Sepolia', 'chain_id': 11155111, 'rpc': 'https://ethereum-sepolia-rpc.publicnode.com', 'scan': 'https://sepolia.etherscan.io/tx', 'token': 'ETH'},

    'sepolia-base' : {'chain': 'Sepolia-base', 'chain_id': 84532, 'rpc': 'https://base-sepolia-rpc.publicnode.com', 'scan': 'https://sepolia.basescan.org/tx', 'token': 'ETH'},

    'sepolia-arbitrum' : {'chain': 'Sepolia', 'chain_id': 421614, 'rpc': 'https://arbitrum-sepolia.blockpi.network/v1/rpc/public', 'scan': 'https://sepolia.arbiscan.io/tx', 'token': 'ETH'},

    'sepolia-optimism' : {'chain': 'Sepolia', 'chain_id': 11155420, 'rpc': 'https://optimism-sepolia.blockpi.network/v1/rpc/public', 'scan': 'https://optimism-sepolia.blockscout.com/tx', 'token': 'ETH'},

    'sepolia-linea' : {'chain': 'Sepolia', 'chain_id': 59141, 'rpc': 'https://linea-sepolia-rpc.publicnode.com', 'scan': 'https://sepolia.lineascan.build/tx', 'token': 'ETH'},

    'sepolia-mantle' : {'chain': 'Sepolia', 'chain_id': 50031, 'rpc': 'https://rpc.sepolia.mantle.xyz', 'scan': '', 'token': 'ETH'},

    'mitosis': {'chain': 'Mitosis', 'chain_id': 124832, 'rpc': 'https://rpc.testnet.mitosis.org/', 'scan': 'https://testnet.mitosiscan.xyz/tx',
                       'token': 'Mito'},
}

@lru_cache
def request_chains_caip_2_data() -> dict[int: CAIP2ChainData]:
    response = requests.get("https://chainid.network/chains.json")
    data = response.json()
    return {chain_data["chainId"]: CAIP2ChainData(**chain_data) for chain_data in data}

def _chain_from_caip_2_data(
    chain_caip2_data: CAIP2ChainData,
    **chain_kwargs,
) -> Chain:
    target_rpc = None
    for rpc in chain_caip2_data.rpc_list:  # type: str
        if rpc.startswith("http") and "$" not in rpc:
            target_rpc = rpc
            break

    if not target_rpc:
        raise ValueError("No http rpc")

    eip1559 = "EIP1559" in {feature.name for feature in chain_caip2_data.features} if chain_caip2_data.features else False

    return Chain(
        target_rpc,
        rpcs = chain_caip2_data.rpc_list,
        id = chain_caip2_data.chain_id,
        name=chain_caip2_data.name,
        short_name=chain_caip2_data.short_name,
        info_url=chain_caip2_data.info_url,
        native_currency=chain_caip2_data.native_currency,
        explorers=chain_caip2_data.explorers,
        eip1559=eip1559,
        **chain_kwargs,
    )

def get_chain(chain_id: int, **chain_kwargs):
    chain_caip2_data = request_chains_caip_2_data()[chain_id]
    if "rpc" in chain_kwargs:
        chain_caip2_data.rpc_list.insert(0, chain_kwargs.pop("rpc"))

    return _chain_from_caip_2_data(chain_caip2_data, **chain_kwargs)

def get_chains(chain_ids: Iterable[int]):
    return [get_chain(chain_id) for chain_id in chain_ids]

# test = get_chain(Chains.BSC.value)
# logger.info(test)

def get_main_wallet():
    with open(f'{os.path.dirname(__file__)}/wallets/wallet.txt', 'r') as file:
        _main_wallet = [row.strip() for row in file]
    return _main_wallet

def get_all_wallets(list):
    web3 = Web3(Web3.HTTPProvider(RPCS["optimism"]["rpc"]))
    web3.eth.account.enable_unaudited_hdwallet_features()
    _wallets = []
    for wallet in list:
        if len(wallet) == 0:
            continue
        if len(wallet) == 64:
            cWallet = web3.eth.account.from_key(wallet)
            _wallets.append({'wallet': cWallet})
        else:
            wallet_format = wallet.split(';')
            if len(wallet_format) == 2:
                num_of_wallet = wallet_format[1]
            elif len(wallet_format) == 3:
                _indexes = wallet_format[2].split(',')
                indexes = []
                for _ind in _indexes:
                    if _ind == '':
                        continue
                    if len(_ind) > 1 and len(_ind.split('-')) == 2:
                        els = _ind.split('-')
                        _start = int(els[0])
                        _finish = int(els[1])
                        for i in range(_start, _finish):
                            indexes.append(i)
                    else:
                        indexes.append(int(_ind))
            else:
                num_of_wallet = 100
            cWallet = wallet_format[0]
            if len(wallet_format) == 3:
                num_of_wallet = indexes[len(indexes) - 1]
                _all_wallets = []
                for i in range(int(num_of_wallet)):
                    wallet_address = web3.eth.account.from_mnemonic(cWallet, account_path=f"m/44'/60'/0'/0/{i}")
                    _all_wallets.append({'wallet': wallet_address})
                _new_wallets = []
                for el in indexes:
                    _new_wallets.append(_all_wallets[el - 1])
                [_wallets.append(_new) for _new in _new_wallets]
            else:
                for i in range(int(num_of_wallet)):
                    wallet_address = web3.eth.account.from_mnemonic(cWallet, account_path=f"m/44'/60'/0'/0/{i}")
                    _wallets.append({'wallet': wallet_address})

    return _wallets

# def load_contract(web3, abi_name, address):
#     address = web3.toChecksumAddress(address)
#     return web3.eth.contract(address=address, abi=_load_abi(abi_name))
#
# def _load_abi(name):
#         path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
#         with open(os.path.abspath(path + f"{name}.abi")) as f:
#             abi: str = json.load(f)
#         return abi


def logger_wrapper(func):
    @functools.wraps(func)
    def logger_func(*args, **kwargs):
        try:
            logger.info(f'launch - {func.__name__}')
            func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
    return logger_func


def logger_wrapper_record(func):
    @functools.wraps(func)
    def logger_func(*args, **kwargs):
        try:
            logger.info(f'launch - {func.__name__}')
            wallet = args[0]
            wallets_with_res = []
            if os.path.exists(f'logs/{func.__name__}.txt'):
                with open(f'logs/{func.__name__}.txt', 'r') as file:
                    wallets_with_res = [row.strip() for row in file]
            for _w in wallets_with_res:
                if _w == wallet["wallet"].address:
                    logger.info(f'current address {_w} has already done the task')
                    return
            func(*args, **kwargs)
            with open(f'logs/{func.__name__}.txt', 'a+') as file:
                file.write(f'{wallet["wallet"].address}\n')
        except Exception as e:
            logger.error(traceback.format_exc())
    return logger_func
