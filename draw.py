import networkx as nx
import matplotlib.pyplot as plt
def draw_graph(edges, labels):
    """
    takes in edges which is a list of lists describing the edges
    len(edges) needs to be the same as len(labels)
    """
    if (len(edges) != len(labels)):
        print("len(edges) != len(labels")
        return
    
    # All elements must be a string
    for tup in range(len(edges)):
        for object in range(len(edges[tup])):
            edges[tup][object] = str(edges[tup][object])
    labels = [str(x) for x in labels]
            

    G = nx.DiGraph()
    G.add_edges_from(edges)

    # pos = nx.spring_layout(G)
    pos = nx.circular_layout(G)
    # pos = nx.spring_layout(G)

    plt.figure()    
    nx.draw(G,pos,edge_color='black',width=1,linewidths=1,node_size=500,node_color='gray',alpha=0.5, labels={node:node for node in G.nodes()})
    # edge_labels = {(x[0], x[1],): x[0] + x[1] for x in labels}
    edge_labels = {}
    for i in range(len(labels)):
        edge_labels.update({ tuple([edges[i][0], edges[i][1]],): labels[i] })
    nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_labels,font_color='black')
    plt.axis('off')
    plt.show()
