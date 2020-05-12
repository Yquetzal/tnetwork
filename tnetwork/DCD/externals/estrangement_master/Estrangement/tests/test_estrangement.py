import networkx as nx
import sys
import os


sys.path.append(os.getcwd() + "/..")
import estrangement

class opt:
        resolution = 0.2
        gap_proof_estrangement = True
        delta = 0.01
        tolerance = 0.4
        lambduh = 0.0

class test_estrangement:
	def setUp(self):
	        self.g0 = nx.Graph()
        	self.g1 = nx.Graph()
		self.g2 = nx.Graph()
		self.g3 = nx.Graph()
		self.g4 = nx.Graph()
		self.g5 = nx.Graph()
		self.g6 = nx.Graph()
		self.g7 = nx.Graph()
		self.g8 = nx.Graph()
		self.g9 = nx.Graph()
        	self.g0.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,4,{'weight':1})])
        	self.g1.add_edges_from([(1,4,{'weight':1}),(2,3,{'weight':1}),(3,4,{'weight':1})])
        	self.g2.add_edges_from([(1,2,{'weight':2}),(2,3,{'weight':1}),(3,4,{'weight':1})])
		self.g3.add_edges_from([(1,2,{'weight':2})])
		self.g4.add_edges_from([(1,2,{'weight':2}),(3,4,{'weight':1})])	
        	self.g5.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,3,{'weight':1}),(2,4,{'weight':1})])
		self.g7.add_edges_from([(1,2,{'weight':1}),(2,3,{'weight':1}),(3,4,{'weight':1}),(4,5,{'weight':1}),(5,6,{'weight':1}),(6,1,{'weight':1})])
		self.g8.add_edges_from([(1,2,{'weight':1}),(2,3,{'weight':1}),(1,3,{'weight':1}),(3,4,{'weight':1}),(4,5,{'weight':1}),(4,6,{'weight':1}),(5,7,{'weight':1}),(6,7,{'weight':1}),(8,9,{'weight':1}),(8,10,{'weight':1}),(9,10,{'weight':1})])
		self.g9.add_edges_from([(1,2,{'weight':1}),(2,3,{'weight':1}),(3,4,{'weight':1}),(4,5,{'weight':1}),(5,6,{'weight':1}),(6,7,{'weight':1}),(7,8,{'weight':1}),(8,9,{'weight':1}),(9,10,{'weight':1}),(10,11,{'weight':1}),(11,12,{'weight':1})])
		self.label_dict1 = {1:'a',2:'a',3:'b',4:'b',5:'c',6:'c'}	
		self.label_dict2 = {1:'a',2:'b',3:'b',4:'b',5:'c',6:'c'}	
		self.label_dict3 = {1:'a',2:'b',3:'c',4:'d',5:'e',6:'f'}	
		self.label_dict4 = {1:'a',2:'a',3:'a',4:'a',5:'a',6:'a'}	
		self.label_dict5 = {1:'b',2:'b',3:'b',4:'b',5:'b',6:'b'}

	def test_maxQ(self):	
		labels = estrangement.maxQ(self.g0,opt.tolerance)
		assert labels[1] == labels[3]
		assert labels[2] == labels[4]

	def test_make_Zgraph(self):
		self.g6  = estrangement.make_Zgraph(self.g0,self.g2,self.label_dict4)  # Just the edge [1,2]
  		GM = nx.isomorphism.GraphMatcher(self.g3,self.g6)
		assert GM.is_isomorphic()
		self.g6 =  estrangement.make_Zgraph(self.g0,self.g0,self.label_dict4)  # same edges and communties
  		GM = nx.isomorphism.GraphMatcher(self.g0,self.g0)
		assert GM.is_isomorphic()
		self.g6 =  estrangement.make_Zgraph(self.g0,self.g0,self.label_dict3)  # no nodes belong to the same community
		assert len(self.g6.nodes()) == 0
		self.g6 =  estrangement.make_Zgraph(self.g0,self.g1,self.label_dict4)  # no overlapping edges
		assert len(self.g6.nodes()) == 0
		self.g6 =  estrangement.make_Zgraph(self.g0,self.g5,self.label_dict1)  # two overlapping edges only one has same label on both ends
		assert len(self.g6.nodes()) == 2
  		GM = nx.isomorphism.GraphMatcher(self.g6,self.g3)
		assert GM.is_isomorphic()
			
	def test_repeated_runs(self):
		# Linear graph 1---2---3---4---5---6---7---8---9---10---11---12
		dictPartition,dictQ,DictE,DictF = estrangement.repeated_runs(self.g9, opt.delta, opt.tolerance, 1,self.g9,3)
		print(dictPartition[0])
		print(dictPartition[1])
		print(dictPartition[2])
		print(DictF[0])
		print(DictF[1])
		print(DictF[2])
		# if the paritions are different the values of F will differ
		assert DictF[0] != DictF[1] or DictF[1] != DictF[2] or DictF[0] != DictF[2]		


	def test_ECA(self):

#               snapshot 0,1    snapshot 2,3    snapshot 4
#
#               1--2  5--6      1--2  5--6      1--2  5--6
#               |\/| /   |      |\/| /|\/|      |\/| /   |
#               |/\|/    |      |/\|/ |/\|      |/\|/    |
#               3--4  7--8      3--4  7--8      3--4  7--8
                # in snapshot 0,1 there should be three communities: {1,2,3,4},{5,6},{7,8}
                # in snapshot 2,3 there should be two communities: {1,2,3,4},{5,6,7,8}
                # in snapshot 4 there should be two communites even though it is the same as snapshot 0
                # check that {1,2,3,4} is a community in snapshot 0


		label_dict = {}
		label_dict = estrangement.ECA(dataset_dir='../sample_data',delta=0.001)
#		with open(os.path.join("task_delta_0.001/matched_labels.log"), 'r') as label_file:
#                        for l in label_file:
#                                line_dict = eval(l)
 #                               time = line_dict.keys()[0]
  #                              label_dict[time] = line_dict[time]



                # in snapshot 0,1 there should be three communities: {1,2,3,4},{5,6},{7,8}
                # in snapshot 2,3 there should be two communities: {1,2,3,4},{5,6,7,8}
                # in snapshot 4 there should be two communites even though it is the same as snapshot 0
                # check that {1,2,3,4} is a community in snapshot 0
                assert label_dict[0][1] == label_dict[0][2]
                assert label_dict[0][1] == label_dict[0][3]
                assert label_dict[0][1] == label_dict[0][4]

                # check that {5,6} and {7,8} are different communities in snapshot 1
                assert label_dict[1][5] == label_dict[1][6]
                assert label_dict[1][7] == label_dict[1][7]
                assert label_dict[1][5] != label_dict[1][7]

                # check that {5,6,7,8} are a community in snapshot 3    
                assert label_dict[3][5] == label_dict[3][6]
                assert label_dict[3][5] == label_dict[3][7]
                assert label_dict[3][5] == label_dict[3][8]

                # check that {5,6,7,8} are a community in snapshot 4,which is the same graph as snapshot 0 and 1    
                assert label_dict[4][5] == label_dict[4][6]
                assert label_dict[4][5] == label_dict[4][7]
                assert label_dict[4][5] == label_dict[4][8]

# Example 1 from: [1] V. Kawadia and S. Sreenivasan, "Online detection of temporal communities 
#           in evolving networks by estrangement confinement", http://arxiv.org/abs/1203.5126.

		label_dict1 = estrangement.ECA(dataset_dir='../sample_data2',delta=0.2)
		label_dict2 = estrangement.ECA(dataset_dir='../sample_data2',delta=0.01)
		

#		with open(os.path.join("task_delta_0.2/matched_labels.log"), 'r') as label_file:
 #           		for l in label_file:
#                		line_dict = eval(l)
  #              		time = line_dict.keys()[0]
 #               		label_dict[time] = line_dict[time]
#		with open(os.path.join("task_delta_0.01/matched_labels.log"), 'r') as label_file2:
 #                       for l in label_file2:
  #                              line_dict = eval(l)
   #                             time = line_dict.keys()[0]
    #                            label_dict[2] = line_dict[time]

		# check that there are three communities in snapshot 0
		assert label_dict1[0][1] == label_dict1[0][2]
		assert label_dict1[0][1] == label_dict1[0][5]
		assert label_dict1[0][6] == label_dict1[0][7]
		assert label_dict1[0][6] == label_dict1[0][7]
		assert label_dict1[0][11] == label_dict1[0][12]
		assert label_dict1[0][11] == label_dict1[0][13]
		assert label_dict1[0][16] == label_dict1[0][17]
		assert label_dict1[0][16] == label_dict1[0][18]
		assert label_dict1[0][1] != label_dict1[0][6]
		assert label_dict1[0][1] != label_dict1[0][11]
		assert label_dict1[0][1] != label_dict1[0][16]
		assert label_dict1[0][6] != label_dict1[0][11]
		assert label_dict1[0][6] != label_dict1[0][16]
		assert label_dict1[0][11] == label_dict1[0][16]
		assert label_dict1[0][11] == label_dict1[0][18]
		assert label_dict1[0][11] == label_dict1[0][20]

		#check that there are four communities in snapshot 1, if delta is 0.2
		assert label_dict1[1][1] == label_dict1[1][2]
                assert label_dict1[1][1] == label_dict1[1][5]
                assert label_dict1[1][6] == label_dict1[1][7]
                assert label_dict1[1][6] == label_dict1[1][7]
                assert label_dict1[1][11] == label_dict1[1][12]
                assert label_dict1[1][11] == label_dict1[1][13]
                assert label_dict1[1][16] == label_dict1[1][17]
                assert label_dict1[1][16] == label_dict1[1][18]
                assert label_dict1[1][1] != label_dict1[1][6]
                assert label_dict1[1][1] != label_dict1[1][11]
                assert label_dict1[1][1] != label_dict1[1][16]
                assert label_dict1[1][6] != label_dict1[1][11]
                assert label_dict1[1][6] != label_dict1[1][16]
                assert label_dict1[1][11] != label_dict1[1][16]
                assert label_dict1[1][11] != label_dict1[1][18]
                assert label_dict1[1][11] != label_dict1[1][20]

		#check that there are three communities in snapshop 1, if delta is 0.01
                assert label_dict2[1][1] == label_dict2[1][2]
                assert label_dict2[1][1] == label_dict2[1][5]
                assert label_dict2[1][6] == label_dict2[1][7]
                assert label_dict2[1][6] == label_dict2[1][7]
                assert label_dict2[1][11] == label_dict2[1][12]
                assert label_dict2[1][11] == label_dict2[1][13]
                assert label_dict2[1][16] == label_dict2[1][17]
                assert label_dict2[1][16] == label_dict2[1][18]
                assert label_dict2[1][1] != label_dict2[1][6]
                assert label_dict2[1][1] != label_dict2[1][11]
                assert label_dict2[1][1] != label_dict2[1][16]
                assert label_dict2[1][6] != label_dict2[1][11]
                assert label_dict2[1][6] != label_dict2[1][16]
                assert label_dict2[1][11] == label_dict2[1][16]
                assert label_dict2[1][11] == label_dict2[1][18]
                assert label_dict2[1][11] == label_dict2[1][20] 

		os.system("rm -r task_delta_0.01")
		os.system("rm -r task_delta_0.2")
		os.system("rm -r task_delta_0.001")

