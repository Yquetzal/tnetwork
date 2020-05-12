#!/usr/bin/env python
"""build similarity graphs from rollcall data from voteview.com

raw senate roll call data gotten via the following bash cmds

for i in `seq 10 111`; do wget ftp://voteview.com/dtaord/sen${i}kh.ord ; done
for i in `seq 1 9`; do wget ftp://voteview.com/dtaord/sen0${i}kh.ord ; done

raw house roll call data gotten via the following bash cmds

for i in `seq 10 111`; do wget ftp://voteview.com/dtaord/hou${i}kh.ord ; done
for i in `seq 1 9`; do wget ftp://voteview.com/dtaord/hou0${i}kh.ord ; done


Network is constrcuted as specified inthe SI of this work:
Party Polarization in Congress: A Network Science Approach

arxiv.org/pdf/0907.3509

"""

import networkx as nx
import os
import sys
import re

if len(sys.argv) > 3:
    print "argv: ", sys.argv
    output_dir = os.path.abspath(sys.argv[1])
    mode = sys.argv[2]
    bystate = eval(sys.argv[3])
    if not mode in [ "senate", "house"] :
        sys.exit("Invalid mode: %s, should be either house or senate"%mode)
else:
    sys.exit("usage: %s output_dir mode(house or senate) aggregration_bystate(True or False)" % sys.argv[0] )


if os.path.isdir(output_dir):
    sys.exit("result dir already exists, will not overwrite")
else:
    os.mkdir(output_dir)


def congress_no_from_filename(fname):
    return int(fname.rstrip("kh.ord").lstrip(mode[:3]))

def vote_to_weight(vote):
    """ convert a vote value to weight inthe bi-partite graph """
    ivote = int(vote)
    if ivote >= 1 and ivote <= 3:
        weight = +1
    elif ivote >= 3 and ivote <= 6:
        weight = -1
    else:
        weight = 0

    return weight    



datadir = "./%s_rollcall_raw"%mode

# read some info for cross checking 
# from http://www.voteview.com/icpsr.htm
## ftp://voteview.com/junkord/s01112nw.txt
icpsr_dict = {} # key = (congress, icpsr_id), val = list of info about the member
with open("%s_icpsr.txt"%mode, 'r') as f:
    for l in f:
        cols = l.split()
        # somtimes there is an asterist after congress no, cant find out why.
        # Strip it anyways  
        icpsr_dict[(cols[0].rstrip('*'), cols[1])] = cols
#print "icpsr_dict: ", icpsr_dict

# read state codes for further disambiguation
# http://voteview.com/state_codes_icpsr.htm
state_icpsr_dict = {} # key = statename[7:], val = icpsr state code 
with open("state_codes_icpsr.txt", 'r') as f:
    for l in f:
        #print "l :", l
        cols = l.split()
        #print "cols: ", cols
        state = ' '.join(cols[2:])
        state_icpsr_dict[state[:7]] = int(cols[0])
print "state_icpsr_dict: ", state_icpsr_dict

raw_file_list = os.listdir(datadir)
#raw_file_list = ["hou48kh.ord"]
timestamps = sorted([congress_no_from_filename(f) for f in raw_file_list if
  f.endswith(".ord")])

print "timestamps:", timestamps


for fname in sorted(raw_file_list, key=congress_no_from_filename):

    print "filename :", fname
    congress = congress_no_from_filename(fname)
    print "congress :", congress
    
    g1 = nx.Graph(name="g1")
    mg1 = nx.MultiGraph(name="mg1")
    senators = []

    prev_state = ""
    with open(os.path.join(datadir, fname)) as f:
        for line in f:
            if not line:
                continue
            print "---------------------------------------"
            print "line: ", line
            # split into fields, wher each field is a numeric group
            fields = re.findall(r'\d+',line)
            print "fields: ", fields
            alphafields = re.findall(r"[A-Z., '-]+",line)
            print "alphafields: ", alphafields
            # Special case to deal with name BURDICK2 in congress 104
            if alphafields[-1] == '   ' :
                del alphafields[-1]
            name = alphafields[-1].strip()
            state = alphafields[-2].strip()
            print "name: ", name, "state: ", state, "state_icpsr_id: ", state_icpsr_dict[state], "prev_state: ", prev_state

            if mode == "senate":

                # there are 4 different formats for the first 3 fields in the data
                # Notice there may or may not be a space
                # Congress ICPSRID STATEID 
                # Congress ICPSRIDSTATEID 
                # CongressICPSRIDSTATEID
                # CongressICPSRID STATEID 
                
                # Luckily there is redundant info in the line: the state name which
                # we can parse to figure out the stateid. Similarly the congress no
                # can be gotten from the filename. Finally the parse info can be
                # verified from the ICPSR ID's known separtely.
                

                if int(fields[0]) == congress:   
                    if int(fields[2]) == state_icpsr_dict[state]: # Congress ICPSRID STATEID 
                        icpsr_id = int(fields[1])
                    elif fields[1].rfind(str(state_icpsr_dict[state])) != -1 : # Congress ICPSRIDSTATEID    
                        icpsr_id = fields[1][:fields[1].rfind(str(state_icpsr_dict[state]))]
                    else:
                        sys.exit("State %s, %d not found in line" % (state, state_icpsr_dict[state]))
                else:   # CongressICPSRIDSTATEID
                    congress_loc = fields[0].find(str(congress))
                    if congress_loc == -1:
                        sys.exit("%d not found in fields[0]:%s" %(congress, fields[0]) )
                    # senator id is the 5 digits after congress no.    
                    # or if there is whitespace then its the next word which could be less than 5 digits
                    icpsr_start = congress_loc + len(str(congress))
                    if int(fields[1]) == state_icpsr_dict[state]: # CongressICPSRIDSTATEID
                        icpsr_id = int(fields[0][icpsr_start:])
                    else:
                        icpsr_end = fields[0].rfind(str(state_icpsr_dict[state]))
                        icpsr_id = int(fields[0][icpsr_start:icpsr_end])
               
            else: #mode == "house" 
                m = re.match(r"[0-9 ]+", line) # assume there is no space in the fields so there are fewer cases to deal with
                first4 = m.group().replace(' ','')
                print "first4fields: ", first4	
                      
                # find and remove the congress no from the beginning of the
                # string
                congress_loc = first4.find(str(congress))
                if congress_loc == -1:
                    sys.exit("%d not found in first4:%s" %(congress, first4) )
                next3 = first4[congress_loc+len(str(congress)):]
                print "next 3 fields: ", next3

                # remove congressional district no from the end of the string
                # assume congressional district no increases sequentially from 1
                # for each state, and check for some special codes like 98
                
                special_dist_numbers = ['98', '99']

                found = False
                for special_distno in special_dist_numbers:
                    distno_loc = next3[-2:].rfind(special_distno)
                    if distno_loc != -1:
                        mid2 = next3[:-2]
                        found = True
                        print "may be found special_distno: ", special_distno
                        # the foll line creates a problem since 98 matches, try to deal
                        # with ith
                        # line:   48 648749 8TEXAS   10001MILLER, J.F11616666111....

                        if mid2.rfind(str(state_icpsr_dict[state])) == -1: 
                            print "could not confirm found special_distno: ", special_distno
                            found = False
                            continue
                        break

                if not found:
                    if state == "USA":
                        expected_distno = 0
                    elif state != prev_state:
                        expected_distno = 1
                    
                    while expected_distno < 60:
                        print "expected_distno: ", expected_distno
                        distno_loc = next3[-len(str(expected_distno)):].rfind(str(expected_distno))
                        if distno_loc != -1:
                            mid2 = next3[:-len(str(expected_distno))]
                            found = True
                            break
                        else: # sometimes there are two congressmen from the same district, so try to find that    
                            expected_distno += 1
                            
                if not found:
                    sys.exit("Could not find expected_distno: %s"% str(expected_distno))

                print "mid2: ", mid2
                # find state id and remove it from the end of the string

                state_loc = mid2.rfind(str(state_icpsr_dict[state])) 
                print "state_loc: ", state_loc
                if state_loc != -1 : 
                    icpsr_id = mid2[:state_loc]
                else:
                    sys.exit("ERROR: state %s not found in mid2: %s"%(state,mid2))

                # whats remaining is the icpsr id, check that it is indeed so
                print "congress: ", congress, "icpsr_id: ", icpsr_id 

            # check if (congress, icpsr_id) is found in the icpsr dict. 
            if not (str(congress), str(icpsr_id)) in icpsr_dict:
                sys.exit("ERROR: (congress,icpsr_id) = (%s,%s) not found in icpsr_dict" 
                   % (str(congress),str(icpsr_id)))

            votes = fields[-1]
            if bystate is True:
                state_id = state_icpsr_dict[state]
                g1.add_node(state_id)
                senators.append(state_id)
                if not votes.isdigit():
                    sys.exit("ERROR   non digits in votes:%s"% votes)
                print "votes: ", votes
      
                # if edge state_id, bill exists, then add to its weight
                # else add the edge with the new weight

                # make a bi-partite multi-graph first, so that we can capture
                # the votes of both senators
                mg1.add_weighted_edges_from([(state_id, 'b'+str(c), vote_to_weight(votes[c]))
                        for c in xrange(len(votes))
                        if vote_to_weight(votes[c]) is not 0])

                
            else:  
                g1.add_node(icpsr_id)
                senators.append(icpsr_id)
                #cols = line.split()[-1] # Sometimes there is no whitespace between
                                  # senator name and voting stats, so split does not work
                if not votes.isdigit():
                    sys.exit("ERROR   non digits in votes:%s"% votes)
                print "votes: ", votes
                g1.add_weighted_edges_from([(icpsr_id, 'b'+str(c), vote_to_weight(votes[c]))
                        for c in xrange(len(votes))
                        if vote_to_weight(votes[c]) is not 0])

            prev_state = state


    if bystate is True:
        # now simplify the multigraph by adding up the weights of
        # multi-edges between any two nodes
        for e in mg1.edges():
            if g1.has_edge(*e):
                continue
            #print "Sum: ", sum([i['weight'] for i in mg1[e[0]][e[1]].values()])
            g1.add_edge(e[0], e[1], 
                weight=sum([i['weight'] for i in mg1[e[0]][e[1]].values()]))


    print nx.info(g1)
    #print "g1 nodes: ", str(g1.nodes())
    #print "g1 edges: ", str(g1.edges(data=True))
    #print "mg1 edges: ", str(mg1.edges(data=True))
    #print "mg1 edges: ", str(mg1.edges(data=True))

    g2 = nx.Graph(name="g2")

    for n1 in senators:
        for n2 in senators:
            if n1==n2 :
                continue
            n1_bills = g1.neighbors(n1)
            n2_bills = g1.neighbors(n2)
            common_bills = list(set(n1_bills) & set(n2_bills))
            if len(common_bills) is 0:
                continue
            similar_votes = 0
            for b in common_bills:
                if g1[n1][b]['weight'] == g1[n2][b]['weight']:
                    similar_votes += 1
                    #print  "weights: ", g1[n1][b]['weight'] ,  g1[n2][b]['weight']
            similarity = float(similar_votes)/len(common_bills)    
            g2.add_weighted_edges_from([(n1, n2, similarity)])

    print nx.info(g2)
    print "g2 nodes: ", str(g2.nodes())
    outfname = os.path.join(output_dir, str(congress)+'.ncol')
    nx.write_weighted_edgelist(g2, outfname)

        
