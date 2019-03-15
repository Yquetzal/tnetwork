*************************************
Dynamic Network Classes
*************************************

A simple demo of usage can be found `here
<https://colab.research.google.com/github/Yquetzal/tnetwork/blob/master/Network_Graph_classes.ipynb>`_.


Dynamic graphs can be represented as:

* Sequences of affiliations
* Interval Graphs
* Link streams (Not implemented yet)

Each representation has strengths and weaknesses. The representation to use depends on

#. Algorithms we wish to use and
#. properties of the network to represent.



.. currentmodule:: tnetwork


Sequences of snapshots
===========================

.. autoclass:: DynGraphSN

Examples

Adding and removing nodes and edges
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.add_node_presence
        DynGraphSN.add_nodes_presence_from
        DynGraphSN.add_interaction
        DynGraphSN.add_interactions_from
        DynGraphSN.remove_node_presence
        DynGraphSN.remove_interaction
        DynGraphSN.remove_interactions_from
        DynGraphSN.add_snapshot

Accessing the graph
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.node_presence
        DynGraphSN.graph_at_time
        DynGraphSN.snapshots_timesteps
        DynGraphSN.last_snapshot

Conversion to different formats
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.to_DynGraphSG
        DynGraphSN.to_tensor

Aggregation
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.cumulated_graph
        DynGraphSN.aggregate_sliding_window
        DynGraphSN.aggregate_time_period


Other graph operations
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.apply_nx_function


----------

Interval graphs
======================

.. autoclass:: DynGraphIG

Examples

Adding and removing nodes and edges
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphIG.add_node_presence
        DynGraphIG.add_nodes_presence_from
        DynGraphIG.add_interaction
        DynGraphIG.add_interactions_from


Accessing the graph
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphIG.node_presence
        DynGraphIG.graph_at_time
        DynGraphIG.interactions
        DynGraphIG.change_times


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
