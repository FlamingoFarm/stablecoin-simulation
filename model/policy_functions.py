from model.state_variables import OwnerStrategy, Owners
from utils.price_simulation import jump_diffusion


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
    updated_owners = owners

    return {"delta_stability_pool_balance": delta_stability_pool_balance, "updated_owners": updated_owners}


def p_vault_management(params, substep, state_history, previous_state):
    owners = previous_state["owners"]
    stability_pool = previous_state["stability_pool"]
    collateral = previous_state["collateral"]

    liquidation_ratio = params["liquidation_ratio"]
    stability_fee = params["stability_fee"]

    stability_pool_balance = stability_pool.stable_coin_balance   
    
    for owner in owners:
        if not owner.blocked:
            match owner.strategy:
                case OwnerStrategy.ACTIVE:
                    modify_vault_via_active_strategy(owner)
                case OwnerStrategy.PASSIVE:
                    pass
                case OwnerStrategy.RANDOM:
                    modify_vault_via_random_strategy(owner)
                case OwnerStrategy.SIMPLE_COLL:
                    modify_vault_via_simple_coll_strategy(owner)
                case OwnerStrategy.SIMPLE_LOAN:
                    modify_vault_via_simple_loan_strategy(owner)
                case OwnerStrategy.TRADITIONAL:
                    modify_vault_via_traditional_strategy(owner)
                case _:
                    raise ValueError("Not a valid strategy")
                

def modify_vault_via_active_strategy(owner):
    pass

def modify_vault_via_random_strategy(owner):
    pass

def modify_vault_via_simple_coll_strategy(owner):
    pass

def modify_vault_via_simple_loan_strategy(owner):
    pass

def modify_vault_via_traditional_strategy(owner):
    pass