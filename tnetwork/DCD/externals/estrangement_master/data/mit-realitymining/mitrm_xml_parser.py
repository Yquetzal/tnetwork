#!/usr/bin/python

import networkx as nx
from xml.dom import minidom
import datetime
import sys
import os

if len(sys.argv) > 2:
    output_dir = os.path.abspath(sys.argv[1])
    xml_inputs = sys.argv[2:]
else:
    sys.exit("usage: %s output_dir list of xml_data_files" % sys.argv[0] )


if os.path.isdir(output_dir):
    sys.exit("result dir already exists, will not overwrite")
else:
    os.mkdir(output_dir)

snapshot_window = 7 # in number of days

# key is device_oid, value is person.phonenumber_oid
device_to_person = {}
# key is "day" of presence, value is a devicespan tuple
graph_dict = {}
time_format = "%Y-%m-%d %H:%M:%S"
time_origin = datetime.datetime.max
alldevices = set()
persons_with_multiple_devices = set()


# pass 1 : build device_to_person and get time_origin
for input in xml_inputs :
    print "reading ", input
    mitdom = minidom.parse(input)
    for person in mitdom.getElementsByTagName("person"):
        person_oid = person.getAttribute("phonenumber_oid")
        #print "Person: ", person_oid
        
        indiv_device_count = 0
        for device in person.getElementsByTagName("device"):
            device_oid1 = device.getAttribute("oid")
            #print "device_oid: ", device_oid1
            if not device_to_person.has_key(device_oid1):
                device_to_person[device_oid1] = person_oid
            alldevices.add(device_oid1)
            indiv_device_count += 1

        for devicespan in person.getElementsByTagName("devicespan"):
            starttime = datetime.datetime.strptime(devicespan.getAttribute("starttime"),
                time_format)
            if starttime < time_origin :
                time_origin = starttime

            device_oid2 = devicespan.getAttribute("device_oid")
            alldevices.add(device_oid2)

        if indiv_device_count > 1:
            persons_with_multiple_devices.add(person_oid)
    # unlink before reading next dom; try avoiding memory overflow        
    mitdom.unlink()

time_origin_ordinal = time_origin.toordinal()
print "time_origin: ", str(time_origin), " ordinal: ", time_origin_ordinal
print "# of persons seen", len(set(device_to_person.values()))
print "# of devices seen", len(alldevices)
print "# of persons with multiple devices", len(persons_with_multiple_devices)


unattributed_devices = set()
edge_count = 0
contact_count = 0
skipped_contacts = 0

# pass 2 : make the edge files
for input in xml_inputs :
    print "reading ", input
    mitdom = minidom.parse(input)
    merged_graph = nx.Graph()
    for person in mitdom.getElementsByTagName("person"):
        person_oid = person.getAttribute("phonenumber_oid")
        #print "Person: ", person_oid
        
        for device in person.getElementsByTagName("device"):
            device_oid1 = device.getAttribute("oid")

        # @todo: some devicespans have starttime = endtime, not sure if we should include
        # those, currently including
        for devicespan in person.getElementsByTagName("devicespan"):
            starttime = datetime.datetime.strptime(devicespan.getAttribute("starttime"),
                time_format)
            
            endtime = datetime.datetime.strptime(devicespan.getAttribute("endtime"),
                time_format)
            
            td = endtime - starttime
            #if (td.seconds + td.days * 24 * 3600) < 1:
            #    #print "skipping contact less than 1 sec"
            #    skipped_contacts += 1
            #    continue

            daystart = int((starttime.toordinal() - time_origin_ordinal)/snapshot_window)
            dayend = int((endtime.toordinal() - time_origin_ordinal)/snapshot_window)
            
            device_oid2 = devicespan.getAttribute("device_oid")

            #print "Device span: %s, %s, %d, %d\n" % (device_oid1, device_oid2,
            #    daystart, dayend)
            if not device_to_person.has_key(device_oid2):
                #print "Do not know who has device %s\n" % device_oid2
                unattributed_devices.add(device_oid2)
                continue;

#            print "Device span: %s, %s, %d, %d\n" % (device_to_person[device_oid1], device_to_person[device_oid2],
#                daystart, dayend)

            # use number of contacts as the weight of an edge
            for d in xrange(daystart, dayend+1):
                if not graph_dict.has_key(d):
                    graph_dict[d] = nx.Graph()
                e = (device_to_person[device_oid1], device_to_person[device_oid2])
                if not e in graph_dict[d].edges():
                    graph_dict[d].add_edge(device_to_person[device_oid1],
                        device_to_person[device_oid2], weight=1)
                else:
                    graph_dict[d][e[0]][e[1]]['weight'] +=1
                #edge_dict[d].add(tuple(sorted((device_to_person[device_oid1],
                #    device_to_person[device_oid2]))))
                contact_count += 1
    mitdom.unlink()



def merge_snapshots(target, list_source):
    """ merge edges from snapshots in list_source into target"""
    for d in list_source:
        for edge in graph_dict[d].edges(data=True):
            if graph_dict[target].has_edge(edge[0], edge[1]):
                graph_dict[target].edge[edge[0]][edge[1]]['weight'] += graph_dict[d].edge[edge[0]][edge[1]]['weight']
            else:
                graph_dict[target].add_edge(edge[0], edge[1], weight=edge[2]['weight'])
        del graph_dict[d]

# christmas break has very few edges, so merge them into one snapshot
merge_snapshots(26, [23, 24, 25])

# things are sparse at the beginning and end so delete the first few and the
# last few snapshots
for d in range(9) + range(38,43):
    del graph_dict[d]


for d in sorted(graph_dict.keys()):
    f = open(os.path.join(output_dir, "%s.ncol" % d), 'w')
    for edge in graph_dict[d].edges(data=True):
        f.write("%s %s %f\n" % (edge[0], edge[1], edge[2]['weight']))
    edge_count += graph_dict[d].number_of_edges()
    f.close()    


enddate_dict = {}
for d in sorted(graph_dict.keys()):
    enddate_dict[d] = str(datetime.date.fromordinal(d * snapshot_window +
      time_origin_ordinal))
    print d, " : ", str(enddate_dict[d])

with open(os.path.join(output_dir, "enddate_dict.txt"), 'w') as f:
    f.write(repr(enddate_dict))


with open(os.path.join(output_dir, "enddate_dict.txt"), 'w') as f:
    f.write(repr(enddate_dict))

# make a merged graph
merged_graph = nx.Graph()
for d in sorted(graph_dict.keys()):
    for edge in graph_dict[d].edges(data=True):
        if merged_graph.has_edge(edge[0], edge[1]):
            merged_graph.edge[edge[0]][edge[1]]['weight'] += graph_dict[d].edge[edge[0]][edge[1]]['weight']
        else:
            merged_graph.add_edge(edge[0], edge[1], weight=edge[2]['weight'])


#with open(os.path.join(output_dir, "network.merged"), 'w') as f:
#    for edge in merged_graph.edges(data=True):
#        f.write("%s %s %f\n" % (edge[0], edge[1], edge[2]['weight']))


print "# of unattributed_devices: %d" % len(unattributed_devices)
print "# of contacts seen: " , contact_count
print "# of contacts skipped: " , skipped_contacts
print "# of edges seen: " , edge_count
