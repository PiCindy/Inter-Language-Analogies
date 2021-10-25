import sknetwork as skn
import pandas as pd
from ast import literal_eval as make_tuple
from sknetwork.clustering import Louvain
from sknetwork.hierarchy import Ward, cut_straight, dasgupta_score, tree_sampling_divergence
from sknetwork.visualization import svg_graph, svg_digraph, svg_bigraph, svg_dendrogram
import numpy as np
from scipy import sparse
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Run simple visualizations.')
    parser.add_argument("--input_file", type=str, default="partial_transfer.csv", 
                        help='Name of the file where is table with distances is lying')
    parser.add_argument('output', choices=['dendrogram', 'graph'], help="What type of visualization to output")
    args = parser.parse_args()
    return args


def save_dendrogram(adj):
    ward = Ward()
    dendrogram = ward.fit_transform(adj)
    
    image = svg_dendrogram(dendrogram, names=df.columns[1:], filename="dendro_part")
    

def save_graph(adj):
    louvain = Louvain()
    labels = louvain.fit_transform(adj)
    
    image = svg_graph(adjacency=adj, labels=labels, names=df.columns[1:],
                      filename="result_part")
    

if __name__ == "__main__":
    args = parse_args()
    
    df = pd.read_csv(args.input_file)
    
    num = len(df.columns) - 1

    matrix = [[0] * num for _ in range(num)]

    for i in range(num):
        for j in range(1, num + 1):
            matrix[i][j - 1] = make_tuple(df.iloc[i][j])[1]
            
    adj = sparse.csr_matrix(np.array(matrix, dtype=float))
    
    if args.output == 'dendrogram':
        save_dendrogram(adj)
    else:
        save_graph(adj)
