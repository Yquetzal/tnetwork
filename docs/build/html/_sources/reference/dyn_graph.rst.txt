*************************************
Dynamic Network Classes
*************************************

A simple demo of usage can be found `here
<https://colab.research.google.com/github/Yquetzal/tnetwork/blob/master/Network_Graph_classes.ipynb>`_.

Introduction
==================
Dynamic graphs can be represented as:

* Sequences of snapshots
* Interval Graphs
* Link streams

Each representation has strengths and weaknesses. The representation to use depends on

#. Algorithms we wish to use
#. Information we need to access to efficiently
#. Properties of the network to represent.

In summary, the properties of each representation are the following:

Sequences of snapshots
--------------------------
Time is discrete. Interactions are ponctual.

Most appropriate if there are a few timesteps (<50?), or if you need to access efficiently the network at a given time.

Inefficient to access the list of all interactions of a particular node/edge.

Interval Graph
--------------------------

Time is continuous. Interactions have a duration.

Most appropriate when observed relations last a consequent time relatively to the whole period of study, i.e., if the original data is continuous or if
it is discrete but an edge observed at time t tends to be also present from t to t+n, with n large.

Efficient to access all the interactions of a node or a pair of nodes, but not to access all interactions at a particular time.

Link Streams:
--------------------------

Time is continuous. Interactions are ponctual.

Most appropriate when interactions are rare compared to the frequency of observation. For instance, an email dataset
in which each emails timestamp is at the level of the second.

Efficient to access all the interactions of a node or a pair of nodes, but not to access all interactions at a particular time.

Automatic model selection
--------------------------
As introduced in *Data compression to choose a proper dynamic network representation* (TBP), the library propose to choose automatically
the representation when provided with a file containing interactions as triplets <Time, Node1,Node2>. The method
is based on the most efficient data compression. Check the `Read/Write` section to know more.



Shared methods
===============
All representation share a set of common fonctions to access and modify them. Note that the implementation of
those methods vary.

Those methods are:



.. currentmodule:: tnetwork.dyn_graph.dyn_graph.DynGraph
.. autosummary::
    :toctree: generated/

        start
        end
        summary
        add_node_presence
        add_nodes_presence_from
        add_interaction
        add_interactions_from
        remove_node_presence
        remove_interaction
        remove_interactions_from
        edge_presence
        interactions
        change_times
        graph_at_time
        cumulated_graph
        slice
        aggregate_sliding_window
        frequency
        write_interactions

.. currentmodule:: tnetwork

Sequences of snapshots
===========================

.. autoclass:: DynGraphSN


Adding and removing nodes and edges
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.__init__
        DynGraphSN.add_node_presence
        DynGraphSN.add_nodes_presence_from
        DynGraphSN.add_interaction
        DynGraphSN.add_interactions_from
        DynGraphSN.remove_node_presence
        DynGraphSN.remove_interaction
        DynGraphSN.remove_interactions_from
        DynGraphSN.add_snapshot
        DynGraphSN.remove_snapshot
        DynGraphSN.discard_empty_snapshots

Accessing the graph
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.summary
        DynGraphSN.snapshots
        DynGraphSN.node_presence
        DynGraphSN.edge_presence
        DynGraphSN.graph_at_time
        DynGraphSN.snapshots_timesteps
        DynGraphSN.last_snapshot
        DynGraphSN.start
        DynGraphSN.end
        DynGraphSN.change_times
        DynGraphSN.frequency


Conversion to different formats
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.to_DynGraphIG
        DynGraphSN.to_DynGraphLS
        DynGraphSN.to_tensor

Aggregation
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.cumulated_graph
        DynGraphSN.slice
        DynGraphSN.aggregate_sliding_window
        DynGraphSN.aggregate_time_period


Other graph operations
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.apply_nx_function
        DynGraphSN.code_length
        DynGraphSN.write_interactions


----------

Interval graphs
======================

.. autoclass:: DynGraphIG

Examples

Adding and removing nodes and edges
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphIG.__init__
        DynGraphIG.add_node_presence
        DynGraphIG.add_nodes_presence_from
        DynGraphIG.add_interaction
        DynGraphIG.add_interactions_from
        DynGraphIG.remove_node_presence
        DynGraphIG.remove_interaction
        DynGraphIG.remove_interactions_from


Accessing the graph
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphIG.summary
        DynGraphIG.node_presence
        DynGraphIG.edge_presence
        DynGraphIG.graph_at_time
        DynGraphIG.interactions
        DynGraphIG.interactions_intervals
        DynGraphIG.change_times
        DynGraphIG.start
        DynGraphIG.end


Conversion to different formats
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphIG.to_DynGraphSN

Aggregation
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphIG.cumulated_graph
        DynGraphIG.slice
        DynGraphIG.code_length
        DynGraphIG.write_interactions

Link Streams
======================

.. autoclass:: DynGraphLS


Adding and removing nodes and edges
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphLS.__init__
        DynGraphLS.start
        DynGraphLS.end
        DynGraphLS.add_interaction
        DynGraphLS.add_interactions_from
        DynGraphLS.add_node_presence
        DynGraphLS.add_nodes_presence_from
        DynGraphLS.remove_node_presence
        DynGraphLS.remove_interaction
        DynGraphLS.remove_interactions_from




Accessing the graph
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphLS.summary
        DynGraphLS.interactions
        DynGraphLS.node_presence
        DynGraphLS.edge_presence
        DynGraphLS.graph_at_time
        DynGraphLS.change_times




Conversion to different formats
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphLS.to_DynGraphSN

Aggregation
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphLS.cumulated_graph
        DynGraphLS.slice
        DynGraphLS.aggregate_sliding_window

Other
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphLS.code_length
        DynGraphLS.write_interactions