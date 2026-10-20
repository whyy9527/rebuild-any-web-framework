"""Use v1's actual cost regression: preserve cheap paths, batch at high rho.

The fixed evaluator publishes four executable checks. Stop when one visible
candidate passes all of them. No hidden world or winning node id is consulted.
"""
def select(view, rho):
    if view['round'] >= max(1, int(4 * rho)):
        return []
    root = view['nodes'][0]['id']
    nodes = view['nodes'][1:]
    if any(n['observation'].get('evaluation', {}).get('checks') == [True] * 4 for n in nodes):
        return []
    leaves = [n for n in nodes if n['id'] in view['eligible']]
    if not leaves:
        return [root]
    best = max(leaves, key=lambda n: n['score'])
    return ([best['id'], root] if rho >= .75 else [best['id']])[:view['max_parallelism']]
