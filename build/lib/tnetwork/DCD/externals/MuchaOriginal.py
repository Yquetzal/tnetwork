import networkx as nx
import matlab
from matlab import engine
import numpy
import scipy
from tnetwork.utils import dynamicCommunitiesSN
import os
import time

###############################
######For this class, it is necessary to have Matlab installed
######And to set up the matlab for python engine, see how to there
###### https://fr.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
###### (you can find the value of matlabroot by tapping matlabroot in your matlab console)
################################

# def preprocessMatrixForm(om):
#     #initialisation inspired by http://netwiki.amath.unc.edu/GenLouvain/GenLouvain
#
#     Gs = [nx.karate_club_graph(), nx.karate_club_graph()]
#     nodeOrder = list(Gs[0].nodes())
#     N = len(nodeOrder)
#     T = len(Gs)
#
#     print("N", N)
#     print("T", T)
#     twomu = 0
#     B = numpy.zeros(shape=(N * T, N * T))
#     i = 1
#
#     for g in Gs:
#         gmat = nx.to_numpy_matrix(g, nodelist=nodeOrder)
#         k = gmat.sum(axis=0)
#         twom = k.sum(axis=1)
#         twomu = twomu + twom
#         indx = numpy.arange(start=0, stop=N) + numpy.array([(i - 1) * N] * N)
#
#         nullModel = k.transpose() * k / twom
#         B[numpy.ix_(indx, indx)] = gmat - nullModel  # for each slice, put the modularity matrix
#
#         i += 1
#
#     twomu = twomu + 2 * om * N * (T - 1)
#     ones = numpy.ones((2, N * T))
#     diags = [-N, N]
#     omegaMat = scipy.sparse.spdiags(ones, diags, N * T, N * T)
#     numpy.savetxt("test", omegaMat.A, fmt="%.2f")
#
#     omegaMat = omegaMat * om
#     B = B + omegaMat
#
#     # matlab code
#     S = runMatlabCode(B)
#     print(S)


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

    duration = (time.time() - start_time)


    return(S,duration)
    # S = numpy.asarray(S).reshape(2, 34)

def muchaOriginal(dynNetSN, om=0.5,form="local",runningTime=False):
    print("INITIALISING MUCHA ")

    #dynNetSN.remove_nodes_from(dynNetSN.isolates())


    graphs = dynNetSN.snapshot_affiliations()

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
        print(multipleAppearances)
        for (n,nAppearences) in multipleAppearances.items():
            orderedAppearences = nAppearences
            for i in range(0,len(orderedAppearences)-1,1):
                    B[orderedAppearences[i],orderedAppearences[i+1]]=om

    print("saving temp file")
    numpy.savetxt("test.csv", B, fmt="%.2f", delimiter=",")
    print("file saved")

    #B = scipy.sparse.coo_matrix(B)

    (S,duration) = runMatlabCode(B)
    if runningTime:
        return duration
    print("transforming back to dynamic net")

    DCSN = dynamicCommunitiesSN()
    for i in range(len(S)):
        DCSN.add_affiliation(nodeOrderAllSN[i][1], S[i], nodeOrderAllSN[i][0])
    return DCSN



#preprocessMatrixForm(0.5)
#muchaOriginal("bla")