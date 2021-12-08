#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse

from collections import namedtuple, defaultdict
from tabulate import tabulate, simple_separated_format
from copy import deepcopy

import nlg.NlgSymbols as NlgSymbols

from nlg.Cluster.Cluster import Cluster
from _nlg import solvenlg

###############################################################################

__author__ = 'Fam Rashel <fam.rashel@fuji.waseda.jp>'

__date__, __version__ = '01/05/2016', '0.10' # Creation
__date__, __version__ = '15/06/2017', '1.00' # Class: NlgGrid
__date__, __version__ = '21/05/2020', '1.01' # Update read_argv() and main() to fit the newest version of Python

__description__ = 'Class for analogical grids'

__verbose__ = False		# Gives information about timing, etc. to the user.
__trace__ = False		# To be used by the developper for debugging.

###############################################################################


class Grid(list):
	"""
	Class for analogical grid for string.
	It is basically list of list of strings where:
		for any i, j, m, n in G's dimension
			G[i][m] : G[i][n] :: G[j][m] : G[j][n]
	"""

	def __init__(self, list_of_rows=[]):
		"""
		Create an empty Grid.
		"""
		list.__init__(self, list_of_rows)
		self._update_term_index()

	@classmethod
	def fromFile(cls, line):
		"""
		Read grid from file with the following format:

			A : B : C : ... :: ...

		"""
		return cls(
			list( col.split(NlgSymbols.ratio) for col in line.strip().split(NlgSymbols.conformity) ))

	def _new(self, cluster):
		"""
		Cast a cluster into an empty Grid
		"""
		A, B = cluster.AB_list()
		self.extend([list (A), list (B)])
		self._update_term_index()

	def _update_term_index(self):
		term_index = dict()
		for i in range(len(self)):
			for j in range(len(self[i])):
				term_index[self[i][j]] = (i, j)
		self.term_index = term_index

	def checkninsert(self, cluster, saturation_threshold):
		"""
		Check and then insert cluster if it can be inserted into the grid.
		
		>>> grid = Grid()
		>>> cluster = Cluster('minum : diminum :: makan : dimakan :: beli : dibeli')
		>>> grid.checkninsert(cluster)
		(True, 'column')
		>>> cluster = Cluster('minum : makan :: minuman : makanan :: meminum : memakan :: diminum : dimakan')
		>>> grid.checkninsert(cluster)
		(True, 'row')
		>>> cluster = Cluster('main : mainan :: minum : minuman :: makan : makanan')
		>>> grid.checkninsert(cluster)
		(True, 'column')
		>>> cluster = Cluster('minum : minumlah :: makan : makanlah :: beli : belilah')
		>>> grid.checkninsert(cluster)
		(True, 'column')
		>>> cluster = Cluster('mainan : main :: makanan : makan :: pukulan : pukul')
		>>> grid.checkninsert(cluster)
		(True, 'column')
		>>> cluster = Cluster('masak : makan :: dimasak : dimakan :: memasak : memakan :: masakan : makanan')
		>>> grid.checkninsert(cluster)
		(True, 'row')
		"""
		if len(self) == 0:
			self._new(cluster)
			return (True, 'column')

		insertable, details = self.check(cluster)
		if insertable:
			if saturation_threshold == 0:
				self.insert(cluster, details[0], details[1], details[2], details[3], details[4])
				if details[0]:
					if __trace__: print('### Inserted - row', details, file=sys.stderr)
					return (True, 'row')
				else:
					if __trace__: print('### Inserted - column',details, file=sys.stderr)
					return (True, 'column')
			else:
				newGrid = deepcopy(self)
				newGrid.insert(cluster, details[0], details[1], details[2], details[3], details[4])
				newGrid.set_attributes()
				if newGrid.attributes[4] >= saturation_threshold:
					self.insert(cluster, details[0], details[1], details[2], details[3], details[4])
					if details[0]:
						if __trace__: print('### Inserted - row', details, file=sys.stderr)
						return (True, 'row')
					else:
						if __trace__: print('### Inserted - column',details, file=sys.stderr)
						return (True, 'column')
				else:
					if __trace__: print('### Insertable but rejected - saturation %.3f < %.3f' % (newGrid.attributes[4], saturation_threshold), file=sys.stderr)
					return (False, None)
		else:
			if __trace__: print('### Rejected', file=sys.stderr)
			return (False, None)

	def check(self, cluster):
		"""
		Check whether a cluster can be inserted into the grid.
		Criteria: at least 2 words (either in As or Bs) appear in the same row or column in the grid.
		"""
		A, B = cluster.AB_list()
		A_exist = False
		B_exist = False
		row = False
		A_Xs = defaultdict(int)
		A_Ys = defaultdict(int)
		B_Xs = defaultdict(int)
		B_Ys = defaultdict(int)

		for A, B in cluster:
			# Both A and B exist in the grid
			if self.term_index.get(A) is not None and self.term_index.get(B) is not None:
				xA, yA = self.term_index.get(A)
				xB, yB = self.term_index.get(B)
				# Commonalities in the position detected
				if xA == xB or yA == yB:
					A_exist = True
					B_exist = True
					if xA == xB: # Located in the same column
						iAs = yA
						iBs = yB
						row = True
					else: # yA == yB; Located in the same row
						iAs = xA
						iBs = xB
					break
				else:
					continue
			# A exists in the grid
			elif self.term_index.get(A) is not None:
				X, Y = self.term_index.get(A)
				A_Xs[X] += 1
				A_Ys[Y] += 1
				if A_Xs.get(X) > 1 or A_Ys.get(Y) > 1:
					A_exist = True
					if A_Xs.get(X) > 1:
						iAs = X
					else:
						iAs = Y
						row = True
					break
				else:
					continue
			# B exists in the grid
			elif self.term_index.get(B) is not None:
				X, Y = self.term_index.get(B)
				B_Xs[X] += 1
				B_Ys[Y] += 1
				if B_Xs.get(X) > 1 or B_Ys.get(Y) > 1:
					B_exist = True
					if B_Xs.get(X) > 1:
						iBs = X
					else:
						iBs = Y
						row = True
					break
				else:
					continue
			# None of A or B exist in the grid
			else:
				continue

		if not A_exist and not B_exist:
			iAs = 0
			iBs = 0
		else:
			if row:
				if not A_exist: iAs = len(self[0])
				elif not B_exist: iBs = len(self[0])
			else:
				if not A_exist: iAs = len(self)
				elif not B_exist: iBs = len(self)

		return (A_exist or B_exist, (row, iAs, A_exist, iBs, B_exist))

	def insert(self, cluster, row, iAs, A_exist, iBs, B_exist):
		"""
		Insert a cluster into the grid:
			1. expand if needed 
			2. search for pivot
			3. glue/insert clusters
		(We assume that we always have the pivot!!)
		"""
		if not A_exist or not B_exist:
			self.expand(row)
		if row:
			if A_exist:
				for A, B in cluster:
					if self.term_index.get(A) is None:
						self.glue(False, len(self), iAs, A, len(self), iBs, B)
					else:
						if self.term_index.get(A)[1] != iAs:
							continue
						else:
							self.term_index[B] = (self.term_index.get(A)[0], iBs)
							self[self.term_index.get(A)[0]][iBs] = B
			else:
				for A, B in cluster:
					if self.term_index.get(B) is None:
						self.glue(False, len(self), iAs, A, len(self), iBs, B)
					else:
						if self.term_index.get(B)[1] != iBs:
							continue
						else:
							self.term_index[A] = (self.term_index.get(B)[0], iAs)
							self[self.term_index.get(B)[0]][iAs] = A
		else:
			if A_exist:
				for A, B in cluster:
					if self.term_index.get(A) is None:
						self.glue(True, iAs, len(self[0]), A, iBs, len(self[0]), B)
					else:
						if self.term_index.get(A)[0] !=  iAs:
							continue
						else:
							self.term_index[B] = (iBs, self.term_index.get(A)[1])
							self[iBs][self.term_index.get(A)[1]] = B
			else:
				for A, B in cluster:
					if self.term_index.get(B) is None:
						self.glue(True, iAs, len(self[0]), A, iBs, len(self[0]), B)
					else:
						if self.term_index.get(B)[0] != iBs:
							continue
						else:
							self.term_index[A] = (iAs, self.term_index.get(B)[1])
							self[iAs][self.term_index.get(B)[1]] = A

	def glue(self, expand_row, col_A, row_A, A, col_B, row_B, B):
		"""
		Glue the new ratio (A : B) into the grid:
			1. expand the grid for the new ratio
			2. assign the ratio into the designated indexes
		"""
		self.expand(expand_row)
		self.term_index[A] = (col_A, row_A)	# Update grid index for the term
		self[col_A][row_A] = A
		self.term_index[B] = (col_B, row_B)	# Update grid index for the term
		self[col_B][row_B] = B

	def expand(self, row=True):
		"""
		Expand the grid by adding one column or row based on the parameter.
		"""
		if row:
			for i in range(len(self)):
				self[i] += (None, )
		else:
			self.append([None] * len(self[0]))

	def set_attributes(self):
		"""
		Set the attributes of the grid.
		"""
		Attributes = namedtuple('Attributes', ['length', 'width', 'size', 'filled', 'saturation'])
		length = len(self)
		width = len(self[0])
		size = length * width
		filled_cells = 0
		for line in self:
			filled_cells += sum(x is not None for x in line)
		saturation = filled_cells/float(size)
		self.attributes = Attributes(length, width, size, filled_cells, saturation)

	def predictable_words(self):
		"""
		Return a set of new word forms generated from holes in the grid.
		"""
		predictable_words = set()
		self.set_attributes()

		if self.attributes[4] == 1: return	# Complete grid (no holes)
		for i in range(len(self)):
			for j in range(len(self[i])):
				if self[i][j] is None:
					predictable_words.add(self._fill_hole(i, j))
				else:
					continue
		return predictable_words

	def _fill_hole(self, i, j):
		"""
		Fill hole [i,j] in the grid by solving analogy
		"""
		if __trace__: print('### Filling hole [%d][%d]' % (i, j), file=sys.stderr)
		for i_masked in range(len(self)):
			for j_masked in range(len(self[i])):
				if self[i][j_masked] is not None and \
					self[i_masked][j] is not None and \
					self[i_masked][j_masked] is not None:
					solution = solvenlg(self[i_masked][j_masked], self[i][j_masked], self[i_masked][j])
					if solution is not None:
						if __trace__: print('### Solving analogy =>  [%d][%d]:[%d][%d]::[%d][%d]:[%d][%d]' \
								% (i_masked, j_masked, i, j_masked, i_masked, j, i, j), file=sys.stderr)
						if __trace__: print('### Solving analogy =>  %s : %s :: %s : %s' \
								% (self[i_masked][j_masked], self[i][j_masked], self[i_masked][j], solution), file=sys.stderr)
						return solution
					else:
						if __trace__: print('### No luck with this analogy. Finding another equation.', file=sys.stderr)
		if __trace__: print('### No solution for this cell.', file=sys.stderr)

	def pretty_print(self):
		"""
		Give the string representation of the grid for HUMAN.
		Using ratio symbol as column separator.
		"""
		separator = simple_separated_format(NlgSymbols.ratio)
		s = tabulate(self, tablefmt=separator)
		return s + '\n'

	def __str__(self):
		"""
		Give the string representation of the grid for PROGRAM.
		One grid per line.
		"""
		return NlgSymbols.conformity.join( NlgSymbols.ratio.join(str(word) for word in line) for line in self )
		
###############################################################################

class ListOfGrids(list):
	"""
	Class for list of analogical grids (Grid).
	"""

	def __init__(self, grids=[]):
		list.__init__(self, grids)

	@classmethod
	def fromFile(cls, line):
		"""
		Read list of grids from a file.
		"""
		return cls(list(Grid.fromFile(grid) for grid in line.strip().split('\n')))

	@classmethod
	def fromClusters(cls, clusters, saturation=float(0.0)):
		"""
		Build list of analogical grids from list of analogical clusters.
		"""
		from nlg.Grid.Words2Grids.nlgclu2grid import nlgclus2grids
		return cls(nlgclus2grids(clusters, saturation))

	def pretty_print(self):
		"""
		Give the string representation of the list of grids for HUMAN.
		Using ratio symbol as column separator.
		"""
		s = ''
		for gridnbr, grid in enumerate(self):
			grid.set_attributes()
			s += '# Grid no.: %d - %s\n%s\n' % (gridnbr+1, grid.attributes, grid.pretty_print())
		return s

	def __str__(self):
		s = ''
		for grid in self:
			s += '%s\n' % grid.__str__()
		return s

###############################################################################

def statistics(grids_attributes):
	"""
	Calculate the statistics of grids
		1. Distribution of size against saturation against frequency
	"""
	size_saturation_freq = defaultdict(int)
	for length, width, size, filled_cells, saturation in grids_attributes:
		size_saturation_freq[(size, saturation)] += 1

	stat_file = open("size_saturation_freq.gridstat", 'w')
	stat_file.write('size\tsaturation\tfreq\n')
	for (size, saturation) in size_saturation_freq:
		stat_file.write('%d\t%f\t%d\n' % (size, saturation, size_saturation_freq[(size,saturation)]))
	stat_file.close()

	print(f"Average size: {(sum([ att[2] for att in grids_attributes ])/float(len(grids_attributes)))}")
	print(f"Average saturation: {(sum([ att[4] for att in grids_attributes ])/float(len(grids_attributes)))}")


###############################################################################

def read_argv():

	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """
	%(prog)s  <  FILE_OF_GRIDS
	"""

	parser = argparse.ArgumentParser(description=this_description, usage=this_usage, epilog=this_version)
	parser.add_argument('-s', '--statistics',
                  action='store_true', dest='statistics', default=False,
                  help='output statistics of the grids to file')
	parser.add_argument('-V', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')
	parser.add_argument('-t', '--trace',
                  action='store_true', dest='trace', default=False,
                  help='runs in tracing mode')
	parser.add_argument('-T', '--test',
                  action='store_true', dest='test', default=False,
                  help='run all unitary tests')
						
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

def _test():
	import doctest
	doctest.testmod()
	sys.exit(0)

def main(file=sys.stdin):
	
	grids_attributes = list()
	for i, line in enumerate(file):
		grid = Grid.fromFile(line.rstrip('\n'))
		if __verbose__: print(f'\r# Number of analogical grids read: {i+1}', end='\t ', file=sys.stderr)

		# For statistics ...
		grid.set_attributes()
		grids_attributes.append(grid.attributes)
		if __trace__:
			print(f'### Attributes:{grid.attributes}', file=sys.stderr)
			print(f'### [{i}] => {grid}', file=sys.stderr)

	if options.statistics and len(grids_attributes) > 0:
		if __verbose__: print('# Calculating some statistics ...', file=sys.stderr)
		statistics(grids_attributes)

if __name__ == '__main__':
	options = read_argv()
	if options.test: _test()
	__verbose__ = options.verbose
	__trace__ = options.trace
	t_start = time.time()
	main(sys.stdin)
	if __verbose__: print(f'# {os.path.basename(__file__)} - Processing time: {(convert_time(time.time() - t_start))}', file=sys.stderr)
