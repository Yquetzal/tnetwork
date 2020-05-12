*************************************
Evaluation of Dynamic Communities
*************************************

This section contains functions useful to evaluate the quality of dynamic communities.

They were introduced in ...

They can be split in 3 categories:
 * Evaluation of an average value at each step (`similarity_at_each_step`,similarity_at_each_step`)
 * Evaluation of smoothness (`nb_node_change`,`entropy_by_node`,`consecutive_sn_similarity`)
 * Longitudinal evaluation (`longitudinal_similarity`)

.. currentmodule:: tnetwork.DCD.analytics

Internal algorithms
------------------------------------------
These algorithms are implemented in python.`

.. autosummary::
    :toctree: generated/

         longitudinal_similarity
         similarity_at_each_step
         quality_at_each_step
         consecutive_sn_similarity
         nb_node_change
         entropy_by_node
