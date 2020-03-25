*************************************
Benchmark Generator
*************************************

Some methods are proposed to visualize dynamic networks and snapshot_communities.
A simple demo of usage can be found `here
<https://colab.research.google.com/github/Yquetzal/tnetwork/blob/master/demo_generation.ipynb>`_.




.. currentmodule:: tnetwork

.. autoclass:: ComScenario

.. autosummary::
    :toctree: generated/

        ComScenario.__init__

Function to define events
-----------------------------------
.. autosummary::
    :toctree: generated/

        ComScenario.INITIALIZE
        ComScenario.BIRTH
        ComScenario.DEATH
        ComScenario.MERGE
        ComScenario.SPLIT
        ComScenario.THESEUS
        ComScenario.RESURGENCE
        ComScenario.GROW_ITERATIVE
        ComScenario.SHRINK_ITERATIVE
        ComScenario.MIGRATE_ITERATIVE
        ComScenario.ASSIGN
        ComScenario.CONTINUE

Run
-----------------------------------
.. autosummary::
    :toctree: generated/

        ComScenario.run

Commnity class
-----------------------------------
.. currentmodule:: tnetwork.DCD.community

.. autoclass:: Community

.. autosummary::
    :toctree: generated/

        Community.name
        Community.nodes
        Community.nb_intern_edges