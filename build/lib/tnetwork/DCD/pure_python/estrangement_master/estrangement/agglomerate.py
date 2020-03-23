#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module implements community detection using an agglomerative approach as
decribed in [Blondel08]_. It has been modified for estrangement confinement. Tje
original code is available here: http://perso.crans.org/aynaud/communities/
"""
# modified by vkawadia to do agglomerative lpam

__all__ = ["partition_at_level", "modularity", "best_partition", "generate_dendogram", "induced_graph"]

__author__ = """Thomas Aynaud (thomas.aynaud@lip6.fr)"""
#    Copyright (C) 2009 by
#    Thomas Aynaud <thomas.aynaud@lip6.fr>
#    All rights reserved.
#    BSD license.

__PASS_MAX = -1
__MIN = 0.0000001

from tnetwork.DCD.pure_python.estrangement_master.estrangement import lpa
from tnetwork.DCD.pure_python.estrangement_master.estrangement import utils as est_utils


import networkx as nx
#import types
#import lpa
import logging
#import utils
import multiprocessing

def partition_at_level(dendogram, level) :

    """Function which return the partition of the nodes at the given level.

    A dendogram is a tree and each level is a partition of the graph nodes.
    Level 0 is the first partition, which contains the smallest communities, 
    and the best partition is at height [len(dendogram) - 1].
    The higher the level in the dendogram, the bigger the communities in that level.
    This function merely processes an existing dendogram, which is created by 
    :mod:`estrangement.agglomerate.generate_dendogram`. 

    Parameters
    ----------
    dendogram : list of dict
       A list of partitions, i.e. dictionaries where keys at level (i+1) are the values at level i.
    level : int
       The level in the dendogram of the desired partitioning, which belongs to [0..len(dendogram)-1].

    Returns
    -------
    partition : dictionary
       A dictionary where keys are the nodes and the values are the set (community) to which it belongs.

    Raises
    ------
    KeyError
       If the dendogram is not well formed or the level is greater than the height of the dendogram.

    See Also
    --------
    best_partition
    generate_dendogram

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> dendo = generate_dendogram(G)
    >>> for level in range(len(dendo) - 1) :
    >>>     print "partition at level", level, "is", partition_at_level(dendo, level)
    """

    partition = dendogram[0].copy()
    for index in range(1, level + 1) :
        for node, community in partition.items() :
            partition[node] = dendogram[index][community]
    return partition
    

def modularity(partition, graph) :

    """Function to compute the modularity of a partitioning of a graph, as defined in [Newman04]_.

    Parameters
    ----------
    partition : dictionary {node:community label}
       The partition of the nodes, i.e a dictionary where keys are their nodes and values the communities.
    graph : networkx.Graph
       The graph showing the relationships between the nodes. 

    Returns
    -------
    modularity : float
       The modularity of the graph, given the partition, see: [Newman04]_

    Raises
    ------
    KeyError:
       If the partition is not a partition of all graph nodes.
    ValueError:
        If the graph has no link.
    TypeError:
        If graph is not a networkx.Graph.

    References
    ----------
    .. [Newman04] M.E.J. Newman and M. Girvan, "Finding and evaluating community structure in networks." Physical Review E 69:26113 (2004).

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> part = best_partition(G)
    >>> modularity(part, G)
    """

    if type(graph) != nx.Graph :
        raise TypeError("Bad graph type, use only non directed graph")

    inc = dict([])
    deg = dict([])
    links = graph.size(weight='weight')
    if links == 0 :
        raise ValueError("A graph without link has an undefined modularity")
    
    for node in graph :
        com = partition[node]
        deg[com] = deg.get(com, 0.) + graph.degree(node, weight = 'weight')
        for neighbor, datas in graph[node].items() :
            weight = datas.get("weight", 1)
            if partition[neighbor] == com :
                # inc is A_ij/2 
                if neighbor == node :
                    # loops are visited only once
                    inc[com] = inc.get(com, 0.) + float(weight)
                else :
                    # other edges are visited twice, so we divide by 2
                    inc[com] = inc.get(com, 0.) + float(weight) / 2.

    res = 0.
    for com in set(partition.values()) :
        res += (inc.get(com, 0.) / links) - (deg.get(com, 0.) / (2.*links))**2
    return res


def best_partition(graph, delta, tolerance, lambduh, Zgraph, partition = None,q=multiprocessing.Queue()) :

    """Function to compute the partition of the graph nodes which maximises the modularity
    (or tries to) using the Louvain heuristices.

    This is the partition of highest modularity, i.e. the highest partition of the dendogram
    generated by the Louvain algorithm, see: [Blondel08]_
    
    Parameters
    ----------
    graph : networkx.Graph
       The networkx graph of the network.
    tolerance: float
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller it is, the fewer dominant labels there 
        will be. 
    lambduh: float
        The Lagrange multiplier.
    Zgraph : networkx.Graph
         A graph containing edges between nodes of the same community in all previous snapshots.
    partition: dictionary {node : community label}
         The current labelling of the nodes in the graph.
    q : multiprocessing.Queue
         A queue used to store the results from multiple processes.

    Returns
    -------
    partition : dictionnary {node : community label}
       A dictionary which maps each node to a label (community) in the graph, which maximizes modularity.


    See Also
    --------
    generate_dendogram

    References
    ----------
    .. [Blondel08] Blondel, V.D. et al. Fast unfolding of communities in large networks. J. Stat. Mech 10008, 1-12(2008).

    Examples
    --------
    >>>  #Basic usage
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> part = best_partition(G)
    
    >>> #other example to display a graph with its community :
    >>> #better with karate_graph() as defined in networkx examples
    >>> #erdos renyi don't have true community structure
    >>> G = nx.erdos_renyi_graph(30, 0.05)
    >>> #first compute the best partition
    >>> partition = community.best_partition(G)
    >>>  #drawing
    >>> size = float(len(set(partition.values())))
    >>> pos = nx.spring_layout(G)
    >>> count = 0.
    >>> for com in set(partition.values()) :
    >>>     count = count + 1.
    >>>     list_nodes = [nodes for nodes in partition.keys()
    >>>                                 if partition[nodes] == com]
    >>>     nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
                                    node_color = str(count / size))
    >>> nx.draw_networkx_edges(G,pos, alpha=0.5)
    >>> plt.show()
    """

    dendo = generate_dendogram(graph, delta, tolerance, lambduh, Zgraph, partition)
    r_partition = partition_at_level(dendo, len(dendo) - 1 )
    q.put(r_partition)
    return partition_at_level(dendo, len(dendo) - 1 )


def generate_dendogram(graph, delta, tolerance, lambduh, Zgraph, part_init = None) :

    """Function to find communities in a graph and return the associated dendogram.

    A dendogram is a tree and each level is a partition of the graph nodes.  
    Level 0 is the first partition, which contains the smallest communities, 
    and the best is len(dendogram) - 1. The higher the level, the bigger 
    the size of the communities. At each step, nodes (which are the communities
    from the previous step) are merged into aggregate communities such that modularity
    is maximized, subject to the estrangement constraint. For more details on the 
    basic agglomerative procedure, see: [Blondel08]_.

    Parameters
    ----------
    graph : networkx.Graph
        The networkx graph representing the network.
    delta : float
        The temporal divergence. Smaller values imply greater emphasis on temporal
        contiguity whereas larger values place greater emphasis on finding better
        instanteous communities.
    tolerance: float
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller it is, the fewer dominant labels there 
        will be.     
    lambduh: float
        The Lagrange multiplier.
    Zgraph : networkx.Graph
        A graph containing edges between nodes of the same community in all previous snapshots
        The current labelling of the nodes in the graph
    part_init : dictiionary, optional {node:community}
        The algorithm will start using this partition of the nodes. 
        It is a dictionary where keys are their nodes and values the communities.



    Returns
    -------
    dendogram : list of dictionaries
        A list of partitions, ie dictionnaries where keys of the i+1 are the values of the i, 
        and where keys of the first are the nodes of graph.
    
    Raises
    ------
    TypeError:
        If the graph is not a networkx.Graph

    See Also
    --------
    best_partition

    Notes
    -----
    Uses Louvain algorithm: [Blondel08]_

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> dendo = generate_dendogram(G)
    >>> for level in range(len(dendo) - 1) :
    >>>     print "partition at level", level, "is", partition_at_level(dendo, level)
    """


    if type(graph) != nx.Graph :
        raise TypeError("Bad graph type, use only non directed graph")
    current_graph = graph.copy()
    current_Zgraph = Zgraph.copy()
    
    partition_list = []
    F = -99999999.0

    while True :
        partition = lpa.lpa(current_graph, tolerance, lambduh, Z=current_Zgraph)

        mod = modularity(partition, current_graph)
        E = est_utils.Estrangement(current_graph, partition, current_Zgraph)
        new_F = mod - lambduh*E + lambduh*delta
        logging.info("level=%d, Q=%f, E=%f, F=%f -----------", len(partition_list), mod, E, new_F)

        if new_F - F < __MIN :
            break
        partition_list.append(partition)
        F = new_F
        current_graph, current_Zgraph = induced_graph(partition, current_graph, current_Zgraph)
    return partition_list


def induced_graph(partition, graph, zgraph) :

    """Function to produce a graph where the nodes belonging to the same community are aggregated
    into a single node.

    In the induced graph, there is a link of weight w between communities if the sum of the weights of the 
    links between their elements is w. Communities are merged until there is no significant improvement on 
    the objective function.

    Parameters
    ----------
    partition : dictionary {node:community}
       A dictionary where keys are graph nodes and the values are the partition to which  the node belongs.
    graph : networkx.Graph
        The current snapshot of the graph
    Zgraph : networkx.Graph
        A graph containing edges between nodes of the same community in all previous snapshots
        The current labelling of the nodes in the graph
    

    Returns
    -------
    g : networkx.Graph
       A networkx graph where nodes are the communities of the input graph.

    Examples
    --------
    >>> n = 5
    >>> g = nx.complete_graph(2*n)
    >>> part = dict([])
    >>> for node in g.nodes() :
    >>>     part[node] = node % 2
    >>> ind = induced_graph(part, g)
    >>> goal = nx.Graph()
    >>> goal.add_weighted_edges_from([(0,1,n*n),(0,0,n*(n-1)/2), (1, 1, n*(n-1)/2)])
    >>> nx.is_isomorphic(int, goal)
    True
    """
    ret = nx.Graph()
    ret.add_nodes_from(partition.values())

    
    zret = nx.Graph()
    zret.add_nodes_from(partition.values())
    
    for node1, node2, datas in graph.edges(data = True) :
        weight = datas.get("weight", 1)
        com1 = partition[node1]
        com2 = partition[node2]
        w_prec = ret.get_edge_data(com1, com2, {"weight":0}).get("weight", 1)
        ret.add_edge(com1, com2, weight = w_prec + weight)
        
    # do the same induce operation on the zgraph    
    for node1, node2, datas in zgraph.edges(data = True) :
        weight = datas.get("weight", 1)
        com1 = partition[node1]
        com2 = partition[node2]
        w_prec = zret.get_edge_data(com1, com2, {"weight":0}).get("weight", 1)
        zret.add_edge(com1, com2, weight = w_prec + weight)
    
 
    logging.debug("ret nodes: %s", str(ret.nodes()))
    logging.debug("zret nodes: %s", str(zret.nodes()))

    return ret, zret
