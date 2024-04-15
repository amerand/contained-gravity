#!/usr/bin/env python3

import sys, os

directory = sys.argv[1]

# http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
colors = {'GREEN':'\033[92m',   'GREENBG':'\033[42m',
          'BLUE':'\033[94m',    'BLUEBG':'\033[44m',
          'RED':'\033[91m',     'REDBG':'\033[41m',
          'YELLOW':'\033[93m',  'YELLOWBG':'\033[43m',
          'GRAY':'\033[90m',    'GRAYBG':'\033[40m',
          'CYAN':'\033[36m',    'CYANBG':'\033[46m',
          'MAGENTA':'\033[95m', 'NO_COL':'\033[0m' }

ls = os.popen('cd %s; dfits *.fits | fitsort DPR.CATG DPR.TYPE DPR.TECH INS.SPEC.RES INS.POLA.MODE DET2.SEQ1.DIT PRO.REC1.PIPE.ID '%directory)
n = 0

configs = []

for l in ls.readlines():
    if "Pipeline" in l:
        c = 'GREENBG'
    else:
        if 'SCIENCE' in l:
            c = 'BLUEBG'
        elif 'DARK' in l:
            c = 'GRAY'
        elif 'P2VM' in l:
            c = 'YELLOW'
        elif 'WAVE' in l:
            c = 'RED'
        elif 'FLAT' in l:
            c = 'MAGENTA'
        elif 'DIRECT' in l:
            c = 'YELLOWBG'
        else:
            c = 'NO_COL'
    if not "Pipeline" in l:
        print(colors[c]+l.strip()+colors['NO_COL'])
        if not l.startswith('FILE'):
            config = '-'.join(l.split()[-3:])
            if not config in configs:
                configs.append(config)
    else:
        n+=1
if n>0:
    print("%d reduced files ignored"%n)
#print configs
