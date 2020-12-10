When the 'first_choice_to_finalist' option is marked as TRUE in the output_config.csv file, the files described below are written out to the `contest_sets/[your_contest_set_dir]/results/first_choice_to_finalist` directory.

These tables track how ballots transferred from the first candidate they counted towards in the first round to the finalist candidate they counted towards in the final round.

Each row in the table describes how the ballots that first counted towards a candidate in the first round ended up being distributed to those candidates that still had votes in the final round. The first element each row in the candidate name, followed by the candidates first round vote count, and the successive elements in each row describe the percentage breakdown of how those first round votes were distributed to candidates who maintained any votes into the final round. (This includes early round winners in multi-winner elections who retain the threshold number of votes). The final column just acts as a check to see that the percentages sum to 100 (with potential minor rounding error).

Notes:

These tables do account for fractional ballot transfer.

One table will be produced per each tabulation in an RCV contest. (Some contests, such as the Payson and Vineyard jurisdictions in Utah use a sequential RCV voting system that requires multiple full tabulations.)

Last edited on 12/7/2020
