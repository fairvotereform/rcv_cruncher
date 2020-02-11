
from cache_helpers import tmpsave

@tmpsave
def place(ctx):
    return '????'

# currently depends on place(), but should remove this dependency
def state(ctx):
    if place(ctx) in {'Berkeley', 'Oakland', 'San Francisco', 'San Leandro'}:
        return 'CA'
    if place(ctx) in {'Burlington'}:
        return 'VT'
    if place(ctx) in {'Cambridge'}:
        return 'MA'
    if place(ctx) in {'Maine'}:
        return 'ME'
    if place(ctx) in {'Minneapolis'}:
        return 'MN'
    if place(ctx) in {'Pierce County'}:
        return 'WA'
    if place(ctx) in {'Santa Fe'}:
        return 'NM'


@tmpsave
def date(ctx):
    return '????'


@tmpsave
def office(ctx):
    return '????'



def state_code(ctx):
    return {
        'Oakland': '06',
        'San Francisco': '06',
        'San Leandro': '06',
        'Berkeley': '06'
    }.get(place(ctx))


def county(ctx):
    return {
        'Oakland': '001',
        'Berkeley': '001',
        'San Leandro': '001',
        'San Francisco': '075'
    }.get(place(ctx))


def election_type(ctx):
    return 'g'


@tmpsave
def dop(ctx):
    return ','.join(str(f(ctx)) for f in [date, office, place])
