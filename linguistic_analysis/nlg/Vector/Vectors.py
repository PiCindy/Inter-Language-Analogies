#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import re

import nlg.NlgSymbols as NlgSymbols

from collections import defaultdict

from nlg.Cluster.Words2Clusters.Indistinguishables import Indistinguishables
###############################################################################

__author__ = 'Fam Rashel <fam.rashel@fuji.waseda.jp>'
__date__, __version__ = '10/04/2017', '1.00' # Creation

__date__, __version__ = '30/08/2021', '1.1'	# Add alphabet as an argument to fromFile method in Vectors.
											# Modifications of _build_vector method. Addition of a conditional statement for alphabet as an argument.

__description__ = 'Class for vector representation of string for nlgclu input'

__verbose__ = True
__trace__ = False

###############################################################################

def inverse_dictionary(dictionary):
	""" Inverse key and value of given dictionary """
	result = defaultdict(list)
	for key, value in dictionary.items():
		result[str(value)].append(key)
	return result

def print_duplicates(alphagrams):
	""" Print strings that represented by the same vector """
	for aword in alphagrams:
		parangon = alphagrams[aword][0]
		for word in alphagrams[aword][1:]:
			print('{} {}{}{}'.format(NlgSymbols.comment,
						parangon.replace(':','\\:'),
						NlgSymbols.duplicate,
						word.replace(':','\\:')))

###############################################################################

class Vectors(defaultdict):

	"""
	Class for vector representations of strings.
	Possible dimensions:
		- Alphabet
		- Tokens (given a separator)
		- Morphological features (mainly for SIGMORPHON file)
		- Lemmas (mainly for SIGMORPHON file)

	word: (value, value, value, ...)
	"""
	def __init__(self):
		self.feature_list = None
		defaultdict.__init__(self, tuple)
		self.indistinguishables = Indistinguishables.fromFeatureVectors(self)

	# RH modified on 18/08/2021
	@classmethod
	def fromFile(cls, lines=None, alphabet=None, char_feature=True, token_feature=False, token_delimiter=" "):
		vectors = cls()
		if lines != None:
			lines = [ line.strip() for line in lines ]
			vectors._build_vector(lines,
							alphabet,
							char_feature=char_feature,
							token_feature=token_feature,
							token_delimiter=token_delimiter)
			vectors.indistinguishables = Indistinguishables.fromFeatureVectors(vectors)
		return vectors

	@classmethod
	def fromSigmorphonFile(cls, lines, char_feature=True, morph_feature=True, lemma_feature=False, gen_lemma=True):
		vectors = cls()
		vectors.feature_list = defaultdict(list)
		vectors.lemma_list = defaultdict(list)
		words = set()
		lines = [ line.strip().split('\t') for line in lines ]
		for line in lines:
			if len(line) == 3:
				lemma,form,features = line
				vectors.feature_list[form] = features
				vectors.lemma_list[form] = lemma
				words.add(form)
				if gen_lemma:
					vectors.feature_list[lemma] = [ "LEMMA" ]
					vectors.lemma_list[lemma] = lemma
					words.add(lemma)
		vectors._build_vector(list(words),
						char_feature=char_feature,
						morph_feature=morph_feature,
						lemma_feature=lemma_feature)
		vectors.indistinguishables = Indistinguishables.fromFeatureVectors(vectors)
		return vectors

	@classmethod
	def fromListOfVectors(cls, lines):
		vectors =  cls()
		for line in lines:
			if re.match(rf"^{NlgSymbols.comment}", line) is None: # Not comment lines
				word, vector = line.strip().split('\t')
				vector = vector.replace('(', '')
				vector = vector.replace(')', '')
				if len(vector.split(', ')) > 1:
					vector = tuple(map(int, vector.split(', ')))
				elif len(vector.split(', ')) == 1:
					vector = tuple(map(int, vector.split(',')[0]))
				else: # vector's length = 0
					vector = tuple()
				vectors[word] = vector
		# Get the indistinguishable lines
		vectors.indistinguishables = Indistinguishables.fromFeatureVectors(vectors)
		return vectors

	# RH modified on 18/08/2021
	def _build_vector(self, lines, alphabet=None, char_feature=True, token_feature=False, morph_feature=False, lemma_feature=False, token_delimiter=" ", ):
		# Defining vector dimension
		self.dimension = []
		if char_feature:
			if alphabet is None: # RH added on 18/08/2021
				dim_alphabet = self._build_char_dim(lines)
				self.dimension += dim_alphabet
				if __verbose__: print(f"# Alphabet size: {len(dim_alphabet)}", file=sys.stderr)
				if __trace__: print(f"# Alphabet computed: {' '.join( '%c' % c for c in dim_alphabet )}", file=sys.stderr)
			else: # RH added on 18/08/2021
				dim_alphabet = alphabet # RH added on 18/08/2021
		if token_feature:
			dim_token = self._build_dim_by_separator(lines, delimiter=token_delimiter)
			self.dimension += dim_token
			if __verbose__: print(f"# Token size: {len(dim_token)}", file=sys.stderr)
			if __trace__: print(f"# Token computed: {' '.join( '%s' % c for c in dim_token )}", file=sys.stderr)
		if morph_feature:
			dim_features = self._build_morph_dim()
			self.dimension += dim_features
			if __verbose__: print(f"# Morph feature size: {len(dim_features)}", file=sys.stderr)
			if __trace__: print(f"# Morph feature computed: {' '.join( '%s'.encode('utf-8') % s for s in dim_features )}", file=sys.stderr)
			if lemma_feature:
				dim_lemmas = self._build_lemmas_dim()
				self.dimension += dim_lemmas
				if __verbose__: print(f"# Lemma feature size: {len(dim_lemmas)}",file=sys.stderr)
				if __trace__: print(f"# Lemma feature computed: {' '.join( '%s'.encode('utf-8') % s for s in dim_lemmas )}", file=sys.stderr)

		# Build vector representation for each line
		for line in lines:
			vector = tuple()
			if char_feature:
				vector += tuple( line.count(char) for char in dim_alphabet )
			if token_feature:
				vector += tuple( line.split(token_delimiter).count(token) for token in dim_token )
			if morph_feature:
				vector += tuple( self.feature_list[line].count(feature) for feature in dim_features )
				if lemma_feature:
					vector += tuple( 1 if self.lemma_list[line] == lemma else 0 for lemma in dim_lemmas )
			self[line] = vector

	def _build_char_dim(self, lines):
		""" Build vector dimension for the alphabet """
		return sorted(list(frozenset( c for line in lines for c in line )))

	def _build_dim_by_separator(self, lines, delimiter):
		""" Build vector dimension from the string tokenised by the given separator """
		return sorted(list(frozenset( token for line in lines for token in line.split(delimiter) )))

	def _build_morph_dim(self):
		""" Build the vector dimension for morphological features """
		return sorted(list(frozenset( f for w in self.feature_list.keys() for f in self.feature_list[w] )))

	def _build_lemmas_dim(self):
		""" Build vector dimension for lemmas """
		return sorted(list(frozenset( lemma for lemma in self.lemma_list.values() )))

	def get_distinguishables(self):
		""" Return only strings that are distinguishable """
		return { line : self[line] for line in self.indistinguishables }

	def __repr__(self):
		# Old way to get indistinguishables
		# vectors_to_lines = inverse_dictionary(self)
		# print_duplicates(vectors_to_lines) # Print indistunguishable lines
		# vectors = { vectors_to_lines[vector][0] : vector  for vector in vectors_to_lines }
		# return '\n'.join( '%s\t%s' % (key, tuple(self[key])) for key in sorted(vectors.keys()) ) # Print distinguishable lines
		# return '\n'.join( '%s\t%s' % (key, tuple(self[key])) for key in sorted(self.keys()) ) # Print all

		return '\n'.join(
			[ f'{self.indistinguishables}' ] +
			[ f'{key}\t{tuple(self[key])}' for key in self.indistinguishables ])
