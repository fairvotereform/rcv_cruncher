from functools import lru_cache, partial
from dbfread import DBF
import scipy.linalg
import scipy.optimize
from collections import Counter, defaultdict
from itertools import product
import csv

# cruncher imports
from .cache_helpers import save
from .ballot_stats import exhausted_or_undervote, cleaned, overvote


@save
def precincts(ctx):
    return [i.precinct.replace('/', '+')
            for i in ctx['parser'](ctx)]


@save
def precinct_totals(ctx):
    return Counter(precincts(ctx))


@save
def precinct_overvotes(ctx):
    return Counter(p for p, o in zip(precincts(ctx), overvote(ctx)) if o)


@save
def precinct_participation(ctx):
    return Counter(p for p, o in zip(precincts(ctx), cleaned(ctx)) if o)


@save
def precinct_ranked_finalists(ctx):
    return Counter(p for p, o in zip(precincts(ctx), exhausted_or_undervote(ctx)) if not o)


@save
def precinct_overvote_rate(ctx):
    return {k: precinct_overvotes(ctx)[k] / v for k, v in precinct_totals(ctx).items()}


@save
def unique_precincts(ctx):
    return set(precincts(ctx))


@lru_cache(maxsize=2)
def processed_sov(file_name):
    result = {}
    asian_ethnicities = ['kor', 'jpn', 'chi', 'ind', 'viet', 'fil']
    with open(file_name) as f:
        reader = csv.DictReader(f)
        for i in reader:
            result[i['srprec']] = {
                'total': int(i['totreg_r']),
                'latin': sum(int(i[k]) for k in i if k.startswith('hisp')),
                'asian': sum(int(i[k]) for k in i
                             if any(map(k.startswith, asian_ethnicities)))
            }
    return result


@save
def precinct_percent_sov(ctx, precinct, ethnicity):
    total = 0
    ethnic = 0
    int_year = int(ctx['date'])
    year = str(min(int_year + int_year % 2, 2018))
    precincts = split_precincts(precinct)
    file_name = 'precincts/SOV/c{}_g{}_voters_by_g{}_srprec.csv'.format(ctx['county'], year[-2:], year[-2:])
    for p in precincts:
        try:
            ethnic += processed_sov(file_name)[p][ethnicity]
            total += processed_sov(file_name)[p]['total']
        except KeyError:
            print('\tSOV:\tPOSSIBLE MISSING OR CONSOLIDATED PRECINCT IN SOV:', p)

    return ethnic / total if total else 0


@lru_cache(maxsize=11)
def cvap_by_block(file_name):
    table = DBF(file_name)
    counties = {'001', '075'}
    result = {}
    for row in table:
        block = next(v for k, v in row.items() if 'BLOCK' in k)
        cvap = next(v for k, v in row.items() if 'CVAP' in k)
        if block[2:5] in counties:
            result[block] = cvap
    return result


@save
def block_ethnicities(ctx, ethnicity):
    year = {'2019': '2017', '2018': '2017', '2012': '2013'}.get(ctx['date'], ctx['date'])
    file_name = 'precincts/CVAPBLOCK/{}/{}_cvap_by_block.dbf'.format(year, ethnicity.replace(' ', '_'))
    return cvap_by_block(file_name)


@save
def sr_blk_map(file_name):
    _, state, county, *_ = file_name.split('/')
    result = defaultdict(list)
    with open(file_name) as f:
        next(f)
        for line in f:
            srprec, tract, block, blkreg, srtotreg, pctsrprec, blktotreg, pctblk = \
                [i.strip('"') for i in line.strip('\n').split(',')]
            result[srprec].append((state + county + tract.zfill(6) + block, float(pctblk) / 100))
    return dict(result)


def split_precincts(precinct):
    split = precinct.split('+')
    if len(split) == 1 or len(set(map(len, split))) == 1:
        return split
    first = split[0]
    return [first[:-len(i)] + i for i in split]


@save
def precinct_ethnicity_totals(ctx, precinct, ethnicity):
    ethnic = 0
    int_year = int(ctx['date'])
    year = str(int_year - int_year % 2)
    precinct_block_fraction = 'precincts/precinct_block_maps/06/{}/c{}_g{}_sr_blk_map.csv'.format(
        ctx['county'], ctx['county'], year[-2:])

    precincts = split_precincts(precinct)
    for p in precincts:
        try:
            blocks = sr_blk_map(precinct_block_fraction)[p]
        except:
            print("\tCVAP:\tPOSSIBLE MISSING PRECINCT:", p)
            continue
        for (b, f) in blocks:
            for eth in cvap_ethnicities(ethnicity):
                ethnic += block_ethnicities(ctx, eth)[b] * float(f)
    return ethnic


@save
def election_ethnic_cvap_totals(ctx, ethnicity):
    if ctx['state_code'] is None or int(ctx['date']) < 2012:
        return None or None
    return sum(precinct_ethnicity_totals(ctx, p, ethnicity)
               for p in unique_precincts(ctx))


def cvap_ethnicities(eth):
    return {
        'black': ['Black or African American Alone'],
        'white': ['White Alone'],
        'latin': ['Hispanic or Latino'],
        'asian': ['Asian Alone'],
        'total': ['Total'],
        'other': ['American Indian or Alaska Native Alone',
                  'Native Hawaiian or Other Pacific Islander Alone',
                  'American Indian or Alaska Native and White', 'Asian and White',
                  'Black or African American and White',
                  'American Indian or Alaska Native and Black or African American',
                  'Remainder of Two or More Race Responses'],
    }[eth]


@save
def precinct_percent_cvap(ctx, precinct, ethnicity):
    total = 0
    ethnic = 0
    int_year = int(ctx['date'])
    year = str(int_year - int_year % 2)
    precinct_block_fraction = 'precincts/precinct_block_maps/06/{}/c{}_g{}_sr_blk_map.csv'.format(
        ctx['county'], ctx['county'], year[-2:])

    precincts = split_precincts(precinct)
    for p in precincts:
        try:
            blocks = sr_blk_map(precinct_block_fraction)[p]
        except:
            print("\tCVAP:\tPOSSIBLE MISSING PRECINCT:", p)
            continue
        for (b, f) in blocks:
            for eth in cvap_ethnicities(ethnicity):
                ethnic += block_ethnicities(ctx, eth)[b] * float(f)
            total += block_ethnicities(ctx, 'Total')[b] * float(f)
    return ethnic / total if total else 0


def precinct_estimate(eth, ethnicity_rate, precinct_metric, ctx):
    '''
    assumes precinct explains behavior
    '''
    if ctx['state_code'] is None or int(ctx['date']) < 2012:
        return None
    numerator = 0
    for precinct, good_ballots in precinct_metric(ctx).items():
        numerator += good_ballots * ethnicity_rate(ctx, precinct, eth)
    return numerator


def ethnicity_estimate(eth, ethnicity_rate, precinct_metric, ctx):
    '''
    assumes group status explains behavior
    '''
    if ctx['state_code'] is None or int(ctx['date']) < 2012:
        return None
    b = []
    A = []
    for precinct, total in precinct_totals(ctx).items():
        b.append(precinct_metric(ctx).get(precinct, 0))
        pct = ethnicity_rate(ctx, precinct, eth)
        specific = total * pct
        general = total * (1 - pct)
        A.append([specific, general])
    rate = scipy.optimize.lsq_linear(A, b, (0, 1))['x'][0]
    return sum(rate * i[0] for i in A)

def asian_ethnic_cvap_totals(ctx):
    return election_ethnic_cvap_totals(ctx, 'asian')


def black_ethnic_cvap_totals(ctx):
    return election_ethnic_cvap_totals(ctx, 'black')


def latin_ethnic_cvap_totals(ctx):
    return election_ethnic_cvap_totals(ctx, 'latin')


def white_ethnic_cvap_totals(ctx):
    return election_ethnic_cvap_totals(ctx, 'white')


def cvap_totals(ctx):
    return election_ethnic_cvap_totals(ctx, 'total')


def ethnicity_stats_func_list():

    STAT_ESTIMATORS = [precinct_estimate, ethnicity_estimate]
    PRECINCT_STATS = [precinct_participation, precinct_ranked_finalists, precinct_overvotes]
    PRECINT2ETHNICITY = [precinct_percent_cvap, precinct_percent_sov]
    ETHS = ['black', 'white', 'latin', 'asian', 'other']
    ETHNICITY_STATS = [partial(*prod)
                       for prod in product(STAT_ESTIMATORS, ETHS, PRECINT2ETHNICITY, PRECINCT_STATS)
                       if prod[1] in {'latin', 'asian'} or prod[2].__name__[-3:] != 'sov']

    for f in ETHNICITY_STATS:
        f.__name__ = f.func.__name__ + '(' + ','.join(a.__name__ if callable(a) else str(a) for a in f.args) + ')'

    ETHNICITY_STATS += [cvap_totals, asian_ethnic_cvap_totals,
                        black_ethnic_cvap_totals, latin_ethnic_cvap_totals,
                        white_ethnic_cvap_totals]

    return ETHNICITY_STATS
