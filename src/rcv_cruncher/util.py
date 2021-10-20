import decimal
import os
import pathlib
import csv

###############################################################
# constants

NAN = decimal.Decimal("NaN")

########################
# helper funcs


class CSVLogger:
    def __init__(self, path, header_list):
        self.row_length = len(header_list)
        self.path = path
        self.file = open(path, "w", newline="")
        self.writer = csv.writer(self.file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        self.lines_added = None
        self.write(header_list)
        self.lines_added = False

    def write(self, row_list):
        if len(row_list) != self.row_length:
            msg = f"CSVLogger.write ({self.path.name}) row list has length {len(row_list)}, "
            msg += f"doesn't match header list length ({self.row_length})"
            raise RuntimeError(msg)
        self.writer.writerow(row_list)
        self.file.flush()
        if self.lines_added is not None and not self.lines_added:
            self.lines_added = not self.lines_added

    def close(self):
        self.file.flush()
        self.file.close()


def before(victor, loser, ballot):
    """
    Used to calculate condorcet stats. Each ballot passed through this
    function gets mapped to either
    1 (winner ranked before loser),
    0 (neither appear on ballot),
    or -1 (loser ranked before winner).
    """
    for rank in ballot:
        if rank == victor:
            return 1
        if rank == loser:
            return -1
    return 0


def remove(x, lst):
    # removes all x from list l
    return [i for i in lst if i != x]


def isInf(x):
    # checks if x is inf
    return x == float("inf")


def index_inf(lst, el):
    # return element index if in list, inf otherwise
    if el in lst:
        return lst.index(el)
    else:
        return float("inf")


def verifyDir(dir_path, make_if_missing=True, error_msg_tail="is not an existing folder"):
    """
    Check that a directory exists and if missing, either error or create it.

    :param dir_path: directory path to verify
    :param make_if_missing: if True, create directory if missing
    :param error_msg_tail: if make_if_missing is False and directory missing,
     print this error message after the dir_path.
    """
    if os.path.isdir(dir_path) is False:
        if make_if_missing:
            os.mkdir(longname(dir_path))
        else:
            print(dir_path + " " + error_msg_tail)
            raise RuntimeError


def flatten_list(lst):
    return [i for sublist in lst for i in sublist]


def decimal2float(stat, round_places=3):
    """Convert any decimal objects used internally into float for reporting.

    Args:
        stat (any): Any value.

    Returns:
        any type not Decimal: If the stat passed is type Decimal, it is converted to float.
    """

    if isinstance(stat, decimal.Decimal):
        return round(float(stat), round_places)
    else:
        return stat


def DL2LD(dl):
    return [dict(zip(dl, t)) for t in zip(*dl.values())]


def LD2DL(ld):
    # assumes all dicts have same keys, which they should in these use cases
    return {k: [dic[k] for dic in ld] for k in ld[0]}


def longname(path):
    return pathlib.Path("\\\\?\\" + os.fspath(path.resolve()))


def filter_bool_dict(ballots, field_name):
    val_list = ballots[field_name]
    return {split_val: [split_val == i for i in val_list] for split_val in set(val_list)}
