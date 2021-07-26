import rcv_cruncher
import rcv_cruncher.parsers as parsers

def test_initial():
    cvr_file = './tests/contest_sets/urcvt-tests/dominion_wyoming/dominion_wyoming_contest_1_expected.csv'

    rcv = rcv_cruncher.SingleWinner(
            jurisdiction='Minneapolis',
            state='MN',
            year='2017',
            office='Mayor',
            parser_func=parsers.cruncher_csv,
            parser_args={'cvr_path': cvr_file},
            exhaust_on_duplicate_candidate_marks=True,
            exhaust_on_overvote_marks=True,
            combine_writein_marks=True
        )
