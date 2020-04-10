from inspect import isfunction
import sys

class A:

    def _f(self, i):
        return str(i)

    fs = {key: value for key, value in globals().items()}


    if isfunction(value) and key[0] == "_" and key != "w" and value.__module__ == __name__}

def w(f):
    def new_f(tabulation_range=range(1, 2)):
        return ", ".join([f(i) for i in tabulation_range])
    return new_f

this_module = sys.modules[__name__]
fs = {key[1:]: w(value) for key, value in globals().items()
      if isfunction(value) and key[0] == "_" and key != "w" and value.__module__ == __name__}

globals()['f'] = fs['f']
