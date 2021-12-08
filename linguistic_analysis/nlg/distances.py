#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from _fast_distance import init_memo_fast_distance, memo_fast_distance

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '29/08/2017', '1.0'			# Creation.

###############################################################################

words = open('tmp.wrd').readlines()

d = dict()
for i1, word1 in enumerate(words):
	if not word1.startswith('#'):
		if word1 not in d: d[word1] = dict()
		init_memo_fast_distance(word1.decode('UTF-8'))
		for word2 in words[i1+1:]:
			d[word1][word2] = memo_fast_distance(word2.decode('UTF-8'))
