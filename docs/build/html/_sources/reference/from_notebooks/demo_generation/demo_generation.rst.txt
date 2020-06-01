Generation of dynamic networks with communities
===============================================

Table of Contents
-----------------

1. `Introduction: simple generation <#Introduction>`__

-  `Initialization <#Introduction>`__
-  `Merge <#Introduction>`__
-  `Run <#Introduction>`__
-  `Conservation of identity of communities <#Introduction>`__

2. `Events chaining <#chaining>`__

-  `Natural Chaining <#chaining>`__
-  `Fix Delay <#chaining>`__
-  `Triggers <#chaining>`__

3. `Events <#Events>`__

-  `MERGE/SPLIT <#Events>`__
-  `BIRTH/DEATH <#Events>`__
-  `Iterative GROW/SHRINK <#Events>`__
-  `Iterative Node MIGRATION <#Events>`__
-  `RESURGENCE <#Events>`__
-  `Ship of Theseus <#Events>`__
-  `CONTINUE <#Events>`__
-  `Custom Event: ASSIGN <#Events>`__

4. `Generating random scenarios <#Random>`__
5. `Mixing parameters <#Mixing>`__

.. code:: ipython3

    #%%capture #avoid printing output
    #!pip install --upgrade git+https://github.com/Yquetzal/tnetwork.git

.. code:: ipython3

    %load_ext autoreload
    %autoreload 2
    
    import tnetwork as tn
    import numpy as np

Introduction: simple generation
-------------------------------

The generation process works in 2 phases: 1. Define the scenario that
you want 2. Run the generation

Everything is done on a community scenario ``ComScenario`` instance

.. code:: ipython3

    #First, we create an instance of community scenario
    my_scenario = tn.ComScenario()

Initialization
~~~~~~~~~~~~~~

We can define the original community structure. We set the size of
communities and, optionnaly, their names. The function returns objects
that represent those communities

.. code:: ipython3

    [com1,com2] = my_scenario.INITIALIZE([4,6],["com1","com2"])

As soon as we have declared those communities, we can check their number
of nodes ``n`` and number of internal edges ``m``. The number of edges
is automatically determined by a density function that depends on the
size of the community and a global parameter that can be specified when
creating the scenario, more on that in the *mixing parameters* section

.. code:: ipython3

    print(com1)
    print(com2)


.. parsed-literal::

    (com1:n=4,m=5)
    (com2:n=6,m=11)


Merge
~~~~~

Let’s define a first operation on these communities. It will be a merge
operation, using the function ``MERGE``

.. code:: ipython3

    #We merge com1 and com2. 
    absorbing = my_scenario.MERGE([com1,com2],"merged")

Run
~~~

To better understand what is going on, let’s run the generation, by
calling the function ``run``. This has two consequences: 1. It generates
a network corresponding to the described community structure 2. It fixes
the details of the number of steps required to do an operation. This is
not known in advance, since it depends on a stochastic process

.. code:: ipython3

    (generated_network,generated_comunities) = my_scenario.run()


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00

We can now plot the community structre and the state of the graphs at
some times. We can observe that: since the merge is progressive, nodes
belong to no community while the operation is in progress (grey color).
We can also observe the topology of the graph evolving from two
communities to one.

.. code:: ipython3

    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    /usr/local/lib/python3.7/site-packages/numpy/core/numeric.py:2327: FutureWarning: elementwise comparison failed; returning scalar instead, but in the future will perform elementwise comparison
      return bool(asarray(a1 == a2).all())



.. image:: output_15_1.png


.. code:: ipython3

    last_time = generated_network.end()
    times_to_plot = [0,int(last_time/3),int(last_time/3*2),last_time-1]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=200,height=200)



.. image:: output_16_0.png


Conservation of identity of communities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that the label/name we give to communities is important, it
corresponds to their *identity*, i.e., two communities with the same
label have the same identity (=same community).

If we reuse the same scenario, only changing the label of the merged
community from “merged” to “com1”, we observe in the visualization that
the community after the merge has now the same color (i.e., is “the same
community”) as one of the original ones.

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([4,6],["com1","com2"])
    absorbing = my_scenario.MERGE([com1,com2],"com1")
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_18_1.png


Events chaining
~~~~~~~~~~~~~~~

Several options are available to control the chaining of operations.

Natural chaining
^^^^^^^^^^^^^^^^

First, each operation takes some communities as input. In order for the
event to start, the communities required in input must be ready.

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2,com3] = my_scenario.INITIALIZE([4,6,4],["c1","c2","c3"])
    absorbing = my_scenario.MERGE([com1,com2],"c1")
    absorbing = my_scenario.MERGE([absorbing,com3],"c1")
    
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (2 of 2) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_20_1.png


Fix delay
^^^^^^^^^

It is possible to explicitely require to wait for a given period before
starting the event using the ``delay`` argument of any event

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2,com3] = my_scenario.INITIALIZE([4,6,4],["c1","c2","c3"])
    absorbing = my_scenario.MERGE([com1,com2],"c1",delay=5)
    absorbing = my_scenario.MERGE([absorbing,com3],"c1",delay=15)
    
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (2 of 2) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_22_1.png


Triggers
^^^^^^^^

One can also use triggers to define that an event can start only when
another (unrelated) operations finished. This can be done using the
keywork ``triggers``.

In the following example, the second merge, completely unrelated to the
first one, is triggered by its end

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2,com3,com4] = my_scenario.INITIALIZE([4,6,4,6],["c1","c2","c3","c4"])
    absorbing1 = my_scenario.MERGE([com1,com2],"c1")
    absorbing2 = my_scenario.MERGE([com3,com4],"c3",triggers=[absorbing1])
    
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (2 of 2) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_24_1.png


Events
~~~~~~

Let’s now go through the different existing events

MERGE/SPLIT
^^^^^^^^^^^

We have alredy seen the ``MERGE`` event, there is a symmetric ``SPLIT``
event.

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([4,6],["c1","c2"])
    merged = my_scenario.MERGE([com1,com2],"c1")
    my_scenario.SPLIT(merged,["split1","split2","split3"],[3,3,4],delay=5)
    
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (2 of 2) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_26_1.png


.. code:: ipython3

    last_time = generated_network.end()
    times_to_plot = [0,int(last_time/3),int(last_time/3*2),last_time-1]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=200,height=200)



.. image:: output_27_0.png


BIRTH/DEATH
^^^^^^^^^^^

Communities can appear and disappear. Note that communities appear
progressively, edge by edge.

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([6,6],["c1","c2"])
    my_scenario.BIRTH(6,"born",delay=20)
    my_scenario.DEATH(com1)
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (2 of 2) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_29_1.png


Iterative GROW/SHRINK
^^^^^^^^^^^^^^^^^^^^^

It is possible to make a community grow (creating new nodes) or shring
(nodes disappear), one node after the other, node by node. It can be
used to add/remove a single node too, of course.

A parameter allow to tune the time between each addition/removal

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([6,10],["c1","c2"])
    my_scenario.GROW_ITERATIVE(com1,nb_nodes2Add=4,wait_step=5,delay=20)
    my_scenario.SHRINK_ITERATIVE(com2,nb_nodes2remove=4,wait_step=1)
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (8 of 8) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_31_1.png


Iterative node MIGRATION
^^^^^^^^^^^^^^^^^^^^^^^^

Most of the time, in the real world, when a community change size, it is
not by integrating nodes newly created, but by taking nodes from
existing communities. This is one this event corresponds to: nodes are
moving from one community to another one, one after the other

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([10,4],["c1","c2"])
    my_scenario.MIGRATE_ITERATIVE(com1,com2,6,wait_step=1,delay=20)
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (6 of 6) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_33_1.png


RESURGENCE
^^^^^^^^^^

Resurgence is a type of event in which a community disappear for some
time, and reappear later, identical to its state before the
disappearance. Think of seasonal events for instance, with groups of
people/animals/keywords observed together at regular periods.

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([10,4],["c1","c2"])
    com2 = my_scenario.RESURGENCE(com2,death_period=20,delay=20)
    com2 = my_scenario.RESURGENCE(com2,death_period=3,delay=20)
    my_scenario.RESURGENCE(com2,death_period=15,delay=20)
    
    
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (6 of 6) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_35_1.png


Ship of theseus
^^^^^^^^^^^^^^^

The ship of theseus is a typical example of the problem of community
identity attribution: starting with a community A, all the nodes are
replaced by new ones, one after the other, until none of the original
remains. A new community B then appears with exactly the same nodes as
the ones originally composing A. Which one is the *correct* A, the
community currently labeled A but having no node in common with the
original state of A, or the one labelled B ?

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([6,6],["c1","c2"])
    my_scenario.THESEUS(com2,delay=20)
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (7 of 7) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_37_1.png


CONTINUE
^^^^^^^^

The CONTINUE event allows to define a period without change for a
community. It is mostly useful to add some period without any change at
the end of the scenario.

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([10,4],["c1","c2"])
    com2 = my_scenario.RESURGENCE(com2,death_period=20,delay=20)
    my_scenario.CONTINUE(com2,delay=20)
    
    
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot= tn.plot_longitudinal(generated_network,generated_comunities,height=300)


.. parsed-literal::

    100% (3 of 3) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_39_1.png


Custom event: ASSIGN
^^^^^^^^^^^^^^^^^^^^

Most typical scenarios can be described by combining events described
above. However, real community evolution might be even more complex than
that. For instance, a community of 10 nodes might split in 2 communities
of size 4, while 2 of its nodes merge with two nodes leaving another
community to create a new community !

We can define any such scenario using the ASSIGN event. Note that in
this case, we have to take care of a lower level and describe the event
*node by node*

.. code:: ipython3

    my_scenario = tn.ComScenario()
    [com1,com2] = my_scenario.INITIALIZE([10,6],["c1","c2"])
    nodesC1 = list(com1.nodes())
    nodesC2 = list(com2.nodes())
    new_split = [nodesC1[:4],nodesC1[4:8],nodesC1[8:10]+nodesC2[:2],nodesC2[2:]]
    my_scenario.ASSIGN(comsBefore=[com1,com2],comsAfter=["C1_split1","C1_split2","new_com","c2"],splittingOut=new_split,delay=10)
    
    
    
    #visualization
    (generated_network,generated_comunities) = my_scenario.run()
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=300,nodes=nodesC1+nodesC2)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_41_1.png


Let’s check that the generated network structure do match the described
community structure:

.. code:: ipython3

    
    last_time = generated_network.end()
    times_to_plot = [0,int(last_time/3),int(last_time/3*2),last_time-1]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=200,height=200)



.. image:: output_43_0.png


Generating random scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In what we have seen until now, the scenario was generated manually, by
describing precisely the chaining of events.

In typical benchmarks, we want more flexibility, and generate several
scenarios with random variations. This can easily been done by writing
some code, as examplified below. Of course, all choices made have
consequences, but the goal of this benchmark is to provide the atomic
tools to provide good high level generators…

.. code:: ipython3

    def generate_graph(nb_com =6,min_size=4,max_size=15,operations=10,mu=0.1):
        print("generating graph with nb_com = ",nb_com)
        prog_scenario = tn.ComScenario(verbose=False,external_density_penalty=mu)
        all_communities = set(prog_scenario.INITIALIZE(np.random.randint(min_size,max_size,size=nb_com)))
    
        for i in range(operations):
            [com1] = np.random.choice(list(all_communities),1,replace=False)
            all_communities.remove(com1)
    
            if len(com1.nodes())<max_size and len(all_communities)>0: #merge
                [com2] = np.random.choice(list(all_communities),1,replace=False)
                largest_com = max([com1,com2],key=lambda x: len(x.nodes()))
                merged = prog_scenario.MERGE([com1,com2],largest_com.label(),delay=20)
                all_communities.remove(com2)
                all_communities.add(merged)
            else: #split
                smallest_size = int(len(com1.nodes())/3)
                (com2,com3) = prog_scenario.SPLIT(com1,[prog_scenario._get_new_ID("CUSTOM"),com1.label()],[smallest_size,len(com1.nodes())-smallest_size],delay=20)
                all_communities|= set([com2,com3])
        (dyn_graph,dyn_com) = prog_scenario.run()
    
    
        return(dyn_graph,dyn_com)

.. code:: ipython3

    (generated_network,generated_comunities) = generate_graph(nb_com=6,max_size=10,operations=10)


.. parsed-literal::

     70% (7 of 10) |#################        | Elapsed Time: 0:00:00 ETA:   0:00:00

.. parsed-literal::

    generating graph with nb_com =  6


.. parsed-literal::

    100% (10 of 10) |########################| Elapsed Time: 0:00:00 ETA:  00:00:00

.. code:: ipython3

    #visualization
    plot = tn.plot_longitudinal(generated_network,generated_comunities,height=600)



.. image:: output_47_0.png


 ### Mixing parameters Some parameters allow to tune how well defined is
the community structure in term of network topology \* ``alpha``
determines the internal density of communities. The average degree
inside a community is approximately$ (n_{c}-1)^:raw-latex:`\alpha `$
with :math:`n_c` the number of nodes of community :math:`c`. More
precisely, the number of edges inside a community is equal to
:math:`d_c=\lceil \frac{n_c(n_c-1)^\alpha}{2} \rceil`. \*
``external_density_penalty`` corresponds to a penalty applied to the
formula above for the density of the whole graph. The density among all
nodes not in a community is defined as
``external_density_penalty``\ *:math:`d_G`. Beware, with small graphs,
larger values often yield poor community structures. Note that edges
added using this function are*\ stable\ *, i.e., if the community
structure do not change, those nodes to not change either, contrary to
the next option* ``random_noise`` corresponds to a different way to add
randomness: this time, for each generated snapshot, a fraction of edges
taken at random are rewired. It therefore adds randomness both inside an
between communities. Unlike the previous one, choosing this parameter
will lead to less edges inside communities than what has been set
according to ``alpha``.

We can illustrate this difference by generating a scenario without any
community change and plotting the graph at some points.

First, all internal edges exist, no external edges exist

.. code:: ipython3

    my_scenario = tn.ComScenario(alpha=1,external_density_penalty=0,random_noise=0)
    [com1,com2,com3] = my_scenario.INITIALIZE([5,9,12],["c1","c2","c3"])
    my_scenario.CONTINUE(com1,delay=4)
    (generated_network,generated_comunities) = my_scenario.run()
    
    times_to_plot = [0,1,2]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=300,height=300,k=2.5,iterations=100)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_49_1.png


By decreasing ``alpha``, communities become less dense.

.. code:: ipython3

    my_scenario = tn.ComScenario(alpha=0.8,external_density_penalty=0,random_noise=0)
    [com1,com2,com3] = my_scenario.INITIALIZE([5,9,12],["c1","c2","c3"])
    my_scenario.CONTINUE(com1,delay=4)
    (generated_network,generated_comunities) = my_scenario.run()
    
    times_to_plot = [0,1,2]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=300,height=300,k=2.5,iterations=100)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_51_1.png


By increasing external_density, some edges appear between communities.
Note that, since the community structure do not evolves, the edges
between communities do not change (see the article describing the
benchmark for more details)

.. code:: ipython3

    my_scenario = tn.ComScenario(alpha=0.8,external_density_penalty=0.1,random_noise=0)
    [com1,com2,com3] = my_scenario.INITIALIZE([5,9,12],["c1","c2","c3"])
    my_scenario.CONTINUE(com1,delay=4)
    (generated_network,generated_comunities) = my_scenario.run()
    
    times_to_plot = [0,1,2]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=300,height=300,k=2.5,iterations=100)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_53_1.png


Instead, if we increase the ``random_noise``, edges modifications are
present but they differ from one snaphsots to the next, despite the
community structure being unchanged

.. code:: ipython3

    my_scenario = tn.ComScenario(alpha=1,external_density_penalty=0,random_noise=0.1)
    [com1,com2,com3] = my_scenario.INITIALIZE([5,9,12],["c1","c2","c3"])
    my_scenario.CONTINUE(com1,delay=4)
    (generated_network,generated_comunities) = my_scenario.run()
    
    times_to_plot = [0,1,2]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=300,height=300,k=2.5,iterations=100)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_55_1.png


We can set all three parameters, but be careful when interpreting the
results ! The community structure might quickly degrade

.. code:: ipython3

    my_scenario = tn.ComScenario(alpha=0.8,external_density_penalty=0.2,random_noise=0.2)
    [com1,com2,com3] = my_scenario.INITIALIZE([5,9,12],["c1","c2","c3"])
    my_scenario.CONTINUE(com1,delay=4)
    (generated_network,generated_comunities) = my_scenario.run()
    
    times_to_plot = [0,1,2]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,auto_show=True,width=300,height=300,k=2.5,iterations=100)


.. parsed-literal::

    100% (1 of 1) |##########################| Elapsed Time: 0:00:00 ETA:  00:00:00


.. image:: output_57_1.png


Benchmark for Multiple Temporal Scales
--------------------------------------

This benchmark allows to generate temporal networks as described in
``Detecting Stable Communities in Link Streams at Multiple Temporal Scales. Boudebza, S., Cazabet, R., Nouali, O., & Azouaou, F. (2019).``.

To sum up the method, *stable* communities are generated (i.e., no node
change). These communities exist for some periods, but have different
*temporal scales*, i.e., some of them have a high frequency of edges
(their edges appear at every step) while others have a lower frequency
(i.e., each edge appear only every :math:`t` steps). To simplify,
communities are complete cliques.(but for the low frequency ones, we
might observe only a small fraction of their edges in every step)

The basic parameters are the number of steps, number of nodes and number
of communities. There are other parameters allowing to modify the random
noise, the maximal size of communities and the maximal duration of
communities, that are by default assigned with values scaled according
to the other parameters. Check documentation for details.

.. code:: ipython3

    (generated_network,generated_comunities) = tn.generate_multi_temporal_scale(nb_steps=1000,nb_nodes=100,nb_com=10)
    plot = tn.plot_longitudinal(communities=generated_comunities,sn_duration=1)



.. image:: output_59_0.png


We can observe that communities are not well defined on a given
particular snapshot

.. code:: ipython3

    last_time = generated_network.end()
    times_to_plot = [int(last_time/4),int(last_time/3),int(last_time/2)]
    plot = tn.plot_as_graph(generated_network,generated_comunities,ts=times_to_plot,width=300,height=300)



.. image:: output_61_0.png

