#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import collections
import itertools

import nlg.NlgSymbols as NlgSymbols

from nlg.Cluster.Cluster import Cluster, ListOfClusters
from nlg.Cluster.Words2Clusters.SquareMatrix import SquareMatrix
from _fast_distance import fast_distance, init_memo_fast_distance, memo_fast_distance

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '05/07/2013', '1.0'
__date__, __version__ = '01/09/2014', '2.0'
__date__, __version__ = '15/05/2015', '2.1'		# Import NlgCluster. Inherit from NlgClu.
__date__, __version__ = '06/06/2015', '2.2'		# Import SquareMatrix and use it in cluster_to_matrix.
__date__, __version__ = '26/02/2016', '2.3'		# Improved speed in horizontal splitting.
__description__ = 'The clusters output by nlgclu.py do not necessarily meet the distance constraint for analogies between strings of symbols. ' \
					'This program verifies the distance constraint on analogical clusters output by nlgclu.py. ' \
					'As a result, some clusters will be further split into smaller clusters to meet the distance constraint.' \
					'The output format is the same as the input format, i.e., the output format of nlgclu.py'

__verbose__			= False			# Gives information about timing, etc. to the user.
__trace__			= False			# To be used by the developper for debugging.
__visualization__ 	= False			# Visualization of matrices before and after vertical splitting of clusters.

__minimal_size__	= 2				# Minimal size of clusters output. Two is the minimal to get one analogy.
__maximal_size__	= None			# Maximal size of clusters output. None for no limit.

###############################################################################

__no_horizontal_splitting__	= False
__no_vertical_splitting__	= False
__no_discard_duplicates__	= False

###############################################################################

def common_substring(A, B):
	"""
	>>> common_substring('dreux', 'radeaux')
	False
	>>> common_substring('oin', 'iona')
	False
	>>> common_substring('muslim', 'mursil')
	False
	>>> common_substring('aslama', 'arsala')
	False
	>>> common_substring('muslim', 'aslama')
	True
	>>> common_substring('mursil', 'arsala')
	True
	>>> common_substring('', '')
	True
	>>> common_substring('ab', '')
	True
	"""
	setA, setB = set(A), set(B)
	multiA, multiB = collections.Counter(A), collections.Counter(B)
	union, inter = (setA | setB), (setA & setB)
	if __trace__: print('in common_substring: union = %s, inter = %s' % (union, inter), file=sys.stderr)
	for c in union:
		if c in inter:
			if multiA[c] != multiB[c]:
				A, B = A.replace(c,''), B.replace(c,'')
		else:
			A, B = A.replace(c,''), B.replace(c,'')
	if __trace__: print(A, B, file=sys.stderr)
	return A == B

###############################################################################

class StrCluster(Cluster):
	"""
	Class for analogical clusters of strings.
	The distance constraints should be verified.
	"""

	def is_of_length_in_range(self, minsize=__minimal_size__, maxsize=__maximal_size__):
		length = len(self)
		return minsize <= length and (maxsize == None or length <= maxsize)


	def discrepancies(self):
		result = collections.defaultdict(int)
		for i, [A, B] in enumerate(self):
			for C, D in self[i+1:]:
				if fast_distance(A,C) != fast_distance(B,D):
					if __trace__: print('# d(%s, %s) = %d != %d = d(%s, %s)...' % \
						(A,C,fast_distance(A,C),fast_distance(B,D),B,D), file=sys.stderr)
					result[A,B] += 1
					result[C,D] += 1
		return result
	
	def cluster_to_matrix(self):
		"""
		Builds a matrix representing the consistency of distances between ratios in a cluster.
		If d(A_i,B_i) == d(dA_j, B_j)
			then we fill the cell (i, j) in the matrix with a 0,
			else with a 1.
		"""
		length = len(self)
		labels = [ (NlgSymbols.ratio).join(ratio) for ratio in self ]
		matrix = [ [ 1 for j in range(length) ] for i in range(length) ]
		for i, [A, B] in enumerate(self):
			dA = dict()
			init_memo_fast_distance(A)
			matrix[i][i] = 0
			for C, _ in self[i+1:]:
				dA[C] = memo_fast_distance(C)
			init_memo_fast_distance(B)
			for xj, [C, D] in enumerate(self[i+1:]):
				j = i + 1 + xj
				dBD = memo_fast_distance(D)
				if __trace__: print('# %s : %s :: %s : %s, d(%s, %s) = %d %s %d = d(%s, %s)' % \
						(A, B, C, D, A, C, dA[C], '==' if dA[C]==dBD else '=/=', dBD, B, D), file=sys.stderr)
				if (dA[C] == dBD):	 # For x == False, this will be: dAC != dBD
					matrix[i][j] = matrix[j][i] = 0
		return SquareMatrix(matrix, labels=labels, visualization=__visualization__)


	def split_by_horizontal_distance(self, indistinguishables):

		if __no_horizontal_splitting__:
			if __trace__: print('# No horizontal splitting...', file=sys.stderr)
			yield self
			raise StopIteration
		if __trace__: print('# hcluster = %s' % self, file=sys.stderr)
		subclusters = collections.defaultdict(list)
		for Aprime, Bprime in self:
			# Include all the possible equivalent strings.
			equivA = indistinguishables.all(Aprime)
			equivB = indistinguishables.all(Bprime)
			if __trace__: print('equivA = %s, equivB = %s' % (equivA, equivB), file=sys.stderr)
			for A, B in itertools.product(equivA, equivB):
#				if common_substring(A,B):		# This was a heuristic! May be theoretically not valid.
				dAB = fast_distance(A,B)
				if __trace__: print('d(%s, %s) = %d' % (equivA, equivB, dAB), file=sys.stderr)
				subclusters[dAB].append((A,B))
		if __trace__: print('# subclusters = %s' % subclusters, file=sys.stderr)
		if 0 < len(subclusters):		# Split into subclusters by distance.
			for dAB in subclusters:	# Then insert each subcluster.
				if __minimal_size__ <= len(subclusters[dAB]):	# The subcluster should contain at least 2 ratios to make a valid cluster or be bigger than min size.
					if __trace__: print('subclusters[%d] = %s' % (dAB, subclusters[dAB]), file=sys.stderr)
					result = StrCluster( subclusters[dAB] )
#					if not result.all_distances_correct():
#						print 'HORIZONTAL %s' % result
					yield result

	def apply_discard_duplicate_words(self):
		if __no_discard_duplicates__:
			if __trace__: print('# No discarding of duplicate words...', file=sys.stderr)
			yield self
			raise StopIteration
		self.discard_duplicate_words()
		if __minimal_size__ <= len(self):	# The cluster should contain at least 2 ratios to make a valid cluster or be bigger than min size.
			yield self

	def split_by_vertical_distance(self):
		if __no_vertical_splitting__:
			if __trace__: print('# No vertical splitting...', file=sys.stderr)
			yield self
			raise StopIteration
		if __trace__: print('# Entering split_by_vertical distance (size=%d)...' % len(self), file=sys.stderr)
		if __trace__: print('# vcluster = %s' % self, file=sys.stderr)
		for indices in self.cluster_to_matrix().covering_cliques(minsize=__minimal_size__):
			if __trace__: print('cluster = %s' % \
				( (NlgSymbols.conformity).join( '%d: %s%s%s' % \
					(i, ratio[0], NlgSymbols.ratio, ratio[1]) for (i, ratio) in enumerate(self) ) ), file=sys.stderr)
			if __trace__: print('# indices = %s' % indices, file=sys.stderr)
			if __minimal_size__ <= len(indices):	# The subcluster should contain at least 2 ratios to make a valid cluster or be bigger than min size.
				result = StrCluster( [self[i] for i in indices] )
#				if not result.all_distances_correct():
#					print 'VERTICAL %s' % result
				yield result

	def distance_constraint(self, indistinguishables):
		for hcluster in self.split_by_horizontal_distance(indistinguishables):
			for vcluster in hcluster.split_by_vertical_distance():
				for cluster in vcluster.apply_discard_duplicate_words():
					yield vcluster

	def gamma_hypothesis(self):
		# Checking the gamma hypothesis: \gamma(A,B,C,D) == \gamma(B,A,D,C) == \gamma(C,D,A,B) == \gamma(D,C,B,A)
		# Y. Lepage, De l'analogie rendant compte..., thèse d'habilitation, 2003, p. 145--147.
		# Seems to be always verified by clusters output by this program.
		if __verbose__: print('# Checking gamma constraint...', file=sys.stderr)
		if len(cluster) == 2:
			A, B, C, D = cluster[0][0], cluster[0][1], cluster[1][0], cluster[1][1]
			lenA, lenB, lenC, lenD = len(A), len(B), len(C), len(D)
			init_memo_fast_distance(A)
			dAB, dAC = memo_fast_distance(B), memo_fast_distance(C)
			sAB, sAC = lenA + lenB - 2 * dAB, lenA + lenC - 2 * dAC
			init_memo_fast_distance(D)
			dDB, dDC = memo_fast_distance(B), memo_fast_distance(C)
			sDB, sDC = lenD + lenB - 2 * dDB, lenD + lenC - 2 * dDC
			gammaA, gammaB, gammaC, gammaD = sAB + sAC - lenA, sAB + sDB - lenB, sAC + sDC - lenC, sDB + sDC - lenD
			if gammaA == gammaB == gammaC == gammaD:
				yield cluster
		else:
			yield cluster

###############################################################################

class ListOfStrClusters(ListOfClusters):

#	def __init__(self, strclusters=[]):
#		list.__init__(strclusters)
#
	@classmethod
	def fromFile(cls, file=sys.stdin, **kwargs):
		return cls.fromListOfClusters(ListOfClusters.fromFile(file))

	@classmethod
	def fromCluster(cls, cluster, indistinguishables=[]):
		return cls(clusters=[ strcluster for strcluster in StrCluster(cluster).distance_constraint(indistinguishables) ], indistinguishables=indistinguishables)

	@classmethod
	def fromListOfClusters(cls, clusters, **kwargs):
		# Generate a list of lists of strclusters
		# from a list of cluster (each cluster generates a possibly empty list of strcluters,
		# i.e. a strclusterfile).
		list_of_lists_of_strclusters = [ ListOfStrClusters.fromCluster(cluster, clusters.indistinguishables) for cluster in clusters ]
		# Flatten the list of list of strclusters
#		strclusters  = [ strcluster for list_of_strclusters in list_of_lists_of_strclusters for strcluster in list_of_strclusters ]
		strclusters  = itertools.chain.from_iterable(list_of_lists_of_strclusters)
		# Filter the strclusters by size.
		minimal_size = kwargs['minimal_size']
		maximal_size = kwargs['maximal_size']
		list_of_strclusters  = [ strcluster for strcluster in strclusters if strcluster.is_of_length_in_range(minimal_size, maximal_size) ]
		return cls(list_of_strclusters)

###############################################################################

def read_argv():

	from argparse import ArgumentParser
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """%(prog)s  <  FILE_OF_CLUSTERS
	"""

	parser = ArgumentParser(version=this_version, description=this_description, usage=this_usage)
	parser.add_argument('-m','--mimimal_cluster_size',
						action='store',dest='minsize', type=int, default=2,
						help = 'minimal size of clusters output (default: %(default)s, ' \
								'to output all possible clusters, because ' \
								'there should be at least 2 lines in a cluster to form at least one analogy)')
	parser.add_argument('-M','--maximal_cluster_size',
						action='store',dest='maxsize', type=int, default=None,
						help = 'maximal size of clusters output (default: %(default)s)')
	parser.add_argument('-V', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')
	parser.add_argument('-u', '--visualize-matrix',
                  action='store_true', dest='visualization', default=False,
                  help='visualizes matrices before and after vertical splitting of clusters')
				  
	parser.add_argument('--no-horizontal-splitting',
                  action='store_true', dest='no_horizontal_splitting', default=False,
                  help='(for developper only) do not apply horizontal splitting')
	parser.add_argument('--no-discard-duplicates',
                  action='store_true', dest='no_discard_duplicates', default=False,
                  help='(for developper only) do not apply discarding of duplicate words')
	parser.add_argument('--no-vertical-splitting',
                  action='store_true', dest='no_vertical_splitting', default=False,
                  help='(for developper only) do not apply vertical splitting')
	return parser.parse_args()

###############################################################################

def string_cluster_file(file=sys.stdin, minimal_size=__minimal_size__, maximal_size=__maximal_size__):
	clunbr, output_clunbr = 0, 0
	for indistinguishables, cluster in ListOfClusters.fromFile(file):
		cluster = StrCluster(cluster)
		clunbr += 1
		msg = '\r# Checking distance constraint (cluster number = %d, size = %d)...\t\t'
		if __verbose__: print(msg % (clunbr, len(cluster)), end=' ', file=sys.stderr)
		for subcluster in cluster.distance_constraint(cluster.indistinguishables):
			if subcluster.is_of_length_in_range(minimal_size, maximal_size):
				yield subcluster
				output_clunbr += 1
	if __verbose__: print('', file=sys.stderr)
	if __verbose__: print('# Number of clusters output: %d' % output_clunbr, file=sys.stderr)

if __name__ == '__main__':
	options = read_argv()
	__verbose__ = options.verbose
	__visualization__ = options.visualization
	__no_horizontal_splitting__ = options.no_horizontal_splitting
	__no_discard_duplicates__ = options.no_discard_duplicates
	__no_vertical_splitting__ = options.no_vertical_splitting
	if options.minsize < 2:
		print('Minimal size of cluster should be bigger than 2.', file=sys.stderr)
		sys.exit(-1)
	if options.maxsize != None and options.maxsize < 2:
		print('Maximal size of cluster should be bigger than 2.', file=sys.stderr)
		sys.exit(-1)
	__minimal_size__ = options.minsize
	__maximal_size__ = options.maxsize
	t1 = time.time()
	print('\n'.join('{}'.format(cluster) for cluster in string_cluster_file() ))
	if __verbose__: print('# Processing time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
	
	
	
