
from argparse import ArgumentParser
from pprint import pprint
import csv

import manifest
from math import sqrt

# cruncher imports





ALLSTATS = [place, state, date, office,
    total, undervote, total_overvote, first_round_overvote,
    total_exhausted_by_overvote, total_fully_ranked, ranked2,
    ranked_winner,
    two_repeated, three_repeated, total_skipped, irregular, total_exhausted,
    total_exhausted_not_by_overvote, total_involuntarily_exhausted,
    effective_ballot_length, minneapolis_undervote, minneapolis_total,
    total_voluntarily_exhausted, condorcet, come_from_behind, number_of_rounds,
    finalists, winner, exhausted_by_undervote,
    naive_tally, candidates, count_duplicates,
    any_repeat, validly_ranked_winner, margin_when_2_left,
    margin_when_winner_has_majority,
    cvap_totals,
    asian_ethnic_cvap_totals, black_ethnic_cvap_totals,
    latin_ethnic_cvap_totals, white_ethnic_cvap_totals
] + ETHNICITY_STATS

def calc(ctx, functions):
    print(dop(ctx))
    results = {}
    for f in functions:
        results[f.__name__] = f(ctx)
    return results


def main():
    p = ArgumentParser()
    p.add_argument('-j', '--json', action='store_true')
    a = p.parse_args()
    if a.json:
        for k in manifest.competitions.values():
            pprint(calc(k, FUNCTIONS))
        return

    with open('results.csv', 'w', newline='\n') as f:
        w = csv.writer(f)
        w.writerow([fun.__name__ for fun in ALLSTATS])
        w.writerow([' '.join((fun.__doc__ or '').split())
                    for fun in ALLSTATS])
        for k in sorted(manifest.competitions.values(), key=lambda x: x['date']):
            if True:  # k['office'] == 'Democratic Primary for Governor': #county(k) in {'075'} and int(date(k)) == 2012:
                result = calc(k, ALLSTATS)
                w.writerow([result[fun.__name__] for fun in ALLSTATS])


#    with open('headline.csv', 'w') as f:
#        w = csv.writer(f)
#        w.writerow([fun.__name__ for fun in HEADLINE_STATS])
#        w.writerow([' '.join((fun.__doc__ or '').split())
#                     for fun in HEADLINE_STATS])
#        for k in sorted(manifest.competitions.values(),key=lambda x: x['date']):
#            if True: #k['office'] == 'Democratic Primary for Governor': #county(k) in {'075'} and int(date(k)) == 2012:
#                result = calc(k, HEADLINE_STATS)
#                w.writerow([result[fun.__name__] for fun in HEADLINE_STATS])

if __name__ == '__main__':
    main()

