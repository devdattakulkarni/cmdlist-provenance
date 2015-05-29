#!/bin/python

# Author: Devdatta Kulkarni (devdatta@cs.utexas.edu)

import re
import sys

def check_if_exists(cmd, cmdlist):
    for c in cmdlist:
        pattern = c
        reg = re.compile(pattern)
        m = reg.match(cmd)
        if m is not None:
            return True
    return False


cmdfile = sys.argv[1]

print "Cmd file: %s" % cmdfile

navigation_cmds = ['cd', 'pushd', 'popd']
listing_cmds = ['ls', 'history']
viewing_cmds = ['less', 'more']
editing_cmds = ['emacs', 'vi']

anchor_cmds = ['apt-get update']

f = open(cmdfile, 'r')

lines_in_file = []

pattern = '^\d+ '
reg = re.compile(pattern)

for line in f:
    line = line.strip()
    m = reg.match(line)
    if m is not None:
        line = line.replace(m.group(0), '')
        lines_in_file.append(line.strip())

print "Lines in file:"
print lines_in_file

candidate_list = []

#for l in reversed(lines_in_file):
#    if l not in listing_cmds:
#        print l
#    if not check_if_exists(l, listing_cmds):
#        print l
#exit(0)

provenance_generated = False
while not provenance_generated:
    for l in reversed(lines_in_file):

        if (not check_if_exists(l, navigation_cmds) and
            not check_if_exists(l, listing_cmds) and
            not check_if_exists(l, viewing_cmds) and
            not check_if_exists(l, editing_cmds)):
            candidate_list.append(l)

        if (l not in navigation_cmds and
            l not in listing_cmds and
            l not in viewing_cmds and
            l not in editing_cmds):
             candidate_list.append(l)

        if l in anchor_cmds:
           print "Candidate list:"
           print cand_list
           print candidate_list

           provenance_generated = True
           break


  


    
