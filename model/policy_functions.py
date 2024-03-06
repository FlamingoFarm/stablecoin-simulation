from utils.price_simulation import jump_diffusion


def p_coll_price_change(params, substep, state_history, previous_state):
    new_coll_price = jump_diffusion(previous_state["coll_price"], params)
    return {
        'new_coll_price': new_coll_price
    }