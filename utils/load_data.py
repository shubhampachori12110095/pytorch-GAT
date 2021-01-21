import enum
import os
import pickle
from itertools import repeat
import time


import scipy.sparse as sp
import numpy as np
import networkx as nx
import torch
import matplotlib.pyplot as plt


from utils.constants import *
# nobody except for PyTorch Geometric did coalescing of the edge index...

# todo: link how the Cora was created and what the feature vectors represent
# todo: Visualize Cora (TikZ, networkx or whatever graph package)
# todo: compare across 5 different repos how people handled Cora
# todo: add t-SNE visualization of trained GAT model

# todo: understand csr, csc, coo, lil, dok sparse matrix formats (understand the other 2 from scipy)

# Currently I only have support for Cora - feel free to add your own data
# GAT and many other papers used the processed version of Cora that can be found here:
# https://github.com/kimiyoung/planetoid


class DatasetType(enum.Enum):
    CORA = 0


def pickle_read(path):
    with open(path, 'rb') as file:
        out = pickle.load(file)

    return out


def plot_in_out_degree_distributions(edge_index, num_of_nodes):
    assert isinstance(edge_index, np.ndarray), f'Expected NumPy array got {type(edge_index)}.'

    # Store each node's input and output degree (they're the same for undirected graphs such as Cora)
    in_degrees = np.zeros(num_of_nodes)
    out_degrees = np.zeros(num_of_nodes)

    # Edge index shape = (2, num_of_edges), the first row contains the source nodes, the second one target/sink nodes
    # Note on terminology: source nodes point to target/sink nodes
    for cnt in range(edge_index.shape[1]):
        source_node_id = edge_index[0, cnt]
        target_node_id = edge_index[1, cnt]

        out_degrees[source_node_id] += 1  # source node points towards some other node -> increment it's out degree
        in_degrees[target_node_id] += 1

    plt.figure()
    plt.subplot(211)
    plt.plot(in_degrees, color='blue')
    plt.xlabel('node id'); plt.ylabel('degree count'); plt.title('In degree')

    plt.subplot(212)
    plt.plot(out_degrees, color='red')
    plt.xlabel('node id'); plt.ylabel('degree count'); plt.title('Out degree')
    plt.show()


def visualize_graph(edge_index, node_labels):
    assert isinstance(edge_index, np.ndarray), f'Expected NumPy array got {type(edge_index)}.'

    edge_index_tuples = list(zip(edge_index[0, :], edge_index[1, :]))
    G = nx.Graph()
    G.add_edges_from(edge_index_tuples)
    nx.draw_networkx(G)
    plt.show()


def load_data(dataset_name, should_visualize=True):
    if dataset_name.lower() == DatasetType.CORA.name.lower():

        node_features_csr = pickle_read(os.path.join(CORA_PATH, 'node_features.csr'))
        # todo: process features
        node_labels_npy = pickle_read(os.path.join(CORA_PATH, 'node_labels.npy'))
        adjacency_list_dict = pickle_read(os.path.join(CORA_PATH, 'adjacency_list.dict'))
        num_of_nodes = len(adjacency_list_dict)

        # Build edge index explicitly (faster than nx ~100 times and as fast as PyGeometric imp, far less complicated)
        row, col = [], []
        seen = set()
        for source_node, neighboring_nodes in adjacency_list_dict.items():
            for value in neighboring_nodes:
                if (source_node, value) not in seen:
                    row.append(source_node)
                    col.append(value)
                seen.add((source_node, value))
        # todo: be explicit about shapes throughout the code
        edge_index = np.row_stack((row, col))

        if should_visualize:
            # plot_in_out_degree_distributions(edge_index, num_of_nodes)
            visualize_graph(edge_index, node_labels_npy)

        # todo: int32/64?
        # todo: add masks

        # todo: convert to PT tensors
        return node_features_csr, node_labels_npy, edge_index
    else:
        raise Exception(f'{dataset_name} not yet supported.')


def index_to_mask(index, size):
    mask = torch.zeros((size, ), dtype=torch.bool)
    mask[index] = 1
    return mask


def build_edge_index_nx(adjacency_list_dict):
    nx_graph = nx.from_dict_of_lists(adjacency_list_dict)
    adj = nx.adjacency_matrix(nx_graph)
    adj = adj.tocoo()

    return np.row_stack((adj.row, adj.col))


if __name__ == "__main__":
    print('yo')
    load_data('cora')