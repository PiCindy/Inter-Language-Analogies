#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from itertools import chain
from collections import Counter

flatten = chain.from_iterable

import nlg.NlgSymbols as NlgSymbols
from nlg.Cluster.Cluster import Cluster, ListOfClusters
from _fast_distance import fast_distance

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'

__date__, __version__ = '28/08/2017', '0.10' # Creation

__description__ = """
	Class for analogies.
	An analogy is an analogical cluster that meets the following constraints:
		having exactly two ratios and
		character occurrence constraint and
		distance constraint.
"""

###############################################################################

class Analogy(Cluster):
	"""
	Class for analogy.
	An analogy is a cluster with exactly two ratios.
	"""

	def __init__(self, cluster):
		"""
		Create an analogy from a cluster.
		Check that it is a valid analogy by checking
			that it contains exactly two ratios and
			the constraint on number of coccurence of characters and
			the constraint on distances.
		
		>>> Analogy([['a', 'aa'], ['aaa', 'aaaa']])
		a : aa :: aaa : aaaa
		>>> Analogy([['aslama', 'arsala'], ['muslim', 'mursil']])
		aslama : arsala :: muslim : mursil
		>>> Analogy([['anything', 'bad'], ['invalid', 'wrong']])
		anything : bad :: invalid : wrong
		>>> Analogy([['anything', 'bad'], ['invalid', 'wrong']]).is_valid
		False
		"""
		Cluster.__init__(self, cluster)
		self.A, self.B, self.C, self.D = (term for term in flatten(self))
		self.is_valid = self.TwoRatios() and self.CharacterOccurrenceConstraint() and self.DistanceConstraint()
		self.is_trivial = self.is_trivial()

	@classmethod
	def fromTerms(cls, A, B, C, D):
		"""
		Create an analogy from four terms.
		Check that it is a valid analogy by checking
			the constraint on number of coccurence of characters
			the constraint on distances.
		
		>>> Analogy.fromTerms('a', 'aa', 'aaa', 'aaaa')
		a : aa :: aaa : aaaa
		>>> Analogy.fromTerms('aslama', 'arsala', 'muslim', 'mursil')
		aslama : arsala :: muslim : mursil
		>>> Analogy.fromTerms('anything', 'bad', 'invalid', 'wrong')
		anything : bad :: invalid : wrong
		>>> Analogy.fromTerms('anything', 'bad', 'invalid', 'wrong').is_valid
		False
		"""
		return cls([[A, B], [C, D]])

	def is_trivial(self):
		"""
		Check whether the analogy is trivial, i.e. of the form
			A : A :: B : B or
			A : B :: A : B.
		"""
		return (self.A == self.B and self.C == self.D) or \
				(self.A == self.C and self.B == self.D)

	def TwoRatios(self):
		"""
		Check that there are exactly two ratios.
		A ratio is a list of two strings.
		"""
		return len(self) == 2 and all(len(ratio) == 2 for ratio in self)
	
	def CharacterOccurrenceConstraint(self):
		"""
		Check the character occurrence constraint which states that:
			|A|_a + |D|_a = |B|_a + |C|_a, for any character a,
		where |X|_a stands for the number of occurrences of character a in string X.
		
		>>> Analogy.fromFile('a : aa :: aaa : aaaa').CharacterOccurrenceConstraint()
		True
		>>> Analogy.fromFile('toto : popo :: tata : apap').CharacterOccurrenceConstraint()
		True
		>>> Analogy.fromFile('toto : popo :: tata : apapa').CharacterOccurrenceConstraint()
		False
		>>> Analogy.fromFile('abc : abd :: efg : efh').CharacterOccurrenceConstraint()
		False
		"""
		return Counter(self.A) + Counter(self.D) == Counter(self.B) + Counter(self.C)

	def DistanceConstraint(self):
		"""
		Check the distance constraint which states that:
			d(A, B) = d(C, D) and
			d(A, C) = d(B, D),
		where d(X, Y) stands for the LCS distance between strings X and Y.
		This distance uses only insertion and deletion as edit operations.
		LCS stands for longest common subsequence.
		
		>>> Analogy.fromFile('a : aa :: aaa : aaaa').DistanceConstraint()
		True
		>>> Analogy.fromFile('toto : popo :: tata : apap').DistanceConstraint()
		True
		>>> Analogy.fromFile('toto : popo :: tata : apapa').DistanceConstraint()
		False
		>>> Analogy.fromFile('abc : abd :: efg : efh').DistanceConstraint()
		True
		"""
		return fast_distance(self.A, self.B) == fast_distance(self.C, self.D) and \
				fast_distance(self.A, self.C) == fast_distance(self.B, self.D)

################################################################################

class ListOfAnalogies(ListOfClusters):
	"""
	Class for a list of analogies.
	"""

	def __init__(self, analogies):
		"""
		Create a list of analogies.
		The functionality of this initialization is to discard invalid analogies.
		"""
		ListOfClusters.__init__(self, clusters=[analogy for analogy in analogies if analogy.is_valid and not analogy.is_trivial])

	@classmethod
	def fromFile(cls, file=sys.stdin):
		"""
		Read a list of analogies from a file.
		The file should contain one analogy per line.
		Each line should be of the form
			
			A : B :: C : D
		
		where A, B, C and D are strings of characters.
		*** Invalid and trivial analogies will be discarded. ***

		>>> ListOfAnalogies.fromFile(['a : aa :: aaa : aaaa', 'abc : abd :: efg : efh', 'b : bb :: bbb : bbbb'])
		a : aa :: aaa : aaaa
		b : bb :: bbb : bbbb
		"""
		return cls(Analogy.fromFile(line) for line in file)

	@classmethod
	def fromCluster(cls, cluster):
		"""
		Enumerate all the analogies contained in an analogical cluster.
		*** Invalid and trivial analogies will be discarded. ***
		"""
		analogies = []
		cluster = list(set((tuple(ratio) for ratio in cluster)))
		for i1, AB in enumerate(cluster):
			for CD in cluster[i1+1:]:
				analogies.append(Analogy([AB, CD]))
		return cls(analogies)

	@classmethod
	def fromListOfClusters(cls, list_of_clusters):
		"""
		Enumerate all the analogies contained in a list of analogical clusters.
		*** Invalid and trivial analogies will be discarded. ***
		"""
		return cls(flatten(ListOfAnalogies.fromCluster(cluster) for cluster in list_of_clusters))
