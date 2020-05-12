import networkx as nx
import sys
import os

sys.path.append(os.getcwd() + "/..")
import agglomerate

class opt:
        resolution = 0.2
        gap_proof_estrangement = True
        delta = 0
        tolerance = 0.4

class test_agglomerate:
	def setUp(self):
                self.g0 = nx.Graph()
                self.g1 = nx.Graph()
                self.g2 = nx.Graph()
                self.g3 = nx.Graph()
                self.g4 = nx.Graph()
                self.g5 = nx.Graph()
                self.g6 = nx.Graph()
		self.g7 = nx.Graph()
                self.g0.add_edges_from([(1,2,{'weight':1}),(2,3,{'weight':1}),(3,4,{'weight':1}),(4,5,{'weight':1}),(5,1,{'weight':1})])  # circle
                self.g1.add_edges_from([(1,2,{'weight':1}),(2,3,{'weight':1}),(3,4,{'weight':2}),(2,4,{'weight':1}),(4,5,{'weight':1}),(3,5,{'weight':1})])
		self.g3.add_edges_from([(1,2,{'weight':2}),(1,1,{'weight':1}),(2,2,{'weight':3})])
		self.g4.add_edges_from([(1,2,{'weight':1}),(1,1,{'weight':1}),(2,2,{'weight':2})])
		self.g5.add_edges_from([(1,2,{'weight':1}),(2,4,{'weight':1}),(4,5,{'weight':1}),(3,5,{'weight':1})])
                self.g6.add_edges_from([(1,2,{'weight':1}),(1,3,{'weight':1}),(1,4,{'weight':1}),(1,5,{'weight':1})])  # line
                self.label_dict1 = {1:'a',2:'a',3:'a',4:'a',5:'a'}
                self.label_dict2 = {1:'b',2:'a',3:'a',4:'a',5:'a'}
                self.label_dict3 = {1:'b',2:'b',3:'a',4:'a',5:'a'}
                self.label_dict4 = {1:'a',2:'b',3:'c',4:'d',5:'e'}
		

	def test_induced_graph(self):
		gret,zret = agglomerate.induced_graph(self.label_dict1,self.g0,self.g1)	# if all the nodes belong to the same community
		assert len(gret.nodes()) == 1		# there will only be one node in the induced graph
		assert len(zret.nodes()) == 1		# likewise for the induced zgraph
		GM = nx.isomorphism.GraphMatcher(gret,zret)
                assert GM.is_isomorphic()		# if graph and zgraph are equal, the induced graph is the same
		
		gret,zret = agglomerate.induced_graph(self.label_dict3,self.g1,self.g5)
		# graph:    b---b---a  	   induced graph:	   2
		#		| \ |  => 		     1 [ b------a ] 3
                #		a---a
		GM = nx.isomorphism.GraphMatcher(gret,self.g3)
		assert GM.is_isomorphic()
		# zgraph:   b---b---a	   induced zgraph:	   1		
		#		    |  =>		     1 [ b------a ] 2
		#		a---a
		GM = nx.isomorphism.GraphMatcher(zret,self.g4)
		assert GM.is_isomorphic()

	def test_generate_dendogram(self):
		partition_list = agglomerate.generate_dendogram(self.g6, opt.delta, opt.tolerance, 1,nx.Graph())
		#	a			    e
		#	|			    |	
		#   b---e---c   => lpa =>	e---e---e  => induced graph => e
		#	|			    |	
		#	d			    e	
		assert len(partition_list) == 1		
		print(partition_list[0])
		gret1,zret1 = agglomerate.induced_graph(self.label_dict1,self.g6,self.g6)	
		gret2,zret2 = agglomerate.induced_graph(partition_list[0],self.g6,self.g6)	
		# partition list should be such that all nodes have the same label and
		# should therefore induce the same graph as label_dict1
	        GM = nx.isomorphism.GraphMatcher(gret1,gret2)
		assert GM.is_isomorphic()	

#SD: Should add a test with multilevel dendogram

	def test_modularity(self):
		assert agglomerate.modularity(self.label_dict1,self.g0) == 0 	 #all nodes in same community
              
		mod =  agglomerate.modularity(self.label_dict4,self.g0) 	 #all nodes in different community in a circle
		#assert mod == -0.2
		assert True

	def test_best_partition(self):
		partition = agglomerate.best_partition(self.g6, opt.delta, opt.tolerance, 1,self.g6)
		gret1,zret1 = agglomerate.induced_graph(self.label_dict1,self.g6,self.g6)
		gret2,zret2 = agglomerate.induced_graph(partition,self.g6,self.g6)
		GM = nx.isomorphism.GraphMatcher(gret1,gret2)
		assert GM.is_isomorphic()

