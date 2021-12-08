#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import argparse

import nlg.Cluster.Words2Clusters.Words2Vectors as Words2Vectors

from nlg.Cluster.Cluster import ListOfClusters
from nlg.Cluster.Words2Clusters.StrCluster import ListOfStrClusters
from nlg.Grid.Grid import ListOfGrids

###############################################################################

__author__ = 'Fam Rashel <fam.rashel@fuji.waseda.jp>'
__date__, __version__ = '22/08/2017', '0.10' # Creation
__description__ = """
	Produce analogical grids from a list of words (or sequence of words).
"""

###############################################################################

def read_argv():
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """
	%(prog)s  <  FILE_OF_WORDS
	"""

	parser = argparse.ArgumentParser(description=this_description, usage=this_usage)
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
	parser.add_argument('-c','--minimal_grids_cluster_size',
					action='store', type=int, default=3,
					help = 'minimal size in clusters (default: %(default)s, ' \
								'as 1 analogy implies at least 2 ratios in a cluster)')
	parser.add_argument('-d', '--saturation',
						action='store', dest='saturation', type=float, default=0,
						help='min saturation (0 - 1.0) to keep when building grids (default = %(default)s)')
	parser.add_argument('--pretty-print',
						action='store', dest='pretty_print', type=str,
						help='print the grids in the representation for HUMAN instead of SCRIPT format')
	parser.add_argument('-V', '--verbose',
                  action='store_true', dest='verbose', default=False,
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
		print('# Clustering the words according to their feature vectors...', file=sys.stderr)
		print(f'#\t- min cluster size: {options.minimal_cluster_size}', file=sys.stderr)
		print(f'#\t- max cluster size: {options.maximal_cluster_size}', file=sys.stderr)
	list_of_clusters = ListOfClusters.fromVectors(distinguishable_words_and_vectors,
			minimal_size=options.minimal_cluster_size,
			maximal_size=options.maximal_cluster_size,
			focus=options.focus)
	if options.verbose: print('# Add the indistinguishables...', file=sys.stderr)
	list_of_clusters.set_indistinguishables(words_and_vectors.indistinguishables)
	if options.verbose: print('# Checking distance constraints...', file=sys.stderr)
	list_of_strclusters = ListOfStrClusters.fromListOfClusters(clusters=list_of_clusters,
			minimal_size=options.minimal_cluster_size,
			maximal_size=options.maximal_cluster_size)
	# print list_of_strclusters								# Print clusters
	if options.verbose:
		print('# Building grids...', file=sys.stderr)
		print(f'#\t- saturation ≥ {options.saturation:.3f}', file=sys.stderr)
		print('#\t- cluster size ≥ {options.minimal_grids_cluster_size}', file=sys.stderr)
	
	list_of_grids = ListOfGrids.fromClusters(list_of_strclusters, options.saturation)
	if options.pretty_print == '':
		print(list_of_grids.pretty_print())
	elif options.pretty_print is not None:
		grids_pretty_print_file = open(options.pretty_print, 'w')
		grids_pretty_print_file.write(list_of_grids.pretty_print())
		grids_pretty_print_file.close()
	else:
		print(list_of_grids)
	if options.verbose: print('# Processing time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
