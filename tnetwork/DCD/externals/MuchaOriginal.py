import networkx as nx
from matlab import engine
import scipy
import os
import time
import tnetwork as tn
import io
import scipy.io


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


def runMatlabCode(matrix,matlab_session):
    #matrix = scipy.sparse.coo_matrix(matrix)
    dir = os.path.dirname(__file__)
    visuAddress = os.path.join(dir, "GenLouvain-master")

    #print("saving matrix for matlab ")
    scipy.io.savemat(visuAddress+'/file.mat',{"B":matrix})
    result_file = visuAddress+'/result.mat'
    ###matFormat = matlab.double(matrix.tolist())

    #print("starting matlab engine")
    eng = matlab_session
    if eng==None:
        eng = engine.start_matlab()
    eng.addpath(visuAddress, nargout=0)
    #print("matlab engine started successfully")
    start_time = time.time()

    out = io.StringIO()
    err = io.StringIO()
    #(S, Q) = eng.genlouvain('file.mat', nargout=2)
    eng.genlouvain('file.mat',result_file, stdout=out, stderr=err)

    duration = time.time() - start_time

    #print("matlab code ran successfully")

    #print(err.getvalue())

    res = scipy.io.loadmat(result_file)
    S = res["S"]



    return(S,duration)
    # S = numpy.asarray(S).reshape(2, 34)

def muchaOriginal(dynNetSN:tn.DynGraphSN, om=0.5,form="local",elapsed_time=False,matlab_session=None):
    print("INITIALISING MMUCHA ")

    #dynNetSN.remove_nodes_from(dynNetSN.isolates())


    graphs = dynNetSN.snapshots()

    nodeOrderAllSN = []
    listModularityMatrices = []

    #for each graph in order
    for t,gT in enumerate(graphs):
        g=graphs[gT]
        nodeOrder = list(g.nodes())
        if len(nodeOrder)>0:
            nodeOrderAllSN+=[(t,n) for n in nodeOrder]

            gmat = nx.to_scipy_sparse_matrix(g, nodelist=nodeOrder,format="dok")
            k = gmat.sum(axis=0) #degrees of nodes
            twom = k.sum(axis=1) #sum of degrees
            nullModel  = k.transpose() * k /twom
            listModularityMatrices.append(gmat - nullModel)

    #Concatenate all null modularity matrices
    #B = scipy.sparse.block_diag(*listModularityMatrices)
    B = scipy.sparse.block_diag(listModularityMatrices,format="dok")
    listModularityMatrices=None

    #B = scipy.sparse.dok_matrix(B)


    #add the link between same nodes in different timestamps
    multipleAppearances={} #for each node, list of indices where it appears

    ordered_real_times = dynNetSN.snapshots_timesteps()
    for (i,(t,n)) in enumerate(nodeOrderAllSN):
        multipleAppearances.setdefault(n,[]).append((i,t))

    if form=="global":
        for (n,nAppearences) in multipleAppearances.items():
            for (i,t) in nAppearences:
                for (j,t) in nAppearences:
                    if i!=j:
                        B[i,j]=om
    if form=="local":
        #print(multipleAppearances)
        for (n,orderedAppearences) in multipleAppearances.items():
            #print(orderedAppearences)
            for i in range(0,len(orderedAppearences)-1):
                #BE CAREFUL, modified recently
                ii,t = orderedAppearences[i]
                ii_next,t_next = orderedAppearences[i+1]
                #index_t = ordered_real_times.index(t)

                if ordered_real_times[t+1]==ordered_real_times[t_next]:
                    B[ii,ii_next]=om

    if form=="local_relaxed":
        #print(multipleAppearances)
        for (n,orderedAppearences) in multipleAppearances.items():
            for i in range(0,len(orderedAppearences)-1):
                ii,t = orderedAppearences[i]
                ii_next,t_next = orderedAppearences[i+1]
                B[ii,ii_next]=om

    #print("saving temp file")
    #numpy.savetxt("test.csv", B, fmt="%.2f", delimiter=",")
    #print("file saved")

    #B = scipy.sparse.coo_matrix(B)

    (S,duration) = runMatlabCode(B,matlab_session=matlab_session)
    #print("transforming back to dynamic net")

    DCSN = tn.DynCommunitiesSN()
    times = dynNetSN.snapshots_timesteps()
    for i in range(len(S)):
        DCSN.add_affiliation(nodeOrderAllSN[i][1], S[i], times[nodeOrderAllSN[i][0]])

    print("sucessfully finished MUCHA ")

    if elapsed_time:
        return (DCSN,{"total":duration})
    return DCSN



#preprocessMatrixForm(0.5)
#muchaOriginal("bla")