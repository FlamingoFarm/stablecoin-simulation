from model.state_variables import Collateral, StabilityPool


def s_collateral(params, substep, state_history, prev_state, policy_input):
    coll_price = policy_input["updated_coll_price"]
    collateral = Collateral(coll_price)
    return ("collateral", collateral)


def s_stability_pool(params, substep, state_history, prev_state, policy_input):
    stability_pool_balance = policy_input["updated_stability_pool_balance"]
    stability_pool = StabilityPool(stability_pool_balance)
    return ("stability_pool", stability_pool)


def s_owners(params, substep, state_history, prev_state, policy_input):
    owners = policy_input["updated_owners"]
    return ("owners", owners)
