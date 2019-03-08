************
Input-Output
************

Functions to read and write dynamic graphs and snapshots

.. automodule:: tnetwork.readwrite

--------------------------
Manipulate snapshot graphs
--------------------------


.. autosummary::
    :toctree: iof/

    read_snapshots_dir
    write_snapshots_dir
    read_graph_link_stream

--------------------------
Manipulate stream graphs
--------------------------


.. autosummary::
    :toctree: iof/

    write_SG
    read_SG
    write_ordered_changes


-------------------------------
Manipulate snapshot snapshots
-------------------------------


.. autosummary::
    :toctree: iof/

    read_static_coms_by_node
    read_SN_by_com
    write_com_SN

-------------------------------------
Manipulate stream graph snapshots
-------------------------------------


.. autosummary::
    :toctree: iof/

    write_SGC
    read_com_ordered_changes
    write_ordered_changes