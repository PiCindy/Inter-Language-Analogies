#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Class that provides a heuristic to find cliques in a graph represented by an adjacency matrix
where arcs are represented by 0s and absence of arcs by 1s.
The matrix is of course a symmetric square matrix.
"""

import sys
import time

import operator
import collections
import random
import matplotlib
matplotlib.use('TKAgg') # Comment this line if there is a 'headless backend' error
import matplotlib.pyplot as plt

##############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '18/05/2015', '1.0'		# Creation.
__date__, __version__ = '08/06/2015', '1.1'		# Better criterion for diagonalization.
__date__, __version__ = '26/06/2015', '1.2'		# Inversion of matrix content (0 = distance constraint met).
__date__, __version__ = '29/02/2016', '1.3'		# Solved (??) bug on production of improper cliques:
												# 	in function compactify, replaced
												#		return start, stop  by  return start, next_stop.
												# Renamed variables in that function.
												# Added documentation and comments.
												# Made some functions private.
												# Subcompactify from start to mid for column content.
__date__, __version__ = '15/04/2016', '1.4'		# New algorithm: cliques attempt to cover all indices in the matrix.
__description__ = 'Heuristic to find maximal (large?) cliques in a graph represented by a square matrix.'

__verbose__			= False
__trace__			= False
__visualization__	= False

##############################################################################

class SquareMatrix(list):
	"""
	Class for matrices that are adjacency matrices of graphs.
	CAUTION: arcs are represented with 0s, and absence of arc with 1s.
	A matrix in this class should verify the three following properties:
		1. It is a square matrix (same number of rows and columns).
		2. The first diagonal is filled with 0s.
		3. It is symmetrical (relatively to the first diagonal).
	
	The main purpose of this class is to compute cliques
	which are maximal in some sense.
	"""

	def __init__(self, matrix, labels=None, visualization=False):
		global __visualization__
		__visualization__ = visualization or __visualization__
		dimension = len(matrix)
		assert all( dimension == len(matrix[i]) for i in range(dimension) ), 'Not a square matrix.'
		list.__init__(self, matrix)
		self.dimension = dimension
		self.order = list(range(self.dimension))
		self.labels = labels
#		if labels != None:
#			self.labels = [ label for label in self.labels ]
		if __trace__: print('Labels = %s' % self.labels, file=sys.stderr)
	
	@classmethod
	def random_matrix(cls, dimension):
		"""
		Create a random negative adjacency matrix, i.e.,
			a symmetrical matrix
				of dimension dimension x dimension
				containing random values of 0 or 1
				with the diagonal filled with 0s.
		"""
		A = [ [ random.randint(0,1) for _ in range(options.dimension) ] for _ in range(options.dimension) ]
		# Symmetrize the matrix and fill the main diagonal with 0s.
		for i in range(options.dimension):
			A[i][i] = 0
			for j in range(i+1,options.dimension):
				A[j][i] = A[i][j]
		return SquareMatrix(A)

	def neighbors(self, v, indices=None):
		if indices == None: indices = range(self.dimension)
		return set([ i for i in indices if v != i and self[i][v] == 0 ])
	
	def _Bron_Kerbosch1(self, R, P, X, minsize=2, indices=None):
		"""
		First call:
			Bron_Kerbosch({}, V, {})
		where V is the set of vertices in the graph.
		"""
		if __trace__: print('R = %s, P = %s, X = %s' % (R, P, X), file=sys.stderr)
		if 0 == len(P) and 0 == len(X):
			if minsize <= len(R):
				yield list(R)
		else:
			# Choose a pivot from P u X.
			u = list(P | X)[0]
			P0 = P.copy()
			# repeat for the vertices in P minus the eighbors of u.
			for v in P0.difference_update(self.neighbors(u, indices=indices)):
				N = self.neighbors(v, indices=indices)
				for clique in self._Bron_Kerbosch1(R | set([v]), P & N, X & N, minsize=minsize, indices=indices):
					yield clique
				P.remove(v)
				X.add(v)

	def all_cliques(self, minsize=2):
		for clique in self._Bron_Kerbosch1(set([]), set(range(self.dimension)), set([])):
			yield clique

	def _is_fully_connected(self, i, clique):
		return all( self[i][j] == 0 for j in clique )

	def _expand_clique(self, clique, covered):
		for i in self._indices:
			if self._is_fully_connected(i, clique):
				clique.add(i)
				covered.add(i)
		return clique, covered

	def covering_cliques(self, minsize=2):
		"""
		Output cliques which try to cover all the indices in the matrix given.
		"""
		if __trace__: print('# Covering cliques...', file=sys.stderr)
		if __visualization__: self.visualize()
		# Remember that links are noted by 0, not by 1.
		# So connections gives indirectly the number of links (minus len(self)) of an index.
		connections = { i: sum(self[i]) for i in range(len(self)) }
		# Self.indices will contain the indices in self
		# ranked by decreasing number of connections.
		self._indices = sorted(connections, key=connections.get)
		covered = set([])
		for i in self._indices:
			if i not in covered:
				clique, covered = self._expand_clique(set([i]), covered)
				if minsize <= len(clique):
					yield clique

	def visualize(self, title=None, indices=None):
		"""
		Visualize the matrix by showing white cells for 0s and black cells for 1s.
		For analogical clustering, the indices and ratios (given in labels) are shown.
		"""
		plt.matshow(self, cmap='binary') # cmap= 'Greys', 'hot_r'
		# To show the color bar.
		#plt.colorbar(orientation='horizontal')
		if self.labels != None:
			if indices == None: indices = range(self.dimension)
			plt.yticks(list(range(self.dimension)), [ self.labels[i] + (' %2d' % i) for i in range(self.dimension) ])
#		plt.set_xlabel(self.order)
#		plt.set_ylabel(self.order)
		plt.title(title)
		plt.show()

	def __repr__(self):
		return '\n'.join( '%s' % self[i] for i in range(self.dimension))

##############################################################################

def read_argv():

	from optparse import OptionParser
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = '''%prog
	'''

	parser = OptionParser(version=this_version, description=this_description, usage=this_usage)
	parser.add_option('-m','--mimimal_cluster_size',
						action='store',dest='minsize', type=int, default=2,
						help = 'minimal size of lists of indices (default: %default).')
	parser.add_option('-d','--dimension',
						action='store',dest='dimension', type=int, default=10,
						help = 'dimension of a random matrix (default: %default).')
	parser.add_option('-v', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='run in verbose mode')
	parser.add_option('-u', '--visualize-matrix',
                  action='store_true', dest='visualization', default=False,
                  help='visualize matrices before and after finding large cliques')
						
	(options, args) = parser.parse_args()
	return options, args

##############################################################################

if __name__ == '__main__':
	options, args = read_argv()
	__verbose__ = options.verbose
	__visualization__ = options.visualization
	if __verbose__: print('# Creating data...', file=sys.stderr)
	A = SquareMatrix.random_matrix(options.dimension)
	print(A)
	t1 = time.time()
	if __verbose__: print('# Clustering data...', file=sys.stderr)
	for indices in A.covering_cliques(minsize=options.minsize):
		print(list(indices))
	if __verbose__: print('# Total time: %.2fs' % (time.time() - t1), file=sys.stderr)

	
