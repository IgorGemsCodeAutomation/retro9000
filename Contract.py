from eth_typing import ChecksumAddress
from web3 import Web3
import os
import json
from web3 import Web3
from utils import RPCS
from loguru import logger
from utils import Chains, Chains_testnets

class Contract:
    def __init__(self, web3: Web3, abi: str = '', address: ChecksumAddress = None):
        self.contract = self.load_contract(web3, abi, address) #name?

    def load_contract(self, web3, abi_name, address):
        address = web3.toChecksumAddress(address)
        return web3.eth.contract(address=address, abi=self._load_abi(abi_name))

    def _load_abi(self, name):
        path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
        with open(os.path.abspath(path + f"{name}.json")) as f:
            abi: str = json.load(f)
        return abi

    def isExitChain(self, chainId):
        _all = [Chains, Chains_testnets]
        name = 'None'
        for _ in _all:
            try:
                name = Chains(chainId).name
                break
            except Exception as e:
                logger.error(e)

        return name

    def __repr__(self):
        chainId = self.chain.eth.chainId
        return f"{self.__class__.__name__}(address={self.contract.address}, chain.name={self.isExitChain(chainId)})"
