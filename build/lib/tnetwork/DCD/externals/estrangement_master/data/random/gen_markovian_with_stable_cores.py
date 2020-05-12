#!/usr/bin/python 

import networkx as nx
import random
import sys
import os


def evolve(g, p_c, p):
    """ 

   Do one markovian evolution where existing edge disappears with prob
p (stays with prob 1-p) and a non-existing one appears with prob q
(and stays off with prob 1-q). Arbitrary values of p and q however
change the density of edges in the cluster. It turns out however if we
set q= p*p_c/(1-p_c) then the density of the cluster stays the same on
average.

    """
    g_new = nx.Graph()
    for e in g.edges_iter(data=True):
        if random.random() <= 1-p:  # edge remains on with prob 1-p
            g_new.add_edge(e[0], e[1], weight=1.0)
        

    # q is chosen so as to keep density invariant
    # set fraction of edges turning on equal to those turning off
    # Solve p *p_c = (1-p_c) q
    # Check this logic!!

    # note p_c <= 1/(1+p) for q <= 1
    q = (p_c*p)/(1-p_c)

    g_complement = nx.complement(g)  
    for e in g_complement.edges_iter():
        if random.random() <= q:  # add edge from g_complement with prob q
            g_new.add_edge(e[0], e[1], weight=1.0)

    return g_new


def gen_markovian_with_stable_cores(p_r=0.02, p_c=0.2, p=0.5, n=50, n_c=20,
    snapshots=25, core_age=10):
    """ generate a markovly evolving core with a random background 
    
    p_r : prob of random background edges
    p_c : initial prob of intra-core edges
    p : markov transition prob of an edge going from up to down
    n: number of nodes in the entire graph
    n_c: number of nodes in each core
    
    """

    output_dir = "benchmark_markovian_pc%1.2f_p%1.2f_pr%1.2f_nc%d_n%d" %(p_c, p, p_r, n_c, n)

    if os.path.isdir(output_dir):
        sys.exit("output dir already exists, will not overwrite")
    else:
        os.mkdir(output_dir)
        # make the expt dirs as well to save work
        os.mkdir(os.path.join("/home/vkawadia/repos/improp/runs",output_dir))
        configsdir = os.path.join("/home/vkawadia/repos/improp/runs",output_dir, "configs")
        os.mkdir(configsdir)
        parameterlistsconf = """ # simulation configuration parameter lists file.
# the entire file is a single python dict whose keys are valid  options
# and values is a dict of all values to be iterated over in this run of
# simulations.
# Do lpa.py --help for a complete list of options and help text.
# Note string options need to be enclosed in "' '"
# 
# $Id: $
{
    'loglevel' : ['INFO'],
    'graph_reader_fn' : ['read_general'],
    'graph_reader_fn_arg' : ["'%s'"],
    'delta' : [ 0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 1.0 ],
    'minrepeats' : [ 10 ],
    'increpeats' : [ 5 ],
    'convergence_tolerance': [ 0.01 ],
    'savefor_layouts' : [True],
    'profiler_on' : [False],
}
""" % (output_dir)
    with open(os.path.join(configsdir, "parameter-lists.conf"),'w') as fout:
        fout.write(str(parameterlistsconf))
    postproconf = """ nodes_of_interest = '[]'
colorbar = False
deltas_to_plot = '[ 0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 1.0 ]'
nodeorder = 'range(50)'
tiled_figsize = '(16, 9)'
wspace = 0.04
frameon = True
show_yticklabels = True
loglevel = 'DEBUG'
label_sorting_keyfunc = 'math.sin'
fontsize = 24
image_extension = "eps"
ground_truth_file = "../../../datasets/%s/ground_truth_temporal_labels.txt"
""" %(output_dir)

    with open(os.path.join(configsdir, "postpro.conf"),'w') as fout:
        fout.write(str(postproconf))

    open(os.path.join(configsdir, "analysis.conf"),'w').close()
    open(os.path.join(configsdir, "vcsrev"),'w').close()



    # dictionary for recording the ground truth
    ground_truth_temporal_label_dict = {} # key = (node, time), val = label

    
    #assert p_c < 1/(1+float(p)), "p_c can be at most 1/(1+p)=%f" % 1/(1+float(p))
    assert p_c <= 1/(1+float(p))

    for t in xrange(snapshots):
        print "t :", t

        if t == 0:
            g_core = nx.gnp_random_graph(n_c, p_c)
        elif t == snapshots - core_age:    
            g_core_tmp = nx.gnp_random_graph(n_c, p_c)
            #print "g_core_tmp:", g_core_tmp.edges()
            # function returns nodes startting from 0. relabel them to start from n-n_c
            #print "n: ", n
            mapping = dict([(i, i+n-n_c) for i in xrange(n_c)])
            #print "mapping:", mapping
            g_core = nx.relabel_nodes(g_core_tmp, mapping)
            #print "g_core:", g_core.edges()
        else:
            g_core = evolve(g_core, p_c, p)
        
        # backgriound random graph        
        g_bg = nx.fast_gnp_random_graph(n, p_r)
        
        if t >= core_age and t< snapshots - core_age:    # no core in the middle few snapshots
            g_full = g_bg
        else:    
            g_full = nx.compose(g_bg, g_core)

        g_fullw = nx.Graph()
        g_fullw.add_edges_from(g_full.edges(), weight=1.0)
        # note isolated nodes were left out when g_full_w was made inthis
        # fashion

        nx.write_weighted_edgelist(g_fullw, (os.path.join(output_dir, "%d.ncol"%t)))
        print g_fullw.edges()

        # make the ground truth partitions
        #default unique temporal label
        for i in g_fullw.nodes():
            ground_truth_temporal_label_dict[(i,t)] = 100000*t + i    

        # technically should leave out isolated nodes but the core is always
        # connected for our benchmarks.
        # 1st core
        if t in xrange(core_age):
          for i in xrange(n_c): 
                ground_truth_temporal_label_dict[(i,t)] = 1    
        
        # 2nd core
        if t in xrange(snapshots - core_age, snapshots) :
          for i in xrange(n-n_c, n):
                ground_truth_temporal_label_dict[(i,t)] = 2    

    with open(os.path.join(output_dir, "ground_truth_temporal_labels.txt"),'w') as fout:
        fout.write(str(ground_truth_temporal_label_dict))

if __name__ == "__main__":
    
    # generate a bunch of dirs for the final runs
    for p_c in [0.2, 0.4, 0.6] :
        for p in [0.2, 0.3, 0.4, 0.5, 0.6] :
            gen_markovian_with_stable_cores(p_r=0.05, p_c=p_c, p=p, n=50, n_c=20,
            snapshots=25, core_age=10)
    


    # test some corner cases

    #gen_markovian_with_stable_cores(p_r=0.0, p_c=0.99, p=0.0, n=5, n_c=2,
    #snapshots=5, core_age=2)
