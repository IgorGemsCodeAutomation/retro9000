from typing import List
from eth_typing import ChecksumAddress, HexStr, Address, Hash32
from models import Explorer, NativeCurrency
from web3 import Web3, HTTPProvider
from web3.middleware import Middleware
from hexbytes import HexBytes
import random

class Chain():

    #provider: HTTPProvider

    def __init__(
            self,
            rpc: str,
            rpcs: List[str],
            id: int,
            *,
            explorers: list[Explorer] = None,
            name: str = None,
            short_name: str = None,
            title: str = None,
            info_url: str = None,
            native_currency: NativeCurrency = None,
            eip1559: bool = True,
            # Connection settings
            provider_timeout: int = 15,
            proxy: str = None,
            # Middleware
            use_poa_middleware: bool = True
    ):
        self.rpc = rpc
        self.rpcs = rpcs
        self.explorers = explorers
        self.id = id
        self.name = name
        self.short_name = short_name
        self.title = title
        self.info_url = info_url
        self.native_currency = native_currency or NativeCurrency()
        self.eip1559 = eip1559
        # http_provider = HTTPProvider(rpc, request_kwargs={"timeout": provider_timeout})
        # http_provider.cache_allowed_requests = True
        # super().__init__(provider=http_provider)
        #
        # if use_poa_middleware:
        #     self.middleware_onion.inject(Middleware, layer=0)

        self.proxy = proxy


    def __str__(self):
        return f"{self.name}"

    def change_rpc(self):
        while True:
            new_rpc = random.choice(self.rpcs)
            if self.rpc != new_rpc and new_rpc.startswith("http") and "$" not in new_rpc:
                self.rpc = new_rpc
                break


    def __repr__(self):
        if  'provider' in self and self.provider != None:
            return f"{self.__class__.__name__}(rpc={self.provider.endpoint_uri}, name={self.name})"
        else:
            return f"{self.__class__.__name__}(rpc={self.rpc}, name={self.name})"

    @property
    def proxy(self) ->  str | None:
        return self.proxy

    @proxy.setter
    def proxy(self, proxy: str | None):
        if proxy is None:
            # if "proxy" in self.provider._request_kwargs:
            #     del self.provider._request_kwargs["proxy"]
            return

        self.proxy = f"{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"

        # self.provider._request_kwargs["proxy"] = self.proxy

    def tx_urls(
            self, tx_hash: HexBytes | HexStr | str,
    ) -> list[tuple[Explorer, str]]:
        if isinstance(tx_hash, HexBytes):
            tx_hash = tx_hash.hex()

        return [(explorer, explorer.tx_url(tx_hash)) for explorer in self.explorers]