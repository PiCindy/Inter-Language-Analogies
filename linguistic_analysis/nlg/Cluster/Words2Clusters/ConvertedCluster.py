#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from nlg.Cluster.Cluster import Cluster, ListOfClusters

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '23/08/2017', '1.0'			# Creation.
__description__ = """Convert clusters containing integers to clusters with words
by using two dictionaries giving the mapping from integers to words.
One dictionary for the As and another one for the Bs for a cluster A1 : B1 :: A2 : B2 : ....
"""

__verbose__ = False
__trace__ = False

###############################################################################

class ConvertedCluster(Cluster):

	def __init__(self, cluster, dictA, dictB=None):
		"""
		Convert a cluster.
		Input: self is a cluster with keys.
		Output: result is a cluster with the values corresponding to the keys.
		
		>>> dictA = ['a', 'aa', 'aaa', 'aaaa']
		>>> ConvertedCluster(Cluster.fromFile("0 : 1 :: 2 : 3"), dictA)
		a : aa :: aaa : aaaa
		"""
		if dictB == None: dictB = dictA
		if isinstance(dictA, list):
			# The dictionaries are lists,
			# convert the keys (strings) converted into integers
			# before using them (list[i] where i is an integer).
			convert_key = lambda x: int(x)
		else:
			# Use the key as is.
			convert_key = lambda x: x
		result = list()
		for ratio in cluster:
			iA, iB = ratio
			iA, iB = convert_key(iA), convert_key(iB)
			ratio = [dictA[iA], dictB[iB]]
			result.append(ratio)
		Cluster.__init__(self, result)

###############################################################################

class ListOfConvertedClusters(ListOfClusters):

	def __init__(self, list_of_clusters, dictA, dictB=None):
		"""
		Convert a cluster file.
		Input: self is a cluster file with integers.
		Output: result is a cluster file with the lines corresponding to the integers.
		
		>>> dictA = ['a', 'aa', 'aaa', 'aaaa']
		>>> ListOfConvertedClusters(ListOfClusters.fromFile(["0 : 1 :: 2 : 3"]), dictA)
		#
		a : aa :: aaa : aaaa
		>>> ListOfConvertedClusters(ListOfClusters.fromFile(["0 : 1 :: 2 : 3", "3 : 1 :: 2 : 0"]), dictA)
		#
		a : aa :: aaa : aaaa
		aaaa : aa :: aaa : a
		>>> ListOfConvertedClusters(ListOfClusters.fromFile(["# ab == ba", "#", "0 : 1 :: 2 : 3"]), dictA)
		#
		a : aa :: aaa : aaaa
		"""
		clusters = list()
		for cluster in list_of_clusters:
			clusters.append(ConvertedCluster(cluster, dictA, dictB))
		ListOfClusters.__init__(self, clusters=clusters, indistinguishables=list_of_clusters.indistinguishables)



	
	
