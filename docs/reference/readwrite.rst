*****************
Read/Write/Load
*****************

Functions to read, write and load dynamic graphs.

--------------------------
Simple example
--------------------------
::

    import tnetwork as tn
    sn = tn.read_snapshots("file_to_Read")
    tn.write_snapshots(sn,"file_to_write")

.. currentmodule:: tnetwork

--------------------------
Load example graphs
--------------------------
A few dynamic graphs are already included in the library and can be loaded in one command in the chosen format

.. autosummary::
    :toctree: iof/

    graph_socioPatterns2012
    graph_socioPatterns_Hospital
    graph_socioPatterns_Primary_School
    graph_GOT

--------------------------
Read/Write graphs
--------------------------

Read/Write Generic
---------------------------
.. autosummary::
    :toctree: iof/

    read_interactions
    from_pandas_interaction_list

Read/Write snapshot graphs
---------------------------

.. autosummary::
    :toctree: iof/

    read_interactions
    read_snapshots
    write_snapshots

Read/Write interval graphs
------------------------------


.. autosummary::
    :toctree: iof/

    read_interactions
    read_period_lists
    write_as_IG
    write_period_lists
    write_ordered_changes

Read/Write Link Streams
------------------------------


.. autosummary::
    :toctree: iof/

    read_interactions
    read_LS
    write_as_LS

--------------------------
Read/Write Communities
--------------------------

Read/Write snapshot snapshot_affiliations
------------------------------------------


.. autosummary::
    :toctree: iof/

    write_com_SN
    read_SN_by_com


Read/Write interval graph snapshot_affiliations
--------------------------------------------------


.. autosummary::
    :toctree: iof/

    write_IGC