# rcv_cruncher

A python package for tabulating and analysing Ranked Choice Voting results.

<br/>

Features:
* Many types of RCV tabulation implemented.
* Allows weighted ballots.
* Allows for statistics (not tabulation) to be calculated by group (e.g. by precinct).
* Includes parers for most common RCV formats.

<br/>

Table of Contents:
- [rcv_cruncher](#rcv_cruncher)
  - [Install](#install)
  - [Examples](#examples)
    - [CVR analysis](#cvr-analysis)
    - [Tabulate Election](#tabulate-election)
  - [Functions and Classes](#functions-and-classes)
    - [*class* **BallotMarks**](#class-ballotmarks)
      - [Variables](#variables)
      - [Methods](#methods)
    - [*class* **CastVoteRecord**](#class-castvoterecord)
      - [Variables](#variables-1)
      - [Methods](#methods-1)
    - [*class* **all RCV classes** (SingleWinner, STVFractionalBallot, STVWholeBallot, Until2, Sequential, BottomsUp15)](#class-all-rcv-classes-singlewinner-stvfractionalballot-stvwholeballot-until2-sequential-bottomsup15)
      - [Methods](#methods-2)
  - [Stat List](#stat-list)
    - [CVR stats](#cvr-stats)
    - [RCV stats](#rcv-stats)


## Install

Only tested on Python 3.9 so far.

<br/>

```
pip install rcv-cruncher
```

## Examples

Using 2017 Minneapolis Mayor [Cast Vote Record](https://github.com/fairvotereform/rcv_cruncher/tree/big_changes/src/rcv_cruncher/example/example_cvr/minneapolis2017/2017-mayor-cvr.csv).

### CVR analysis

```python
# reading CVR
import rcv_cruncher as rcvc
import rcv_cruncher.parsers as parsers

cvr_file = '2017-mayor-cvr.csv'

cvr = rcvc.CastVoteRecord(
        jurisdiction='Minneapolis',
        state='MN',
        year='2017',
        office='Mayor',
        parser_func=parsers.cruncher_csv,
        parser_args={'cvr_path': cvr_file}
    )



# add_rule_set - apply some rules to create new a version of CVR.
cvr.add_rule_set('test_rule_set',
                 rcvc.BallotMarks.new_rule_set(
                    combine_writein_marks: bool = True,
                    exclude_writein_marks: bool = True,
                    exclude_duplicate_candidate_marks: bool = False,
                    exclude_overvote_marks: bool = False,
                    exclude_skipped_marks: bool = False,
                    treat_combined_writeins_as_exhaustable_duplicates: bool = False,
                    exhaust_on_duplicate_candidate_marks: bool = False,
                    exhaust_on_overvote_marks: bool = False,
                    exhaust_on_repeated_skipped_marks: bool = False
                 )
            )



# get_candidates - returns BallotMarks object

# no rules applied candidates
candidates = cvr.get_candidates()

# test_rule_set candidates
candidates = cvr.get_candidates('test_rule_set')



# get_cvr_dict - returns dict of lists

# no rules applied cvr data
cvr_dict = cvr.get_cvr_dict()

# test_rule_set candidates
cvr_dict = cvr.get_cvr_dict('test_rule_set')



# stats
cvr_stats = cvr.stats()
```

### Tabulate Election

```python
import rcv_cruncher as rcvc
import rcv_cruncher.parsers as parsers

cvr_file = '2017-mayor-cvr.csv'

cvr = rcvc.SingleWinner(
        jurisdiction='Minneapolis',
        state='MN',
        year='2017',
        office='Mayor',
        parser_func=parsers.cruncher_csv,
        parser_args={'cvr_path': cvr_file},
        exhaust_on_duplicate_candidate_marks=True,
        exhaust_on_overvote_marks=True,
        combine_writein_marks=True
        # ... other rules from BallotMarks.new_rule_set()
    )
```

Other tabulation methods implemented but not yet fully tested:

* STVFractionalBallot - multi-winner fractional ballot transfer (Gregory method).
* STVWholeBallot - multi-winner whole ballot transfer (used in Cambridge).
* Until2 - single winner election run until 2 candidates remain.
* Sequential - multi-winner election that consists on sequential single winner elections (used in Utah).
* BottomsUp15 - multi-winner election run until all candidates are above 15% (used in 2020 Dem Pres Primaries).


## Functions and Classes
### *class* **BallotMarks**

This class is intended to hold individual lists of ballot marks and provide useful functions for manipulating them. Collections of BallotMarks are used with CastVoteRecord and RCV objects.

#### Variables

* Constants
  * SKIPPED
  * OVERVOTE
  * WRITEIN
  * UNDERVOTE
  * PRETALLY_EXHAUST
  * MAYBE_EXHAUSTED
  * MAYBE_EXHAUSTED_BY_OVERVOTE
  * MAYBE_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING
  * MAYBE_EXHAUSTED_BY_DUPLICATE_RANKING

* Instance:
  * **marks**: List of candidates in rank order
  * **unique_marks**: Set of unique marks in self.marks
  * **unique_candidates**: Set of unique candidates in self.marks. This excludes special marks BallotMarks.SKIPPED and BallotMarks.OVERVOTE
  * **rules**: Dictionary of rules applied to marks. Only one rule set may be applied per object.
  * **inactive_type**: After rules are applied, a string indicated the possible means by which this ballot will be exhausted in an election. They include:
    * UNDERVOTE: All skipped rankings.
    * PRETALLY_EXHAUST: Ballot is left empty after rules are applied and will therefore not even be active in the first round of tabulation.
    * MAYBE_EXHAUSTED_BY_OVERVOTE: The ballot was trucated due the occurrence of an overvote, when rules apply. Whether or not it will exhaust will be determined by how the remaining candidates marked on the ballot perform in the election.
    * MAYBE_EXHAUSTED_BY_REPEATED_SKIPPED_RANKING: The ballot was trucated due the occurrence of two or more skipped marks (that were followed by at least 1 non-skipped mark), when rules apply. Whether or not it will exhaust will be determined by how the remaining candidates marked on the ballot perform in the election.
    * MAYBE_EXHAUSTED_BY_DUPLICATE_RANKING: The ballot was trucated due the occurrence of repeated candidate mark, when rules apply. Whether or not it will exhaust will be determined by how the remaining candidates marked on the ballot perform in the election.
    * MAYBE_EXHAUSTED: All ballot not receiving one of the labels above. These ballots may still be exhausted during tabulation because they failed to rank a finalist candidate.

#### Methods

static function **new_rule_set**:

  Dictionary factory.

  * Arguments:
    * combine_writein_marks: bool (default: False)
    * exclude_writein_marks: bool (default: False)
    * exclude_duplicate_candidate_marks: bool (default: False)
    * exclude_overvote_marks: bool (default: False)
    * exclude_skipped_marks: bool (default: False)
    * treat_combined_writeins_as_exhaustable_duplicates: bool (default: False)
    * exhaust_on_duplicate_candidate_marks: bool (default: False)
    * exhaust_on_overvote_marks: bool (default: False)
    * exhaust_on_repeated_skipped_marks: bool (default: False)

  * Returns:
    * Dictionary of argument names and values.

  **combine_writein_marks**: changes any candidate mark containing the anycase string 'write' or equalling the anycase string 'uwi' into the standardized BallotMarks.WRITEIN constant.

  **exclude_writein_marks**: all WRITEIN marks are removed from ballot.

  **exclude_duplicate_candidate_marks**: remove repeated candidate marks from ballot.

  **exclude_overvote_marks**: remove OVERVOTE marks from ballot.

  **exclude_skipped_marks**: remove SKIPPED marks from ballot.

  **treat_combined_writeins_as_exhaustable_duplicates**: treats combined writein marks as identical marks for the purposes of exhaust conditions.

  **exhaust_on_duplicate_candidate_marks**: truncate the ballot once a repeated candidate mark is reached.

  **exhaust_on_overvote_marks**: truncate the ballot once an OVERVOTE mark is reached.

  **exhaust_on_repeated_skipped_marks**: truncate the ballot once two or more succesive SKIPPED marks (but followed by at least 1 non-skipped mark) are reached.

<br/>
<br/>

instance **constructor**:

  * Arguments:
    * marks: a list of candidate marks and BallotMarks constants.

<br/>
<br/>

instance function **update_marks**:

  Replace marks. Unique sets will also be updated.

  * Arguments:
    * new_marks: a new list or marks to replace current values.

  * Return: None

<br/>
<br/>


instance function **apply_rules**:

  Marks and unique sets will be updated based on rules.

  * Arguments:
    * combine_writein_marks: bool (default: False)
    * exclude_writein_marks: bool (default: False)
    * exclude_duplicate_candidate_marks: bool (default: False)
    * exclude_overvote_marks: bool (default: False)
    * exclude_skipped_marks: bool (default: False)
    * treat_combined_writeins_as_exhaustable_duplicates: bool (default: False)
    * exhaust_on_duplicate_candidate_marks: bool (default: False)
    * exhaust_on_overvote_marks: bool (default: False)
    * exhaust_on_repeated_skipped_marks: bool (default: False)

  * Returns: None


### *class* **CastVoteRecord**

This class provides a way to organize various version of a cast vote record with different rule sets applied. It also calculates various ballot statistics that do not depend on an election outcome.

#### Variables

* Instance:

  * **jurisdiction**: string
  * **state**: string
  * **date**: string
  * **year**: string
  * **office**: string
  * **notes**: string
  * **split_fields**: list of string indicating which columns of the cvr should be used to calculate split statistics.
  * **unique_id**: combination of jurisdiction, date or year, and office.

#### Methods

instance **constructor**:

* Arguments:
  * jurisdiction: string
  * year: string
  * date: string
  * office: string
  * notes: string
  * split_fields: (Optional[List[string]]) List of CVR field names to calculate split stats on.
  * parser_func: A parser function that returns either list of ranks or, if including more ballot information, a dictionary of lists, one of which is named 'ranks'.
  * parser_args: A dictionary of parser arguments. They will be ** unrolled into the parser function.
  * parsed_cvr: A list of rankings or a dict of lists. If passed, the parser function and arguments will be ignored.

<br/>
<br/>

instance function **add_rule_set**:

  Creates a version of the cvr with rules applied to all ballots.

  * Arguments:
    * rule_set_name: string naming rule for cvr.
    * rule_set_dict: dictionary containing all or some of the outputs of BallotMarks.new_rule_set().

  * Returns: None

<br/>
<br/>

instance function **get_candidates**:

  Returns the candidates present on all ballots (after rules have been applied).

  * Arguments:
    * rule_set_name: string naming rule set added using add_rule_set(). Defaults to the unmodified parsed CVR ballots.

  * Returns: BallotMarks object contructed from list of unique candidates across all ballots.

<br/>
<br/>

instance function **get_cvr_dict**:

Returns a dictionary of lists. One list is called 'ballot_marks' and contains modified BallotMarks objects. All other lists correspond to all other columns in the parsed CVR. If no 'weight' column was present in CVR, a column of all 1's is added.

  * Arguments:
    * rule_set_name: string naming rule set added using add_rule_set(). Defaults to the unmodified parsed CVR ballots.

  * Returns: Dict of Lists

<br/>
<br/>

instance function **stats**:

Returns a pandas DataFrame of CVR statistics. See statistics list for more information on which are included. These statistics do not depend on any rule sets added and use the unmodified parsed cvr data.

  * Arguments:
    * keep_decimal_type: (default: False) For internal calculations numbers are represented using python decimal libary. By default, the resulting statistics are converted into rounded floats when returned.
    * add_split_stats: (default: False) Some statistics will be calculated per split value contained in the CVR columns specified with the 'split_fields' constructor  arguments.
    * add_id_info: (default: True) Contest ID info (jurisdiction, state, date, office, etc) is added to the returned DataFrame.

  * Returns: List[DataFrame].


### *class* **all RCV classes** (SingleWinner, STVFractionalBallot, STVWholeBallot, Until2, Sequential, BottomsUp15)

These classes apply rules to a CVR and then tabulate the election rounds.

All RCV classes inherit from CastVoteRecord.

#### Methods

instance **constructor**:

* Arguments:
  * All CastVoteRecord arguments ...
  * n_winners: (optional integer) Only needed if multi-winner class.
  * multi_winner_rounds: (default False) Only needed for multi-winner class. Determines if multiple winners can be declared in the same round.
  * exhaust_on_duplicate_candidate_marks: (default False) see BallotMarks for description of these rule arguments.
  * exhaust_on_overvote_marks: (default False)
  * exhaust_on_repeated_skipped_marks: (default False)
  * treat_combined_writeins_as_exhaustable_duplicates: (default True)
  * combine_writein_marks: (default True)
  * exclude_writein_marks: (default False)

<br/>
<br/>

instance function **stats**:

Returns a pandas DataFrame of both CVR and RCV statistics (one DataFrame per contest tabulation). See statistics list for more information on which are included.

  * Arguments:
    * keep_decimal_type: (default: False) For internal calculations numbers are represented using python decimal libary. By default, the resulting statistics are converted into rounded floats when returned.
    * add_split_stats: (default: False) Some statistics will be calculated per split value contained in the CVR columns specified with the 'split_fields' constructor  arguments.
    * add_id_info: (default: True) Contest ID info (jurisdiction, state, date, office, etc) is added to the returned DataFrame.

  * Returns: List[DataFrame].

<br/>
<br/>

instance function **get_round_tally_tuple**:

Get a list of two tuples. The first containing candidate names and the second containing corresponding round vote totals. By default the values are sorted in descending order.

* Arguments:
  * round_num (int): Which round tally to get results for.
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).
  * only_round_active_candidates (default False): Filters out candidatess that are either previously elected or eliminated before the round specified.

* Return: List[Tuple, Tuple]

<br/>
<br/>

instance function **get_round_tally_dict**:

Same as get_round_tally_tuple() but the tuples are zipped into a dictionary.

<br/>
<br/>

instance function **get_round_transfer_dict**:

Get a dictionary with candidates as keys and transfer values as values. All value should sum to 0.

* Arguments:
  * round_num (int): Which round tally to get results for.
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: Dict

<br/>
<br/>

instance function **get_candidate_outcomes**:

Get a list of dictionaries describing candidate outcomes. One dictionary per candidates. Each dictionary has the form {name: 'candidate A', round_elected: (defualt None), round_eliminated: (defualt None)}

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: List of Dict

<br/>
<br/>

instance function **get_final_weights**:

List of weights remaining for each ballot at the end of tabulation. Will only change from initial weights due to fractional ballot transfer methods.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: List

<br/>
<br/>

instance function **get_initial_weights**:

List of weights for each ballot at the start of tabulation. Should match any weights provided in CVR.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: List

<br/>
<br/>

instance function **get_final_weight_distrib**:

List of weight distributions for each ballot at the end of tabulation. Each weight distribution is represented by a list of 2-tuples. Each tuple contains the allocated candidate name as well as the weight allocated to that candidates. Summing across tuples should recover the input weight for a ballot.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: List

<br/>
<br/>

instance function **get_initial_ranks**:

List of BallotMarks at the start of each tabulation.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: List[BallotMarks]

<br/>
<br/>

instance function **get_final_ranks**:

List of BallotMarks at the end of each tabulation.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: List[BallotMarks]

<br/>
<br/>

instance function **get_win_threshold**:

If a static threshold is using in tabulation, it is returned. Else returns None.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: None or int or float

<br/>
<br/>

instance function **n_rounds**:

Returns number of rounds in a tabulation.

* Arguments:
  * tabulation_num (int, default 1): Only applies to contest types which have multiple tabulations (e.x. Sequential).

* Return: int

<br/>
<br/>


instance function **n_tabulations**:

Returns number of tabulations in a contest.

* Return: int

## Stat List

### CVR stats

**n_candidates** - number of candidates excluding WRITEIN marks


**rank_limit** - number of rankings allowed on the CVR.


**restrictive_rank_limit** - True if number of candidates - number of ranks is greater than 1.

(All stats below are also able to calcualted by group (e.g. by precinct))

**first_round_overvote** - number of ballots in which the first non-skipped mark is an overvote.


**ranked_single** - number of ballot which only contained 1 valid rankings.


**ranked_multiple** - number of ballot which only contained more than 1 valid rankings.


**ranked_3_or_more** - number of ballot which only contained more than 2 valid rankings.

**total_fully_ranked** - number of ballots that have EITHER validly used all rankings on the ballot OR validly ranked every non-writein candidate.

**includes_overvote_ranking** - number of ballots with an overvote ranking.


**includes_duplicate_ranking** - number of ballots with a duplicate ranking.


**includes_skipped_ranking** - number of ballots with a skipped ranking (that is then followed by at least 1 non-skipped ranking).


**total_irregular** - total number of ballots with EITHER a duplicate ranking OR skipped ranking OR overvote.


**total_ballots** - total number of ballots


**total_undervote** - total number of ballots that contain all skipped rankings.


**mean_rankings_used** - mean number of non-undervote rankings used.


**median_rankings_used** - mean number of non-undervote rankings used.

### RCV stats

**number_of_winners** - number of winners in the contest.


**number_of_rounds** - number of rounds in the tabulation.


**winner** - tabulation winners.

**first_round_winner_vote** - If more than 1 winner in tabulation, then None. Else, the vote total for the tabulation winner in the first round.

**first_round_winner_percent** - If more than 1 winner in tabulation, then None. Else, the vote percent for the tabulation winner in the first round.

**first_round_winner_place** - If more than 1 winner in tabulation, then None. Else, the place the tabulation winner finished in the the first round.

**final_round_winner_vote** - If more than 1 winner in tabulation, then None. Else, the vote total for the tabulation winner in the final round.

**final_round_winner_percent** - If more than 1 winner in tabulation, then None. Else, the vote percent for the tabulation winner in the final round.

**final_round_winner_votes_over_first_round_active** - If more than 1 winner in tabulation, then None. Else, the vote total for the tabulation winner in the final round divided by the number of active ballots in the first round.

**condorcet** - If more than 1 winner in tabulation, then None. Else, True if the winner is the condorcet winner, else False.

**come_from_behind** - If more than 1 winner in tabulation, then None. Else, True if the winner was not in first place in the first round, else False.

**ranked_winner** - If more than 1 winner in tabulation, then None. Else, the number of ballots that ranked the winner.

**win_threshold** - If less than 2 winner in tabulation, then None. Else, the static threshold needed to win.

**ranked_winner** - If more than 1 winner in tabulation, then None. Else, the number of ballots that ranked the winner.

**winners_consensus_value** - The number of ballots that rank any winner in their top 3 (after rules applied).

**first_round_active_votes** - The number of votes active in the first round.

**final_round_active_votes** - The number of votes active in the final round.

(All stats below are also able to calcualted by group (e.g. by precinct))

**total_pretally_exhausted** - The number of ballots that were not undervotes, yet were not active in the first round.

**total_posttally_exhausted** - The number of ballots that exhausted after the first round.

**total_posttally_exhausted_by_overvote** - The number of ballots that exhausted due to an overvote after the first round.

**total_posttally_exhausted_by_skipped_rankings** - The number of ballots that exhausted due to repeated skipped rankings after the first round.

**total_posttally_exhausted_by_duplicate_rankings** - The number of ballots that exhausted due to duplicate candidate rankings after the first round.

**total_posttally_exhausted_by_rank_limit** - The number of ballots that exhausted after the first round. Only applied to contest with a restrictive rank limit. The count towards this category ballots must either use all ranks OR at least use the last ranking.

**total_posttally_exhausted_by_abstention** - The number of ballots that exhausted after the first round which do not fall into the categories above.






