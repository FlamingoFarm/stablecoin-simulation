from model.state_variables import OwnerStrategy, Owners
from utils.price_simulation import jump_diffusion

import numpy as np


def p_coll_price_change(params, substep, state_history, previous_state):
    new_coll_price = jump_diffusion(previous_state["coll_price"], params)[-1]
    return {
        'new_coll_price': new_coll_price
    }


def p_liquidation(params, substep, state_history, previous_state):
    owners = previous_state["owners"]
    stability_pool = previous_state["stability_pool"]
    collateral = previous_state["collateral"]

    liquidation_ratio = params["liquidation_ratio"]
    
    stability_pool_balance = stability_pool.stable_coin_balance

    for owner in owners:
        if owner.vault.debt_balance / (owner.vault.collateral_balance * collateral.price) > liquidation_ratio:
            owner.vault.blocked = True
            if stability_pool_balance > owner.vault.debt_balance:
                stability_pool_balance -= owner.vault.debt_balance
                owner.vault.debt_balance = 0
                owner.vault.collateral_balance = 0
    
    delta_stability_pool_balance = stability_pool_balance - stability_pool.stable_coin_balance

    return {"delta_stability_pool_balance": delta_stability_pool_balance, "updated_owners": owners}


def p_vault_management(params, substep, state_history, previous_state):
    owners = previous_state["owners"]
    stability_pool = previous_state["stability_pool"]
    collateral = previous_state["collateral"] 
    
    for owner in owners:
        if not owner.blocked:
            match owner.strategy:
                case OwnerStrategy.ACTIVE:
                    modify_vault_via_active_strategy(owner, stability_pool, collateral, params)
                case OwnerStrategy.PASSIVE:
                    pass
                case OwnerStrategy.RANDOM:
                    modify_vault_via_random_strategy(owner, stability_pool, collateral, params)
                case OwnerStrategy.TRADITIONAL:
                    modify_vault_via_traditional_strategy(owner, stability_pool, collateral, params)
                case _:
                    raise ValueError("Not a valid strategy")
    
    return {"updated_stability_pool": stability_pool, "updated_owners": owners}
                

def modify_vault_via_active_strategy(owner, stability_pool, collateral, params):
    '''Owner tries to keep a debt to max loan ratio between 80% and 90%'''
    liquidation_ratio = params["liquidation_ratio"]
    max_loan = (liquidation_ratio * owner.vault.collateral_balance * collateral.price)
    debt_ratio = owner.vault.debt_balance / max_loan

    # Repay loan and if there is not enough stable coin in wallet, add collateral 
    if debt_ratio > 0.9:
        # Calculates the amount of loan repayment to get a debt ratio of 85%
        loan_repayment = owner.vault.debt_balance - 0.85 * max_loan

        if loan_repayment > owner.wallet.stable_coin_balance:  
            owner.vault.debt_balance -= owner.wallet.stable_coin_balance
            owner.wallet.stable_coin_balance = 0

            # Calculates the amount of collateral that needs to be added to get a debt ratio of 85%
            add_collateral_amount = (owner.vault.debt_balance / 0.85 - max_loan) / (liquidation_ratio * collateral.price)
            if add_collateral_amount > owner.wallet.collateral_balance:
                owner.vault.collateral_balance += owner.wallet.collateral_balance
                owner.wallet.collateral_balance = 0
            else:
                owner.vault.collateral_balance += add_collateral_amount
                owner.wallet.collateral_balance -= add_collateral_amount

        else:
            owner.wallet.stable_coin_balance -= loan_repayment
            owner.vault.debt_balance -= loan_repayment

    # Take more loan or remove collateral
    if debt_ratio < 0.8:
        borrow_propability = 0.7

        # Take more loan
        if np.random.random() < borrow_propability:
            # Calculates the amount of how much loan can be taken to get a debt ratio of 85%
            borrow_amount = 0.85 * max_loan - owner.vault.debt_balance

            fee_amount = params["stability_fee"] * borrow_amount
            spending_amount = (borrow_amount - fee_amount) * (0.2 + 0.5 * np.random.random())

            stability_pool.stable_coin_balance += fee_amount + spending_amount
            owner.vault.debt_balance += borrow_amount
            owner.wallet.stable_coin_balance += borrow_amount - fee_amount - spending_amount
            owner.wallet.collateral_balance += spending_amount/collateral.price

        # Remove collateral
        else:
            # Calculates the amount of collateral that can to be removed to get a debt ratio of 85%
            removing_collateral = (max_loan - owner.vault.debt_balance / 0.85 ) / (liquidation_ratio * collateral.price)
            owner.vault.collateral_balance -= removing_collateral
            owner.wallet.collateral_balance += removing_collateral
            
    

def modify_vault_via_random_strategy(owner, stability_pool, collateral, params):
    liquidation_ratio = params["liquidation_ratio"]
    max_loan = (liquidation_ratio * owner.vault.collateral_balance * collateral.price)

    # Take more loan
    if (np.random.random() < 0.5):
        borrow_amount = 0.8 * np.random.random() * (max_loan - owner.vault.debt_balance)
        fee_amount = params["stability_fee"] * borrow_amount

        stability_pool.stable_coin_balance += fee_amount
        owner.vault.debt_balance += borrow_amount 
        owner.wallet.stable_coin_balance += borrow_amount - fee_amount
    # Repay part of loan
    else:
        repay_amount = 0.4 * np.random.random() * owner.vault.debt_balance
        if repay_amount < owner.wallet.stable_coin_balance:
            owner.wallet.stable_coin_balance -= repay_amount
            owner.vault.debt_position -= repay_amount
        else:
            owner.vault.debt_position -= owner.wallet.stable_coin_balance
            owner.wallet.stable_coin_balance = 0


def modify_vault_via_traditional_strategy(owner, stability_pool, collateral, params):
    '''Owner tries to keep a debt to max loan ratio between 50% and 70%'''
    liquidation_ratio = params["liquidation_ratio"]
    max_loan = (liquidation_ratio * owner.vault.collateral_balance * collateral.price)
    debt_ratio = owner.vault.debt_balance / max_loan

    # Repay loan and if there is not enough stable coin in wallet, add collateral 
    if debt_ratio > 0.7:
        # Calculates the amount of loan repayment to get a debt ratio of 60%
        loan_repayment = owner.vault.debt_balance - 0.6 * max_loan

        if loan_repayment > owner.wallet.stable_coin_balance:  
            owner.vault.debt_balance -= owner.wallet.stable_coin_balance
            owner.wallet.stable_coin_balance = 0

            # Calculates the amount of collateral that needs to be added to get a debt ratio of 60%
            add_collateral_amount = (owner.vault.debt_balance / 0.6 - max_loan) / (liquidation_ratio * collateral.price)
            if add_collateral_amount > owner.wallet.collateral_balance:
                owner.vault.collateral_balance += owner.wallet.collateral_balance
                owner.wallet.collateral_balance = 0
            else:
                owner.vault.collateral_balance += add_collateral_amount
                owner.wallet.collateral_balance -= add_collateral_amount

        else:
            owner.wallet.stable_coin_balance -= loan_repayment
            owner.vault.debt_balance -= loan_repayment

    # Take more loan or remove collateral
    if debt_ratio < 0.5:
        borrow_propability = 0.6

        # Take more loan
        if np.random.random() < borrow_propability:
            # Calculates the amount of how much loan can be taken to get a debt ratio of 60%
            borrow_amount = 0.6 * max_loan - owner.vault.debt_balance

            fee_amount = params["stability_fee"] * borrow_amount
            spending_amount = (borrow_amount - fee_amount) * (0.2 + 0.5 * np.random.random())

            stability_pool.stable_coin_balance += fee_amount + spending_amount
            owner.vault.debt_balance += borrow_amount
            owner.wallet.stable_coin_balance += borrow_amount - fee_amount - spending_amount
            owner.wallet.collateral_balance += spending_amount/collateral.price
            
        # Remove collateral
        else:
            # Calculates the amount of collateral that can to be removed to get a debt ratio of 60%
            removing_collateral = (max_loan - owner.vault.debt_balance / 0.6 ) / (liquidation_ratio * collateral.price)
            owner.vault.collateral_balance -= removing_collateral
            owner.wallet.collateral_balance += removing_collateral