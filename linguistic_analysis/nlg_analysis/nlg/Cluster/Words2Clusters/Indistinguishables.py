#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import collections

import nlg.NlgSymbols as NlgSymbols

#...!....1....!....2....!....3....!....4....!....5....!....6....!....7....!....8
################################################################################

__author__ = 'Yves Lepage <yves.lepage@dwaseda.jp>'
__date__, __version__ = '24/04/2017', '1.0'
__description__ = """
	Build the list of indistinguishable words
	for a list of words with their feature vectors.
"""

__verbose__ = False
__trace__ = False

###############################################################################

class Indistinguishables(dict):
	"""
	Indistinguishables is a dictionary.
	A key is a word and the values are all words with the same feature vector
	(including itself)
	"""

	@classmethod
	def fromFile(cls, file=sys.stdin):
		"""
		Build the list of indistinguishable words
		from lines of equalities, format shown below.
		The last line to stop reading should be an empty line starting with #.
		
		# word1 == word2 == word3 == ...
		#
		"""
		# Build an inverse dictionary where the keys are the vectors
		# and the value is the list of of all
		indistinguishables = dict()
		for line in file:
			if line.startswith(NlgSymbols.comment):
				# Comment line.
				if NlgSymbols.duplicate in line:
					# Line commented giving indistinguishable objects.
					# Remove comment symbol, heading spaces and trailing spaces.
					line = line[len('{}'.format(NlgSymbols.comment)):].strip()
					# Remember in a dictionary.
					As = sorted([ A.strip() for A in line.split(NlgSymbols.duplicate) ])
					indistinguishables[As[0]] = As
					if __trace__: print(indistinguishables, file=sys.stderr)
				else:
					# The last line should be an empty line,
					# or any commented line not containing the duplicate symbol.
					break
		return cls(indistinguishables)

	@classmethod
	def fromFeatureVectors(cls, words_to_vectors):
		"""
		Build the list of indistinguishable words
		from a list of feature vectors.
		"""
		# Build an inverse dictionary where the keys are the vectors
		# and the value is the list of of all
		vectors_to_words = collections.defaultdict(set)
		for word, vector in words_to_vectors.items():
			vectors_to_words[vector].add(word)
		# Cast the sets to a list to be able to access the first element easily afterwards.
		vectors_to_words = { k: sorted(list(v)) for k, v in vectors_to_words.items() }
		# Return a dictionary of first word with all words with same feature vector.
		return cls({ v[0] : v for v in list(vectors_to_words.values()) })
		
	def all(self, word):
		"""
		Return all objects which are indistinguishable from word.
		If word did not exist in self,
		then return word itself,
		as it is trivially indistinguishable from itself.
		"""
		return self[word] if word in self else [word]

	def __repr__(self):
	
		def indistinguishables_line_repr(indistinguishable_list):
			return '{} '.format(NlgSymbols.comment) \
					+ '{}'.format(NlgSymbols.duplicate).join('{}'.format(word) \
							for word in indistinguishable_list)

		return '\n'.join(
					[ indistinguishables_line_repr(self[word]) for word in self if len(self[word]) > 1 ] +
					[ '{} '.format(NlgSymbols.comment) ]
				)

