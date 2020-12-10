When the 'cumulative_ranking' option is marked as TRUE in the output_config.csv file, the files described below are written out to the `contest_sets/[your_contest_set_dir]/results/cumulative_ranking` directory.

The purpose of these tables is to get a sense of voter approval of candidates based on how high up they ranked them. Moving down the ranking list from rank1 to the rank limit, the more approved of candidates will the be more likely to quickly accumulate ranking positions across ballots.

These tables have candidate names as row names and ranking positions as column names. Each column indicates the count/percentage of ballots that ranked each candidate at that ranking or earlier. For example, the rank2 column indicates the number/percentage of ballots that ranked each candidate first or second. The count and percentages accumulate as the rankings increase. Until the final column 'Did Not Rank', which is the percentage of ballots remaining that did not mark the candidate for any rank.

Note: the ballots used for this calculation are truncated if they contain an exhaust condition (overvote or repeated skipped rankings). These rules vary by jurisdiction. Any skipped rankings or overvotes that do not cause exhaust are skipped.

Last edited on 12/4/2020
