from dataclasses import dataclass
from enum import Enum
from typing import List
import numpy as np


@dataclass
class Collateral:
    price: float


@dataclass
class StabilityPool:
    stable_coin_balance: float


@dataclass
class Vault:
    collateral_balance: float
    debt_balance: float
    # blocked becomes True if liquidation ratio is crossed for the first time
    # that means either the vault is fully liquidated or debt has not yet been fully paid due
    # to insufficient funds in the stability pool
    blocked: bool = False
    liquidated_collateral: float = 0.0
    liquidated_debt: float = 0.0


@dataclass
class Wallet:
    collateral_balance: float
    stable_coin_balance: float


OwnerStrategy = Enum(
    "OwnerStrategy",
    [
        "RISKY",
        "RISK_AVERSE",
        "PASSIVE",
        "IRRATIONAL",
    ],
)


@dataclass
class Owner:
    vault: Vault
    wallet: Wallet
    strategy: OwnerStrategy


@dataclass
class Owners:
    owner: List[Owner]


def set_initial_state(
    initial_coll_price: float,
    num_owners: int,
    liquidation_ratio: float,
    strategy_distribution: List[float],
):
    collateral = Collateral(initial_coll_price)

    vault_coll_balance = 20 + 400 * np.random.random(num_owners)
    debt = (
        (0.5 + 0.4 * np.random.random(num_owners))
        * liquidation_ratio
        * initial_coll_price
        * vault_coll_balance
    )
    vault_states = [Vault(*values) for values in zip(vault_coll_balance, debt)]

    wallet_coll_balance = 5 + 10 * np.random.random(num_owners)
    wallet_stable_coin_balance = 0.1 + 0.4 * np.random.random(num_owners) * debt
    wallet_states = [
        Wallet(*values)
        for values in zip(wallet_coll_balance, wallet_stable_coin_balance)
    ]

    strategies = np.random.choice(
        a=OwnerStrategy, size=num_owners, p=strategy_distribution
    )

    owners = [Owner(*values) for values in zip(vault_states, wallet_states, strategies)]

    stability_pool_balance = np.sum(debt - wallet_stable_coin_balance)
    stability_pool = StabilityPool(stability_pool_balance)

    initial_state = {
        "collateral": collateral,
        "owners": owners,
        "stability_pool": stability_pool,
    }

    return initial_state
