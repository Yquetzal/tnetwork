import matlab
from matlab import engine
import numpy
from tnetwork.utils import dynamicCommunitiesSN
import os


###############################
######For this class, it is necessary to have Matlab installed
######And to set up the matlab for python engine, see how to there
###### https://fr.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
###### (you can find the value of matlabroot by tapping matlabroot in your matlab console)
################################


def prepareArgumentsOnline(dynNetSN,k,online):
    #initialisation inspired by http://netwiki.amath.unc.edu/GenLouvain/GenLouvain

    #get all nodes in a sorted set so that they have a unique ID we can find easily (index+1)
    # allNodes =  list(dynNetSN.aggregate().nodes().keys())
    # nodeIDdict = bidict()
    # for i in range(len(allNodes)):
    #     nodeIDdict[allNodes[i]]=i+1


    #Create a dynamic network as seuqence of nx graphs
    # Gs = list(dynNetSN.snapshot_communities().values())
    # nodesPresent = []
    # GsMat = []
    # for g in Gs:
    #     #get nodes of the current graph ordered according to the global order
    #     filteredOrderedNodes = [x for x in nodeIDdict.keys() if x in g.nodes]
    #     # transform to numpy matrix
    #     GsMat.append(nx.to_numpy_matrix(g, nodelist=filteredOrderedNodes).tolist())
    #     nodesPresent.append([nodeIDdict[name] for name in filteredOrderedNodes])
    SocNet = dict()
    net=dict()
    net["Z"]=[] #empty means default value / random assignment
    Indexx=[]

    if online:
        (GsMat,nodeIDdict,nodesPresent) = dynNetSN.to_set_of_matrices()
        SocNet["cellW"] = [matlab.double(x) for x in GsMat]
        SocNet["W"] = matlab.double([])
        for t in nodesPresent:
            Indexx.append(matlab.double([[x] for x in t]))
    else:
        (GsMat, nodeIDdict, nodesPresent) = dynNetSN.to_tensor()
        for a in GsMat: print(len(a))
        stacked = numpy.stack(GsMat, axis=2)
        listed = stacked.tolist()
        SocNet["cellW"] = []
        SocNet["W"] = matlab.double(listed)
        matL = matlab.double(range(1, len(nodeIDdict) + 1))
        Indexx=[matL for x in range(len(GsMat))]
        #for t in nodesPresent:
        #    Indexx.append(matlab.double([[x] for x in t]))

        #net["Z"]=[[0]*len(nodeIDdict)]*len(GsMat)
        #print(net["Z"])


    #SocNet["W"]=matlab.double(numpy.stack(GsMat).tolist())

    #make a tensor
    #stacked = numpy.stack(GsMat,axis=2)
    #stacked=numpy.stack([])
    #listed = stacked.tolist()


    SocNet["n"] = float(len(nodeIDdict))
    SocNet["T"]=len(GsMat)

    #SocNet["Index"]=nodeOrder

    #Indexx=[matlab.double(x) for x in nodesPresent]

    K=float(k)

    net["type"]="binary"
    net["wthreshold"]=-1 #ignored, checked only for similarity graphs
    net["paraP"]=[] #empty means default values
    net["paraA"]=[] #empty means default values

    net["Temp"]=matlab.double(numpy.arange(1,-0.1,-0.1).tolist())#"1:-0.1:0"
    net["N"]=matlab.double([20]*2+[10]*5+[5]*4)#"[20*ones(1,2) 10*ones(1,5) 5*ones(1,4)]"
    net["verbosity"]=0
    net["objfunc"]=[]

    return(SocNet,K,net,Indexx,nodeIDdict,nodesPresent)


# def prepareArguments(dynNetSN,k,online):
#     #initialisation inspired by http://netwiki.amath.unc.edu/GenLouvain/GenLouvain
#
#     #get all nodes in a sorted set so that they have a unique ID we can find easily (index+1)
#     allNodes =     SortedSet(dynNetSN.aggregate().nodes().keys())
#
#     #Create a dynamic network as seuqence of nx graphs
#     Gs = list(dynNetSN.snapshot_communities().values())
#     nodeNamesDic = []
#     GsMat = []
#     for mat in Gs:
#         nodeOrder = list(Gs[0].nodes())
#         GsMat.append(nx.to_numpy_matrix(mat, nodelist=nodeOrder).tolist())
#         nodeNamesDic.append(nodeOrder)
#     #transform to list of numpy matrices
#     GsMat = [nx.to_numpy_matrix(mat,nodelist=nodeOrder).tolist() for mat in Gs]
#
#     #fix node order
#
#     SocNet = dict()
#     #SocNet["W"]=matlab.double(numpy.stack(GsMat).tolist())
#
#     #make a tensor
#     stacked = numpy.stack(GsMat,axis=2)
#     listed = stacked.tolist()
#     SocNet["W"]=matlab.double(listed)
#
#     SocNet["n"] = float(len(nodeOrder))
#     SocNet["T"]=len(listed[0][0])
#     SocNet["cellW"]=[matlab.double(x) for x in GsMat]
#     #SocNet["Index"]=nodeOrder
#     if online==False:
#         matL = matlab.double(range(1,len(nodeOrder)+1))
#         Indexx=[matL for x in range(len(Gs))]
#     else:
#         Indexx = [for t]
#     K=float(k)
#
#     net=dict()
#     net["type"]="binary"
#     net["wthreshold"]=-1 #ignored, checked only for similarity graphs
#     net["paraP"]=[] #empty means default values
#     net["paraA"]=[] #empty means default values
#
#     net["Temp"]=matlab.double(numpy.arange(1,-0.1,-0.1).tolist())#"1:-0.1:0"
#     net["N"]=matlab.double([20]*2+[10]*5+[5]*4)#"[20*ones(1,2) 10*ones(1,5) 5*ones(1,4)]"
#     net["Z"]=[] #empty means default value / random assignment
#     net["verbosity"]=0
#     net["objfunc"]=[]
#
#     return(SocNet,K,net,Indexx,nodeOrder)


def launchMatlab():
    dir = os.path.dirname(__file__)
    visuAddress = os.path.join(dir, "YangOriginal")


    #matFormat = matlab.double(matrix.tolist())

    print("starting matlab engine")
    eng = engine.start_matlab()
    eng.addpath(visuAddress, nargout=0)
    print("matlab engine started successfully")
    return(eng)

    #print(matFormat)
    #net = eng.SBMDynamicEvolutionOfflineDynamic2(SocNet,K,net,Indexx)

    return(net)

def YangOriginal(dynNetSN, k=5,online=False):
    (SocNet, K, net, Indexx,nodeOrder,nodesPresent) = prepareArgumentsOnline(dynNetSN,k,online)
    engine = launchMatlab()

    if online==False:
        struct = engine.SBMDynamicEvolutionOfflineDynamic2(SocNet,K,net,Indexx)
    else:
        struct = engine.SBMDynamicEvolutionOnlineDynamic(SocNet,K,net,Indexx)

    tComs = struct["Z"]
    DCSN = dynamicCommunitiesSN()


    times = dynNetSN.snapshots_timesteps()
    i=0
    for partition in tComs: #for each timestep
        tID = times[i]
        for (n,c) in partition: #for each node
            if n in nodesPresent[i]:  #if this node is present (problems with the offline method)
                DCSN.add_affiliation(nodeOrder.inv[n], c, tID)
        i+=1
    return DCSN


# dynX = dx.DynGraphSN()
# dynX.addSnaphsot(1,nx.karate_club_graph())
# dynX.addSnaphsot(2,nx.karate_club_graph())
#
# #Gs = [nx.karate_club_graph(), nx.karate_club_graph()]
#
# DCSN = YangOriginal(dynX,5,online=True)
# print(DCSN.snapshot_communities())