#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools

from setuptools import setup, Extension

setup(name = 'nlg',
	version = '3.2.1',
	description = 'Analogical clustering',
	author = 'Rashel Fam & Yves Lepage',
	author_email = 'fam.rashel@fuji.waseda.jp & yves.lepage@waseda.jp',
	ext_modules =	[Extension('_nlg',
						sources = ['nlg/Analogy/C/nlg.i', 'nlg/Analogy/C/nlg.c', 'nlg/Analogy/C/utf8.c'],
						# swig_opts=['-modern', '-new_repr'], # Comment this line if you have newer version of swig
						extra_compile_args = ['-std=c99']),
					 Extension('_nlgclu',
						sources = ['nlg/Cluster/Words2Clusters/nlgclu_in_C/nlgclu.i', 'nlg/Cluster/Words2Clusters/nlgclu_in_C/nlgclu.c'],
						# swig_opts=['-modern', '-new_repr'] # Comment this line if you have newer version of swig
					)],
	# packages=['nlg'],
	packages = setuptools.find_packages(),
	install_requires=[
		  'tabulate',
          'numpy',
		  'matplotlib'
      ],
	python_requires = '>=3.5'
	)
