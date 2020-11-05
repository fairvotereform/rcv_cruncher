import xmltodict
import glob

ctx_contest = "President"
glob_str = "C:\\Users\\User\\Documents\\fairvote\\projects\\dem_primary2020\\Hawaii_cvr\\CD1/*.xml"

contestIDdicts = {}

overvotes = []
undervotes = []
undervotes_dict = {}
writeins = []
nselections = []
nselections2 = []
status = []
snapshot_keys = []
contest_keys = []

for f in glob.glob(glob_str):

    with open(f) as fd:
        xml_dict = xmltodict.parse(fd.read())

    # get candidates
    candidatesIDs = {}
    for cand_dict in xml_dict['CastVoteRecordReport']['Election']['Candidate']:
        candidatesIDs[cand_dict['@ObjectId']] = cand_dict['Name']

    # loop through CVR snapshots
    for cvr_dict in xml_dict['CastVoteRecordReport']['CVR']:

        contest_keys.append(tuple(cvr_dict['CVRSnapshot']['CVRContest'].keys()))
        snapshot_keys.append(tuple(cvr_dict['CVRSnapshot'].keys()))

        writeins.append(cvr_dict['CVRSnapshot']['CVRContest']['WriteIns'])
        undervotes.append(cvr_dict['CVRSnapshot']['CVRContest']['Undervotes'])

        if cvr_dict['CVRSnapshot']['CVRContest']['Undervotes'] not in undervotes_dict:
            undervotes_dict.update({cvr_dict['CVRSnapshot']['CVRContest']['Undervotes']: []})
        undervotes_dict[cvr_dict['CVRSnapshot']['CVRContest']['Undervotes']].append(cvr_dict['CVRSnapshot']['CVRContest'])

        overvotes.append(cvr_dict['CVRSnapshot']['CVRContest']['Overvotes'])

        cvr_contest = cvr_dict['CVRSnapshot']['CVRContest']
        nselections.append(int(cvr_contest['Selections']))
        if int(cvr_contest['Selections']) > 2:
            nselections2.append(cvr_contest)

        if 'Status' in cvr_contest:
            status.append(cvr_contest['Status'])

        if cvr_contest['ContestId'] not in contestIDdicts:
            contestIDdicts.update({cvr_contest['ContestId']: []})
        contestIDdicts[cvr_contest['ContestId']].append(cvr_contest)

# check that all rank lists are equal
first_rank = list(contestIDdicts.keys())[0]
rank_length_equal = [len(contestIDdicts[k]) == len(contestIDdicts[first_rank]) for k in contestIDdicts]
if not all(rank_length_equal):
    print("not all rank lists are equal.")
    raise RuntimeError

overvotes = []
undervotes = []
ballot_lists = []
for idx in range(len(contestIDdicts[first_rank])):

    idx_ranks = [int(contestIDdicts[rank_key][idx]['CVRContestSelection']['Rank']) for rank_key in contestIDdicts]

    idx_snapshots = []
    idx_candidates = []
    for rank_key in contestIDdicts:
        idx_snapshots.append(contestIDdicts[rank_key][idx])
        contest_dict = contestIDdicts[rank_key][idx]['CVRContestSelection']
        if 'SelectionPosition' in contest_dict:
            if isinstance(contest_dict['SelectionPosition'], list):
                idx_candidates.append("overvote")
            else:
                idx_candidates.append(candidatesIDs[contest_dict['SelectionPosition']['Position']])
        elif contest_dict['TotalNumberVotes'] == '0':
            idx_candidates.append("skipped")

    if set(idx_candidates) == {'skipped'}:
        undervotes.append(idx_snapshots)

    if set(idx_candidates) == {'overvote', 'skipped'} or set(idx_candidates) == {'overvote'}:
        overvotes.append(idx_snapshots)

    ordered_ranks = sorted(zip(idx_candidates, idx_ranks), key=lambda x: x[0])
    ballot_lists.append([t[0] for t in ordered_ranks])


x = 0




