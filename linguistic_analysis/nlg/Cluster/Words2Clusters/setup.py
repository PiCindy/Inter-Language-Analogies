#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, Extension

setup(name = 'nlgclu_in_C',
	version = '2.0',
	description = 'Analogical clustering',
	author = 'Yves Lepage',
	author_email = 'yves.lepage@waseda.jp',
	ext_modules =	[Extension('_nlgclu',
						sources = ['nlgclu_in_C/nlgclu.i', 'nlgclu_in_C/nlgclu.c'],
						swig_opts=['-modern', '-new_repr']
					)],
	)

# IGNORE THIS SETUP FILE (DEPRECATED)
# Please use the setup.py in the top directory instead

# Use the following command to compile (-e is optional):
# sudo -H pip install [-e] .

# Use the following command to test the help:
# python2 nlgclu.py -h

# Use the following commands to test the execution:
# printf "toto\ntata\npopo\npapa\n" | python2 Words2Vectors.py | python2 nlgclu.py -V
