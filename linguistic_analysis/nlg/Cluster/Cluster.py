#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import doctest
import time
import collections
import random
import numpy as np

import nlg.NlgSymbols as NlgSymbols
from nlg.Cluster.Words2Clusters.Indistinguishables import Indistinguishables
from _fast_distance import fast_distance, init_memo_fast_distance, memo_fast_distance, memo_fast_similitude

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '24/04/2015', '1.0'			# Creation from strnlgclu.dist.
__date__, __version__ = '15/05/2015', '1.1'			# New design to work as superclass for strnlgclu.
__date__, __version__ = '17/06/2015', '1.2'			# Sort ratios in clusters by closeness to median ratio.
													# Production of the annotated lexicon contained in a cluster file.
__date__, __version__ = '20/12/2015', '1.3'			# Added equality between clusters and intersection between cluster files.
__date__, __version__ = '20/02/2016', '1.4'			# Added option clean.
													# Made sort_by_median_ratio faster by using sampling.
__date__, __version__ = '13/02/2017', '1.5'			# Corrected mistake in median computation.
__date__, __version__ = '24/08/2017', '1.6'			# Added Indistinguishables class.
__description__ = 'Classes for analogical clusters and files of analogical clusters.'

__verbose__ = False
__trace__ = False

__visualization__ = False
__cluster_size__ = None

###############################################################################

def visualize(dist, nlg):
	import matplotlib
	matplotlib.use('TKAgg')
	import matplotlib.pyplot as plt
	distrib = collections.defaultdict(int)
	length = len(dist)
	for str in dist:
		distrib[dist[str]/length] += 1
	plt.plot(list(distrib.keys()), list(distrib.values()), 'o')
	print('Cluster: %s' % nlg, file=sys.stderr)
	plt.title('Number of strings with same combined similarity')
	plt.xlabel('Combined similarity')
	plt.ylabel('Number of strings')
	plt.show()

###############################################################################

def sort_by_median_ratio(strings):
	"""
	Sort the strings in a set of strings, median strings first.
	The combined edit distance with all strings in the set is used.
	>>> sort_by_median_ratio(['a', 'ab', 'abcd', 'abcdef'])
	['abcd', 'ab', 'a', 'abcdef']
	>>> sort_by_median_ratio(['a : a', 'aa : aa', 'aaaa : aaaa'])
	['aa : aa', 'a : a', 'aaaa : aaaa']
	>>> sort_by_median_ratio(['a : aa', 'aa : aaa', 'aaa : aaaa', 'aaaa : aaaaa', 'aaaaa : aaaaaa'])[0]
	'aaa : aaaa'
	>>> sort_by_median_ratio(['', 'go', 'brew', 'study' , 'overlook', 'understand'])
	['', 'go', 'brew', 'study', 'overlook', 'understand']
	"""
	dist = collections.defaultdict(int)
	# If strings contains too many strings,
	# shuffling the string and then considering only the first 100 members
	# is the same as taking a sample of 100 members.
	# Caution: this introduces randomness,
	# and thus the results may not be the same for two subsequent runs of the program.
	random.shuffle(strings)
	# If strings contains too many strings,
	# we compare each member of strings
	# to only a sample of 100 other members.
	for	A in strings[:100]:
		init_memo_fast_distance(A)
		for B in strings:
			dist[B] += memo_fast_distance(B)
	sum_val, length = sum(dist.values()), len(dist)
	# Equivalent to take the average of all similarities and
	# sort by closeness to average similarity.
	avg_dist = dict( (key, dist[key]) for key in dist )
	result = sorted(avg_dist, key=avg_dist.get)
	if __visualization__ and __trace__: visualize(dist, NlgSymbols.conformity.join(result[:2]))
	return result

###############################################################################

class Cluster(list):
	"""
	Class for an analogical cluster.
	"""

	def __init__(self, ratios=[]):
		"""
		Externally,
			a cluster is one line of ratios separated by ::.
			A ratio is a pair of strings separated by :.
		Internally,
			a cluster is a list of ratios of objects.
			A ratio is a list with two elements.
		"""
		assert 2 <= len(ratios), 'Invalid cluster: less than 2 ratios.'
		# clu is an enumerable, i.e., a list, a tuple, a set...
		list.__init__(self, ratios)
		# States of the object.
		self.is_sorted = False
		self.is_normalized = False
		self.is_analogy = False
		self.attributes_set = False
		# Check whether the cluster is an analogy, i.e. a cluster of only 2 ratios.
		if 2 == len(self): self.is_analogy = True
		
	@classmethod
	def fromFile(cls, line):
	
		def RatioFromFile(line):
			return list(word.strip() for word in line.strip().split(NlgSymbols.ratio))
	
		return cls(list(RatioFromFile(subline) for subline in line.split(NlgSymbols.conformity)))
	
	def clean(self):
		# Sort and normalize.
		if clean:
			self.sort()
			self.normalize()
			self.set_attributes()

	def normalize(self):
		"""
		Exchange As and Bs so that As are smaller than Bs.
		"""
		if self.is_normalized: return
		A, B = self[0][0], self[0][1]
		if len(B) < len(A):
			self[:] = [ [ratio[1], ratio[0]] for ratio in self ]
		if 2 == len(self):
			A, B, C = self[0][0], self[0][1], self[1][0]
			init_memo_fast_distance(A)
			if memo_fast_similitude(B) < memo_fast_similitude(C):
				self[0][1], self[1][0] = self[1][0], self[0][1]
		self.is_normalized = True

	def sort(self):
		"""
		Sort the ratios in the cluster according to closeness to median ratio,
		i.e., the ratio with the least distance to all other ratios.
		"""
		if self.is_sorted: return
		ABs = [ NlgSymbols.ratio.join(ratio) for ratio in self ]
		self[:] = [ str.split(NlgSymbols.ratio) for str in sort_by_median_ratio(ABs) ]
		self.is_sorted = True
	
	def set_attributes(self):
		"""
		Compute the attributes of a cluster.
		At the moment, there are the following attributes:
			1. the distance between As and Bs;
			2. the difference of multisets of symbols in As and in Bs.
			3. the difference of multisets of symbols in Bs and in As.
		"""
		if self.attributes_set: return
		self.normalize()
		Attributes = collections.namedtuple('Attributes', ['distance', 'left_diff', 'right_diff'])
		A, B = self[0][0], self[0][1]
		multisetA, multisetB = collections.Counter(A), collections.Counter(B)
		self.attributes = Attributes(fast_distance(A, B), multisetA - multisetB, multisetB - multisetA)
		self.attributes_set = True

	def __eq__(self, other):
		"""
		Testing for equality with ==.
		Caution: this test is not exact as it tests only the first analogy (median strings) between the two clusters.
		>>> Cluster.fromFile('jouer : jouais :: trouver : trouvais') == Cluster.fromFile('chantais : chanter :: portais : porter :: regardais : regarder')
		False
		>>> Cluster.fromFile('a : abc :: d : dbc') == Cluster.fromFile('a : acb :: d : dcb')
		False
		>>> Cluster.fromFile('ab : aabb :: aaabbb : aaaabbbb') == Cluster.fromFile('ab : abab :: abab : ababab :: ababab : abababab')
		False
		
		"""
		self.set_attributes()
		other.set_attributes()
		if self.attributes == other.attributes:
			for pair1 in self:
				for pair2 in other:
					if not fast_distance(pair1[0], pair2[0]) == fast_distance(pair1[1], pair2[1]):
						return False
			return True
		else:
			return False

	def AB_list(self):
		"""
		Returns two lists: the list of As and the list of Bs.
		"""
		return list(zip(*self))

	def filter_words(self, words, delete=True):
		if delete:
			self[:] = [ pair for pair in self if pair[0] not in words and pair[1] not in words ]
		else:
			self[:] = [ pair for pair in self if pair[0] in words and pair[1] in words ]

	def is_empty_intersection(self, other):
		selfAs, selfBs, otherAs, otherBs = self.AB_list(), other.AB_list()
		return selfAs.intersection(otherAs) == emptyset() \
		   and selfAs.intersection(otherBs) == emptyset() \
		   and selfBs.intersection(otherAs) == emptyset() \
		   and selfBs.intersection(otherBs) == emptyset()

	def all_distances_correct(self):
		length = len(self)
		As, Bs = self.AB_list()
		for i in range(length):
			for j in range(i+1,length):
				if fast_distance(As[i],As[j]) != fast_distance(Bs[i],Bs[j]) or \
					fast_distance(As[i],Bs[i]) != fast_distance(As[j],Bs[j]):
						return False
		return True

	def no_duplicate_words(self):
		As, Bs = self.AB_list()
		return len(As) == len(set(As)) and len(Bs) == len(set(Bs)) and all(A != B for (A,B) in self)
	
	def discard_duplicate_words(self):
		As, Bs = self.AB_list()
		A_counts, B_counts = collections.Counter(As), collections.Counter(Bs)
		self[:] = [ [A, B] for [A, B] in self if A_counts[A] == 1 and B_counts[B] == 1 ]
	
	def look_up(self, string):
		As, Bs = self.AB_list()
		return string in As or string in Bs
	
	def __repr__(self):
		As, Bs = self.AB_list()
		bad_cluster_mark = ''
		if len(As) == len(set(As)) and len(Bs) == len(set(Bs)) and all(A != B for (A,B) in self):
			bad_cluster_mark = ''
		else:
			if self.all_distances_correct():
				bad_cluster_mark = 'OOO '
			else:
				bad_cluster_mark = 'XXX '
		firstcol = ''
		if __cluster_size__ != None:
			firstcol = '%d\t' % len(self)
		return firstcol + bad_cluster_mark + \
			NlgSymbols.conformity.join( NlgSymbols.ratio.join(ratio)
				for ratio in self[:__cluster_size__] )

###############################################################################

class ListOfClusters(list):
	"""
	Class for a list of clusters,
		possibly with a list of indistinguishable objects.
	"""

	def __init__(self, clusters=[], indistinguishables=[]):
		"""
		After processing,
			comments and empty lines will be lost,
			but indistinguishable objects will be kept.
		A line of undistinguishable objects is a commented line consisting of two objects separated by ==.
		A line of cluster consists of ratios separated by :: (internal representation: list).
			A ratio consists of two objects separated by : (internal representation: list of two objects).
		"""
		list.__init__(self, clusters)
		if indistinguishables == [] and len(clusters) != 0 and hasattr(clusters[0], 'indistinguishables'):
				indistinguishables = clusters[0].indistinguishables
		self.set_indistinguishables(indistinguishables)
		self.is_sorted = False

	@classmethod
	def fromFile(cls, file=sys.stdin, read_indistinguishables=True):
		"""
		Class method: read clusters from a file.
		A file of clusters is made of
			lines of undistinguishable objects,
			a sperator line (a commented line with no == on it).
			lines of clusters.
		"""
		if read_indistinguishables:
			indistinguishables = Indistinguishables.fromFile(file)
		else:
			indistinguishables = Indistinguishables([])
		clusters = [ Cluster.fromFile(line) for line in file ]
		return cls(clusters=clusters, indistinguishables=indistinguishables)
	
	@classmethod
	def fromVectors(cls, vectors, **kwargs):
		"""
		Class method to build clusters from vectors.
		"""
		from .Words2Clusters.nlgclu import NlgClusteringFromVectors
		indistinguishables = kwargs['indistinguishables'] if hasattr(kwargs, 'indistinguishables') else []
		clusterfile = NlgClusteringFromVectors(vectors, **kwargs)
		return cls(clusters=clusterfile, indistinguishables=indistinguishables)

	def clean(self):
		if self.is_sorted: return
		self[:] = sorted(self, key=len, reverse=True)
		self.is_sorted = True
	
	def statistics(self):
		eqv_sizes = collections.defaultdict(int)
		for A in list(self.indistinguishables.keys()):
			eqv_sizes[len(self.indistinguishables[A])] += 1
		clu_sizes = collections.defaultdict(int)
		for clu in self:
			clu_sizes[len(clu)] += 1
		print('# Distribution of equivalent objects')
		print('# Column 1: cardinal')
		print('# \tColumn 2: number of equivalence sets with the same cardinal')
		print('\n'.join( '%d\t%d' % (size, eqv_sizes[size]) for size in sorted(eqv_sizes.keys()) ))
		print('# Distribution of cluster sizes')
		print('# Column 1: size')
		print('# \tColumn 2: number of clusters with that size')
		print('\n'.join( '%d\t%d' % (size, clu_sizes[size]) for size in sorted(clu_sizes.keys()) ))
		if __visualization__:
			import matplotlib.pyplot as plt
			if 0 < len(eqv_sizes):
				plt.figure(1)
				plt.title('Distribution of equivalence sets by cardinal')
				plt.xlabel('Cardinal')
				plt.ylabel('Number of equivalence sets with same cardinal')
				XY = sorted(eqv_sizes.items())
				X, Y = list(zip(*XY))
				plt.plot(X, Y, marker='o', linestyle=':', color='k')	# r, b, g, c, y, w for colors, k is black.
			plt.figure(2)
			plt.title('Distribution of clusters by size')
			plt.xlabel('Size (log scale)')
			plt.ylabel('Number of clusters with same size (log scale)')
			plt.xscale('log')
			plt.yscale('log')
			XY = sorted(clu_sizes.items())
			X, Y = list(zip(*XY))
			plt.plot(X, Y, marker='o', linestyle='', color='k')
			plt.show()
		print('# Number of cluster with duplicate words:     %d' % [ clu.no_duplicate_words() for clu in self ].count(False))
		print('# Number of cluster with incorrect distances: %d' % [ clu.all_distances_correct() for clu in self ].count(False))

	def intersection_size(self, other):
		"""
		Returns the number of equal clusters in self and other.
		The comparison is done on the abstract level,
			not by comparing the strings inside the cluster.
		See function __eq__ in class Cluster.
		"""
		for clu in self: clu.set_attributes()
		for clu in other: clu.set_attributes()
		n = 0
		for clu1 in self:
			for clu2 in other:
				if clu1 == clu2:
					n += 1
#					break
		return n
	
	def filter_words(self, filename, delete=True):
		words = open(filename, mode='r').readlines()
		words = set([ word.rstrip('\n') for word in words ])
		for clu in self:
			clu.filter_words(words, delete)
		self[:] = [ clu for clu in self if 1 < len(clu) ]

	def annotated_lexicon(self):
	
		def marked_str(str):
			return '<' + str + '>'

		def sided_name(ratio, left=True):
			if left:
				return NlgSymbols.ratio.join([marked_str(ratio[0]), ratio[1]])
			else:	# Right
				return NlgSymbols.ratio.join([ratio[0], marked_str(ratio[1])])

		lexicon = collections.defaultdict(set)
		for clu in self:
			median = clu[0]	# The cluster should have been sorted by closeness to median ratio.
			for ratio in clu:
				lexicon[ratio[0]].add(sided_name(median, left=True))
				lexicon[ratio[1]].add(sided_name(median, left=False))
		return lexicon

	def paradigm_lexicon(self):
		# We suppose that the clusters have been normalized.
		lexicon = collections.defaultdict(set)
		for clu in self:
			for ratio in clu:
				A, B = ratio[0], ratio[1]
				lexicon[A].add(B)
				lexicon[B].add(A)
		return lexicon
	
	def set_indistinguishables(self, indistinguishables):
		self.indistinguishables = indistinguishables
		for cluster in self:
			cluster.indistinguishables = self.indistinguishables

	def _indistinguishables_repr(self):
		s = ''
		if self.indistinguishables != None:
			for A in sorted(self.indistinguishables.keys()):
				for B in sorted(self.indistinguishables[A]):
					if A != B:
						s += '%s %s%s%s\n' % (NlgSymbols.comment, A, NlgSymbols.duplicate, B)
		return s

	def __repr__(self):
		# Print a file of analogical clusters.
		# For readability, first sort the clusters by decreasing sizes.
		self[:] = sorted(self, key=len, reverse=True)
		return '\n'.join(
			( [] if self.indistinguishables == [] else ['{}'.format(self.indistinguishables) ]) +
			[ '{}'.format(cluster) for cluster in self ]
			)

###############################################################################

def read_argv():

	from optparse import OptionParser
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """%prog  <  FILE_OF_CLUSTERS
	
	Reorder clusters by decreasing sizes and by ratios closest to median ratio.
	"""

	parser = ArgumentParser(version=this_version, description=this_description, usage=this_usage)
	parser.add_argument('--discard_duplicate_words',
                  action='store_true', default=False,
                  help='delete ratios which contain a word repeated in the cluster')
	parser.add_argument('--delete_words',
                  action='store', type='str', default=None,
				  metavar='FILE',
                  help='delete all pairs in all clusters that contain a word ' \
				  		'from the list of words given in the file FILE passed as argument')
	parser.add_argument('--keep_words',
                  action='store', type='str', default=None,
				  metavar='FILE',
                  help='retain only pairs in clusters where both words are ' \
				  		'from the list of words given in the file FILE passed as argument')
	parser.add_argument('-p', '--paradigm',
                  action='store_true', default=False,
                  help='outputs the lexicon contained in the clusters with paradigms')
	parser.add_argument('-S', '--statistics',
                  action='store_true', dest='statistics', default=False,
                  help='graph distribution of cluster sizes')
	parser.add_argument('-s', '--cluster-size',
                  action='store', type=int, default=None,
				  metavar='N',
                  help='print only the first N ratios in the cluster, median strings first, ' \
				  		'print also the number of ratios in the cluster as a first column ' \
				  		'(default is %default, i.e., all ratios, no number of ratios displayed)')
	parser.add_argument('-C', '--clean',
                  action='store_true', default=False,
                  help='clean the cluster file, i.e., ' \
				  		'sort clusters by decreasing sizes and ' \
				  		'normalize them (i.e., As are shorter than Bs).')
	parser.add_argument('-u', '--visualization',
                  action='store_true', default=False,
                  help='visualize distribution of strings by combined distances for each cluster')
	parser.add_argument('-V', '--verbose',
                  action='store_true', default=False,
                  help='runs in verbose mode')
	return parser.parse_args()

###############################################################################

def _test():
	import doctest
	doctest.testmod()
	sys.exit(0)

if __name__ == '__main__':
	options = read_argv()
	if options.test: _test()
	__verbose__ = options.verbose
	__visualization__ = options.visualization
	__cluster_size__ = options.cluster_size
	t1 = time.time()
	clusterfile = ListOfClusters.fromFile()
	if options.paradigm:
		lexicon = clusterfile.paradigm_lexicon()
		for key in sorted(lexicon, key=lambda x: (len(lexicon[x]), x), reverse=True):
			print('%s: { %s }' % (key, ', '.join( lexicon[key] )))
	elif options.statistics:
		clusterfile.statistics()
	else:
		if options.discard_duplicate_words:
			for clu in clusterfile:
				clu.discard_duplicate_words()
		if None != options.delete_words:
			clusterfile.filter_words(options.delete_words, delete=True)
		if None != options.keep_words:
			clusterfile.filter_words(options.keep_words, delete=False)
		clusterfile.clean()
		print(clusterfile)
	if __verbose__: print('# Processing time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
	
	
	
