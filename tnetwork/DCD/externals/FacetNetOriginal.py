import networkx as nx
import matlab
from matlab import engine
import numpy
import scipy
import os
import time
import tnetwork as tn


def runMatlabCode(matrix):
    dir = os.path.dirname(__file__)
    visuAddress = os.path.join(dir, "GenLouvain-master")

    print("converting matrix for matlab (slowwwwwww)")

    matFormat = matlab.double(matrix.tolist())

    print("starting matlab engine")
    eng = engine.start_matlab()
    eng.addpath(visuAddress, nargout=0)
    print("matlab engine started successfully")
    start_time = time.time()


    (S, Q) = eng.genlouvain(matFormat, nargout=2)
    print("matlab code ran successfully")

    duration = time.time() - start_time


    return(S,duration)
    # S = numpy.asarray(S).reshape(2, 34)

def muchaOriginal(dynNetSN:tn.DynGraphSN, om=0.5,form="local",elapsed_time=False):
    print("INITIALISING MUCHA ")

    #dynNetSN.remove_nodes_from(dynNetSN.isolates())


    graphs = dynNetSN.snapshots()

    nodeOrderAllSN = []
    listModularityMatrices = []

    #for each graph in order
    for i,gT in enumerate(graphs):
        g=graphs[gT]
        nodeOrder = list(g.nodes())
        nodeOrderAllSN+=[(i,n) for n in nodeOrder]

        gmat = nx.to_numpy_matrix(g, nodelist=nodeOrder)

        #
        k = gmat.sum(axis=0) #degrees of nodes
        twom = k.sum(axis=1) #sum of degrees
        nullModel = k.transpose() * k / twom
        listModularityMatrices.append(gmat - nullModel)

    #Concatenate all null modularity matrices
    B = scipy.linalg.block_diag(*listModularityMatrices)
    #B = scipy.sparse.block_diag(listModularityMatrices)

    #add the link between same nodes in different timestamps
    multipleAppearances={} #for each node, list of indices where it appears
    for (i,(t,n)) in enumerate(nodeOrderAllSN):
        multipleAppearances.setdefault(n,[]).append(i)

    if form=="global":
        for (n,nAppearences) in multipleAppearances.items():
            for i in nAppearences:
                for j in nAppearences:
                    if i!=j:
                        B[i,j]=om
    if form=="local":
        #print(multipleAppearances)
        for (n,nAppearences) in multipleAppearances.items():
            orderedAppearences = nAppearences
            for i in range(0,len(orderedAppearences)-1,1):
                    B[orderedAppearences[i],orderedAppearences[i+1]]=om

    print("saving temp file")
    numpy.savetxt("test.csv", B, fmt="%.2f", delimiter=",")
    print("file saved")

    #B = scipy.sparse.coo_matrix(B)

    (S,duration) = runMatlabCode(B)
    print("transforming back to dynamic net")

    DCSN = tn.DynCommunitiesSN()
    for i in range(len(S)):
        DCSN.add_affiliation(nodeOrderAllSN[i][1], S[i], nodeOrderAllSN[i][0])

    if elapsed_time:
        return (DCSN,{"total":duration})
    return DCSN



#preprocessMatrixForm(0.5)
#muchaOriginal("bla")