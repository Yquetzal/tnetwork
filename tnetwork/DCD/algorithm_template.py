import time


def DCD_algorithm(dynamic_network,algorithm_name,detection,label_attribution=None,pre_processing=None,post_processing=None,elapsed_time=False):
    print("starting "+algorithm_name)
    time_Steps = {}
    pre_processed = dynamic_network
    if pre_processing!=None:
        pre_processed = pre_processing(dynamic_network)

    start = time.time()
    dynamic_partition = detection(pre_processed)
    after_detection = time.time()
    time_Steps["CD"] = after_detection - start
    time_Steps["total"] = time_Steps["CD"]
    if post_processing!=None:
        dynamic_partition = post_processing(dynamic_partition)
    after_postprocess = time.time()

    if label_attribution!=None:
        dynamic_communities = label_attribution(dynamic_partition)
        time_Steps["match"] = time.time() - after_postprocess
        time_Steps["total"] += time_Steps["match"]

    if elapsed_time:
        return (dynamic_communities,time_Steps)
    return dynamic_communities