#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script demonstrating the use of the estrangement library to detect and
visualize temporal communities. 
"""

__author__ = """\n""".join(['Vikas Kawadia (vkawadia@bbn.com)',
                            'Sameet Sreenivasan <sreens@rpi.edu>',
                            'Stephen Dabideen <dabideen@bbn.com>'])

#   Copyright (C) 2012 by 
#   Vikas Kawadia <vkawadia@bbn.com>
#   Sameet Sreenivasan <sreens@rpi.edu>
#   Stephen Dabideen <dabideen@bbn.com>
#   All rights reserved. 


import sys
import os
from Estrangement import estrangement
from Estrangement import plots
from Estrangement import options_parser
import multiprocessing



def detect_and_plot_temporal_communities():
    """ Function to run simulations, based on a specified dataset, and created 
    tiled plots of the temporal communities. 
    
    Parameters can be specified at the command line, when calling this script.
    Alternatively, a config file specifed at the command line can be used to set
    the parameter. At the very minimum, a path to the data set must be specified.

    Each experiment requires a name, which is used to create a folder to store the
    results of the simulation. If the results already exist in the folder specified
    by the experiment name, plots are created using these existing results and the 
    simulation is not run on subsequent calls to EstrangementDemo.py. 
    To run the simulation again, delete the experiment folder before running this script,
    or use a different experiment name. 

    Examples
    --------
    >>> # To see all configuarable parameters use the -h option 
    >>> EstrangementDemo.py -h
    >>> # Configurable parameters can be specified at the command line
    >>> EstrangementDemo.py --dataset_dir ./data --display_on True --exp_name my_experiment
    >>> # A config file can be used, but it must be preceeded by an '@'
    >>> # Three config files are provided as examples, check that that path to the dataset is valid.
    >>> EstrangementDemo.py @senate.conf
    >>> EstrangementDemo.py @markovian.conf
    >>> EstrangementDemo.py @realitymining.conf 
    """

    # use argparse to parse command-line arguments using optionsadder.py
    opt = options_parser.parse_args()

    # A dir is created, specified by the --exp_name argument in 
    # the current working directory to place all output from the experiment
    if(not os.path.exists(opt.exp_name)):
        os.mkdir(opt.exp_name)
    expdir = os.path.abspath(opt.exp_name)

    # set the values of delta to find communities for
    deltas = opt.delta

    datadir = os.path.abspath(opt.dataset_dir)

    # we use the multiprocessing module to run computations for the different
    # deltas in parallel.
    process_dict = {}
    for d in deltas:
        output_dir = os.path.join(expdir, "task_delta_" + str(d))
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        results_filename = os.path.join(output_dir, "matched_labels.log")
        if not os.path.exists(results_filename):
            print("Detecting temporal communities for delta=%s"%d)
            kwargs={'dataset_dir' : datadir, 
                        'delta' : d,
                        'results_filename' : results_filename,
                        'minrepeats' : opt.minrepeats, 
                        'increpeats' : opt.increpeats,
                        'write_stats': True,
                        }
                    
            os.chdir(output_dir)    
            process_dict[d] = multiprocessing.Process(target = estrangement.ECA, kwargs = kwargs)
            process_dict[d].start()
        else:
            print("Seems like communities have already been computed for delta=%f; to recompute del dir %s" 
            %(d, output_dir))
        
    for k in process_dict.keys():
        process_dict[k].join()

    print("\nDone computing all temporal communities, now producing some visualizations")
    # dictionary to pass the output to the plot function
    matched_labels_dict = {}
    for d in deltas:
        results_filename = os.path.join(expdir, "task_delta_" + str(d), "matched_labels.log")
        with open(results_filename, 'r') as fr:
            result = eval(fr.read())
        matched_labels_dict[d] = result
    
    os.chdir(expdir)
    # plot the temporal communities 
    plots.plot_temporal_communities(matched_labels_dict)
    os.chdir('..')

    # to plot other parameters, set write_stats=True in estrangement.ECA() 
    # and use plots.plot_function(). For example,
    # estrangement.plots.plot_function(['Estrangement'])

if __name__ == "__main__":
    detect_and_plot_temporal_communities()
