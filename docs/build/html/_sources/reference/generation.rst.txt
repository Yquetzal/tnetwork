*************************************
Benchmark Generator
*************************************
A simple demo of usage can be found `here
<https://colab.research.google.com/github/Yquetzal/tnetwork/blob/master/demo_generation.ipynb>`_.

The library implements several benchmark generators.
The aim of those benchmark is to generate both a temporal graph and a *reference*
dynamic community structure.

Currently, two benchmarks are implemented:
 * Benchmark with custom event scenario
 * Benchmark with stable, multiple temporal scale communities


Benchmark with custom communities
++++++++++++++++++++++++++++++++++++++

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

Community class
-----------------------------------
.. currentmodule:: tnetwork.DCD.community

.. autoclass:: Community

.. autosummary::
    :toctree: generated/

        Community.label
        Community.nodes
        Community.nb_intern_edges


Benchmark with stable, multiple temporal scales communities
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
.. currentmodule:: tnetwork.DCD.multi_temporal_scale

.. autosummary::
    :toctree: generated/

        generate_multi_temporal_scale