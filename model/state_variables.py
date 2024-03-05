from dataclasses import dataclass
from enum import Enum
from typing import List
import numpy as np

@dataclass
class CollateralState:
    collateral_price: float

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


def set_initial_state(initial_coll_price, num_owners):
    collateral = CollateralState(initial_coll_price)

    vault_coll_balance = 20 + 400 * np.random.random(num_owners)
    debt = 0.1 + 0.5 * np.random.random(num_owners) * initial_coll_price * vault_coll_balance
    vault_states = [VaultState(*values) for values in zip(vault_coll_balance, debt)]

    wallet_coll_balance = 5 + 10 * np.random.random(num_owners)
    wallet_stable_coin_balance = 0.1 + 0.4 * np.random.random(num_owners) * debt
    wallet_states = [WalletState(*values) for values in zip(wallet_coll_balance, wallet_stable_coin_balance)]

    strategies = np.random.choice(OwnerStrategy, num_owners)

    owners = [OwnerState(*values) for values in zip(vault_states, wallet_states, strategies)]

    stability_pool_balance =np.sum(debt - wallet_stable_coin_balance)
    stability_pool = StabilityPoolState(stability_pool_balance)
        
    initial_state = {
        "colleteral": collateral,
        "owners": owners,
        "stability_pool": stability_pool
    }

    return initial_state