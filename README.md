# rcv_cruncher

Table of Contents:
* [Install](##install)
* [Examples](##examples)
  * [Cast Vote Record](###cvr-analysis)
  * [Tabulate](###tabulate-election)
* Classes and Functions
  * BallotMarks
  * CastVoteRecord
  * All RCV Classes

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

def get_round_tally_tuple(self,
                              round_num: int,
                              tabulation_num: int = 1,
                              only_round_active_candidates: bool = False,
                              desc_sort: bool = False) -> List[Tuple[str], Tuple[decimal.Decimal]]:

    def get_round_tally_dict(self,
                             round_num: int,
                             tabulation_num: int = 1,
                             only_round_active_candidates: bool = False) -> Dict[str, decimal.Decimal]:

    def get_round_transfer_dict(self,
                                round_num: int,
                                tabulation_num: int = 1) -> Dict[str, decimal.Decimal]:


    def get_candidate_outcomes(self, tabulation_num: int = 1) -> Dict[str, Optional[int]]:


    def get_final_weights(self, tabulation_num: int = 1) -> List[decimal.Decimal]:

    def get_initial_ranks(self, tabulation_num: int = 1) -> List[List[str]]:


    def get_initial_weights(self, tabulation_num: int = 1) -> List[decimal.Decimal]:


    def get_final_ranks(self, tabulation_num: int = 1) -> List[List[str]]:

    def get_final_weight_distrib(self, tabulation_num: int = 1) -> List[List[Tuple[str, decimal.Decimal]]]:


    def get_win_threshold(self, tabulation_num: int = 1) -> Optional[Union[int, float]]:



    def n_rounds(self, tabulation_num: int = 1) -> int:

    def n_tabulations(self) -> int:
        return self._tab_num

## Functions and Classes

#### *class* **BallotMarks**

This class is intended to hold individual lists of ballot marks and provide useful functions for manipulating them. Collections of BallotMarks are used with CastVoteRecord and RCV objects.

#### Variables:

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

#### Methods:

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


#### *class* CastVoteRecord

This class provides a way to organize various version of a cast vote record with different rule sets applied. It also calculates various ballot statistics that do not depend on an election outcome.

#### Variables:

* Instance:

  * **jurisdiction**: string
  * **state**: string
  * **date**: string
  * **year**: string
  * **office**: string
  * **notes**: string
  * **split_fields**: list of string indicating which columns of the cvr should be used to calculate split statistics.
  * **unique_id**: combination of jurisdiction, date or year, and office.

#### Methods:

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

  * Returns: DataFrame.


#### *class* all RCV classes (SingleWinner, STVFractionalBallot, STVWholeBallot, Until2, Sequential, BottomsUp15)



