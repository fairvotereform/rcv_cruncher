
import pathlib

from typing import (List, Union, Callable, Dict)

# used in parser function
Path = Union[str, pathlib.Path]

# ballot information in dict-of-list form
BallotDictOfLists = Dict[str, List]

# returned from parser module, get_parser_dict
ParserDict = Dict[str, Callable[[Path], BallotDictOfLists]]
