
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module is a modification of the louvain method that allows to take as input any null model.
The null model must be provided as graph, the weight of each edge corresponding to the estimated weight of the edge
For instance, in the case of the spatial null model, the null model is provided by the result of a gravity model

It is based on an original version provided by Thomas Aynaud.
"""
from __future__ import print_function
__all__ = ["_partition_at_level", "modularity", "best_partition", "_generate_dendrogram", "generate_dendogram",
		   "_induced_graph"]
__author__ = """Thomas Aynaud (thomas.aynaud@lip6.fr)"""
#    Copyright (C) 2009 by
#    Thomas Aynaud <thomas.aynaud@lip6.fr>
#    All rights reserved.
#    BSD license.
#	Modified by Remy Cazabet

__PASS_MAX = -1
__MIN = 0.001

import networkx as nx
import warnings

def _partition_at_level(dendrogram, level) :
	"""Return the partition of the nodes at the given level

	A dendrogram is a tree and each level is a partition of the graph nodes.
	Level 0 is the first partition, which contains the smallest snapshot_affiliations, and the best is len(dendrogram) - 1.
	The higher the level is, the bigger are the snapshot_affiliations

	"""
	partition = dendrogram[0].copy()
	for index in range(1, level + 1) :
		for node, community in partition.items() :
			partition[node] = dendrogram[index][community]
	return partition



def _computeSumWeightsByCom(partition, graph):
	inc = dict([])  # sum of weights of intern edges for each com
	for node in graph:
		com = partition[node]
		# deg[com] = deg.get(com, 0.) + graph.degree(node, weight = 'weight')
		for neighbor, datas in graph[node].items():  # for all edges starting from this node
			weight = datas.get("weight", 1)  # get the weight of the edge
			if partition[neighbor] == com:  # if it is an intern edge
				# increment the sum of intern weights for this com
				if neighbor == node:  # if it is a looping edge, count full, otehrwise count half, as we will find it twice
					inc[com] = inc.get(com, 0.) + float(weight)
				else:
					inc[com] = inc.get(com, 0.) + float(weight) / 2.
	return inc


def modularity(partition, graph,nullModel) :
	"""Compute the modularity of a partition of a graph, according to a provied null model
	:param partition: a partition provided as a dictionary node:com
	:param graph: the observed graph, as nx.Graph
	:param nullModel: the null model, as nx.Graph
	"""
	if type(graph) != nx.Graph :
		raise TypeError("Bad graph type, use only non directed graph")

		#inc = dict([]) #sum of weights of intern edges for each com
	#incNullMod = dict([])
	#deg = dict([]) #sum of degrees for each com
	links = graph.size(weight='weight')
	if links == 0 :
		raise ValueError("A graph without link has an undefined modularity")

	sumWeightsByComOriginal = _computeSumWeightsByCom(partition, graph)
	sumWeightsByComNullMod = _computeSumWeightsByCom(partition, nullModel)

	res = 0.
	for com in set(partition.values()) :
		weightsInCom = (sumWeightsByComOriginal.get(com, 0.) / links)
		weightsInNullModel = (sumWeightsByComNullMod.get(com, 0.) / links)

		#weightsInNullModel = (deg.get(com, 0.) / (2.*links))**2
		res += weightsInCom - weightsInNullModel
	return res




def _generate_dendrogram(graph, nullModel, part_init = None) :
	"""Find snapshot_affiliations in the graph and return the associated dendrogram

	A dendrogram is a tree and each level is a partition of the graph nodes.  Level 0 is the first partition, which contains the smallest snapshot_affiliations, and the best is len(dendrogram) - 1. The higher the level is, the bigger are the snapshot_affiliations

	"""
	if type(graph) != nx.Graph :
		raise TypeError("Bad graph type, use only non directed graph")
	#if round(graph.size(weight="weight")) != round(nullModel.size(weight="weight")):
	#	warnings.warn("STRANGE, the null model and the original network have different size: ORIGINAL: %s NULLmodel: %s"%(graph.size(weight="weight"),nullModel.size(weight="weight")))


	#special case, when there is no link
	#the best partition is everyone in its community
	if graph.number_of_edges() == 0 :
		part = dict([])
		for node in graph.nodes() :
			part[node] = node
		return part

	current_graph = graph.copy()
	current_Null = nullModel.copy()
	status = Status()
	status.init(current_graph, current_Null,part_init)
	#mod = __modularity(status)
	status_list = list()
	status.one_level()

	new_mod = status.modularity()
	#print("moudlarity at first level:" + str(new_mod))

	partition = __renumber(status.node2com)
	status_list.append(partition)
	mod = new_mod
	current_graph = _induced_graph(partition, current_graph)
	current_Null = _induced_graph(partition, current_Null)

	status.init(current_graph,current_Null)

	level = 1
	while True :
		level+=1
		status.one_level()
		new_mod = status.modularity()
		#print("modularity at level %s: %s"%(level,new_mod))
		if new_mod - mod < __MIN :
			break
		partition = __renumber(status.node2com)
		status_list.append(partition)
		mod = new_mod
		current_graph = _induced_graph(partition, current_graph)
		current_Null = _induced_graph(partition, current_Null)

		status.init(current_graph,current_Null)
	return status_list[:]


def getPartitionAtSpecificLevel(graph, nullModel, partition = None, levelToREturn=0) :
	"""
	return the partition at a given level of the louvain hierarchical decomposition. Default is first level
	:param graph: the observed graph, as nx.Graph
	:param nullModel: the null model, as nx.Graph
	:param levelToREturn: the level to return, default 0 is the first level
	"""
	dendo = _generate_dendrogram(graph, nullModel, partition)
	return _partition_at_level(dendo, levelToREturn)

def best_partition(graph, nullModel, partition = None) :
	"""Compute the partition of the graph nodes which maximises the modularity
	(or try..) using the Louvain heuristices

	This is the partition of highest modularity, i.e. the highest partition of the dendrogram
	generated by the Louvain algorithm.

	:param graph: the observed graph, as nx.Graph
	:param nullModel: the null model, as nx.Graph
	:param levelToREturn: the level to return, default 0 is the first level
	"""
	dendo = _generate_dendrogram(graph, nullModel, partition)
	return _partition_at_level(dendo, len(dendo) - 1)


def _induced_graph(partition, graph) :
	"""Produce the graph where nodes are the snapshot_affiliations

	there is a link of weight w between snapshot_affiliations if the sum of the weights of the links between their elements is w
	"""
	ret = nx.Graph()
	ret.add_nodes_from(partition.values())

	#print("partitions", partition)

	for node1, node2, datas in graph.edges(data = True) :
		weight = datas.get("weight", 1)
		com1 = partition[node1]
		com2 = partition[node2]
		w_prec = ret.get_edge_data(com1, com2, {"weight":0}).get("weight", 1)
		ret.add_edge(com1, com2, weight = w_prec + weight)

	return ret


def __renumber(dictionary) :
	"""Renumber the values of the dictionary from 0 to n
	"""
	count = 0
	ret = dictionary.copy()
	new_values = dict([])

	for key in dictionary.keys() :
		value = dictionary[key]
		new_value = new_values.get(value, -1)
		if new_value == -1 :
			new_values[value] = count
			new_value = count
			count = count + 1
		ret[key] = new_value

	return ret



class Status :
	"""
	To handle several data in one struct.

	Could be replaced by named tuple, but don't want to depend on python 2.6
	"""
	total_weight = 0
	internals = {}
	#degrees = {}
	#gdegrees = {}
	PASS_MAX = -1
	MIN = 0.001

	def __init__(self) :

		self.graph = -1
		self.nullModel = -1
		self.node2com = dict([])  # for each node, its community
		self.com2node = {}

		self.internals = dict([])
		self.internalsNull = dict([])


		self.loops = {}
		self.loopsNull = {}

		self.total_weight = -1



	def one_level(self):
		"""Compute one level of snapshot_affiliations
		"""
		modif = True
		nb_pass_done = 0
		cur_mod = self.modularity()
		new_mod = cur_mod

		while modif and nb_pass_done != self.PASS_MAX:
			cur_mod = new_mod
			modif = False
			nb_pass_done += 1
			for node in self.graph.nodes():
				#print("node: %s"%node)
				com_node = self.node2com[node]

				(neigh_communities,neigh_communitiesNull) = self.neighcom(node,self.graph,self.nullModel)

				self.remove(node, com_node,
							neigh_communities.get(com_node, 0.),neigh_communitiesNull.get(com_node, 0.)) #remove intern weight of previous community


				best_com = com_node
				best_increase = 0
				for com, dnc in neigh_communities.items():
					#incr = dnc - self.degrees.get(com, 0.) * degc_totw
					incr = dnc - neigh_communitiesNull[com] #how much we will increase score in moving current node to this com
					if incr > best_increase:
						#print("node %s incr %s from %s - %s" % (node, incr, dnc, neigh_communitiesNull[com]))

						best_increase = incr
						best_com = com
				self.insert(node, best_com,
							neigh_communities.get(best_com, 0.),neigh_communitiesNull.get(best_com, 0.)) #add the intern weight
				if best_com != com_node:
					modif = True
			new_mod = self.modularity()
			#print("--PASS %s , new mod %s "%(nb_pass_done,new_mod))

			if new_mod - cur_mod < self.MIN:
				break

	def __str__(self) :
		return ("node2com : " + str(self.node2com) + " degrees : "
				+ str(self.degrees) + " internals : " + str(self.internals)
				+ " total_weight : " + str(self.total_weight))


	def copy(self) :
		"""Perform a deep copy of status"""
		new_status = Status()

		new_status.graph=self.graph
		new_status.nullModel=self.nullModel
		new_status.node2com = self.node2com.copy()
		new_status.com2node = self.com2node.copy()

		new_status.internals = self.internals.copy() #intern edges in snapshot_affiliations in original graph
		new_status.internalsNull=self.internalsNull #intern edges in snapshot_affiliations in null model

		new_status.total_weight = self.total_weight



	def init(self, graph, nullModel, part = None) :
		count = 0 #community indice
		self.graph=graph
		self.nullModel=nullModel
		self.node2com = dict([]) #for each node, its community
		self.com2node = {}

		self.internals = dict([])
		self.internalsNull = dict([])

		self.loops = {}
		self.loopsNull = {}

		self.total_weight = graph.size(weight = 'weight')


		if part == None :#if it is the first iteration, put each node in its own community, intern edges are only loops
			for node in graph.nodes() :
				self.node2com[node] = count
				self.com2node.setdefault(count,set()).add(node)
				#deg = float(graph.degree(node, weight = 'weight'))

				self.loops[node] = float(graph.get_edge_data(node, node,{"weight":0}).get("weight", 1))
				self.loopsNull[node] = float(nullModel.get_edge_data(node, node,{"weight": 0}).get("weight", 1))

				self.internals[count] = self.loops[node]
				self.internalsNull[count] = self.loopsNull[node]
				count = count + 1
		else:
			for node in graph.nodes():
				self.node2com[node] = part[node]
				self.com2node.setdefault(part[node],set()).add(node)

			self.internals = _computeSumWeightsByCom(part, graph)
			self.internalsNull = _computeSumWeightsByCom(part, nullModel)

	def neighcom(self,node,graph,nullModel):
		"""
		Compute the snapshot_affiliations in the neighborood of node in the graph given
		with the decomposition node2com
		"""
		#compute, for each neighbor of the node, for their snapshot_affiliations, to how much does link to the tested nodes contribute to them

		weightsOriginal = {}
		weightsNullModel = {}

		for neighbor, datas in graph[node].items(): #for each edge starting from this node
			if neighbor != node: #if it is not a loop
				weight = datas.get("weight", 1) #get the weight

				neighborcom = self.node2com[neighbor] #get the community of the neighbor
				weightsOriginal[neighborcom] = weightsOriginal.get(neighborcom, 0) + weight  #increase the weights of the community affected


		weightsOfNeighbs = nullModel[node]
		for com in weightsOriginal:
			neighbIncom = self.com2node[com]
			#edgesIncom = [(node,nei) for nei in neighbIncom]

			#weightsInCom = nullModel.edges(edgesIncom,data=True)
			#weightsInCom = [weightsInCom[n][2] for n in weightsInCom]
			weightsInCom = {k:w["weight"] for k,w in weightsOfNeighbs.items() if k in neighbIncom}


			if node in weightsInCom:
				del weightsInCom[node]
			weightsNullModel[com] = weightsNullModel.get(com, 0) + sum(weightsInCom.values())
			# for neighbInCom in self.com2node[com]:
			# 	if neighbInCom != node:  # if it is not a loop
			# 		w = 0
			# 		try:
			# 			w  = nullModel[node][neighbInCom]["weight"]
			# 		except KeyError:
			# 			pass
			#
			# 		weightsNullModel[com] = weightsNullModel.get(com, 0) + w  #increase the weights of the community affected
			# 		#weightsNullModel[neighborcom] = weightsNullModel.get(neighborcom,0)+nullModel[node][neighbor]["weight"]
		return (weightsOriginal,weightsNullModel)

	def remove(self,node, com, weight,weightNull) :
		""" Remove node from community com and modify status"""

		self.internals[com] = float( self.internals.get(com, 0.) -
									   weight - self.loops.get(node, 0.) )

		self.internalsNull[com] = float(self.internalsNull.get(com, 0.) -
										weightNull - self.loopsNull.get(node, 0.))
		self.com2node[com].remove(node)
		if len(self.com2node[com])==0:
			del self.com2node[com]
		self.node2com[node] = -1


	def insert(self,node, com, weight,weightNull) :
		""" Insert node into community and modify status"""
		self.node2com[node] = com
		self.com2node.setdefault(com,set()).add(node)

		self.internals[com] = float( self.internals.get(com, 0.) +
									   weight + self.loops.get(node, 0.) )
		self.internalsNull[com] = float(self.internalsNull.get(com, 0.) +
										weightNull + self.loopsNull.get(node, 0.))


	def modularity(self) :
		"""
		Compute the modularity of the partition of the graph faslty using status precomputed
		"""
		links = float(self.total_weight)
		result = 0.
		for community in self.com2node :
			in_degree = self.internals.get(community, 0.)
			in_degreeNullMod = self.internalsNull.get(community, 0.)

			#result = result + in_degree / links - ((degree / (2.*links))**2)
			result += in_degree / links - in_degreeNullMod / links

		return result
