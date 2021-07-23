
import pandas as pd

import rcv_cruncher.util as util

from rcv_cruncher.marks import BallotMarks


class CastVoteRecord_tables:

    # EXPORT

    def cvr_table(self, table_format: str = "rank") -> pd.DataFrame:

        if table_format != "rank" and table_format != "candidate":
            raise RuntimeError('table_format argument must be "rank" or "candidate"')

        if table_format == "rank":
            return self._rank_header_cvr()
        elif table_format == "candidate":
            return self._candidate_header_cvr()

    def _rank_header_cvr(self) -> pd.DataFrame:

        ballot_dict = {k: v for k, v in self.get_cvr_dict().items()}
        bs = [b.marks for b in ballot_dict['ballot_marks']]
        weight = ballot_dict['weight']
        del ballot_dict['ballot_marks']
        del ballot_dict['weight']

        # how many ranks?
        num_ranks = max(len(i) for i in bs)

        # shift over all ranks
        # bs = [[m for m in b if m != BallotMarks.SKIPPED] for b in bs]

        # make sure all ballots are lists of equal length, adding trailing 'skipped' if necessary
        bs = [b + ([BallotMarks.SKIPPED] * (num_ranks - len(b))) for b in bs]

        # assemble output_table, start with extras
        output_df = pd.DataFrame.from_dict(ballot_dict)

        # are weights all one, then dont add to output
        if not all([i == 1 for i in weight]):
            output_df['weight'] = [float(w) for w in weight]

        # add in rank columns
        for i in range(1, num_ranks + 1):
            output_df['rank' + str(i)] = [b[i-1] for b in bs]

        # add in rank columns
        # for i in range(1, num_ranks + 1):
        #    output_df[str(i)] = [''.join(b[i-1].split(' ')) for b in bs]
        #    output_df[str(i)] = output_df[str(i)].replace(to_replace=BallotMarks.SKIPPED, value='')

        return output_df

    def _candidate_header_cvr(self) -> pd.DataFrame:

        # get ballots and candidates
        ballot_dl = {k: v for k, v in self.get_cvr_dict().items()}
        candidates = self.get_candidates().unique_candidates.copy()
        candidates.update({BallotMarks.OVERVOTE})

        # remove weights if all equal to 1
        if set(ballot_dl['weight']) == {1}:
            del ballot_dl['weight']

        # add rank limit
        ballot_dl['rank_limit'] = [len(ballot_dl['ballot_marks'][0].marks)] * len(ballot_dl['ballot_marks'])

        # convert dict of list to list of dicts
        ballot_ld = util.DL2LD(ballot_dl)

        # add candidate index information
        for b in ballot_ld:
            b.update({f"candidate_{cand}": None for cand in candidates})
            for rank_idx, cand in enumerate(b['ballot_marks'].marks, start=1):
                if cand != BallotMarks.SKIPPED:
                    if not b[f"candidate_{cand}"]:
                        b[f"candidate_{cand}"] = str(rank_idx)
                    else:
                        b[f"candidate_{cand}"] += f',{rank_idx}'
            del b['ballot_marks']

        df = pd.DataFrame(ballot_ld)
        return df.reindex(sorted(df.columns), axis=1)

    def rank_usage_table(self):
        """
        DOES NOT USE BALLOT WEIGHTS
        """

        # get candidate set
        candidate_set = self.get_candidates()
        candidate_set = BallotMarks.combine_writein_marks(candidate_set)
        # candidate_set = BallotMarks.remove_mark(candidate_set, [BallotMarks.WRITEIN])
        candidate_set = sorted(candidate_set.unique_candidates)

        # get ballots
        ballot_set = [{'ballot_marks': bm, 'weight': weight}
                      for bm, weight in zip(self.get_cvr_dict()['ballot_marks'], self.get_cvr_dict()['weight'])]
        # remove skipped ranks
        ballot_set = [{'ballot_marks': BallotMarks.remove_mark(b['ballot_marks'], [BallotMarks.SKIPPED]),
                       'weight': b['weight']}
                      for b in ballot_set]
        # remove empty ballots and those that start with overvote
        ballot_set = [b for b in ballot_set
                      if len(b['ballot_marks'].marks) >= 1 and b['ballot_marks'].marks[0] != BallotMarks.OVERVOTE]
        # combine writeins
        ballot_set = [{'ballot_marks': BallotMarks.combine_writein_marks(b['ballot_marks']),
                       'weight': b['weight']}
                      for b in ballot_set]
        # remove other overvotes
        ballot_set = [{'ballot_marks': BallotMarks.remove_mark(b['ballot_marks'], [BallotMarks.OVERVOTE]),
                       'weight': b['weight']}
                      for b in ballot_set]
        # remove duplicate rankings
        ballot_set = [{'ballot_marks': BallotMarks.remove_duplicate_candidate_marks(b['ballot_marks']),
                       'weight': b['weight']}
                      for b in ballot_set]

        all_ballots_label = "Any candidate"
        n_ballots_label = "Number of Ballots (excluding undervotes and ballots with first round overvote)"
        mean_label = "Mean Valid Rankings Used (excluding duplicates)"
        # median_label = "Median Valid Rankings Used (excluding duplicates)"

        rows = [all_ballots_label] + candidate_set
        cols = [n_ballots_label, mean_label]  #, median_label]
        df = pd.DataFrame(index=rows, columns=cols)
        df.index.name = "Ballots with first choice:"

        ballot_total = sum(b['weight'] for b in ballot_set)
        mean_rankings = sum(len(b['ballot_marks'].marks) * b['weight'] for b in ballot_set) / ballot_total
        # median_rankings = statistics.median(len(b) for b in ballot_set)

        df.loc[all_ballots_label, n_ballots_label] = ballot_total
        df.loc[all_ballots_label, mean_label] = mean_rankings
        # df.loc[all_ballots_label, median_label] = median_rankings

        # group ballots by first choice
        first_choices = {cand: [] for cand in candidate_set}
        for b in ballot_set:
            first_choices[b['ballot_marks'].marks[0]].append(b)

        for cand in candidate_set:
            first_choice_ballot_total = sum(b['weight'] for b in first_choices[cand])
            df.loc[cand, n_ballots_label] = first_choice_ballot_total
            if first_choices[cand]:
                df.loc[cand, mean_label] = sum(len(b['ballot_marks'].marks) * b['weight']
                                               for b in first_choices[cand]) / first_choice_ballot_total
                # df.loc[cand, median_label] = statistics.median(len(b) for b in first_choices[cand])
            else:
                df.loc[cand, mean_label] = 0
                # df.loc[cand, median_label] = 0

        return df.applymap(util.decimal2float)

    def crossover_tables(self):

        # get candidate set
        candidate_set = self.get_candidates()
        candidate_set = BallotMarks.combine_writein_marks(candidate_set)
        # candidate_set = BallotMarks.remove_mark(candidate_set, [BallotMarks.WRITEIN])
        candidate_set = sorted(candidate_set.unique_candidates)

        ballot_dict = self.get_cvr_dict()
        ballot_weights = ballot_dict['weight']
        ballot_ranks = [BallotMarks.remove_mark(b, [BallotMarks.SKIPPED]) for b in ballot_dict['ballot_marks']]
        ballot_ranks = [BallotMarks.combine_writein_marks(b) for b in ballot_ranks]
        ballot_set = [{'ballot_marks': ranks.marks, 'weight': weight}
                      for ranks, weight in zip(ballot_ranks, ballot_weights)]

        index_label = "Ballots with first choice:"
        n_ballots_label = "Number of Ballots"

        colname_dict = {cand: cand + " ranked in top 3" for cand in candidate_set}

        rows = candidate_set
        cols = [n_ballots_label] + list(colname_dict.values())
        count_df = pd.DataFrame(index=rows, columns=cols)
        count_df.index.name = index_label
        percent_df = pd.DataFrame(index=rows, columns=cols)
        percent_df.index.name = index_label

        # group ballots by first choice
        first_choices = {cand: [] for cand in candidate_set}
        for b in ballot_set:
            if len(b['ballot_marks']) >= 1 and b['ballot_marks'][0] != BallotMarks.OVERVOTE:
                first_choices[b['ballot_marks'][0]].append(b)

        for cand in candidate_set:

            n_first_choice = sum(b['weight'] for b in first_choices[cand])
            count_df.loc[cand, n_ballots_label] = n_first_choice
            percent_df.loc[cand, n_ballots_label] = n_first_choice

            for opponent in candidate_set:

                if n_first_choice:
                    crossover_ballots = [True if opponent in b['ballot_marks'][0:min(3, len(b['ballot_marks']))] else False
                                         for b in first_choices[cand]]
                    crossover_val = sum(b['weight'] for b, flag in zip(first_choices[cand], crossover_ballots) if flag)
                    count_df.loc[cand, colname_dict[opponent]] = crossover_val
                    percent_df.loc[cand, colname_dict[opponent]] = crossover_val*100/n_first_choice
                else:
                    count_df.loc[cand, colname_dict[opponent]] = 0
                    percent_df.loc[cand, colname_dict[opponent]] = 0

        # convert decimal to float
        count_df = count_df.astype(float).round(3)
        percent_df = percent_df.astype(float).round(3)

        return count_df, percent_df

    def annotated_cvr_table(self):
        dfs = [self._rank_header_cvr(), self._cvr_stat_table]
        return pd.concat(dfs, axis='columns', sort=False)

