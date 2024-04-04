from model.state_variables import OwnerStrategy
from utils.price_simulation import jump_diffusion

import numpy as np


def p_coll_price(params, substep, state_history, previous_state):
    updated_coll_price = jump_diffusion(previous_state["collateral"].price, params)[-1]
    return {"updated_coll_price": updated_coll_price}


def p_liquidation(params, substep, state_history, previous_state):
    owners = previous_state["owners"]
    stability_pool = previous_state["stability_pool"]
    collateral = previous_state["collateral"]

    liquidation_ratio = params["liquidation_ratio"]

    stability_pool_balance = stability_pool.stable_coin_balance

    for owner in owners:
        if (
            owner.vault.collateral_balance > 0
            and owner.vault.debt_balance
            / (owner.vault.collateral_balance * collateral.price)
            > liquidation_ratio
        ):
            owner.vault.blocked = True
            if stability_pool_balance >= owner.vault.debt_balance:
                stability_pool_balance -= owner.vault.debt_balance
                owner.vault.liquidated_debt = owner.vault.debt_balance
                owner.vault.liquidated_collateral = (
                    owner.vault.collateral_balance * collateral.price
                )
                owner.vault.debt_balance = 0
                owner.vault.collateral_balance = 0
    return {
        "updated_stability_pool_balance": stability_pool_balance,
        "updated_owners": owners,
    }


def p_vault_management(params, substep, state_history, previous_state):
    owners = previous_state["owners"]
    stability_pool = previous_state["stability_pool"]
    collateral = previous_state["collateral"]

    for owner in owners:
        if not owner.vault.blocked:
            match owner.strategy:
                case OwnerStrategy.RISKY:
                    modify_vault_via_active_strategy(
                        owner, stability_pool, collateral, params, 0.85, 0.95
                    )
                case OwnerStrategy.PASSIVE:
                    pass
                case OwnerStrategy.IRRATIONAL:
                    modify_vault_via_irrational_strategy(
                        owner, stability_pool, collateral, params
                    )
                case OwnerStrategy.RISK_AVERSE:
                    modify_vault_via_active_strategy(
                        owner, stability_pool, collateral, params, 0.4, 0.6
                    )
                case _:
                    raise ValueError("Not a valid strategy")

    return {
        "updated_stability_pool_balance": stability_pool.stable_coin_balance,
        "updated_owners": owners,
    }


########################
### Helper functions ###
########################


def modify_vault_via_active_strategy(
    owner, stability_pool, collateral, params, lower, upper
):
    """Owner tries to keep a debt to max loan ratio between lower and upper"""
    liquidation_ratio = params["liquidation_ratio"]
    max_loan = liquidation_ratio * owner.vault.collateral_balance * collateral.price
    debt_ratio = owner.vault.debt_balance / max_loan
    middle = (lower + upper) / 2

    def repay_loan():
        """Calculates the amount of loan repayment to get a debt ratio of middle. If there is not enough, add collateral."""
        loan_repayment = owner.vault.debt_balance - middle * max_loan

        if loan_repayment > owner.wallet.stable_coin_balance:
            owner.vault.debt_balance -= owner.wallet.stable_coin_balance
            owner.wallet.stable_coin_balance = 0

            add_collateral_amount = (owner.vault.debt_balance / middle - max_loan) / (
                liquidation_ratio * collateral.price
            )
            if add_collateral_amount > owner.wallet.collateral_balance:
                owner.vault.collateral_balance += owner.wallet.collateral_balance
                owner.wallet.collateral_balance = 0
            else:
                owner.vault.collateral_balance += add_collateral_amount
                owner.wallet.collateral_balance -= add_collateral_amount

        else:
            owner.wallet.stable_coin_balance -= loan_repayment
            owner.vault.debt_balance -= loan_repayment

    def add_collateral():
        """Calculates the amount of collateral that needs to be added to get a debt ratio of middle. If there is not enough, repay loan."""
        add_collateral_amount = (owner.vault.debt_balance / middle - max_loan) / (
            liquidation_ratio * collateral.price
        )
        if add_collateral_amount > owner.wallet.collateral_balance:
            owner.vault.collateral_balance += owner.wallet.collateral_balance
            owner.wallet.collateral_balance = 0

            loan_repayment = (
                owner.vault.debt_balance
                - middle
                * liquidation_ratio
                * owner.vault.collateral_balance
                * collateral.price
            )
            if loan_repayment > owner.wallet.stable_coin_balance:
                owner.vault.debt_balance -= owner.wallet.stable_coin_balance
                owner.wallet.stable_coin_balance = 0
            else:
                owner.wallet.stable_coin_balance -= loan_repayment
                owner.vault.debt_balance -= loan_repayment
        else:
            owner.vault.collateral_balance += add_collateral_amount
            owner.wallet.collateral_balance -= add_collateral_amount

    def take_loan():
        """Calculates the amount of how much loan can be taken to get a debt ratio of middle."""
        borrow_amount = middle * max_loan - owner.vault.debt_balance

        fee_amount = params["stability_fee"] * borrow_amount
        spending_amount = (borrow_amount - fee_amount) * (
            0.2 + 0.5 * np.random.random()
        )

        stability_pool.stable_coin_balance += fee_amount + spending_amount
        owner.vault.debt_balance += borrow_amount
        owner.wallet.stable_coin_balance += borrow_amount - fee_amount - spending_amount
        owner.wallet.collateral_balance += spending_amount / collateral.price

    def remove_collateral():
        """Calculates the amount of collateral that can to be removed to get a debt ratio of middle."""
        removing_collateral = (max_loan - owner.vault.debt_balance / middle) / (
            liquidation_ratio * collateral.price
        )
        owner.vault.collateral_balance -= removing_collateral
        owner.wallet.collateral_balance += removing_collateral

    if debt_ratio > upper:
        repay_propability = 0.5

        if np.random.random() < repay_propability:
            repay_loan()
        else:
            add_collateral()

    if debt_ratio < lower:
        borrow_propability = 0.5

        if np.random.random() < borrow_propability:
            take_loan()
        else:
            remove_collateral()


def modify_vault_via_irrational_strategy(owner, stability_pool, collateral, params):
    liquidation_ratio = params["liquidation_ratio"]
    max_loan = liquidation_ratio * owner.vault.collateral_balance * collateral.price

    def take_loan():
        borrow_amount = 0.8 * np.random.random() * (max_loan - owner.vault.debt_balance)
        fee_amount = params["stability_fee"] * borrow_amount

        stability_pool.stable_coin_balance += fee_amount
        owner.vault.debt_balance += borrow_amount
        owner.wallet.stable_coin_balance += borrow_amount - fee_amount

    def repay_loan():
        repay_amount = 0.4 * np.random.random() * owner.vault.debt_balance
        if repay_amount < owner.wallet.stable_coin_balance:
            owner.wallet.stable_coin_balance -= repay_amount
            owner.vault.debt_balance -= repay_amount
        else:
            owner.vault.debt_balance -= owner.wallet.stable_coin_balance
            owner.wallet.stable_coin_balance = 0

    def add_collateral():
        add_collateral_amount = (
            0.8 * np.random.random() * owner.wallet.collateral_balance
        )

        owner.vault.collateral_balance += add_collateral_amount
        owner.wallet.collateral_balance -= add_collateral_amount

    def remove_collateral():
        removing_collateral_amount = (
            0.8
            * np.random.random()
            * (max_loan - owner.vault.debt_balance)
            / (liquidation_ratio * collateral.price)
        )
        owner.vault.collateral_balance -= removing_collateral_amount
        owner.wallet.collateral_balance += removing_collateral_amount

    if np.random.random() < 0.4:
        if np.random.random() < 0.5:
            take_loan()
        else:
            repay_loan()

    elif np.random.random() < 0.7:
        if np.random.random() < 0.5:
            add_collateral()
        else:
            remove_collateral()
