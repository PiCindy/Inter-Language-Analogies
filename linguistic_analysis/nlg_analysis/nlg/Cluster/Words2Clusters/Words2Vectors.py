#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import collections

import nlg.NlgSymbols as NlgSymbols

from nlg.Cluster.Words2Clusters.Indistinguishables import Indistinguishables

#...!....1....!....2....!....3....!....4....!....5....!....6....!....7....!....8
################################################################################

__author__ = 'Yves Lepage <yves.lepage@dwaseda.jp>'
__date__, __version__ = '14/04/2017', '1.0'
__date__, __version__ = '24/08/2017', '1.1'		# Create and extract class Indistinguishables.
__description__ = """
	Outputs vectors of character or morphological features
	for each word given on a line in a file.
"""

__verbose__ = False
__trace__ = False

################################################################################

class Words(list):

	def __init__(self, file=sys.stdin, lemmas=False):
		# Read the words.
		words = [ line.strip() for line in file ]
		# Delete empty words and sort.
		words = sorted([ line for line in words if line != '' ])
		# Delete repeated words.
		words = set(words)
		# Make a list.
		list.__init__(self, words)
		# Determine the type of line.
		self.is_sigmorphon = self.sigmorphon_format()
		# If SIGMORPHON format, check for lemmas or not as features.
		self.has_lemmas = lemmas

	def sigmorphon_format(self):
		split_result = self[0].split('\t')
		result = len(split_result) == 3
		if result:
			if ',' in split_result[1] or '=' in split_result[1]:
				self.sigmorphon_year = 2016
			elif ';' in split_result[2]:
				self.sigmorphon_year = 2017
			else:
				print('Error: cannot determine the year for SIGMORPHON format.', file=sys.stderr)
				exit(-1)
		return result

	def __iter__(self):
		for line in list.__iter__(self):
			if self.is_sigmorphon:
				if self.sigmorphon_year == 2016:
					lemma, features, form = line.split('\t')
				elif self.sigmorphon_year == 2017:
					lemma, form, features = line.split('\t')
				yield lemma, set(['LEMMA=YES'])
				features = [ feature.strip() for feature in features.split(',') ]
				if self.has_lemmas: features += ['LEMMA=%s' % lemma]
				features = set(features)
			else:
				form, features = line, set(line)
			yield form, features

	def __repr__(self):
		return '\n'.join(self)

################################################################################

class FeatureVectors(dict):

	def __init__(self, words=None, char_features=False):
		self.char_features = char_features
		if words == None:
			self.is_sigmorphon = False
			self.feature_list = None
			dict.__init__(self)
		else:
			self.is_sigmorphon = words.is_sigmorphon
			self.feature_list = self._get_feature_list(words)
			# Write the features for each form on a line.
			dict.__init__(self, self._get_dict(words))
		self.indistinguishables = Indistinguishables.fromFeatureVectors(self)
		if __trace__: print('# FeatureVectors = \n%s' % self, file=sys.stderr)
	
	def get_distinguishables(self):
		"""
		Return a list of words which are all distinguishables.
		"""
		return { word: self[word] for word in self.indistinguishables }
	
	def _get_feature_list(self, words):
		if __trace__: print('# Compute feature list...', file=sys.stderr)
		if words.is_sigmorphon and not self.char_features:
			feature_line_list = [ features for _, features in words ]
		else:
			feature_line_list = [ set(form) for form, _ in words ]
		# Make a sorted list of the features to ensure the same order
		# when writing the vectors for each word form.
		result = sorted(list(set.union(*feature_line_list)))
		if __trace__: print('# Feature list = %s' % result, file=sys.stderr)
		return result

	def _get_feature(self, form, feature, features):
		if self.is_sigmorphon and not self.char_features:
			# Feature of the form FEATURE=VALUE for SIGMORPHON.
			return 1 if feature in features else 0
		else:
			# Character feature in the usual case.
			return form.count(feature)

	def _get_dict(self, words):
		if __trace__: print('# Compute feature vectors...', file=sys.stderr)
		# Write the features for each form on a line.
		return { form : tuple( self._get_feature(form, feature, features) for feature in self.feature_list ) \
								for form, features in words }

	def __add__(self, other):
		if __trace__: print('# Adding feature vectors...', file=sys.stderr)
		result = FeatureVectors()
		result.feature_list = self.feature_list + other.feature_list
		result.update({ key: self[key] + other[key] for key in self if key in other })
		return result

	def __repr__(self):
		if __trace__: print('# Feature list = %s' % self.feature_list, file=sys.stderr)
		return '\n'.join(
					[ '{}'.format(self.indistinguishables) ] +
					[ '{}\t{}'.format(word, tuple(self[word])) \
						for word in self.indistinguishables ]
				)

################################################################################

def read_argv():

	from argparse import ArgumentParser
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = """%(prog)s  <  INPUT_FILE
	
	The input file should
	1. either contain one word per line:
		<line>			::= <word form>
	
	E.g., on input file
		child
		children
		plays
	the output is:
		child	(0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0)
		children	(0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0)
		plays	(1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1)

		
	2. or it should be in the SIGMORPHON format:
	in year 2016:
		<line>			::= <lemma> \t <features> \t <word form>
		<features>		::= <feature> [, <feature>]
		<feature>		::= <feature name>=<feature value>
	in year 2017:
		<line>			::= <lemma> \t <word form> \t <features>
		<features>		::= <feature> [; <feature>]
		<feature>		::= <feature value>
	in both years:
		<lemma>			::= string of characters
		<word form>		::= string of characters
		<feature name>	::= string of characters with no space
		<feature value>	::= string of characters with no space
	
	E.g., on input file (SIGMORPHON 2016 format)
		child	CAT=N,NBR=SG	child
		child	CAT=N,NBR=PL	children
		play	CAT=V,NBR=SG,PERS=3	plays
	the output is:
		child	(0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0)
		children	(0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0)
		play	(1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0)
		plays	(1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1)
	"""

	parser = ArgumentParser(description=this_description, usage=this_usage, epilog=this_version)
	parser.add_argument('-L', '--lemmas',
                  action='store_true', dest='lemmas', default=False,
                  help='add the lemmas as features (default: no lemma)')
	parser.add_argument('-V', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')
	return parser.parse_args()

################################################################################

if __name__ == '__main__':
	options = read_argv()
	__verbose__ = options.verbose
	t1 = time.time()
	filewords = sys.stdin.read().split('\n')
	words = Words(filewords, lemmas=options.lemmas)
	if words.is_sigmorphon:
		print(FeatureVectors(words, char_features=True) + FeatureVectors(words))
	else:
		print(FeatureVectors(words, char_features=True))
	if __verbose__: print('# Processing time: ' + ('%.2f' % (time.time() - t1)) + 's', file=sys.stderr)

	
	
