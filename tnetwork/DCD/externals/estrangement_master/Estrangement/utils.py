#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module implements various functions used to compute and plot temporal communities.
"""

__all__ = ['graph_distance','node_graph_distance','Estrangement','match_labels','confidence_interval']

__author__ = """\n""".join(['Vikas Kawadia (vkawadia@bbn.com)',
                            'Sameet Sreenivasan <sreens@rpi.edu>',
                            'Stephen Dabideen <dabideen@bbn.com>'])


# Copyright (C) 2012 by 
# Raytheon BBN Technologies and Rensselaer Polytechnic Institute
# All rights reserved. 
# BSD license. 


import networkx as nx
import collections
import math
import operator
import numpy
import logging


def Estrangement(G, label_dict, Zgraph):

    """Return the Estrangement between G and Zgraph

    Given network snapshots and partitioning at times *t* and *(t-1)*, 
    an edge (u; v) in |Gt| is said to be estranged if, *u* and *v* are
    in the same partition in |G(t-1)| but not in |Gt|.
    Estrangement is defined as the fraction of estranged edges in G\ :sub:`t` \.

    .. |Gt| replace:: G\ :sub:`t`
    .. |G(t-1)| replace:: G\ :sub:`t-1`

    Parameters
    -----------
    G: networkx.Graph
        A networkx graph object representing the current snapshot.
    label_dict: dictionary {node:community}
        A dictionary mapping nodes to communities.
    Zgraph: networkx.Graph
        A graph containing only the edges between nodes of the same community in all previous snapshots.
  
    Returns
    -------
    estrangement: float
	The weighted fraction of estranged edges in *G*. 
 
    See Also
    --------
    lpa.lpa
    agglomerate.generate_dendogram()

    Examples
    --------
    >>> g0 = nx.Graph()
    >>> g0.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,3,{'weight':1})])
    >>> g1.add_edges_from([(1,2,{'weight':2})])
    >>> communities = {1:'a',2:'a',3:'b'}
    >>> print(Estrangement(g0,communities,g1)
    0.333333333333
    """

    consort_edge_set =  set(Zgraph.edges()) & set(G.edges())
    logging.info("Estrangement(): Z edges: %s", str(Zgraph.edges(data=True)))   
    logging.info("Estrangement(): G edges: %s", str(G.edges(data=True)))   
    logging.info("Estrangement(): consort_edge_set: %s", str(consort_edge_set))   
    if len(consort_edge_set) == 0:
        estrangement = 0
    else:   
        estrangement = sum([e[2]['weight'] for e in Zgraph.edges(data=True) if label_dict[e[0]] !=
        label_dict[e[1]]]) / float(G.size(weight='weight'))
    return estrangement


def match_labels(label_dict, prev_label_dict):

    """
    Map labels betweeb adjacent snapshots. See Fig2 in the paper for details.
    
    Parameters
    ----------
    label_dict: dictionary
        {node:community} at time t.
    prev_label_dict: dictionary
        {node:community} at time (t - 1).

    Returns
    -------
    matched_label_dict: dictionary {node:community} 
        The new community labelling.

    Examples
    --------
    >>> label_dict_a = {1:'a',2:'a',3:'a',4:'a',5:'a',6:'a'}
    >>> label_dict_b = {1:'b',2:'b',3:'b',4:'b',5:'b',6:'b'}
    >>> print(match_labels(label_dict_a,label_dict_b)
    {1:'a',2:'a',3:'a',4:'a',5:'a',6:'a'}
    """
    
    # corner case for the first snapshot
    if prev_label_dict == {}:
        return label_dict

    nodesets_per_label_t = collections.defaultdict(set) 
    nodesets_per_label_t_minus_1 = collections.defaultdict(set) 

    # count the number of nodes with each label in each snapshot and store in a dictionary
    # key = label, val = set of nodes with that label 
    for n,l in label_dict.items():
        nodesets_per_label_t[l].add(n)

    for n,l in prev_label_dict.items():
        nodesets_per_label_t_minus_1[l].add(n)

    overlap_dict = {} 
    overlap_graph = nx.Graph() 
    # Undirected bi-partite graph with the vertices being the labels and
    # the weight being the jaccard distance between them in t and (t-1) 
    # key = (prev_label, new_label), value = jaccard overlap

    for l_t, nodeset_t in nodesets_per_label_t.items():
        for l_t_minus_1, nodeset_t_minus_1 in nodesets_per_label_t_minus_1.items():
            jaccard =  len(nodeset_t_minus_1 & nodeset_t)/float(len((nodeset_t_minus_1 | nodeset_t))) 
            overlap_graph.add_edge(l_t_minus_1, l_t, weight=jaccard)

    max_overlap_digraph = nx.DiGraph() 
    # each label at t-1  and at t is a vertex in this bi-partite graph and 
    # a directed edge implies the max overlap with the other side. 

    for v in overlap_graph.nodes():    # find the nbr with max weight
        maxwt_nbr = max([(nbrs[0],nbrs[1]['weight']) for nbrs in overlap_graph[v].items()],
            key=operator.itemgetter(1))[0]
        max_overlap_digraph.add_edge(v, maxwt_nbr)

    matched_label_dict = {} # key = node, value = new label
    for l_t in nodesets_per_label_t.keys():
        match_l_t_minus_1 = list(max_overlap_digraph.successors(l_t))[0]
        # match if it is a bi-directional edge
        if list(max_overlap_digraph.successors(match_l_t_minus_1))[0] == l_t:
            best_matched_label = match_l_t_minus_1
        else:
            best_matched_label = l_t

        for n in nodesets_per_label_t[l_t]:
            matched_label_dict[n] = best_matched_label

    return matched_label_dict


