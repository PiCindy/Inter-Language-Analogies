#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time

from subprocess import Popen, PIPE

import nlg.Cluster.Words2Clusters.Words2Vectors as Words2Vectors

from nlg.Cluster.Cluster import Cluster, ListOfClusters
from nlg.Cluster.Words2Clusters.StrCluster import ListOfStrClusters

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '22/08/2017', '0.10' # Creation
__description__ = """
	Create clusters from a list of words (or sequence of words).
	CAUTION: each word should appear only once in the list.
"""

###############################################################################

def read_argv():
	import argparse
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	parser = argparse.ArgumentParser(description=this_description)
	parser.add_argument('-F','--focus',
					action='store', type=str, default=None,
					help = 'only output those clusters which contain the word FOCUS')
	parser.add_argument('-m','--minimal_cluster_size',
					action='store', type=int, default=2,
					help = 'minimal size in clusters (default: %(default)s, ' \
								'as 1 analogy implies at least 2 ratios in a cluster)')
	parser.add_argument('-M','--maximal_cluster_size',
					action='store', type=int, default=None,
					help = 'maximal size of clusters output (default: no limit)')
	parser.add_argument('-V', '--verbose',
					action='store_true', default=False,
					help='runs in verbose mode')
	return parser.parse_args()

###############################################################################

if __name__ == '__main__':
	options = read_argv()
	t1 = time.time()
	if options.verbose: print('# Reading words and computing feature vectors (features=characters)...', file=sys.stderr)
	words_and_vectors = Words2Vectors.FeatureVectors(Words2Vectors.Words(), char_features=True)
	distinguishable_words_and_vectors = words_and_vectors.get_distinguishables()
	if options.verbose:
			print('# Clustering strings according to their feature vectors...', file=sys.stderr)
			print(f'#\t- min cluster size: {options.minimal_cluster_size}', file=sys.stderr)
			print(f'#\t- max cluster size: {options.maximal_cluster_size}', file=sys.stderr)
	list_of_clusters = ListOfClusters.fromVectors(distinguishable_words_and_vectors,
			minimal_size=options.minimal_cluster_size,
			maximal_size=options.maximal_cluster_size,
			focus=options.focus)
	if options.verbose: print('# Adding indistinguishable strings...', file=sys.stderr)
	list_of_clusters.set_indistinguishables(words_and_vectors.indistinguishables)
	if options.verbose: print('# Checking distance constraint...', file=sys.stderr)
	list_of_strclusters = ListOfStrClusters.fromListOfClusters(clusters=list_of_clusters,
			minimal_size=options.minimal_cluster_size,
			maximal_size=options.maximal_cluster_size)
	print(list_of_strclusters)
	if options.verbose: print('# Processing time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
