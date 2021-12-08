#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '08/04/2017', '1.0'			# Creation.
__description__ = """Symbols and formats for
ratios, analogies, analogical clusters and analogical grids.
"""

###############################################################################

ratio					= ' : '
conformity				= ' :: '
# ratio					= ' ∶ '		# ISO 10646 (Unicode) U+2236 Ratio (1 single character)
# conformity_symbol		= ' ∷ '		# ISO 10646 (Unicode) U+2237 Proportion (1 single character)

comment					= '#'
duplicate				= ' == '

omega					= '*'
zero_symbol				= '_'

ratio_fmt				= ('%s' + ratio + '%s')					# '%s : %s'
nlg_fmt					= (ratio_fmt + conformity + ratio_fmt)	# '%s : %s :: %s : %s'
imp_fmt	 				= '%s' + ratio + 'x  =>  x = %s'
