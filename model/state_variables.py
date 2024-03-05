from dataclasses import dataclass
from enum import Enum
from typing import List

INITIAL_COLL_PRICE = 3000.0

@dataclass
class CollateralState:
    collateral_price: float = INITIAL_COLL_PRICE

@dataclass
class StabilityPoolState:
    stable_coin_balance: float

@dataclass
class VaultState:
    collateral_balance: float
    debt: float
    liquidated: bool = False

@dataclass
class WalletState:
    collateral_balance: float
    stable_coin_balance: float

OwnerStrategy = Enum('OwnerStrategy', [
    'ACTIVE', # characterized by maintaining an appropriate liquidation buffer
    'SENTIMENT_DRIVEN', # following the market sentiment
    'PASSIVE', # hands-off approach
    'RANDOM', # characterized by updating the vault randomly
    'SIMPLE_COLL', # maintains liquidation buffer via simple collateral adjustment
    'SIMPLE_LOAN', # maintains liquidation buffer via simple loan adjustment
    'TRADITIONAL' # risk-averse 
])
   
@dataclass
class OwnerState:
    vault: VaultState
    wallet: WalletState
    strategy: OwnerStrategy

@dataclass
class AllOwnersState:
    owner: List[OwnerState]

