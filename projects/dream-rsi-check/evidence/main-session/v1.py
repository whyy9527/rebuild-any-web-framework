"""First revision: continue the best visible leaf while opening a branch."""
def select(view, rho):
    if view['round'] >= max(1, int(4 * rho)):
        return []
    root = view['nodes'][0]['id']
    leaves = [n for n in view['nodes'] if n['id'] in view['eligible'] and n['id'] != root]
    if not leaves:
        return [root]
    best = max(leaves, key=lambda n: n['score'])
    return [best['id'], root][:view['max_parallelism']]
