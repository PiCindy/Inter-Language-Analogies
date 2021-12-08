#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals

import sys
import time
import tempfile
import numpy as np # RH added on 30/8/2021

import nlg.NlgSymbols as NlgSymbols

from nlg.Cluster.Cluster import Cluster, ListOfClusters
from nlg.Cluster.Words2Clusters.ConvertedCluster import ListOfConvertedClusters
from _nlgclu import nlgclu_in_C

from nlg.Vector.Vectors import Vectors # RH added on 4/8/2021
###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'

__date__, __version__ = '26/06/2014', '1.0' # Creation.
__date__, __version__ = '12/11/2014', '1.1' # Add temporary file A to save features.
__date__, __version__ = '15/11/2014', '1.2' # Add temporary file B to save clusters.
__date__, __version__ = '23/01/2015', '1.3' # Bug fixed: in nlgclu_benchmark.py, replace line 399: 
                                             # self.Clines = '\n'.join(self.lines) with self.Clines = '\n'.join(self.lines) + '\n’
__date__, __version__ = '05/02/2015', '1.4' # Add opthion -n to limit number of features used.
__date__, __version__ = '08/02/2015', '1.5' # Print out processing time at each step.
__date__, __version__ = '17/02/2015', '1.6' # Import module name except of DLL method.
__date__, __version__ = '25/02/2015', '1.7' # Add function "nlgclu" to call the C program when using as library.
__date__, __version__ = '10/03/2015', '1.7' # Modifications to use as a Python package without DLL.
											# Arguments and options from nlgclu_benchmark.py.
__date__, __version__ = '19/04/2015', '1.8'	# Add separation of space of objects and output of duplicate objects.
											# Add option -s for the minimal size of clusters.
											# Rename option -n into -f for number of features.
__date__, __version__ = '03/08/2016', '1.9'	# Add option -F to output only those clusters that contain a given word: __focus__.
__date__, __version__ = '06/08/2016', '2.0'	# Add option -A for features by anchors.
											# Experiments do not show conclusive results.
__date__, __version__ = '14/10/2016', '2.1'	# Replaced functions Alphabet, FeatureVector and FeatureMatrix by a simpler and more efficient class FeatureMatrix.
											# TODO: Add option to limit the differences in character changes as in Langlais' paper at CCIBR-CA-2016.
__date__, __version__ = '30/08/2021', '2.2'	# Modifications to NlgClustering for one file and two files input.
											# Add alphabet as an argument to fromFile method in FeatureMatrix, FeatureTree and CFeatureTree.
											# Import Vectors to obtain word and vector pair in fromFile method in FeatureMatrix.
__date__, __version__ = '16/09/2021', '2.3'	# Modifications to FeatureMatrix for vector representation to be NumPy compatible.
											# Old implementation without numpy (3.2)
											# +----+---------+----------+---------------+
											# |      | 5k        | 10k      | 20k            |
											# +----+---------+----------+---------------+
											# | de | 153.81 | 703.27 | 3660.60     |
											# +----+----------+---------+---------------+
											# | fi    | 175.68 | 878.63 | 4924.44    |
											# +----+----------+----------+--------------+
											# | sv  | 137.30 | 746.49 | 3383.24    |
											# +----+----------+----------+--------------+
											#
											# New implementation with numpy (3.2.1)
											# +----+-------+--------+---------------+
											# |    | 5k      | 10k      | 20k           |
											# +----+-------+--------+---------------+
											# | de | 67.88 | 350.81 | 1838.15  |
											# +----+-------+--------+---------------+
											# | fi | 75.86 | 441.35   | 2470.86   |
											# +----+-------+--------+---------------+
											# | sv | 75.27 | 373.80 |  1871.68  |
											# +----+-------+--------+———————+
											# 
											# The data are lists of words extracted for the Europarl v3 in the German, Finnish and Swedish languages. Three sizes are used: 5k, 10k and 20k.								

__description__ = 'Module for analogical clustering.'

__NODESIZE__ = 6

__verbose__ = False						# Gives information about timing, etc. to the user.
__lineout__ = False						# If true, pass text to the C program. This is normally not required.
										# This option is made available to be able to debug the C program.
__trace__ = False						# If true, output traces for the developper for debugging.

__word__ = False						# Allows the use of words as units instead of characters.
__feature_number__ = None				# Number of features used. None means that all features are used.
__minimal_size__ = 2					# Minimal size of clusters output. Two is the minimal to get one analogy.
__maximal_size__ = None					# Maximal size of clusters output.
__anchors__ = False						# If true, use anchor words to compute features (default number: __anchor_default_number__).
__anchor_default_number__ = 100			# Default number of anchor words.
__focus__ = None						# Focus word to output only those clusters which contain the focus.

###############################################################################
# This example is for the following features and strings:
#
#    a  p  i  t  o
#
#    0  0  0  2  2	toto
#    2  2  0  0  0	papa
#    2  0  0  2  0	tata
#    0  2  2  0  0	pipi
#    0  2  0  0  2	popo
#
# Feature matrix:
#	 toto
#	    popo
#	       pipi
#	          tata
#	             papa
# [	(0, 0, 0, 0, 0),	level 0 = no feature
#  	(0, 0, 0, 2, 2),	level 1 = feature a
#	(0, 2, 2, 0, 2),	level 2 = feature p
#	(0, 0, 2, 0, 0),	level 3 = feature i
#	(2, 0, 0, 2, 0),	level 4 = feature t
#	(2, 2, 0, 0, 0)]	level 5 = feature o

mytestdata = ['toto','popo','pipi','tata','papa']

myfeaturetree = (
#	level,
#		size, number of objects covered by this node
#			object ** first object number, not node number in the tree ***
#				value,
#					is_empty_rest,
#						next_level_begin_node, *** node in this tree ***
#							next_level_end_node (included), *** node in this tree **

	0,	4,	0,	0,	0,	1,	2,		# node 0

	1,	2,	0,	0,	0,	3,	4,		# node 1
	1,	2,	3,	2,	0,	5,	6,		# node 2
	
	2,	1,	0,	0,	0,	7,	7,		# node 3
	2,	2,	1,	2,	0,	8,	9,		# node 4
	2,	1,	3,	0,	0,	10,	10,		# node 5
	2,	1,	4,	2,	0,	11,	11,		# node 6

	3,	1,	0,	0,	0,	12,	12,		# node 7
	3,	1,	1,	0,	0,	13,	13,		# node 8
	3,	1,	2,	2,	0,	14,	14,		# node 9
	3,	1,	3,	0,	0,	15,	15,		# node 10
	3,	1,	4,	0,	0,	16,	16,		# node 11

	4,	1,	0,	2,	0,	17,	17,		# node 12
	4,	1,	1,	0,	0,	18,	18,		# node 13
	4,	1,	2,	0,	0,	19,	19,		# node 14
	4,	1,	3,	2,	0,	20,	20,		# node 15
	4,	1,	4,	0,	0,	21,	21,		# node 16

	5,	1,	0,	2,	0,	-1,	-1,		# node 17	points to -1 on the next level
	5,	1,	1,	2,	0,	-1,	-1,		# node 18		same
	5,	1,	2,	0,	0,	-1,	-1,		# node 19		same
	5,	1,	3,	0,	0,	-1,	-1,		# node 20		same
	5,	1,	4,	0,	0,	-1,	-1,		# node 21		same

)


myfeaturetree2 = (
	0, 0, 0, 0, 1, 2,
	1, 0, 0, 0, 3, 4,
	1, 1, 4, 2, 5, 5,
	2, 0, 0, 0, 6, 7,
	2, 0, 2, 2, 8, 9,
	2, 1, 4, 2, 10, 10,
	3, 1, 0, 0, 11, 11,
	3, 1, 1, 2, 12, 12,
	3, 1, 2, 0, 13, 13,
	3, 1, 3, 2, 14, 14,
	3, 1, 4, 0, 15, 15,
	4, 1, 0, 2, 16, 16,
	4, 1, 1, 2, 17, 17,
	4, 1, 2, 0, 18, 18,
	4, 1, 3, 0, 19, 19,
	4, 1, 4, 0, 20, 20,
	5, 1, 0, 2, -1, -1,
	5, 1, 1, 0, -1, -1,
	5, 1, 2, 2, -1, -1,
	5, 1, 3, 0, -1, -1,
	5, 1, 4, 0, -1, -1,
)

###############################################################################

def list_to_blocks(list, shift=0):
	"""
	Return the slices of the sequences with the same value in a list.
	>>> list_to_blocks([100,100,100,100,100])
	[slice(0, 5, None)]
	>>> list_to_blocks([0,0,0,0,2])
	[slice(0, 4, None), slice(4, 5, None)]
	>>> list_to_blocks([100,101,102,103,104])
	[slice(0, 1, None), slice(1, 2, None), slice(2, 3, None), slice(3, 4, None), slice(4, 5, None)]
	>>> list_to_blocks([100,100,100,100,100,101,101,101,102,102,100,100])
	[slice(0, 5, None), slice(5, 8, None), slice(8, 10, None), slice(10, 12, None)]
	"""
	result = []
	start_i, start_val = 0, list[0]
	for i, val in enumerate(list):
		if val != start_val:
			result.append(slice(start_i+shift,i+shift))
			start_i, start_val = i, val
	result.append(slice(start_i+shift,len(list)+shift))
	return result

def sliced_list_to_blocks(list, blocks):
	"""
	Return the slices of the sequences with the same value in a list.
	>>> sliced_list_to_blocks([100,100,100,100,100],[slice(0,5)])
	[slice(0, 5, None)]
	>>> sliced_list_to_blocks([100,100,100,100,100],[slice(0,2),slice(2,5)])
	[slice(0, 2, None), slice(2, 5, None)]
	>>> sliced_list_to_blocks([100,101,102,103,104],[slice(0,1),slice(1,5)])
	[slice(0, 1, None), slice(1, 2, None), slice(2, 3, None), slice(3, 4, None), slice(4, 5, None)]
	>>> sliced_list_to_blocks([100,100,100,100,100,101,101,101,102,102,100,100],[slice(0,2), slice(2,12)])
	[slice(0, 2, None), slice(2, 5, None), slice(5, 8, None), slice(8, 10, None), slice(10, 12, None)]
	"""
	result = []
	for block in blocks:
		result += list_to_blocks(list[block],block.start)
	return result

###############################################################################

def blocks_to_nodes(level, matrix_row, sub_blocks):
	result = []
	for block in sub_blocks:
		result.append([										# Format of a node:
			level,											# level
#			1 if block.stop - block.start == 1 else 0,		# is_singleton, replaced by size (next line)
			block.stop - block.start,						# size, i.e., number of objects covered by the node
			block.start,									# start_object
			block.stop,										# stop_object
			matrix_row[block.start],						# value
			0,												# is_empty_rest
			-1,												# next_level_begin_node
			-1												# next_level_end_node
		])
	return result

###############################################################################

def Level2Nodes(level, matrix_row, blocks):
	sub_blocks = sliced_list_to_blocks(matrix_row, blocks)
	sub_nodes = blocks_to_nodes(level, matrix_row, sub_blocks)
	return sub_nodes, sub_blocks

###############################################################################

bitfeatures = [ bin(i)[2:].zfill(8) for i in range(256) ]
bitfeatures = { s:s.count('1') for s in bitfeatures }
bitfeatures = sorted( bitfeatures, key=bitfeatures.get )
# print '\n'.join( s for s in bitfeatures )
bitfeatures = [ [ int(s[i]) for i in range(8) ] for s in bitfeatures ]
# print '\n'.join( '%s' % feature for feature in bitfeatures )

def bitvectors(line, alphabet_to_rank):
	list = [ bitfeatures[alphabet_to_rank[c]] for c in line ]
	return tuple( sum(row) for row in zip(*list) )

##########################################################################################################

class FeatureMatrix(list):

	def __init__(self, word_vector_dict={}):
		vectors = {}
		if __verbose__: print('# Reading vectors...', file=sys.stderr)
		# Associate an index to keep trace of the word when sorting several times.
		for i, (word, vector) in enumerate(word_vector_dict.items()):
		#	vectors[word] = vector + ( i, ) # RH commented on 6/9/2021
			vector = np.array(vector) # RH added on 6/9/2021
			vectors[word] = np.append(vector, i) # RH added on 6/9/2021
		if __verbose__: print('# Vectors read.', file=sys.stderr)
		# Create the dictionary of words (= lines) with their associated index.
		lines = { vectors[word][-1] : word for word in vectors }
		
		# Sort the vectors as this is required to build the feature tree.
		# fv = sorted(vectors.values()) # RH commented on 02/09/2021
		fv = np.array([vectors[word] for word in vectors]) # RH added on 13/09/2021
		fv = fv[fv[:, 0].argsort()] # RH added on 13/09/2021

		# Transpose the list of feature vectors.
		# matrix = list(zip(*fv)) # RH commented on 09/09/2021
		matrix = np.transpose(fv) # RH added on 09/09/2021
		# The object indices are the last row in the matrix.
		# They are in the same order as in the tree.
		objects = matrix[-1]
		# Add a first row of 0's for the 0th level (all objects have a value of 0 on this dummy level).
		# Discard the last line which stands for the object indices.
		# fm = [ (0,) * len(matrix[0]) ] + matrix[:-1] # RH commented 14/09/2021
		fm = np.append(np.zeros((1, len(matrix[0])) , dtype=np.int64),matrix[:-1],axis=0) # RH added 14/09/2021
		# Create the object as a list.
		list.__init__(self, fm)
		self.objects = objects
		self.lines = [ lines[i] for i in objects ]
		if __verbose__: print('# Number of objects: %d.' % len(self.objects), file=sys.stderr)

	@classmethod
	def fromFile(cls, file=sys.stdin, alphabet=sys.stdin): # RH modified on 26/8/2021
		word_vector_dict = {}
		vector_temp= ''.join(str(Vectors.fromFile(lines=file, alphabet=alphabet))) # RH added on 26/8/2021
		vector_temp=vector_temp.split('\n') # RH added on 26/8/2021
		vector_temp = [vector_temp[i] for i in range(len(vector_temp)) if vector_temp[i] != '# '] # RH added on 26/8/2021
		if __verbose__: print('# Reading words and vectors...', file=sys.stderr)
		for line in vector_temp:
			if line.startswith('#'):
#				print('in FeatureMatrix >>>' + line, end=' ') # RH commented on 19/8/2021
				print(line, end=' ') # RH modified on 19/8/2021
			else:
				word, vector = line.split('\t')
#				decode is not more needed in Python3.
#				word_vector_dict[word.decode('utf8')] = eval(vector)
				word_vector_dict[word] = eval(vector)
		return cls(word_vector_dict)
		
###############################################################################

class FeatureTree(list):

	def __init__(self, fm=[]):
		if __verbose__: print('# Computing feature tree...', file=sys.stderr)
		ll = self.Vectors2Tree(fm)
		if __trace__: print('# Feature tree:\n%s' % ll, file=sys.stderr)
		list.__init__(self,ll)
		self.objects = fm.objects
		self.lines = fm.lines
		if __verbose__: print('# Computation done.', file=sys.stderr)
	
	@classmethod
	def fromFile(cls, file=sys.stdin, alphabet=sys.stdin): # RH modified on 26/8/2021
		return cls(FeatureMatrix.fromFile(file,alphabet))
	
	@classmethod
	def fromVectors(cls, vectors={}):
		fm = FeatureMatrix(vectors)
		return cls(fm)
	
	def Vectors2Tree(self, matrix):
		# Initialize the list of nodes to an empty list and
		# the first block to a block of the length of a row, i.e., to the number of objects.
		nodes, sub_blocks  = [], [ slice(0,len(matrix[0])) ]
		# Split into nodes of same values level by level, i.e., each row after one another.
		matlen = len(matrix)
		for i, level in enumerate(range(matlen)):
			if __verbose__: print('\r %2d %% ' % int((i/float(matlen))*100), end=' ', file=sys.stderr)
			sub_nodes, sub_blocks = Level2Nodes( level, matrix[level], sub_blocks )
			nodes += sub_nodes
		if __verbose__: print('\r100 %% ', file=sys.stderr)
		# Number the nodes.
		for i, node in enumerate(nodes):
			nodes[i] = [i] + node
		# Name the indices.
		NUMBER, 				\
		LEVEL, 					\
		SIZE,					\
		START_OBJECT, 			\
		STOP_OBJECT, 			\
		VALUE,					\
		IS_EMPTY_REST,			\
		NEXT_LEVEL_BEGIN_NODE,	\
		NEXT_LEVEL_END_NODE		= 0, 1, 2, 3, 4, 5, 6, 7, 8
		# Get length, starting points for levels.
		nodeslen = len(nodes)
		level_start = dict()
		for node in nodes:
			level = node[LEVEL]
			if level not in level_start:
				level_start[level] = node[NUMBER]
		# Explore the tree.
		for level in range(len(level_start)-1):
			if __verbose__: print('\r %2d %%' % int((level/float(len(level_start)))*100), end=' ', file=sys.stderr)
			n, m = level_start[level], level_start[level+1]
			while level == nodes[n][LEVEL]:
				assert nodes[n][START_OBJECT] == nodes[m][START_OBJECT], 'error on start object at levels %d and %d' % (level, level+1)
				nodes[n][NEXT_LEVEL_BEGIN_NODE] = nodes[m][NUMBER]
				mm = m
				while mm < nodeslen:
					if nodes[n][STOP_OBJECT] == nodes[mm][STOP_OBJECT]:
						nodes[n][NEXT_LEVEL_END_NODE] = nodes[mm][NUMBER]
						n, m = n+1, mm+1
						break
					mm += 1
		if __verbose__: print('\r100 %%', file=sys.stderr)
		# Compute the is_empty_rest values.
		for node in nodes[::-1]:
			result = ( 1 == node[SIZE] and 0 == node[VALUE] )
			nextnode = node[NEXT_LEVEL_BEGIN_NODE]
			if -1 != nextnode:
				result &= nodes[nextnode][IS_EMPTY_REST]
			node[IS_EMPTY_REST] = 1 if result else 0
		if __verbose__: print('# Number of nodes: %d.' % len(nodes), file=sys.stderr)
		for node in nodes:
			assert nodes[n][SIZE] == nodes[n][STOP_OBJECT] - nodes[n][START_OBJECT], 'start, stop and size incompatible'
			assert nodes[n][NEXT_LEVEL_BEGIN_NODE] != -1 or nodes[n][SIZE] == 1, 'node %d of size > 1 on last level' % n
			assert nodes[n][SIZE] == 1 or nodes[n][NEXT_LEVEL_BEGIN_NODE] != -1, 'node %d of size > 1 on last level' % n
		return nodes

	def node_to_lines(self, node):
		# This function outputs the lines which are described by a node.
		return ', '.join( self.lines[i] for i in range(node[3], node[4]) ) # node[START_OBJECT], node[STOP_OBJECT]
	
	def __str__(self):
		return '\n'.join('%s\t%s' % (node, self.node_to_lines(node)) for node in self)

###############################################################################

def alphagram(s):
	"""
	>>> alphagram('gfedcba')
	'abcdefg'
	>>> alphagram('toto')
	'oott'
	"""
	return ''.join( c * s.count(c) for c in sorted(list(set(s))) )

class CFeatureTree:

	def __init__(self, featuretree):
		t0 = time.time()
		# Builds the three data structures that will be passed to the C program:
		# Clength, integerlist, Clines (this last one is passed only if __lineout__ is on)
		if __trace__: print('# Feature tree:\n%s' % featuretree, file=sys.stderr)
		# Keeping the necessary elements and flattening to a list of integers.
		if __verbose__: print('# Converting to list of integers...', file=sys.stderr)
		ft = [ node[1:4] + node[5:] for node in featuretree ]
		self.integerlist = [i for node in ft for i in node]
		self.Clength = len(self.integerlist)
		if __trace__: print('# self.Clength = %d' % self.Clength, file=sys.stderr)
		if __trace__: print('# self.integerlist = %s' % self.integerlist, file=sys.stderr)
		if __verbose__: print('# Copying lines...', file=sys.stderr)
#		encode is no more neede in Python3.
#		self.Clines = [ line.replace(':','\\:').encode('utf-8') for line in featuretree.lines ]
		self.Clines = [ line.replace(':','\\:') for line in featuretree.lines ]
		if __trace__: print('lines = %s' % self.Clines, file=sys.stderr)
		if __verbose__: print('# Conversion done in %.2fs.' % (time.time() - t0), file=sys.stderr)
	
	@classmethod
	def fromFile(cls, file=sys.stdin, alphabet=sys.stdin): # RH modified on 26/8/2021
		return cls(FeatureTree.fromFile(file,alphabet))
	
	@classmethod
	def fromVectors(cls, vectors={}):
		return cls(FeatureTree.fromVectors(vectors))
	
	def store(self, filename):
		t1 = time.time()
		cfile = tempfile.NamedTemporaryFile(prefix=filename, suffix=".txt", mode='wt')
		print('%d' % self.Clength, file=cfile)
#		for i in self.integerlist:
#			print >> cfile, '%d' % i
		print('\n'.join( '%d' % i for i in self.integerlist ), file=cfile)
		if __lineout__:
			print('\n'.join(self.Clines), file=cfile)
		cfile.seek(0)
		if __verbose__: print('## [Python] Writing input data: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
		return cfile

	def get_index(self, the_line):
		result = None
		the_line_alphagram = alphagram(the_line)
		# Simply scan all the objects to find the line the_line.
		for index, line in enumerate(self.Clines):
			if the_line_alphagram == alphagram(line):
				result = index
				break
		if __trace__: print('# get_index(%s) = %d' % (the_line, result), file=sys.stderr)
		return result

###############################################################################

def nlgclu(cfileA, cfileB, featuretreeA, featuretreeB, minimal_size=2, maximal_size=None, verbose=False, lineout=False, feature_number=None, anchors=False, focus=None):
	# Create the temporary file which will contain the clusters,
	# but with the lines encoded as line numbers.
	clufile = tempfile.NamedTemporaryFile(prefix="nlgclu_clufile", suffix=".txt", mode='w+t')

	# Parameter adaptation for the C program (no None in C).
	if maximal_size == None: maximal_size = -1
	if focus == None:
		ifocus = -1
	else:
		ifocus = featuretreeA.get_index(focus)
	if ifocus == None:
		print('### WARNING: focus word "{}" not found in fileA; no cluster output.'.format(focus), file=sys.stderr)
		return ListOfClusters('')

	# Call the C program for actual clustering.
	t1 = time.time()
	nlgclu_in_C(cfileA.name, cfileB.name, clufile.name, minimal_size, maximal_size,
				1 if __verbose__ or verbose else 0,
				1 if __lineout__ or lineout else 0,
				ifocus)
	if __verbose__: print('## [Python] Clustering time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
	clufile.flush()

	# Trace for debugging.
	if __lineout__:
		clunbr = 0
		clufile.seek(0)
		for line in clufile:
			clunbr += 1
			print(line, end=' ')
		if __verbose__: print('# Number of clusters output: %d' % clunbr, file=sys.stderr)

	# Input: clufile is the file output by the C program containing clusters with integers.
	# Output: a cluster file of lines (the lines replace the integers).
	# We need to convert the clusters of the C program,
	# where the objects are referred to by integers,
	# into the clusters with lines.
	# The correpondence is done by using the Clines dictionaries of the feature trees.
	t1 = time.time()
	# Interface Python/C: reading the clusters from the temporary file clufile.
	clufile.seek(0)
	integer_cluster_file = ListOfClusters.fromFile(file=clufile, read_indistinguishables=False)
	if __verbose__: print('## Integer_cluster_file:\n%s\n----' % integer_cluster_file, file=sys.stderr)
	# Converting the file of integers into a file with lines (the lines correspond to the integers).
	if __verbose__: print('## [Python] Transcribing clusters: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
	line_cluster_file = ListOfConvertedClusters(integer_cluster_file, featuretreeA.Clines, featuretreeB.Clines)
	if __verbose__: print('# Number of clusters transcribed: %d' % len(line_cluster_file), file=sys.stderr)
	if __verbose__: print('## Transcription time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)
	if __verbose__: print('## ListOfClusters: %s' % line_cluster_file, file=sys.stderr)
	return line_cluster_file

def NlgClustering(fileA=sys.stdin, fileB=None, minimal_size=2, maximal_size=None, verbose=False, lineout=False, feature_number=None, anchors=False, focus=None):
	"""
	This function is the entry point of this module.
	"""

#	FIXED:
#	THE FOLLOWING DOCTESTS DO NOT WORK ANYMORE BECAUSE OT THE INTRODUCTION OF strings2vectors.py.
#	VECTORS SHOULD BE COMPUTED FROM THE WORDS.

#	It should be called like this:	
#	>>> NlgClustering(['toto', 'tata'], ['popo', 'papa'])
#	toto : popo :: tata : papa
#	>>> NlgClustering(['toto', 'tata', 'popo', 'papa'])
#	toto : tata :: popo : papa
#	toto : popo :: tata : papa
#	>>> NlgClustering(['toto', 'tata', 'popo', 'papa', 'apap'])
#	# apap == papa 
#	toto : tata :: popo : apap
#	toto : popo :: tata : apap
	

	if fileB == None:
#		vectorsA = "" # RH added on 17/8/2021; RH commented on 19/8/2021
#		vectorsA+=str(Vectors.fromFile(lines=fileA)) # RH added on 17/8/2021; RH commented on 19/8/2021
#		vectorsA=vectorsA.split('\n') # RH added on 17/8/2021; RH commented on 19/8/2021
#		vectorsA= ''.join(str(Vectors.fromFile(lines=fileA))) # RH added on 19/8/2021; RH commented on 26/8/2021
#		vectorsA=vectorsA.split('\n') # RH added on 19/8/2021; RH commented on 26/8/2021
#		vectorsA = [vectorsA[i] for i in range(len(vectorsA)) if vectorsA[i] != '# '] # RH added on 19/8/2021; RH commented on 26/8/2021		
		featuretreeA = featuretreeB = CFeatureTree.fromFile(fileA,alphabet=None) # RH modified on 26/8/2021
#		featuretreeA = featuretreeB = CFeatureTree.fromFile(vectorsA)
		# Creating the temporary files associated with the data set.
		cfileA = cfileB = featuretreeA.store("nlgclu_fileA")
	else:
#		vectorsA = "" # RH added on 4/8/2021; RH commented on 17/8/2021
#		vectorsA+=str(Vectors.fromFile(lines=fileA))[3:] # RH added on 4/8/2021; RH commented on 17/8/2021
#		vectorsA=vectorsA.split('\n') # added on 4/8/2021; RH commented on 17/8/2021
		linesA = [ line.rstrip('\n').strip() for line in fileA ]
#		linesA = [ line.rstrip('\n').strip() for line in vectorsA ] # RH modified on 4/8/2021; RH commented on 17/8/2021
		if type(fileA) == 'file':
			fileA.close()
#		vectorsB = "" # RH added on 4/8/2021; RH commented on 17/8/2021
#		vectorsB+=str(Vectors.fromFile(lines=fileB))[3:] # RH added on 4/8/2021; RH commented on 17/8/2021
#		vectorsB=vectorsB.split('\n') # RH added on 4/8/2021; RH commented on 17/8/2021
		linesB = [ line.rstrip('\n').strip() for line in fileB ]
#		linesB = [ line.rstrip('\n').strip() for line in vectorsB ] # RH modified on 4/8/2021; RH commented on 17/8/2021
		if type(fileB) == 'file':
			fileB.close()
#		The two following lines are no more needed in Python3.
#		decodedlinesA = [ line.decode('utf-8') for line in linesA ]
#		decodedlinesB = [ line.decode('utf-8') for line in linesB ]
		decodedlinesA = linesA
		decodedlinesB = linesB
#		alphabet = set(''.join(decodedlinesA + decodedlinesB)) # RH commented on 19/8/2021
		alphabet = sorted(list(set(''.join(decodedlinesA + decodedlinesB)))) # RH modified on 19/8/2021
#		lineAB = decodedlinesA + decodedlinesB # RH added on 17/8/2021; RH commented on 18/8/2021
#		vectorsAB = "" # RH added on 17/8/2021; RH commented on 18/8/2021
#		vectorsAB+=str(Vectors.fromFile(lines=lineAB))[3:] # RH added on 17/8/2021; RH commented on 18/8/2021
#		vectorsAB=vectorsAB.split('\n') # RH added on 17/8/2021; RH commented on 18/8/2021

#		vectorsA= ''.join(str(Vectors.fromFile(lines=fileA, alphabet=alphabet))) # RH added on 19/8/2021; RH modified on 23/8/2021; RH commented on 26/8/2021
#		vectorsA=vectorsA.split('\n') # RH added on 19/8/2021; RH commented on 26/8/2021
#		vectorsA = [vectorsA[i] for i in range(len(vectorsA)) if vectorsA[i] != '# '] # RH added on 19/8/2021; RH modified on 23/8/2021; RH commented on 26/8/2021
#		vectorsB = ''.join(str(Vectors.fromFile(lines=fileB, alphabet=alphabet))) # RH added on 19/8/2021; RH modified on 23/8/2021; RH commented on 26/8/2021
#		vectorsB=vectorsB.split('\n') # RH added on 19/8/2021; RH commented on 26/8/2021
#		vectorsB = [vectorsB[i] for i in range(len(vectorsB)) if vectorsB[i] != '# '] # RH added on 19/8/2021; RH modified on 23/8/2021; RH commented on 26/8/2021

		# Create the feature trees using the alphabet previously computed.
		featuretreeA = CFeatureTree.fromFile(linesA, alphabet) # RH commented on 19/8/2021; RH uncommented and modified on 26/8/2021
#		featuretreeA = CFeatureTree.fromFile(vectorsA) # RH commented on 26/8/2021
#		featuretreeA = featuretreeB = CFeatureTree.fromFile(vectorsAB) # RH added on 4/8/2021; RH modified on 17/8/2021; RH commented on 18/8/2021
		featuretreeB = CFeatureTree.fromFile(linesB, alphabet) # RH commented on 19/8/2021; RH uncommented and modified on 26/8/2021
#		featuretreeB = CFeatureTree.fromFile(vectorsB) # RH commented on 26/8/2021
#		featuretreeB = CFeatureTree.fromFile(vectorsAB) # RH added on 4/8/2021; RH commented on 17/8/2021; RH commented on 18/8/2021
		# Create the temporary files associated with each data set.
#		cfileA = cfileB = featuretreeA.store("nlgclu_fileA") # RH modified on 17/8/2021; RH commented on 18/8/2021
		cfileA = featuretreeA.store("nlgclu_fileA")
		cfileB = featuretreeB.store("nlgclu_fileB") 

	# Call analogical clustering.
	return nlgclu(cfileA, cfileB, featuretreeA, featuretreeB,
		minimal_size=minimal_size,
		maximal_size=maximal_size,
		verbose=verbose,
		lineout=lineout,
		feature_number=feature_number,
		anchors=anchors,
		focus=focus)

def NlgClusteringFromVectors(vectors, minimal_size=2, maximal_size=None, verbose=False, lineout=False, feature_number=None, anchors=False, focus=None):
	featuretreeA = featuretreeB = CFeatureTree.fromVectors(vectors)
	# Creating the temporary files associated with the data set.
	cfileA = cfileB = featuretreeA.store("nlgclu_fileA")

	# Call analogical clustering.
	return nlgclu(cfileA, cfileB, featuretreeA, featuretreeB,
		minimal_size=minimal_size,
		maximal_size=maximal_size,
		verbose=verbose,
		lineout=lineout,
		feature_number=feature_number,
		anchors=anchors,
		focus=focus)

def VectorNlgClustering(fileA=sys.stdin, fileB=None, minimal_size=2, maximal_size=-1, verbose=False, lineout=False, feature_number=None, anchors=False, focus=None):
	featuretreeA = CFeatureTree.fromFile(fileA)
	# Creating the temporary files associated with the data set.
	cfileA = featuretreeA.store("nlgclu_fileA")
	
	# Call analogical clustering.
	return nlgclu(cfileA, cfileA, featuretreeA, featuretreeA,
		minimal_size=minimal_size,
		maximal_size=maximal_size,
		verbose=verbose,
		lineout=lineout,
		feature_number=feature_number,
		anchors=anchors,
		focus=focus)

###############################################################################

def read_argv():

	from argparse import ArgumentParser
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """%(prog)s fileA fileB
	%(prog)s fileA -  <  fileB
	%(prog)s - fileB  <  fileA
	The three commands above mean the same.
	
	%(prog)s fileA fileA
	%(prog)s - -  <  fileA
	%(prog)s -  <  fileA
	%(prog)s  <  fileA
	The four commands above mean the same.

	In the above commands, - means the standard input.
	
	%(prog)s --vectors <  vectorfileA

	vectorfileA should be a file made of lines of the format:
		
		word \\t Python tuple of integers
		
	e.g.
	
		ababz\t(2, 2, 0, ..., 1)
	
	All vectors for all words should have the same length.
	Such files can be output by quantize.py from word2vec binary files.
	"""

	parser = ArgumentParser(epilog=this_version, description=this_description, usage=this_usage)
	parser.add_argument('args',
						action='store', type=str, nargs='*',
						help = 'fileA [fileB]')
	parser.add_argument('-f','--feature_number',
						action='store',dest='fn', type=int, default=None,
						help = 'number of features used (default: %(default)s, '\
								'to use all possible features)')
	parser.add_argument('-A','--anchors',
						action='store_true', dest='anchors', default=False,
						help = 'use similarities to anchor words '\
								'instead of characters in the alphabet as features '\
								'(number of anchors given by option -f, default: %d)' % __anchor_default_number__)
	parser.add_argument('-m','--minimal_cluster_size',
						action='store',dest='minsize', type=int, default=2,
						help = 'minimal size of clusters output (default: %(default)s, ' \
								'to output all possible clusters, because ' \
								'there should be at least 2 lines in a cluster to form at least one analogy)')
	parser.add_argument('-M','--maximal_cluster_size',
						action='store',dest='maxsize', type=int, default=None,
						help = 'maximal size of clusters output (default: %(default)s)')
	parser.add_argument('-F','--focus',
						action='store',dest='focus', type=str, default=None,
						help = 'only output those clusters which contain FOCUS')
	parser.add_argument('--vectors',
						action='store_true', dest='vectors', default=False,
                  		help='input file contains vectors')
	parser.add_argument('-V', '--verbose',
						action='store_true', dest='verbose', default=False,
                  		help='run in verbose mode')
	parser.add_argument('-L','--line_out',
						action='store_true',dest='lineout', default=False,
						help = '(for debugging purpose only) let the C program output the lines instead of line numbers')
	parser.add_argument('-X', '--example_test',
						action='store_true', dest='example', default=False,
						help='run the example test included in the Python source file')
	return parser.parse_args()

###############################################################################

def myfileopen(name):
	if name == '-':
		return sys.stdin
	else:
		return open(name)

if __name__ == '__main__':
	options = read_argv()
	args = options.args
	__verbose__ = options.verbose
	__lineout__ = options.lineout
	__feature_number__ = options.fn
	__minimal_size__ = options.minsize
	__focus__ = options.focus
	__anchors__ = options.anchors
	if __verbose__: print('# Focus: %s' % options.focus, file=sys.stderr)
	if __verbose__: print('# Minimal size of clusters: %d' % __minimal_size__, file=sys.stderr)
	__maximal_size__ = -1 if options.maxsize == None else options.maxsize

	if __feature_number__ != None and 1 > __feature_number__:
		print('Number of features should be equal to or greater than 1.', file=sys.stderr)
		exit(-1)
	if 2 > __minimal_size__:
		print('Minimal size of clusters should be equal to or greater than 2.', file=sys.stderr)
		exit(-1)
	if __maximal_size__ != -1 and 2 > __maximal_size__:
		print('Maximal size of clusters should be equal to or greater than 2.', file=sys.stderr)
		exit(-1)

	if len(args) > 2:
		print('At most two arguments may be given.', file=sys.stderr)
		exit(-1)
	elif len(args) == 2 and args[0] != args[1]:
		fileA, fileB = myfileopen(args[0]), myfileopen(args[1])
	else: # Either len(args) == 1 or args[0] == args[1].
		fileB = None
		if len(args) == 2 and args[0] == args[1]:
			fileA = myfileopen(args[0])
		elif len(args) == 1:
			fileA = myfileopen(args[0])
		elif len(args) == 0:
			fileA = sys.stdin
	if options.example:
		fileA = mytestdata
		fileB = None

	"""
	TO BE FIXED:
	NlgClustering IS NOT DOING WHAT WE EXPECT.
	UPDATE: FIXED 30/08/2021
	"""
	if options.vectors:
		if __verbose__: print('# Vector input format.', file=sys.stderr)
		nlgclustering = VectorNlgClustering
	else:
		nlgclustering = NlgClustering

	t1 = time.time()
	print(nlgclustering(fileA, fileB,
		minimal_size=options.minsize,
		maximal_size=options.maxsize,
		verbose=options.verbose,
		lineout=options.lineout,
		feature_number=options.fn,
		anchors=options.anchors,
		focus=options.focus))
	if __verbose__: print('# Processing time: %.2fs' % (time.time() - t1), file=sys.stderr)