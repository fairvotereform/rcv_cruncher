from scripts.contests import new_contest_set
import os

# get the path of this file
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

new_contest_set()
