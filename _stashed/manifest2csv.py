from manifest import competitions
import pandas as pd
import re

def uneval_parser(f):

    fstr = f.__str__()

    output_str = ''
    func_name = ''

    # extract the parser function name
    regex_match = re.search('.*function (.*) at.*', fstr)
    if regex_match:
        output_str = regex_match.group(1)
    else:
        print('uneval_parser not applicable')
        print(fstr)
        raise ValueError()

    # if it was called with partial. get the extra arguments
    if 'partial' in fstr:
        fstr_split = fstr.split('>')[1]
        output_str = 'partial(' + output_str + fstr_split

    return(output_str)


if __name__ == '__main__':

    output_val_defaults = {'break_on_overvote': '',
                           'break_on_repeated_undervotes': '',
                           'candidate_map': '',
                           'chp': '',
                           'contest': '',
                           'date': '',
                           'idparser': '',
                           'master_lookup': '',
                           'number': '',
                           'office': '',
                           'parser': '',
                           'path': '',
                           'place': '',
                           'write_ins': ''}

    listOdict = []
    competitions_keys = ['contest']

    # turn dictionary into list of dictionaries, one entry for each
    # initial key value pair -- key becomes 'contest' entry in each resulting dictionary
    for k in competitions:

        new_dict = {'contest': k}
        new_dict.update(competitions[k])
        listOdict.append(new_dict)

        competitions_keys += competitions[k].keys()

    # collect all the keys that exist in the listed dictionaries
    competitions_keys = set(competitions_keys)

    # make sure all the keys read in have a default
    keys_check = [k for k in competitions_keys if k not in output_val_defaults]

    if len(keys_check) != 0:
        print('output_val_defaults: ', end='')
        print(output_val_defaults)
        print('missing default values: ', end='')
        print(keys_check)
        exit(1)

    # convert list of dicts to a single dictionary with 1 list per key
    # containing all the values for a single key
    dictOlist = {}

    for k in competitions_keys:

        vals = []

        for d in listOdict:

            if k in d:

                if k == 'parser' or k == 'idparser':
                    v = uneval_parser(d[k])
                else:
                    v = d[k]

            else:
                v = output_val_defaults[k]

            vals.append(v)

        dictOlist[k] = vals

    pd.DataFrame.from_dict(dictOlist).to_csv('manifest_unchecked.csv', index=False)