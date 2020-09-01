from tnetwork.DCD.externals.RDyn.RDyn import RDynV2

def benchmark_rdyn(size=100, iterations=100, avg_deg=15, sigma=.6,
                 lambdad=1, alpha=2.5, paction=1, prenewal=.8,
                 quality_threshold=.2, new_node=.0, del_node=.0, max_evts=1):

    rdb = RDynV2( size=size, iterations=iterations, avg_deg=avg_deg, sigma=sigma,
                 lambdad=lambdad, alpha=alpha, paction=paction, prenewal=prenewal,
                 quality_threshold=quality_threshold, new_node=new_node, del_node=del_node, max_evts=max_evts)
    return rdb.execute(simplified=True)
