#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse

from nlg.Vector.Vectors import Vectors
from nlg.Cluster.Cluster import ListOfClusters
from nlg.Cluster.Words2Clusters.StrCluster import ListOfStrClusters

###############################################################################

__author__ = 'Fam Rashel <fam.rashel@fuji.waseda.jp>'
__date__, __version__ = '03/09/2020', '0.10' # Creation
__description__ = 'Produce analogical clusters from a list of vectors.'

###############################################################################

def read_argv():
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """
	%(prog)s  <  FILE_OF_VECTORS
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
	parser.add_argument('-V', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')
						
	return parser.parse_args()

def convert_time(duration):
	"""
	Convert time data (s) to human-friendly format
	"""
	m, s = divmod(round(duration), 60)
	h, m = divmod(m, 60)
	hms = "%d:%02d:%02d" % (h, m,s)
	return hms

###############################################################################

if __name__ == '__main__':
	options = read_argv()
	t_start = time.time()
	if options.verbose: print('# Reading words and their vector representations...', file=sys.stderr)
	vectors = Vectors.fromListOfVectors(lines=sys.stdin)
	distinguishable_vectors = vectors.get_distinguishables()
	if options.verbose:
		print('# Clustering the words according to their feature vectors...', file=sys.stderr)
		print(f'#\t- min cluster size: {options.minimal_cluster_size}', file=sys.stderr)
		print(f'#\t- max cluster size: {options.maximal_cluster_size}', file=sys.stderr)
	list_of_clusters = ListOfClusters.fromVectors(distinguishable_vectors,
			minimal_size=options.minimal_cluster_size,
			maximal_size=options.maximal_cluster_size,
			focus=options.focus)
	if options.verbose: print('# Add the indistinguishables...', file=sys.stderr)
	list_of_clusters.set_indistinguishables(vectors.indistinguishables)
	if options.verbose: print('# Checking distance constraints...', file=sys.stderr)
	list_of_strclusters = ListOfStrClusters.fromListOfClusters(clusters=list_of_clusters,
			minimal_size=options.minimal_cluster_size,
			maximal_size=options.maximal_cluster_size)
	print(list_of_strclusters)
	
	if options.verbose: print(f'# {os.path.basename(__file__)} - Processing time: {(convert_time(time.time() - t_start))}', file=sys.stderr)
