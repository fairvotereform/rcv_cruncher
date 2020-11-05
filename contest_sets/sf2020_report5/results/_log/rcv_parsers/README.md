## rcv-parsers

Contains parsers for all known US RCV elections. Currently only used in the RCV cruncher (https://github.com/fairvotereform/rcv_cruncher).

Parser documentation:

* common_csv - reads a csv file. Expects columns that contain the word "rank" to correspond to the ordered ranks of each ballot. Also checks for a column named "weight".

* dominion5_4 (and 5_10) - extracts the number of rankings from the ContestManifest.json.

* prm - assumes the at least one fully ranked ballot exists in the set.

* burlington2006 - assumes the at least one fully ranked ballot exists in the set.

* sf - ballot rank limit is not obvious based on the formatting.

* sfnoid - ballot rank limit is not obvious based on the formatting.

* old - unclear

* minneapolis - think there a rank limit of 3
* maine - unclear

* santafe
* santafe_id

* sf2005
* dominion5_2 - extracts the number of rankings from the ContestManifest.json.
* utah
* ep
* unisyn - the number of ranks is indicated by the number of contestIDs. (3 ranks 116, 116A, 116B)
* surveyUSA -  Expects columns that contain the word "rank" to correspond to the ordered ranks of each ballot. Also checks for a column named "weight".

chp_names,
chp_order,
sf_precinct_map,
parse_master_lookup,
sf_name_map,
sf_tally_type_map
