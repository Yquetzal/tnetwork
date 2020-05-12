import networkx as nx
from matlab import engine
import scipy.io
import os
import time
import tnetwork as tn
import io
import scipy







def _runMatlabCode(matrix, matlab_session):
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

def transversal_network_mucha_original(dyn_graph:tn.DynGraphSN, om=0.5, form="local", elapsed_time=False, matlab_session=None):
    """
    Multiplex community detection, Mucha et al.

    Algorithm described in : `Mucha, P. J., Richardson, T., Macon, K., Porter, M. A., & Onnela, J. P. (2010). Community structure in time-dependent, multiscale, and multiplex networks. science, 328(5980), 876-878.`

    Brief summary: a single network is created by adding nodes between themselves in different snaphsots. A modified modularity optimization algorithm is run
    on this network

    For this function, it is necessary to have Matlab installed
    And to set up the matlab for python engine, see how to there
    https://fr.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
    (you can find the value of matlabroot by tapping matlabroot in your matlab console)


    :param dyn_graph: dynamic network
    :param om:
    :param form:
    :param elapsed_time:
    :param matlab_session:
    :return:
    """
    print("preprocessing MUCHA ")

    #Original example on genlouvain website
    #N = length(A{1});
    #T = length(A);
    #B = spalloc(N * T, N * T, N * N * T + 2 * N * T);
    #twomu = 0;
    #for s=1:T
    #     k = sum(A
    #     {s});
    #     twom = sum(k);
    #     twomu = twomu + twom;
    #     indx = [1:N]+(s - 1) * N;
    #     B(indx, indx) = A
    #     {s} - gamma * k
    #     '*k/twom;
    #
    #
    # end
    # twomu = twomu + 2 * omega * N * (T - 1);
    # B = B + omega * spdiags(ones(N * T, 2), [-N, N], N * T, N * T);
    # [S, Q] = genlouvain(B);
    # Q = Q / twomu
    # S = reshape(S, N, T);

    graphs = dyn_graph.snapshots()

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

    ordered_real_times = dyn_graph.snapshots_timesteps()
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
    print("calling external code")

    (S,duration) = _runMatlabCode(B, matlab_session=matlab_session)
    #print("transforming back to dynamic net")

    DCSN = tn.DynCommunitiesSN()
    times = dyn_graph.snapshots_timesteps()
    for i in range(len(S)):
        DCSN.add_affiliation(nodeOrderAllSN[i][1], S[i], times[nodeOrderAllSN[i][0]])

    print("sucessfully finished MUCHA ")

    if elapsed_time:
        return (DCSN,{"total":duration})
    return DCSN