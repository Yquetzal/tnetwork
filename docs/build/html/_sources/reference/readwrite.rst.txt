************
Read/Write
************

Functions to read and write dynamic graphs and affiliations.

--------------------------
Simple example
--------------------------
::

    import tnetwork as tn
    sn = tn.read_snapshots("file_to_Read")
    tn.write_snapshots(sn,"file_to_write")

.. automodule:: tnetwork.readwrite

--------------------------
Read/Write graphs
--------------------------


Read/Write snapshot graphs
---------------------------

.. autosummary::
    :toctree: iof/

    write_snapshots
    read_snapshots
    read_graph_link_stream

Read/Write interval graphs
------------------------------


.. autosummary::
    :toctree: iof/

    write_IG
    write_ordered_changes
    read_IG


--------------------------
Read/Write Communities
--------------------------

Read/Write snapshot affiliations
-----------------------------------


.. autosummary::
    :toctree: iof/

    write_com_SN
    read_SN_by_com


Read/Write interval graph affiliations
-----------------------------------------


.. autosummary::
    :toctree: iof/

    write_IGC