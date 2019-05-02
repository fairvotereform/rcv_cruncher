import fileinput
import re
for line in fileinput.input():
    if ': {' in line:
        a,b = line.split(': {')
        old = a
        for i in b.replace("'",' ').split(' '):
            a = a.replace(i,'').strip()
        a = "'office': '{}', {}".format(re.sub(' +', ' ',a).replace("' ",'').replace(" '", ''), b)
        print(old + ': {' + a[:-1])
    else:
        print(line[:-1])

