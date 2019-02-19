*************************************
Dynamic Network Classes
*************************************

Dynamic graphs can be represented as:
* Sequences of snapshots
* Stream Graphs
* Link streams (TO DO)

.. currentmodule:: tnetwork

.. autoclass:: DynGraphSN


Methods
=======

Adding and removing nodes and edges
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynGraphSN.__init__
        DynGraphSN.add_interaction
        DynGraphSN.add_interactions_from
        DynGraphSN.remove_interaction
        DynGraphSN.remove_interactions_from