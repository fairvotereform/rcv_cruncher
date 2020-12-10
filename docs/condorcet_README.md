When the 'condorcet' option is marked as TRUE in the output_config.csv file, the files described below are written out to the `contest_sets/[your_contest_set_dir]/results/condorcet` directory.

The files in this directory contain condorcet tables. These tables indicate which of the candidates, if any, is the condorcet winner of the election. A condorcet winner is a candidate that beats all other candidates in head-to-head matchups. The leftmost column and the top of row of these tables both contain candidate names. The cells in the rest of the table indicate the number/percent of ballots in which the row candidate is ranked higher than the column candidate. (If one candidate is ranked and one is not, the ranked candidate is considered to be ranked higher than the unranked candidate.) The sum of cells across the diagonal is the total number of ballots that ranked either candidate. That sum is the number then used as a denominator for the conversion of counts into percentages.

The top left corner will include the name of the cordorcet winner. They will be the candidate that won >50% of ballots against all other candidates.

Note: the ballots used for this calculation are truncated if they contain an exhaust condition (overvote or repeated skipped rankings). These rules vary by jurisdiction. Any skipped rankings or overvotes that do not cause exhaust are skipped.

Last edited on 12/4/2020
