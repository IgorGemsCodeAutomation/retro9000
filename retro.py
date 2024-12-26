from web3 import Web3
import random
from loguru import logger
from utils import get_main_wallet, get_all_wallets, RPCS
from multiprocessing.dummy import Pool
from helpers import Transaction, check_approval, sign_message
from utils import get_chain
from Contract import Contract
from requests import Session
import json
import os

def task(wallet):
    proxies = get_proxy(wallet)
    while True:
        try:

            address = wallet['wallet'].address
            chain = get_chain(43114)
            web3 = Web3(Web3.HTTPProvider(chain.rpc))

            session = Session()
            resp = session.get(f'https://api-retro-9000.avax.network/api/auth/get-nonce/{address}', proxies=proxies)
            if resp.status_code == 200 or resp.status_code == 201:
                _d = json.loads(resp.content)
                if 'data' in _d and 'nonce' in _d['data']:
                    msg = _d['data']['nonce']

                    signature = sign_message(web3, wallet, msg)

                    params = {
                        "walletAddress": address,
                        "signature": signature
                    }

                    resp = session.post('https://api-retro-9000.avax.network/api/auth/login', json=params,proxies=proxies)
                    if resp.status_code == 200 or resp.status_code == 201:
                        userData = json.loads(resp.content)

                        if 'data' in userData and 'user' in userData['data']:
                            userInfo = userData['data']['user']

                            logger.info(f'{address}  -> userinfo - {userInfo}')

                            vote_power = {
                                "voteCount": userInfo['chill_factor']
                            }

                            resp = session.post('https://api-retro-9000.avax.network/api/vote/rounds/cm3tfqk550005irarqtv047hz/projects/cm479vkin0j53pq54alx8uwb3/vote', json=vote_power,proxies=proxies)
                            if resp.status_code == 200 or resp.status_code == 201:
                                if json.loads(resp.content)['message'] == 'Voting successful!':
                                    logger.success(f'voting -> {address}')
                                else:
                                    logger.warning(f'unluck for {address}')

                                break
        except Exception as e:
            logger.error(e)


def get_proxies():
    with open(f'{os.path.dirname(__file__)}/connection.txt', 'r') as file:
        _proxies = [row.strip() for row in file]
    return _proxies

def get_proxy(wallet):
    proxy = wallet["proxy"]

    _p = f"{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"

    proxies = {
        'http': f"socks5://{_p}",
        'https': f"socks5://{_p}"
    }

    return proxies


if __name__ == '__main__':
    list_mnemonic = get_main_wallet()
    wallets = get_all_wallets(list_mnemonic)

    proxies = get_proxies()

    multith = str(input("multithreading? - y/n \n"))
    if multith == 'Y' or multith == 'y':
        threads = int(input("number of threads? \n"))
    else:
        threads = 1

    for idx, wal in enumerate(wallets):
        wal['proxy'] = proxies[idx % len(proxies)]

    random.shuffle(wallets)
    pool = Pool(threads)

    pool.map(task, wallets)