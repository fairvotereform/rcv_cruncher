When the 'first_second_choices' option is marked as TRUE in the output_config.csv file, the files described below are written out to the `contest_sets/[your_contest_set_dir]/results/first_second` directory.

These files contain tables that describe the distribution of first choices as well as the distribution of second choices, conditional on a first choice.

Each table contains a top row with candidate names. The first row label is 'first_choice' and the cells in the rest of this row describe the number/percent of ballots that counted towards each candidate in the first round. The following rows are each labelled with a candidate name and describe the number/percent of ballots that ranked each row candidate second out of the ballots that counted towards the column candidate in the first round.

In terms of percentage calculations, the denominator for the 'first_choice' row is the sum of the row. However, the denominator for each of the columns below the 'first_choice' row is the sum of the column below the 'first_choice' row. There are also two types of percentage table outputs, one that includes second round exhausted ballots in the second choice percentage calculation and one that excludes the second round exhausted ballots in that calculation. The two files are differentiated by their endings 'percent' and 'percent_no_exhaust'.

Note: the ballots used for this calculation are truncated if they contain an exhaust condition (overvote or repeated skipped rankings). These rules vary by jurisdiction. Any skipped rankings or overvotes that do not cause exhaust are skipped.

Last edited on 12/4/2020
