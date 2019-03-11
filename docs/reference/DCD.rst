*************************************
Dynamic Community Detection
*************************************

Dynamic community detection is the problem of discovering communities in dynamic networks.

Currently, the following methods are implemented

* Rolling CPM
* Iterative match
* Survival graph

All of them are based on snapshots graphs. Iterative match and Survival graph are generic methods, since they can
be parameterized by the community detection method to use at each step, and by the community similarity function to
match communities. They can even use a smoothed algorithm to discover communities at each step.

.. currentmodule:: tnetwork

.. autosummary::
    :toctree: generated/

        iterative_match
        match_survival_graph
        rollingCPM

