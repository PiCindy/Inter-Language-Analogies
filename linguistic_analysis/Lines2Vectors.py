#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import time

from argparse import ArgumentParser, ArgumentTypeError

from nlg.Vector.Vectors import Vectors
###############################################################################

__author__ = 'Fam Rashel <fam.rashel@fuji.waseda.jp>'
__date__, __version__ = '03/09/2020', '1.00' # Creation
__description__ = 'Produce vectors from list of words'

###############################################################################

def read_argv():
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = '''%(prog)s  <  FILE_OF_LEMMA_tab_WORDFORM_tab_FEATURES
	'''

	parser = ArgumentParser(description=this_description, usage=this_usage, epilog=this_version)
	parser.add_argument('-d', '--decompose',
                  action='store_true', dest='decompose', default=False,
                  help='decompose multi-value features into independent vector dimension (not yet implemented')
	parser.add_argument('--char_feature',
                  action='store', dest='char_feature', type=str2bool, default=True,
                  help='use character feature (default: True)')
	parser.add_argument('--token_feature',
                  action='store', dest='token_feature', type=str2bool, default=False,
                  help='use character feature (default: False)')
	parser.add_argument('--token_delimiter',
                  action='store', dest='token_delimiter', type=str, default=' ',
                  help='delimiter for tokenisation of token feature')
	parser.add_argument('-s', '--sigmorphon',
                  action='store_true', dest='sigmorphon', default=False,
                  help='sigmorphon data')
	parser.add_argument('--morph_feature',
                  action='store', dest='morph_feature', type=str2bool, default=False,
                  help='use MSD feature (default: False)')
	parser.add_argument('--morph_delimiter',
                  action='store', dest='morph_delimiter', type=str, default=';',
                  help='delimiter for MSD feature')
	parser.add_argument('-L', '--lemma_feature',
                  action='store_true', dest='lemma_feature', default=False,
                  help='build vector dimension for lemmas (SIGMORPHON data)')
	parser.add_argument('-l', '--gen-lemma',
                  action='store_true', dest='gen_lemma', default=True,
                  help='generate separated vectors for lemmas (SIGMORPHON data)')
	parser.add_argument('-V', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')

	return parser.parse_args()

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')

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
	if options.verbose: print('# Reading file...', file=sys.stderr)
	lines = []
	for i, line in enumerate(sys.stdin):
		if options.sigmorphon:
			lemma, wordform, raw_features = line.rstrip('\n').split('\t')
			features = raw_features.split(options.morph_delimiter)
			lines.append((wordform, lemma, features))
		else:
			lines.append(line.rstrip('\n'))
		if options.verbose: print('\r# Number of lines read: {}\t'.format(i+1), end='', file=sys.stderr)
		
	if options.verbose:
		print('\n# Building vector with feature...', file=sys.stderr)
		print(f"#\t- char : {options.char_feature}", file=sys.stderr)
		print(f"#\t- token: {options.token_feature}", file=sys.stderr)
		print(f"#\t- morph: {options.morph_feature}", file=sys.stderr)
		print(f"#\t- lemma: {options.lemma_feature}", file=sys.stderr)
	
	if options.sigmorphon:
		print(Vectors.fromSigmorphonFile(lines=lines,
									char_feature=options.char_feature,
									morph_feature=options.morph_feature,
									lemma_feature=options.lemma_feature,
									gen_lemma=options.gen_lemma))
	else:
		print(Vectors.fromFile(lines=lines,
					char_feature=options.char_feature,
					token_feature=options.token_feature,
					token_delimiter=options.token_delimiter))
	if options.verbose: print(f'# {os.path.basename(__file__)} - Processing time: {(convert_time(time.time() - t_start))}', file=sys.stderr)