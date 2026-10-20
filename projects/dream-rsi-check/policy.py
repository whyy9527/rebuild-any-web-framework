"""Opening policy: alternate root branching and continuing the newest leaf."""
def select(view, rho):
    if view['round'] >= max(1, int(4 * rho)):
        return []
    if view['round'] % 2 == 0:
        return [view['nodes'][0]['id']]
    return [view['eligible'][-1]]
