from hashlib import md5
from inspect import getsource
import shutil
import os
import pickle  # faster than json, shelve
from contextlib import suppress
from functools import wraps

#from .global_dict import get_global_dict

global global_dict
def set_global_dict(d):
    global global_dict
    global_dict = d

global cache_dir
def set_cache_dir(d):
    global cache_dir
    cache_dir = d

    if os.path.isdir(cache_dir) is False:
        os.mkdir(cache_dir)


def unwrap(function):
    """
        checks if the function has been decorated + wrapped
        (using a @decorator using @wraps)
        and returns the wrapped function (the function decorated with @decorator)
    """
    while '__wrapped__' in dir(function):
        function = function.__wrapped__
    return function


def srchash(function):
    """
        input is the name of a function (str)

        returns a hash string representing the set of all function source code
        implicated by the input function

    """

    #gd = get_global_dict()
    global global_dict

    visited = set()
    frontier = {function}  # start with input function
    while frontier:

        fun = frontier.pop()
        visited.add(fun)

        fun_obj = unwrap(global_dict[fun])  # retrieve function object, unwrapped
        code = fun_obj.__code__  # get function's underlying code object
        helpers = list(code.co_names)  # get list of names used by function bytecode

        for const in code.co_consts:  # loop through constants used by bytecode
            if 'co_names' in dir(const):  # if they are code objects
                helpers.extend(const.co_names)  # add their names to helpers

        for helper in set(helpers) - visited:  # for any new helpers
            if '__code__' in dir(global_dict.get(helper)):  # if they have code objects
                frontier.add(helper)  # add them to be looped through

    # at the end of this loop, all functions called by the input function
    # should have been recursively checked for all their function calls and
    # added to the visited set

    # visited should contain the set of all functions implicated by calling the
    # input function

    # the next lines effectively concatenate all the functions' source code
    # in visited and produce a hash unique to that code set

    h = md5()
    for f in sorted(visited):
        h.update(bytes(getsource(global_dict[f]), 'utf-8'))
    return h.hexdigest()


def shelve_key(arg):
    """
        only used in save() decorator def

        returns a string. either 'date, office, place' (if arg == dict)
            or callable.__name__ (if arg == callable)
    """
    if isinstance(arg, dict):
        return arg['dop']
        #return dop(arg)
    if callable(arg):
        return arg.__name__
    return arg


def save(f):
    """
        decorator def


    """
    global cache_dir

    f.not_called = True
    f.cache = {}

    @wraps(f)
    def fun(*args):

        # if this is the first time the function is being called during this run,
        # check that there isn't already a saved computation from previous runs
        if f.not_called:
            check = srchash(f.__name__)
            dirname = cache_dir + '/' + f.__name__
            checkname = dirname + '.check'
            # check if the saved srchash is the different from the current one
            # if so, delete the results previosuly saved from this function
            if os.path.exists(checkname) and check != open(checkname).read().strip():
                shutil.rmtree(dirname)
                os.remove(checkname)
            # if the check is absent at this point, write a new one out
            # and make a fresh results dir for this function
            if not os.path.exists(checkname):
                open(checkname, 'w').write(check)
                os.mkdir(dirname)
            # indicate that now the function has been called
            f.not_called = False

        key = tuple(str(shelve_key(a)) for a in args)

        # check if the current call is for the same election, if not, clear the cache
        if next(iter(f.cache), key)[0] != key[0]:
            f.cache = {}  # evict cache if first part of key (election id usually) is different
            f.visited_cache = False
        if key in f.cache:
            return f.cache[key]

        file_name = cache_dir + '/{}/{}'.format(f.__name__, '.'.join(key).replace('/', '.'))

        with suppress(IOError, EOFError), open(file_name, 'rb') as file_object:
            f.cache[key] = pickle.load(file_object)
            return f.cache[key]
        with open(file_name, 'wb') as file_object:
            f.cache[key] = f(*args)
            pickle.dump(f.cache[key], file_object)
            return f.cache[key]

    return fun


def tmpsave(f):
    """
        decorator used to stash function results in the ctx object. Future calls
        retrieve the stashed value instead of recomputing the actual function
    """
    @wraps(f)
    def fun(ctx):
        if f.__name__ in ctx:
            return ctx[f.__name__]
        return ctx.setdefault(f.__name__, f(ctx))

    return fun
