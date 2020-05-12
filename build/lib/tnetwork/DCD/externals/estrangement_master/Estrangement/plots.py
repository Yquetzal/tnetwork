#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 
This module implements functions used to produce evolution charts and other
plots based on the
output of estrangement confinement :mod:`estrangement.estrangement.ECA` ."""

__all__ = ['GetDeltas','plot_by_param','plot_function','ChoosingDelta','preprocess_temporal_communities','plot_temporal_communities','plot_with_lambdas']

__author__ = """\n""".join(['Vikas Kawadia (vkawadia@bbn.com)',
                            'Sameet Sreenivasan <sreens@rpi.edu>',
                            'Stephen Dabideen <dabideen@bbn.com>'])

# Copyright (C) 2012 by 
# Raytheon BBN Technologies and Rensselaer Polytechnic Institute
# All rights reserved. 
# BSD license. 


import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
import pylab
import os
import numpy
import collections
import random
import logging
from utils import match_labels

markers = [
  'o'   ,
  'v'   ,
  '^'   ,
  '<'   ,
  '>'   ,
  '1'   ,
  '2'   ,
  '3'   ,
  '4'   ,
  's'   ,
  'p'   ,
  '*'   ,
  'h'   ,
  'H'   ,
  '+'   ,
  'x'   ,
  'D'   ,
  'd'   ,
  '|'   ,
  '_'   ,
]




def GetDeltas():

    """ Function to scan for simulation folders in the current working directory and read 
    the values of delta used in ECA.

    The :mod:`estrangement.estrangement.ECA` function creates a folder specific to the value 
    of delta used in each simulation (e.g. task_delta_0.01). Within each of these folders, 
    a config file (simulation.conf) specifies the value of delta used in the simulation.
    This function reads the value of delta from each such config file and returns them in
    a list.  

    Alternatively, delta can be specified in the function calls, bypassing this
    function. See :mod:`EstrangementDemo` for more details. 

    Returns
    -------
    deltas : list
        A list of float, where each member denotes a value of delta used in :mod:`estrangement.estrangement.ECA`.

    Examples
    --------
    >>> deltas = GetDeltas()
    >>> print(deltas)
    """

    deltas = []
    dictOptions = {}
    for dirname in os.listdir(os.getcwd()):
        if not os.path.isdir(dirname):
            continue
        if not dirname.startswith("task"):
            continue
        infile = open(os.path.join(dirname, "options.log"), 'r')
        for l in infile:
                dictOptions = eval(l)
                delta = dictOptions['delta']
        deltas.append(delta)
    deltas.sort()
    return(deltas)


def plot_by_param(dictX, dictY, deltas=[], linewidth=2.0, markersize=15, label_fontsize=20, xfigsize=16.0, yfigsize=12.0, fontsize=28, fname=None, listLinestyles=None, xlabel="", ylabel="", title="", xscale='linear', yscale='linear', dictErr=None, display_on=False):

    """ Given dictionaries, dictX with key=label, val = iterable of X values, 
    and dictY with key=label, val = iterable of Y values, this function 
    plots lines for each the labels specified on the same axes.  

    Parameters
    ----------
    dictX : dictionary {label:[list of values]}
        The X values of a set of lines to be plotted and their respective label.
    dictY : dictionary {lable:[list of values]}
        The Y values of a set of lines to be plotted and their respective label.
    deltas : list of floats
        The values of delta used for ECA for which there are results.
    linewidth : float, optional
        The desired font size of the lines to be plotted.
    markersize : float, optional
        The size of the markers used on each line.
    label_fontsize : integer, optional
        The size of the font used for the labels.
    xfigsize : float, optional
        The desired length of the x-axis.
    yfigsize : float, optional
        The desired length of the y-axis.
    fontsize : integer, optional
        The size of the font to be used in the figure.
    fname : string, optional
        The file is saved with this name.
    listLinesstyles : list of strings, optional
        A list consisting of the line styles to be used in the figures.
    xlabel : string, optional
        The label to appear on the x-axis.
    ylabel : string, optional 
        The label to appear on the y-axis.
    title : string, optional
        The title of the figure.
    xscale : string, optional
        The type of scale to be used on the x-axis. 
    yscale : string, optional
        The type of scale to be used on the y-axis.      
    dictErr : Dictionary {label:[list of values]}
        Dictionary containing the Error Bars to be plotted on each line
    display_on : boolean
        If True, the graph is shown on the screen       

    Examples
    --------
    >>> dictX = {'Estrangement:delta_0.05': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'Estrangement:delta_0.025': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'Estrangement:delta_0.01': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'Estrangement:delta_1.0': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
    >>> dictY = {'Estrangement:delta_0.05': [0.0, 0.020202020202020204, 0.04040404040404041, 0.031578947368421054, 0.010309278350515464, 0.010101010101010102, 0.020202020202020204, 0.030612244897959183, 0.030303030303030304, 0.0103092783505154], 'Estrangement:delta_0.025': [0.0, 0.020202020202020204, 0.0, 0.021052631578947368, 0.0, 0.020202020202020204, 0.010101010101010102, 0.02040816326530612, 0.010101010101010102, 0.0], 'Estrangement:delta_0.01': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'Estrangement:delta_1.0': [0.061224489795918366, 0.020202020202020204, 0.04040404040404041, 0.05263157894736842, 0.0, 0.020202020202020204, 0.06060606060606061, 0.02040816326530612, 0.04040404040404041, 0.041237113402061855]}
    >>> plot_by_param(dictX, dictY,deltas=[],fname='estrangement.svg', listLinestyles=['bs--', 'ro-',], xlabel="Time", ylabel='Estrangement', title="Estrangement")
    """

    pyplot.clf()
    fig2 = pyplot.figure(figsize=(xfigsize,yfigsize))
    ax2 = fig2.add_subplot(111)
    ax2.set_title(title, fontsize=fontsize)
    ax2.set_xlabel(xlabel, fontsize=fontsize)
    ax2.set_ylabel(ylabel, fontsize=fontsize)

    ax2.set_xscale(xscale)
    ax2.set_yscale(yscale)

    xticklabels = pyplot.getp(pyplot.gca(), 'xticklabels')
    pyplot.setp(xticklabels, fontsize=label_fontsize)

    yticklabels = pyplot.getp(pyplot.gca(), 'yticklabels')
    pyplot.setp(yticklabels, fontsize=label_fontsize)
    pyplot.hold(True)
    
    line_dict = {} # key = label, val = pyplot line object

    i=0
    for label in sorted(dictX.keys()):
        arrayX = dictX[label]
        arrayY = dictY[label]

        if listLinestyles is not None:
            fmt = listLinestyles[i]
            i += 1
        else:
            fmt = random.choice(markers)

        if dictErr is not None:    # plot with errorbars
            arrayErr = dictErr[label]
            line_dict[label] = pyplot.errorbar(
                arrayX, arrayY, yerr=[arrayErr, numpy.zeros(len(arrayErr))],
                fmt=fmt,
                label="%s"%str(label), linewidth=linewidth,
                elinewidth=linewidth / 2.0,
                markersize=markersize)
        else:
            line_dict[label] = pyplot.plot(
                arrayX, arrayY, fmt,
                label="%s"%str(label), linewidth=linewidth, 
                markersize=markersize)

    pyplot.legend()

    if fname is not None:
        pyplot.savefig('%s'%fname)
    if display_on is True:
        pyplot.show()

    return ax2

def plot_function(listNames,image_extension="svg"):

    """ Plots a graph with the attributes specified in *listNames*.

    This function relies on the file output of :mod:`estrangement.estrangement.ECA`.
    The value of the parameter *write_stats* should be set to *True* when calling 
    :mod:`estrangement.estrangement.ECA`. 

    Parameters
    ----------
    listNames : list of strings
        Each string is an attribute to be plotted e.g. 'Estrangement','Q','F' etc.
    image_extension : string, optional
        The extension of the plot file to be saved.

    Returns
    ------- 
    Nothing : The image is displayed on the screen and/or written to file.

    Notes
    -----
    The function reads the relevant input data from file and formats it. 
    The actual plotting is done in :mod:`estrangement.plots.plot_by_param`.     

    Examples
    --------
    >>> deltas = [0.01,0.025,0.05,1.0]
    >>> for d in deltas:
    ...         estrangement.ECA(dataset_dir='../data',delta=d,increpeats=opt.increpeats,minrepeats=opt.minrepeats)
    >>> plot_function(['Q', 'F',])
    >>> plot_function(['Estrangement'])
    """
   
    task_list = []
    for dirname in os.listdir(os.getcwd()):
        if not os.path.isdir(dirname):
            continue
        if not dirname.startswith("task"):
            continue
        task_list.append(dirname)

    dictX = collections.defaultdict(list)
    dictY = collections.defaultdict(list)

    concat_datadict = {}
    avg_datadict = {}

    for task in task_list:
        for name in listNames:
            label = name + ':' + task[5:]

            concat_datadict[label] = collections.defaultdict(list)
            avg_datadict[label] = collections.defaultdict(float)

            with open(os.path.join(task,"%s.log"%name), 'r') as infile:
                data_dict = eval(infile.read())
            for t in data_dict.keys():
                concat_datadict[label][t] = data_dict[t]

            for k in sorted(concat_datadict[label].keys(),key=int):
                dictX[label].append(int(k))
                dictY[label].append(concat_datadict[label][k])

    plot_by_param(dictX, dictY, fname='%s.%s'%('-'.join(listNames), image_extension),
        listLinestyles=['bo-', 'ro-', 'go-', 'mo-', 'ko-', 'yo-', 'co-',
                  'bs-', 'rs-', 'gs-', 'ms-', 'ks-', 'ys-', 'cs-',
                  'b*-', 'r*-', 'g*-', 'm*-', 'k*-', 'y*-', 'c*-',],
        xlabel="Time", ylabel=name, title="%s evolution"% ', '.join(listNames))


def ChoosingDelta(image_extension="svg",deltas=[]):

    """ Function to plot avg(Q*-E) versus delta to get insights into the best delta for the given dataset.
   
    This module merely processes the data, the plotting is done by :mod:`estrangement.plots.plot_by_param`.
    It requires the results from :mod:`estrangement.estrangement.ECA` to be outputted to file.        
 
    Parameters
    ----------
    image_extension : string
        The extension of the plot file to be saved
    deltas : list of floats, optional
        The values of deltas used in the simulation. If delta is not
        specifed, :mod:`estrangement.plots.GetDeltas` is called to create the list. 

    Returns
    -------
    Nothing : The plot is displayed on the screen and/or written to file.

    Notes
    -----
    To produce the necessary stat files, set 'write_stats=True' when calling :mod:`estrangement.estrangement.ECA`.

    Examples
    --------
    >>> deltas = [0.01,0.025,0.05,1.0]
    >>> for d in deltas:
    ...         estrangement.ECA(dataset_dir='../data',delta=d,increpeats=opt.increpeats,minrepeats=opt.minrepeats)
    >>> ChooseingDelta()
    """

    dictX = collections.defaultdict(list)
    dictY = collections.defaultdict(list)

    Qavg_dict = {} # {delta: Qavg} 
    Eavg_dict = {} # {delta: Eavg} 

    # Get the values of delta used in the simulations if it is not specified
    if(len(deltas) == 0): 
        deltas = GetDeltas()

    for delta in deltas:
        with open("./task_delta_" + str(delta) + "/Q.log", 'r') as f:
            Q_dict = eval(f.read())  # {time: Q}

        # remove the lowest time entry since the initial parition is a given
        # this also keeps us consistent with Qstar and E below
        del(Q_dict[sorted(Q_dict.keys())[0]])

        with open("./task_delta_" + str(delta) +"/Qstar.log", 'r') as f:
            Qstar_dict = eval(f.read())  # {time: Qstar}

        with open("./task_delta_" + str(delta) +"/Estrangement.log", 'r') as f:
            E_dict = eval(f.read())  # {time: E}

        dictX["Average loss in Modularity"].append(delta)
        dictY["Average loss in Modularity"].append(numpy.mean(Qstar_dict.values()) - numpy.mean(Q_dict.values()))
        
        dictX["Average Estrangement"].append(delta)
        dictY["Average Estrangement"].append(numpy.mean(E_dict.values()))

    plot_by_param(dictX, dictY,deltas=[],fname='choosing_delta.%s' % image_extension,
        listLinestyles=['bs--', 'ro-',], xlabel="$\delta$", ylabel='', title="")



def preprocess_temporal_communities(matched_labels,deltas=[],nodes_of_interest=[],delta_to_use_for_node_ordering=1.0,label_sorting_keyfunc="random",nodeorder=None):

    """ Function to perform the necessary preprocessing before making 
    the tiled plots, of the temporal communities, for all simulation parameters. 

    Parameters
    ----------
    matched_labels : dictionary {delta:{time: {node:label}}}
        The labelling of each node for each snapshot.
    deltas : list of floats, optional
        The values of delta used in the simulation. 
    nodes of interest : list of integers, optional
        If nodes_of_interest is not an empty list then show egocentric view of the
        evolution, meaning plot only the nodes which ever share a label with a node
        in the nodes_of_interest. If this list is empty, all nodes are plotted. 
    delta_to_use_for_node_ordering : float, optional
        The value of delta used to order nodes for all temporal community plots.
    label_sorting_keyfunc : string, optional
        Method used to order the labels to be plotted.

    Returns
    -------
    node_index_dict : dictionary {nodename:index_value}
        A dictionary mapping nodenames to index values, which are to be plotted. 
    t_index_dict : dictionary {timestamp : index_value)
        A dictionary mapping timestamps/snapshot numbers to an index value, which are to be plotted.
    label_index_dict : dictionary {label : index_value}
        A dictionary mapping community labels to an index value, which are to be plotted.
    labels_of_interest_dict : dictionary {delta : labels}
        Dictionary mapping delta to the labels of 'nodes_of_interest' for that delta.

    Examples
    --------
    >>> deltas = [0.01,0.025,0.05,1.0]
    >>> for d in deltas:
    ...         estrangement.ECA(dataset_dir='../data',delta=d,increpeats=opt.increpeats,minrepeats=opt.minrepeats)
    >>> node_index_dict, t_index_dict, label_index_dict, labels_of_interest_dict = preprocess_temporal_communities(
        nodes_of_interest=nodes_of_interest)
    >>> print(node_index_dict)
    >>> print(t_index_dict)   
    """

    if(len(deltas) == 0):
        #deltas = GetDeltas()    
        deltas = sorted(matched_labels.keys())
    
    all_labels_set = set()
    appearing_nodes_set = set()
    all_times_set = set()
    
    labels_of_interest_dict = collections.defaultdict(set) 
    # key = delta, val = set of labels of interest for that delta
    label_time_series_dict = collections.defaultdict(list)
    # key = node, val = list of labels the node gets over time for delta = 1.0
    appearances_dict = collections.defaultdict(list)
    # key = node, val = list of times at which the node appears

    prev_temporal_label_dict = {} # store for alignment across deltas
    for delta in deltas:

        taskdir = "task_delta_" + str(delta)
        temporal_label_dict = {}  # key = (node, time) val, = label

 
        # populate 'temporal_label_dict' based on 'matched_labels' 
      
        for time in matched_labels[delta].keys():
                labelling = matched_labels[delta][time]

                all_times_set.add(time) 
                
                for n,l in labelling.items():
                    temporal_label_dict[(n,time)] = l

                if delta == delta_to_use_for_node_ordering :
                    for n,l in labelling.items():
                        label_time_series_dict[n].append(l)
                        appearances_dict[n].append(time) 
       
        #align temporal communities for various deltas for sensible visualization
        matched_temporal_label_dict = match_labels(temporal_label_dict, prev_temporal_label_dict)
        prev_temporal_label_dict = matched_temporal_label_dict 
        all_labels_set.update(matched_temporal_label_dict.values()) 

        # Write the temporal_labels and matched_temporal_labels to file
        with open(os.path.join(taskdir,"temporal_labels.log"), 'w') as f:
            f.write(repr(temporal_label_dict)) 
        with open(os.path.join(taskdir,"matched_temporal_labels.log"), 'w') as f:
            f.write(repr(matched_temporal_label_dict))

        # keep track of all the labels taken over time by nodes_of_interest 
        if nodes_of_interest:
            for (n,t), l in matched_temporal_label_dict.items():
                if n in nodes_of_interest:
                    labels_of_interest_dict[delta].add(l)
            for (n,t), l in matched_temporal_label_dict.items():
                if l in labels_of_interest_dict[delta]:
                    appearing_nodes_set.add(n)

    # safety check that there are simulation results for the delta value used in ordering        
    if(len(appearances_dict) == 0):
        raise ValueError("The 'delta_to_use_for_node_ordering' parameter must be one of the deltas used in simulation") 

    if nodeorder is not None:
        ordered_nodes = eval(nodeorder)
    else:    
        # node_index_dict,  key = nodename, val=index to use for plotting
        # use the temporal communities for delta=1.0 to get a node ordering for plotting  
        label_count_dict = {} # key = node, val = tuple of labels, ordered by freq
        for n , label_list in label_time_series_dict.items():
            label_freq = collections.defaultdict(int) # key = label, val = freq
            for l in label_list:
                label_freq[l] += 1
            label_count_dict[n] = sorted(label_freq.keys(), key=label_freq.get, reverse=True)

        first_appearances_dict = {} # key = node, val = first time that node appears
        for n in appearances_dict.keys():
            first_appearances_dict[n] = min(appearances_dict[n])

        def node_sorting_function(n):
            return (label_count_dict[n], first_appearances_dict[n])

        ordered_nodes = sorted(label_count_dict.keys(), key=node_sorting_function)

    if nodes_of_interest:
        filtered_ordered_nodes = [ n for n in ordered_nodes if n in appearing_nodes_set]
    else:
        filtered_ordered_nodes = ordered_nodes
    node_index_dict =  dict(zip(filtered_ordered_nodes, range(len(filtered_ordered_nodes))))

    if label_sorting_keyfunc == "identity":
        unique_labels_list = sorted(list(all_labels_set))
    elif label_sorting_keyfunc == "random":
        unique_labels_list = list(all_labels_set)
        random.shuffle(unique_labels_list)
    else:
        unique_labels_list = sorted(list(all_labels_set), key=eval(label_sorting_keyfunc))

    # label_index_dict,  key = label, val=index to use for plotting that label using pcolor
    label_index_dict = dict(zip(unique_labels_list, range(len(unique_labels_list))))
 
    # t_index_dict,  key = time/snapshot, val=index to use for plotting that # snapshot using pcolor
    t_index_dict = dict(zip(sorted(all_times_set), range(len(all_times_set))))
    return node_index_dict, t_index_dict, label_index_dict, labels_of_interest_dict


def plot_temporal_communities(matched_labels,nodes_of_interest=[],deltas=[],tiled_figsize='(36,16)',manual_colormap=None,label_cmap='Paired',frameon=True,xlabel="Time",ylabel="Node ID",label_fontsize=20,show_title=True,fontsize=28,colorbar=False,show_yticklabels=False,nodelabel_func=None,xtick_separation=5,snapshotlabel_func=None,wspace=0.2,bottom=0.1,image_extension="svg",dpi=200,display_on=True):
    """ Module to create tiled plots, illustrating the temporal communities, for different values of paramters.

    Parameters
    ----------
    matched_labels : dictionary {delta : {time : {node : label}}}
        Dictionary containing the labelling of each node, at each snapshot for each value of delta.
    nodes of interest : list of integers, optional
        If nodes_of_interest is not an empty list then show egocentric view of the
        evolution, meaning plot only the nodes which ever share a label with a node
        in the nodes_of_interest. If this list is empty, all nodes are plotted. 
    deltas : list of floats, optional
        The values of delta used for ECA for which there are results. This list
        can be derived from files created during simulation if it is not specified. 
    tiled_figsize : string, optional
        Dimensions of the figure to be plotted.
    manual_colormap : dictionary, optional 
        Maps labels to colors. If not specified, one is returned from 'matlibplot.cm.get_cmap'.
    label_cmap : string, optional
        The name of a colors.Colormap instance, used by 'matlibplot.cm.get_cmap'.
    frameon : boolean, optional
        If False, suppress drawing the figure frame in the subplots.
    xlabel : string, optional
        Label to appear on the x axis. This is set to 'Time' by default.
    ylabel : string, optional 
        Label to appear on the y axis. This is set to 'Node ID' by default.
    label_fontsize : integer, optional
        The size of the font used for the labels. This is set to 20 by default. 
    show_title : boolean, optional
        If False, the title of the figure is not displayed. 
    fontsize : integer, optional
        The font size of the title.
    colorbar : boolean, optional 
        Includes a color in the figure
    show_y_ticklabels : boolean, False
        If True, show tick labels on the y-axis
    nodelabel_func : String, optional
        The name of a function which maps node labels to indicies.    
    xtick_separation : integer, optional
        The distance between ticks on the x-axis
    snapshotlabel_func : string, optional
        The name of a function to determine the ticks on the x-axis.    
    wspace : float, optional
        The amount of width reserved for blank space between subplots   
    bottom : float, optional
        The bottom of the subplots for 'matlibplot.subplots_adjust'     
    image_extension : string, optional
        The extension of plot file to be saved. This is "svg" by default.  
    dpi : integer, optional
        The resolution of the plot. This is set to 200 dpi by default.
    display_on : boolean, optional
        If this is set to False, the plot is not displayed on the screen. 

    Returns
    -------
    Nothing, the plot is written to file and/or displayed on the screen depending on specified parameters.
   
    Examples
    --------
    >>> deltas = [0.01,0.025,0.05,1.0]
    >>> for d in deltas:
    ...         estrangement.ECA(dataset_dir='../data',delta=d,increpeats=opt.increpeats,minrepeats=opt.minrepeats)
    >>> plot_temporal_communities() 
    """

    if(len(deltas) == 0):
        #deltas = GetDeltas()    
        deltas = sorted(matched_labels.keys())

    node_index_dict, t_index_dict, label_index_dict, labels_of_interest_dict = preprocess_temporal_communities(
        matched_labels, nodes_of_interest=nodes_of_interest)

    t_index_to_label_dict = dict([(v,k) for (k,v) in t_index_dict.items()])

    # Make the tiled plots every set of parameters used in the simulations
    fig1 = pylab.figure(figsize=eval(tiled_figsize))
    numRows = 1
    numCols = len(deltas) 

    if os.path.exists("merged_label_dict.txt"):
        numCols += 1 # +1 for the merged network

    #http://matplotlib.sourceforge.net/api/colors_api.html#matplotlib.colors.ListedColormap
    if manual_colormap is not None:
        manual_colormap = eval(manual_colormap)
        if len(manual_colormap) != len(label_index_dict):
            logging.error("Error: Length of manual_colormap does not match that of label_index_dict")
            logging.error("manual_color_map = %s, len=%d", str(manual_colormap), len(manual_colormap))
            logging.error("label_index_dict = %s, len=%d", str(label_index_dict), len(label_index_dict))
            raise nx.NetworkXError("Error: Length of manual_colormap does not match that of label_index_dict")

        cmap = matplotlib.colors.ListedColormap([manual_colormap[l] for l in sorted(manual_colormap.keys())],
            name='custom_cmap', N=None)
    else:
        cmap=pylab.cm.get_cmap(label_cmap, len(label_index_dict))

    # Traverse the task directories and create a subplot for each value of delta
    plotNum = 0
    prev_ax = None
    for delta in deltas:
        taskdir = "./task_delta_" + str(delta)
        plotNum += 1
        if prev_ax is not None:
            ax1 = fig1.add_subplot(numRows, numCols, plotNum, sharex=prev_ax,
                sharey=prev_ax, frameon=frameon)
            ax1.get_yaxis().set_visible(False)
        else:    
            ax1 = fig1.add_subplot(numRows, numCols, plotNum, frameon=frameon)
            prev_ax = ax1

        ax1.set_xlabel(xlabel, fontsize=label_fontsize)
        if plotNum == 1:
            ax1.set_ylabel(ylabel, fontsize=label_fontsize)
        if show_title is True:
            ax1.set_title("$\delta$=%s"%delta , fontsize=fontsize)

        pylab.hold(True)

        x = numpy.array((sorted(t_index_dict.values())))
        y = numpy.array(sorted(node_index_dict.values()))
        Labels = numpy.empty((len(y), len(x)), int)
        Labels.fill(-1)

        with open(os.path.join(taskdir,"matched_temporal_labels.log"), 'r') as label_file:
            matched_temporal_label_dict = eval(label_file.read())
           
        for (n,t), l in matched_temporal_label_dict.items():
            if nodes_of_interest and l in labels_of_interest_dict[str(delta)]:
                Labels[node_index_dict[n], t_index_dict[t]] = label_index_dict[l]
            elif not nodes_of_interest: 
                Labels[node_index_dict[n], t_index_dict[t]] = label_index_dict[l]

        # mask the nodes not seen in some snapshots
        Labels_masked = numpy.ma.masked_equal(Labels, -1)

        im = pylab.imshow(Labels_masked, 
            cmap=cmap,
            vmin = 0,
            vmax = len(label_index_dict) - 1,
            interpolation='nearest',
            aspect='auto',
            origin='lower')

        if colorbar is True:
            levels = numpy.unique(Labels_masked)
            cb = pylab.colorbar(ticks=levels)
            reverse_label_index_dict = dict([(v,k) for (k,v) in label_index_dict.items()])
            level_labels = [ reverse_label_index_dict[l] for l in levels.compressed() ]
            cb.ax.set_yticklabels(level_labels)

        ylocs = sorted(node_index_dict.values(), key=int)
        ylabs = sorted(node_index_dict.keys(), key=node_index_dict.get)

        if show_yticklabels is False:
            ax1.set_yticklabels([])
        else:    
            if nodelabel_func is not None:
                nodelabel_dict = eval(nodelabel_func+'()')
                node_labels = [str(nodelabel_dict[c]) for c in ylabs]
                pylab.yticks(ylocs, node_labels, fontsize=10, rotation=15)
            else:
                pylab.yticks(ylocs, ylabs, fontsize=10)

        # show every 5th label on the x axis
        xlocs = [x for x in sorted(t_index_dict.values(), key=int) if x%xtick_separation == 0]
        logging.debug("xlocs:%s", str(xlocs))
        xlabs = [t_index_to_label_dict[x] for x in xlocs]
        logging.debug("xlabs:%s", str(xlabs))

        if snapshotlabel_func is not None:
            snapshotlabel_dict = eval(snapshotlabel_func+'()')
            snapshot_labels = [snapshotlabel_dict[t] for t in xlabs]
            pylab.xticks(xlocs, snapshot_labels, fontsize=11, rotation=75)
        else:
            pylab.xticks(xlocs, xlabs, fontsize=11)

        suffix=''
        if nodelabel_func is not None:
            nodelabel_dict = eval(nodelabel_func+'()')
            suffix='-'.join([str(nodelabel_dict[n]) for n in nodes_of_interest])
        else:    
            suffix='-'.join([str(n) for n in nodes_of_interest])
            
        xvals = t_index_dict.values()    
        ax1.set_xlim((min(xvals), max(xvals)))

    fig1.subplots_adjust(wspace=wspace, bottom=bottom)
    
    pylab.savefig('dynconsuper%s.%s'%(suffix,image_extension), dpi=dpi)
    # svg viewers are slow, also save pdf
    pylab.savefig('dynconsuper%s.%s'%(suffix,'pdf'), dpi=dpi)
    if display_on is True:
        pylab.show()



def confidence_interval(nums):

    """Return (half) the 95% confidence interval around the mean for the list of input numbers,
    i.e. calculate: 1.96 * std_deviation / sqrt(len(nums)).
    
    Parameters
    ----------
    nums: list of floats

    Returns
    -------
    half the range of the 95% confidence interval

    Examples
    --------
    >>> print(confidence_interval([2,2,2,2]))
    0
    >>> print(confidence_interval([2,2,4,4]))
    0.98
    """

    return 1.96 * numpy.std(nums) / math.sqrt(len(nums))




def plot_with_lambdas(linewidth=2.0,image_extension='svg'):

    """ Function to plot F with lambduhs for various snapshots. 

    Parameters
    ----------
    linewidth : float, optional
        The font size of the lines in the plot. This is set to 2.0 by default.
    image_extension : string, optional
        Specifies the extension of the plot file to be saved. The default image 
        type is '.svg'  
    
    Returns
    -------
    Nothing. The plot is written to file. 

    Examples
    --------
    >>> deltas = [0.01,0.025,0.05,1.0]
    >>> for d in deltas:
    ...         estrangement.ECA(dataset_dir='../data',delta=d,increpeats=opt.increpeats,minrepeats=opt.minrepeats)
    >>> plot_with_lambdas()
    """

    with open("Fdetails.log", 'r') as Fdetails_file:
        Fdetails_dict = eval(Fdetails_file.read())      # {time: {lambda: {run_number: F}}}
        
    with open("Qdetails.log", 'r') as Qdetails_file:    
        Qdetails_dict = eval(Qdetails_file.read())      # {time: {lambda: {run_number: Q}}}

    with open("Edetails.log", 'r') as Edetails_file:
        Edetails_dict = eval(Edetails_file.read())      # {time: {lambda: {run_number: E}}}

    with open("lambdaopt.log", 'r') as f:
      lambdaopt_dict = eval(f.read())                   # {time: lambdaopt}

    with open("best_feasible_lambda.log", 'r') as f:
      best_feasible_lambda_dict = eval(f.read())        # {time: best_feasible_lambda}

    with open("Q.log", 'r') as f:
      Q_dict = eval(f.read())  # {time: lambdaopt}

    with open("F.log", 'r') as f:
      F_dict = eval(f.read())  # {time: lambdaopt}

    for t in sorted(Fdetails_dict.keys()):
        Flam = Fdetails_dict[t]
        Qlam = Qdetails_dict[t]
        Elam = Edetails_dict[t]

        dictX = collections.defaultdict(list)
        dictY = collections.defaultdict(list)
        dictErr = collections.defaultdict(list)
        for l in sorted(Flam.keys()):
            dictX['Q'].append(l)
            dictY['Q'].append(max(Qlam[l].values()))
            dictErr['Q'].append( confidence_interval(Qlam[l].values()) )

            dictX['F'].append(l)
            dictY['F'].append(max(Flam[l].values()))
            dictErr['F'].append( confidence_interval(Flam[l].values()) )

        ax2 = postpro.plot_by_param(dictX, dictY, listLinestyles=['b-', 'g-', 'r-',],
            xlabel="$\lambda$", ylabel="Dual function", title="Dual function at t=%s"%(str(t)),
            dictErr=dictErr)

        ax2.axvline(x=lambdaopt_dict[t], color='m', linewidth=linewidth,
            linestyle='--', label="$\lambda_{opt}$")

        ax2.axvline(x=best_feasible_lambda_dict[t], color='k', linewidth=linewidth,
            linestyle='--', label="best feasible $\lambda$")

        ax2.axhline(F_dict[t], color='b', linewidth=linewidth,
            linestyle='--', label="best feasible F")

        ax2.axhline(Q_dict[t], color='g', linewidth=linewidth,
            linestyle='--', label="best feasible Q")

        pyplot.legend()

        pyplot.savefig('with_lambda_at_t%s.%s'%(str(t), image_extension))

