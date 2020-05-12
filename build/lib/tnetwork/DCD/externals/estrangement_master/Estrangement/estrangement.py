#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 
This module implements the Estrangement Confinement Algorithm (ECA)  and various functions necessary 
to read the input snapshots, process information and return the results and/or print them to file.
"""

__all__ = ['make_Zgraph','read_general','maxQ','repeated_runs','ECA']

__author__ = """\n""".join(['Vikas Kawadia (vkawadia@bbn.com)',
    'Sameet Sreenivasan <sreens@rpi.edu>',
    'Stephen Dabideen <dabideen@bbn.com>'])

# Copyright (C) 2012 by 
# Raytheon BBN Technologies and Rensselaer Polytechnic Institute
# All rights reserved. 
# BSD license. 

import networkx as nx
import math
import os
from scipy import optimize
import pprint
import tnetwork.DCD.externals.estrangement_master.Estrangement.lpa as lpa
import tnetwork.DCD.externals.estrangement_master.Estrangement.utils as utils
import tnetwork.DCD.externals.estrangement_master.Estrangement.agglomerate as agglomerate
import logging
import multiprocessing
import progressbar


itrepeats = 0


def read_general(datadir,tolerance,minrepeats):

    """ Function to read datasets from files in *datadir*.
   
    Each file represents a graph for a particular timestamp. 
    The name of the files is expected to be <timestamp>.ncol,
    and each line in the file represents one edge in the graph e.g.
    line:' 1 2 5 ' indicates there is an edge between nodes
    '1' and '2' with weight '5'

    Parameters
    ----------
    datadir: string
        path to the directory containing the dataset.
    tolerance: float,optional
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller it is, the fewer dominant labels there 
        will be. 
    minrepeats: integer
        The number of variations to try before returning the best partition.            

    Returns 
    ------- 
    t: list
        an array of timestamps, each representing a snapshot of the communities.
    g1: networkx.Graph
        the last graph to be read from file.
    initial_label_dictionary: dictionary { node: community}
        A dictionary mapping nodes to community labels if it is the first snapshot, otherwise *None*.
    """

    raw_file_list = os.listdir(datadir)
    timestamps = sorted([int(f.rstrip(".ncol")) for f in raw_file_list if f.endswith(".ncol")])

    initial_label_dict_filename = os.path.join(datadir, 'initial_label_dict.txt')

    beginning = True
    for t in timestamps:
        f = str(t) + ".ncol"
        fpath = os.path.join(datadir,f)

        # if a file is empty, move on to the next timestamp
        if os.path.getsize(fpath) == 0:
            continue

        g1 = nx.read_edgelist(fpath, nodetype=int, data=(('weight',float),))
        #g1 = nx.read_edgelist(fpath, data=(('weight', float),))
        if beginning is True:
            # when called for the first time just return initial_label_dict
            if not os.path.exists(initial_label_dict_filename):
                initial_label_dict = maxQ(g1,tolerance=tolerance,minrepeats=minrepeats)
                with open(initial_label_dict_filename, 'w') as lf:
                    lf.write(repr(initial_label_dict))

            with open(initial_label_dict_filename, 'r') as lf:
                initial_label_dict = eval(lf.read())
            yield (t, g1, initial_label_dict)
            beginning = False
        else:
            yield (t, g1, None)


def maxQ(g1,tolerance=0.00001,minrepeats=10):

    """ Function which returns the partitioning of the input graph, into communities, 
    which maximizes the value of the quality function Q. 

    In this case, the quality function is modularity. See, [Blondel08]_ for more details. 
    Note that estrangement is not taken into cosideration in this calculation.
    This is only used for computing a partition for the intial snapshot.

    Parameters
    ----------
    g1: networkx.Graph
        The input graph.
    minrepeats: integer, optional
        The number of variations to try before returning the best partition. 
    tolerance: float, optional
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller it is, the fewer dominant labels there 
        will be. 


    Returns
    -------
    dictPartition: dictionary {node:community}
        The partitioning which results in the best value of the quality function: Q (modularity).

    Examples
    --------
    >>> g0 = nx.Graph
    >>> g0.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,4,{'weight':1})])
    >>> print(maxQ(g0,minrepeats=10))
    """

    dictPartition = {}
    dictQ = {}
    # To do pure Q maximization, lambda should be 0 and the ZGraph should be empty
    lambduh = 0.0
    Zgraph = nx.Graph()
    # do multiple runs and pick the best
    for r in range(10*minrepeats):
        # best_partition calls agglomerative lpa
        dictPartition[r] = agglomerate.best_partition(g1,1.0,tolerance,lambduh, Zgraph)  # I removed an opt here
        dictQ[r] = agglomerate.modularity(dictPartition[r], g1)
    logging.info("dictQ = %s", str(dictQ))
    bestr = max(dictQ, key=dictQ.get)
    return dictPartition[bestr]


def make_Zgraph(g0, g1, g0_label_dict):

    """Constructs and returns the Zgraph, as defined in Eq 3 of the paper.

    Parameters
    ----------
    g0, g1: networkx.Graph
        The previous and the current network snapshot, respectively
    g0_label_dict: dictionary {node:community}
        Cpmmunity labels for the nodes in g0 (the previous snapshot)

    Returns
    -------
    Z: graph
        The Zgraph

    Examples
    --------
    >>> g0 = nx.Graph()
    >>> g0.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,4,{'weight':1})])
    >>> g1 = nx.Graph()
    >>> g1.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(3,4,{'weight':1})])
    >>> labels = {1:'b',2:'b',3:'b',4:'b',5:'b',6:'b'}
    >>> print(make_Zgraph(g0,g1,labels)
    """

    Z = nx.Graph()
    Z.add_weighted_edges_from(
        (e[0], e[1], math.sqrt(float(g0[e[0]][e[1]]['weight'] * g1[e[0]][e[1]]['weight'])))
        for e in g1.edges()
            if g0.has_edge(*e[:2]) and g0_label_dict[e[0]] == g0_label_dict[e[1]]
    )        

    return Z 


def repeated_runs(g1, delta, tolerance, lambduh, Zgraph, repeats):

    """ Function to make repeated calls to the Label Propagation Algorithm (LPA) and
    store the values of Q, E and F, as well as the corresponding partitioning
    for later use. F is the Lagrangian, referred to in the paper as L.
   
    Parameters
    ----------
    g1: networkx graph
        The input graph
    delta: float
        The temporal divergence. Smaller values imply greater emphasis on temporal
        contiguity whereas larger values place greater emphasis on finding better
        instanteous communities.
    tolerance: float
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller the value of tolerance, the fewer dominant 
        labels there will be.
    Zgraph: networkx graph
        Graph where each edges join nodes belonging to the same community over
        previous snapshots
    repeats: integer
        The number of calls made to best partition to best_parition.

    Returns
    -------
        dictPartition: List of dictionaries representing community labeling
        dictQ: List of values of Q corresponding to the above labeling
        dictE: List of values of E corresponding to the above labeling
        dictF: List of values of F corresponding to the above labeling
        
    Examples
    --------
    >>> g0 = nx.Graph()
    >>> g0.add_edges_from([(1,2,{'weight':1}),(2,3,{'weight':1}),(1,3,{'weight':1}),(3,4,{'weight':1}),(4,5,{'weight':1}),(4,6,{'weight':1}),(5,7,{'weight':1}),(6,7,{'weight':1}),(8,9,{'weight':1}),(8,10,{'weight':1}),(9,10,{'weight':1})])
    >>> dictPartition,dictQ,DictE,DictF = estrangement.repeated_runs(g0, delta=0.05, tolerance=0.01, lambduh=1,g0,repeats = 3)
    """

    dictPartition = {}  # key = run number, val = label_dict
    dictQ = {}          # key = run number, val = Q for that run
    dictE = {}          # key = run number, val = E for that run
    dictF = {}          # key = run number, val = F for that run
    q = multiprocessing.Queue() 
    # the for loop below does repeat number of runs to find the best F using
    # agglomerate lpa. Node visitation order is randomized in the LPA thus
    # giving potentially different results each run. 
    for r in range(repeats):
#        p = multiprocessing.Process(target=agglomerate.best_partition,args=(g1, delta, tolerance, lambduh, Zgraph,None,q))
#        p.start()
         agglomerate.best_partition(g1, delta, tolerance, lambduh, Zgraph,None,q)


    for r in range(repeats):
        r_partition = q.get()
        dictPartition[r] = r_partition
        dictQ[r] = agglomerate.modularity(r_partition, g1)
        dictE[r] = utils.Estrangement(g1, r_partition, Zgraph)
        dictF[r] = dictQ[r] - lambduh*dictE[r] + lambduh*delta
        
    return (dictPartition, dictQ, dictE, dictF)

def ECA(dataset_dir='./data', results_filename= "matched_labels.log", tolerance=0.00001,convergence_tolerance=0.01,delta=0.05,minrepeats=10,increpeats=10,maxfun=500,write_stats=False):

    """ The Estrangement Reduction Algorithm, as decribed in: [KS12]_. 
    This function detects temporal communities and returns the results. 

    Parameters
    ----------
    dataset_dir: string
        Path to the relevant dataset files
    results_filename: string
        The resulting community partition is written to this file.    
        It is a dictionary of the form: {time : {node : label}}
    tolerance: float, optional
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller it is, the fewer dominant labels there will be. 
    convergence_tolerance: float,optional
        The convergence tolerance used in optimizing the value of lambda.
    delta: float
        The temporal divergence. Smaller values imply greater emphasis on temporal
        contiguity whereas larger values place greater emphasis on finding better
        instanteous communities.
    minrepeats: integer,optional
        The number of times to call LPA. Each call increases the likilhood of finding the optimal
        partition, however, such a partition may be found with few calls depending on the graph. 
    increpeats: integer,optional
        The size of a step in the LPA.
    maxfun: integer, optional
        The maximum number of function calls made to optimize lambda.
    write_stats, optional
        If 'True', the stats are written to files named <stat>.log
        These logs are not needed to plot temporal communities but are needed to plot other stats. 

    Returns
    -------
    matched_labels : dictionary {time: {node:label}}
        The labelling of each node for each snapshot
    
    References
    ----------
    .. [KS12] Vikas Kawadia and Sameet Sreenivasan, ``Sequential detection of temporal communities by estrangement confinement ,'' in Nature Scientific Reports, Nov 2012, http://www.nature.com/srep/2012/121109/srep00794/full/srep00794.html
 
    Examples
    --------
    >>> ECA(dataset_dir='tests/sample_data',delta=0.001)
    """

    # set up directory structure for this delta
    dir_name = 'task_delta_' + str(delta)
    if(not os.path.exists(dir_name)):
        os.mkdir(dir_name)
    os.chdir(dir_name)

    # The results from each set of parameters are written to a unique folder,
    # with name reflecting the parameters chosen. The relevant parameters are
    # written to a log for later reference.
    with open("options.log", 'w') as optf:
        optf.write("{'delta':" + str(delta) + "}")

    matched_labels = {}

    snapstats = SnapshotStatistics()

    # keeping track of max number of nodes and num snapshots for help in plotting
    nodename_set = set()
    snapshots_list = []

    beginning = True
    snapshot_number = 0
    r = len(list(os.listdir(dataset_dir)))-1
    count = 0
    bar = progressbar.ProgressBar(max_value=r)
    for t, g1, initial_label_dict in read_general(dataset_dir,
                        tolerance=tolerance,minrepeats=minrepeats):
        #print(t)

        bar.update(count)
        count+=1
        snapshots_list.append(t)
        nodename_set.update(g1.nodes())

        if beginning is True:
            g0 = g1
            prev_label_dict = {}
            prev_matched_label_dict = {}

            label_dict = initial_label_dict 
            if len(label_dict) != g1.number_of_nodes():
                raise nx.NetworkXError("Initial label_dict does not have the same number of nodes as g1")

            snapstats.Q[t] = agglomerate.modularity(label_dict, g1)
            Zgraph = nx.Graph() 
            beginning = False
        else:
            Zgraph = make_Zgraph(g0, g1, prev_label_dict)

            # Record Q* for comparison
            dictlabel_dict0, dictQ0, dictE0, dictF0 = repeated_runs(g1, delta, tolerance, 0.0, Zgraph, minrepeats)
            snapstats.Qstar[t] = max(dictQ0.values())

            # store some stats for optimization over lambda for a given snapshot this is 
            # kept for analysis purposes, not strictly required for solving the problem
            label_dict_lam = {} # key = lambduh, val = dictPartition where key = run number val = label_dict
            Qlam = {} # key = lambduh, val = dictQ where key = run number val = Q
            Elam = {} # key = lambduh, val = dictE where key = run number val = E
            Flam = {} # key = lambduh, val = dictF where key = run number val = F

            def g_of_lambda(lambduh):
                """ Used by scipy.opimize.fminbound to optimize for lambda """

                global itrepeats
                logging.info("itrepeats: %d", itrepeats)
                dictPartition, dictQ, dictE, dictF = repeated_runs(g1, delta, tolerance, lambduh, Zgraph, itrepeats)

                label_dict_lam[lambduh] = dictPartition
                Qlam[lambduh] = dictQ
                Elam[lambduh] = dictE
                Flam[lambduh] = dictF
                itrepeats += increpeats
                
                return max(dictF.values())
            
            global itrepeats
            itrepeats = minrepeats
                    
            lambdaopt, fval, ierr, numfunc = optimize.fminbound(
                g_of_lambda, 0.0, 10.0, args=(), xtol=convergence_tolerance,
                maxfun=maxfun, full_output=True, disp=0)  
            
            if ierr is 0:
                logging.info("[%d] best lambduh = %f, found in %d function calls", t, lambdaopt, numfunc)
            else:
                logging.error("[%d] No convergence for fminbound", t)
      
            # filter Fs at lambdaopt which are feasible
            dictFeasibleFs = dict([((lambdaopt, r), F) for (r, F) in Flam[lambdaopt].items() if
                Flam[lambdaopt][r] > Qlam[lambdaopt][r]])
            
            logging.info("[%d], lambdaopt=%f, feasibleFs=%s", t, lambdaopt,
                str(dictFeasibleFs))

            listLambduhs = sorted(Flam.keys())
            logging.info("listLambduhs: %s,", str(listLambduhs))
            current_index = listLambduhs.index(lambdaopt)

            while len(dictFeasibleFs) == 0 and current_index < len(listLambduhs) - 1:
                logging.error("No feasible Fs found at current_lambduh=%f, increasing search range of lambduhs",
                    listLambduhs[current_index])

                # get next highest lambda
                next_highest_lambduh = listLambduhs[current_index + 1]
                if(current_index + 1 > len(listLambduhs)):
                        raise nx.NetworkXError("Ran out of values for lambduh") 

                # add those to dictFeasibleFs 
                dictFeasibleFs.update(dict([((next_highest_lambduh, r), F) 
                    for (r, F) in Flam[next_highest_lambduh].items() 
                    if Flam[next_highest_lambduh][r] > Qlam[next_highest_lambduh][r]]))

                logging.info("[%d], next_highest_lambduh=%f, feasibleFs=%s", t,
                    next_highest_lambduh, str(dictFeasibleFs))

                current_index += 1

            if len(dictFeasibleFs) > 0:
                # get best r and best_feasible_lambda
                best_feasible_lambda, bestr = max(dictFeasibleFs, key=dictFeasibleFs.get) 
                snapstats.feasible[t] = 1
            else:
                logging.error("Nothing feasible found, constraint too harsh perhaps.\
                    Using highest lambda wihout worrying about feasibility.")
                best_feasible_lambda = listLambduhs[-1]
                bestr = max(Flam[best_feasible_lambda], key=Flam[best_feasible_lambda].get) 
                snapstats.feasible[t] = 0

            logging.info("best_feasible_lambda=%f, bestr = %d", best_feasible_lambda, bestr)
                  
            label_dict = label_dict_lam[best_feasible_lambda][bestr]
            
            snapstats.lambdaopt[t] = lambdaopt
            snapstats.best_feasible_lambda[t] = best_feasible_lambda
            snapstats.numfunc[t] = numfunc
            snapstats.ierr[t] = ierr
            snapstats.StrengthConsorts[t] = Zgraph.size(weight='weight')
            snapstats.NumConsorts[t] = Zgraph.size()
            snapstats.Estrangement[t] = Elam[best_feasible_lambda][bestr]
            snapstats.Q[t] =  Qlam[best_feasible_lambda][bestr]
            snapstats.F[t] =  Flam[best_feasible_lambda][bestr]
            snapstats.Qdetails[t] = Qlam
            snapstats.Edetails[t] = Elam
            snapstats.Fdetails[t] = Flam
            # end else of if beginning is True:

        # increment the labels by some huge offset each snapshot and let alignment do the work
        for n in label_dict:
            label_dict[n] += 1000000*snapshot_number

        matched_label_dict = utils.match_labels(label_dict, prev_matched_label_dict)
        matched_labels.update({t:matched_label_dict})

        snapstats.NumComm[t] = len(set((label_dict.values())))
                
        snapstats.NumNodes[t] = g1.number_of_nodes()
        snapstats.NumEdges[t] = g1.number_of_edges()
        snapstats.Size[t] = g1.size(weight='weight')
        snapstats.NumComponents[t] = nx.number_connected_components(g1)
        if g1.number_of_nodes() > 0:
            snapstats.LargestComponentsize[t] = len(list(nx.connected_components(g1))[0])
        else:
            snapstats.LargestComponentsize[t] = 0

        # keep track of prev snaphost graph and labelDict
        g0 = g1
        prev_label_dict = label_dict
        
        prev_matched_label_dict = matched_label_dict
        snapshot_number += 1

        # end for t, g1 in ......
        
    if write_stats is True: 
        for statname, statobj in vars(snapstats).items():
            with open('%s.log'%statname, 'w') as fout:
                pprint.pprint(statobj, stream=fout) 

    print("Done computing temporal communities for delta=%f" %delta)
    # result is a dictionary of the form: {time : {node : label}}
    with open(results_filename, 'w') as fw:
        fw.write(str(matched_labels))

    return matched_labels

class SnapshotStatistics():
  """ Helper class used to aggregate results. """
  def __init__(self):
      self.NumComm = {} # key = time t, val = Number of communities at time t
      self.Q = {}       # key = time t, val = Modularity of partition at t
      self.Qstar = {}   # key = time t, val = Modularity of partition at t with tau=0
      self.F = {}       # key = time t, val = F of partition at t
      self.StrengthConsorts = {}# key = time t, val = strength of consorts at time t
      self.NumConsorts = {}     # key = time t, val = Num of conorts at time t
      self.Estrangement = {}    # key = time t, val = number of estranged edges at time t
      self.lambdaopt = {}       # key = time t, lambdaopt found via solving the dual problem
      self.best_feasible_lambda = {} # key = time t, lambdaopt found via solving the dual problem
      self.numfunc = {}         # key = time t, Number of function evaluations needed for solving the dual
      self.ierr = {}            # key = time t, convergence of the dual
      self.feasible = {}        # key = time t, convergence of the dual
      self.NumNodes = {}        # key = time t, val = number of nodes in the graph
      self.NumEdges = {}        # key = time t, val = number of edges in the graph
      self.Size = {}            # key = time t, val = sum of the weight of the edges in the graph 
      self.NumComponents = {}   # key = time t, val = number of connected components in the graph 
      self.LargestComponentsize = {}  # key = time t, val = number of nodes in the largest component
      self.Qdetails = {} # {'time': {'lambduh': {'run_number': Q}}}
      self.Edetails = {} # {'time': {'lambduh': {'run_number': E}}}
      self.Fdetails = {} # {'time': {'lambduh': {'run_number': F}}}

