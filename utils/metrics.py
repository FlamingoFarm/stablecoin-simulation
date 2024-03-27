def num_liquidations(owners):
    n = 0
    for owner in owners:
        if owner.vault.blocked:
            n += 1
    return n


def debt_collateral_ratio(owners, coll_price):
    collateral_value = 0
    debt = 0
    for owner in owners:
        collateral_value += owner.vault.collateral_balance * coll_price
        debt += owner.vault.debt_balance

    return debt / collateral_value
