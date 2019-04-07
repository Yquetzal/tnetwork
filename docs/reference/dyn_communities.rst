*************************************
Dynamic Communities Classes
*************************************

For each representation of dynamic graphs, there is a corresponding representation of dynamic snapshot_affiliations:

* DynGraphSN == DynCommunitiesSN (snapshot_affiliations)
* DynGraphIG == DynCommunitiesIG (interval graphs)

Dynamic snapshot_communities are (currently) identified by labels, i.e. each community is associated with a unique label,
and two nodes that have the same labels (in the same or in different time steps) belongs to the same (dynamic) community.

.. currentmodule:: tnetwork


Sequences of snapshots snapshot_communities
===============================================

.. autoclass:: DynCommunitiesSN


Adding and removing snapshot_affiliations
------------------------------------------
.. autosummary::
    :toctree: generated/

        DynCommunitiesSN.add_affiliation
        DynCommunitiesSN.add_community
        DynCommunitiesSN.set_communities

Accessing snapshot_affiliations
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynCommunitiesSN.affiliations
        DynCommunitiesSN.communities
        DynCommunitiesSN.snapshot_affiliations
        DynCommunitiesSN.snapshot_communities
        DynCommunitiesSN.affiliations_durations



Converting
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynCommunitiesSN.to_DynCommunitiesIG


-----------

Interval graph snapshot_communities
=====================================

.. autoclass:: DynCommunitiesIG



Adding and removing snapshot_affiliations
------------------------------------------
.. autosummary::
    :toctree: generated/

        DynCommunitiesIG.add_affiliation
        DynCommunitiesIG.add_affiliations_from
        DynCommunitiesIG.remove_affiliation

Accessing snapshot_affiliations
-----------------------------------
.. autosummary::
    :toctree: generated/

        DynCommunitiesIG.affiliations
        DynCommunitiesIG.communities
        DynCommunitiesIG.affiliations_durations

Other functions
--------------------------------------
.. autosummary::
    :toctree: generated/

        DynCommunitiesIG.nodes_main_com
        DynCommunitiesIG.nodes_natural_order
        DynCommunitiesIG.nodes_ordered_by_com