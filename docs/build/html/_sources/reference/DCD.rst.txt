*************************************
Dynamic Community Detection
*************************************

Dynamic community detection is the problem of discovering snapshot_communities in dynamic networks.
A simple demo of usage can be found `here
<https://colab.research.google.com/github/Yquetzal/tnetwork/blob/master/demo_DCD.ipynb>`_.

There are two types of methods implemented: those that are written in pure python
and those who require an external tool.

Those in pure python are part of the `tnetwork.DCD` module while others are in `tnetwork.DCD.external`.

Below is a list of implemented methods, with the type of dynamic networks they are designed to manage.
Note that this type of network is unrelated with the tnetwork representation:
a snapshot representation can be used to encode a snapshot graph, a link stream or an interval graph.
The possible types of dynamic networks are:

* snapshot: The graph is well defined at any $t$, changes tend to occur synchronously
* interval gaph: The graph is well defined at any $t$, but graph changes are not synchrone, changes appear edge by edge
* link stream: graphs at any time $t$ are poorly defined, graphs can be studied only by studying a $\Delta$ period of aggregation

.. list-table:: Types of dynamic networks expected by each method
    :widths: 25 50
    :header-rows: 1

    * - Method
      - Type of dynamic network
    * - `iterative_match`
      - snapshots
    * - `match_survival_graph`
      - snapshots
    * - `smoothed_louvain`
      - snapshots
    * - `rollingCPM`
      - snapshots
    * - `MSSCD`
      - link stream
    * - `muchaOriginal`
      - snapshots
    * - `dynamo`
      - interval graph


Some external algorithms require matlab, and the matlab-python engine, ensuring the connection between both.
How to explain it is explained on the matlab website, currenty there: https://fr.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

.. currentmodule:: tnetwork.DCD

Internal algorithms
------------------------------------------
These algorithms are implemented in python.

.. autosummary::
    :toctree: generated/

        iterative_match
        match_survival_graph
        smoothed_louvain
        rollingCPM
        MSSCD


External algorithms
------------------------------------------
These algorithms call external code provided by authors, and thus might require installing
additional softwares (java, matlab).

.. currentmodule:: tnetwork.DCD.externals

.. autosummary::
    :toctree: generated/

        dynamo
        transversal_network_mucha_original
        transversal_network_leidenalg
        estrangement_confinement


