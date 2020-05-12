#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 
This module implements the Label Propagation Algorithm (LPAm) as decribed in: [Barber09]_.
"""

import networkx as nx
import random
import collections
import logging

__all__ = ['lpa']
__author__ = """\n""".join(['Vikas Kawadia (vkawadia@bbn.com)',
                            'Sameet Sreenivasan <sreens@rpi.edu>',
                            'Stephen Dabideen <dabideen@bbn.com>'])


# Copyright (C) 2012 by 
# Raytheon BBN Technologies and Rensselaer Polytechnic Institute
# All rights reserved. 
# BSD license. 


def lpa(G, tolerance=0.00001, lambduh=3.0, initial_label_dict=None, Z=nx.Graph()):

    """Function to run the Label Propagation Algorithm and return the labelling upon convergence.

    The Label Propagation algorithm initially assigns each node a unique label and sequentially
    allows nodes to change their label so as to maximize a specified objective function, which 
    in this case is modularity.   
    
    Parameters
    ----------
    G : networkx.Graph
        The input graph.
    tolerance: float, optional
        For a label to be considered a dominant label, it must be within this much of the maximum
        value found for the quality function. The smaller the value of tolerance, the fewer dominant 
        labels there will be.
    Z: networkx.Graph, optional
        The Z  graph, see paper for details.
    lambduh: 
        The Lagrange multiplier.
    initial_label_dict : dictionary  {node_identifier:label}, optional
        Initial labeling of the nodes in G. If no labelling is specified, each node is assigned
        a unique label. 

    Returns
    -------
    label_dict : dictionary  {node_identifier:label}
        Modified labeling after running the LPA on G.

    Raises
    ------
    NetworkXError
        If the keys in the initial labelling does not match the nodes of the graph. 
        If the number of iterations is greater than 4 times the number of edges in the graph.

    See Also
    --------
    agglomerate.generate_dendogram

    References
    ----------                 
    .. [Barber09] M.J. Barber and J.W. Clark, "Detecting Network Communities by propagating labels under constraints." Physical Review E 80:026129
    .. [Raghavan07] U.N. Raghavan, R. Albert and S. Kumara, "Near linear time algorithm to detect community structure in large-scale networks." Physical Review E 76:036106

    Examples
    --------
    >>> labeling = lpa.lpa(current_graph, tolerance, lambduh, Z=current_Zgraph)
    >>> new_labeling = lpa.lpa(current_graph, tolerance, lambduh, labelling, Z=current_Zgraph)
    >>> list(lpa.lpa(current_graph, tolerance, lambduh, Z=current_Zgraph))
    [(0,1),(1,1),(2,2),(3,1)]
    """

    # If not specifed, each node's initial label is the node's identifier
    if initial_label_dict is None:    
        initial_label_dict = dict(zip(G.nodes(), G.nodes()))
    
    if sorted(initial_label_dict.keys()) != sorted(G.nodes()):
        raise nx.NetworkXError("Invalid initial_label_dict")
 
    two_m = float(2*G.size(weight='weight'))

    nodes = list(G.nodes())
    label_dict = initial_label_dict.copy()              # key = nodeId, value = label 
    degree_dict = G.degree(weight='weight')             # key = nodeId, value = degree of node
    label_volume_dict = collections.defaultdict(float)  # key = label, value = volume of that label (K_l)
    term3_dict = collections.defaultdict(float)         # key = label, value = ??
    for v in G.nodes():
        label_volume_dict[label_dict[v]] += G.degree(v, weight='weight')
        term3_dict[v] = degree_dict[v]**2/two_m         

    logging.debug("initial_labels: %s", str(label_dict)) 
    logging.debug("degree_dict: %s", str(degree_dict))

    running = True
    iteration = 0
    communities = set((label_dict.values()))


    # For multiple orderings of node visitations, calculate the value of
    # the objective function, equation (6) in reference [1]. 
    while running is True:
        running = False
        iteration += 1
        # shuffle the node visitation order
        random.shuffle(nodes)
        logging.debug("node visitation order %s", str(nodes))
        
        for v in nodes:
            if degree_dict[v] == 0:
                continue

            obj_fn_dict = collections.defaultdict(float) 
            # key = label, value = objective function to maximize

            for nbr,eattr in G[v].items():
                # self loops are not included in the N_vl term
                if nbr != v:
                    obj_fn_dict[label_dict[nbr]] += eattr["weight"]    
                else:    
                    obj_fn_dict[label_dict[nbr]] += 0.0
            
            if v in Z.nodes():
                for nbr,eattr in Z[v].items():
                    if nbr != v:
                        obj_fn_dict[label_dict[nbr]] += lambduh*float(eattr["weight"]) 
                                                
            for l in obj_fn_dict.keys():
                obj_fn_dict[l] -= degree_dict[v]*label_volume_dict[l]/two_m
                if l == label_dict[v]:
                    obj_fn_dict[l] += term3_dict[v]
                    
            logging.debug("node:%s, obj_fn_dict: %s", v, repr(obj_fn_dict))
            
            # get the highest weighted label
            maxwt = 0
            maxwt = max(obj_fn_dict.values())
            logging.debug("node:%s, maxwt: %f", str(v), maxwt)
        
            # record only those labels with weight sufficiently close the maxwt 
            dominant_labels = [ l for l in obj_fn_dict.keys()
                if abs(obj_fn_dict[l] - maxwt) < tolerance ]
            
            logging.debug("node:%s, dominant_labels: %s", str(v), str(dominant_labels))
            
            if len(dominant_labels) == 1:        
                the_dominant_label = dominant_labels[0]
            else:    
                # ties are broken randomly to pick THE dominant_label
                the_dominant_label = random.choice(dominant_labels)

            # change the node's label to the dominant label if it is not already
            if label_dict[v] != the_dominant_label :
                my_prev_label = label_dict[v]
                label_dict[v] = the_dominant_label
                # at least one vertex changed labels, so keep running
                running = True
                # update the weights of labels to refect the above change
                label_volume_dict[my_prev_label] -= degree_dict[v]
                label_volume_dict[the_dominant_label] += degree_dict[v]

                logging.debug("node:%s, label= %s", str(v), label_dict[v] )
            
            #clear the dict to be safe
            obj_fn_dict.clear()

        communities = set((label_dict.values()))

        logging.debug("the communities are : %s", str(communities))
        if iteration > 4*G.number_of_edges():
            raise nx.NetworkXError("Too many iterations: %d" % iteration)
    
    return label_dict

