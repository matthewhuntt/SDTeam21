import csv
import sys

# graph:
#      data structure made up of tuples (n1, n2, d) where n1 and n2 are integers representing each node and d is the distance

def Dijkstra (graph, source, target_nodes):
    temp_distances = {}
    distances = {}
    connected_edges = {}
    for edge in graph:
        temp_distances[edge[0]] = float('inf')
        temp_distances[edge[1]] = float('inf')
        if (edge[0] in connected_edges.keys()):
            connected_edges[edge[0]].append(edge)
        else:
            connected_edges[edge[0]] = [edge]
        if (edge[1] in connected_edges.keys()):
            connected_edges[edge[1]].append(edge)
        else:
            connected_edges[edge[1]] = [edge]
    temp_distances[source] = 0
    
    while len(temp_distances) > 0:
        pivot = -1
        pivot_distance = float('inf')
        # get minimum node
        for node in temp_distances.keys():
            if (temp_distances[node] < pivot_distance):
                pivot = node
                pivot_distance = temp_distances[node]
        # make minimum node permanent
        distances[pivot] = pivot_distance
        del temp_distances[pivot]
        
        for edge in connected_edges[pivot]:
            if (edge[0] == pivot):
                if (edge[1] in temp_distances.keys()):
                    if (temp_distances[edge[1]] > pivot_distance + edge[2]):
                        temp_distances[edge[1]] = pivot_distance + edge[2]
            else:
                if (edge[0] in temp_distances.keys()):
                    if (temp_distances[edge[0]] > pivot_distance + edge[2]):
                        temp_distances[edge[0]] = pivot_distance + edge[2]
    return distances

in_graph = []
header = []

with open(sys.argv[1]) as csv_file:
    csv_reader = csv.reader(csv_file)
    header = []
    for row in csv_reader:
        if (len(header) == 0):
            header = row
        else:
            in_graph.append(row)

target_node_list = []
for edge in in_graph:
    if (edge[0] not in target_node_list):
        target_node_list.append(edge[0])
    if (edge[1] not in target_node_list):
        target_node_list.append(edge[1])
    edge[2] = float(edge[2])

out_graph = []

for node in target_node_list:
    node_distances = Dijkstra(in_graph, node, [n for n in target_node_list if n != node])
    for dist_node in node_distances.keys():
        out_graph.append([node, dist_node, node_distances[dist_node]])
print(out_graph)

with open(sys.argv[2], 'w+') as csv_out_file:
    csv_writer = csv.writer(csv_out_file)
    csv_writer.writerow(header)
    for tup in out_graph:
        csv_writer.writerow(tup)
