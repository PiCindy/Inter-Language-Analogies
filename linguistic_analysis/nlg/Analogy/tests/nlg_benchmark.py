#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import doctest
import time
import random
 
sys.path.append('/Users/ylepage/ylepage/python/') # path to personal library
from _nlg import solvenlg, verifnlg

###############################################################################

__author__ = 'Yves Lepage <yves.lepage@waseda.jp>'
__date__, __version__ = '18/06/2013', '1.0'	# Creation
__date__, __version__ = '20/06/2013', '1.1'	# Added switch for statistical measures.
											# Added linguistic and formal examples.
__description__ = 'Unitary tests for library _nlg.'

__verbose__ = False

__nlg_fmt__ = '%s : %s :: %s : %s'

###############################################################################

def read_argv():

	from optparse import OptionParser
	this_version = 'v%s (c) %s %s' % (__version__, __date__.split('/')[2], __author__)
	this_description = __description__
	this_usage = '''%prog
	Run %prog -T for unitary tests.
	Run %prog -r 1000000 for some stats on runtimes.
	'''

	parser = OptionParser(version=this_version, description=this_description, usage=this_usage)
	parser.add_option('-L', '--max-len',
                  action='store', dest='strlen', type=int, default=8,
                  help='maximum length of strings (default: %default)')
	parser.add_option('-V', '--vocabulary-size',
                  action='store', dest='vocsize', type=int, default=8,
                  help='maxmum size of the vocabulary size for random generation of strings (default: %default)')
	parser.add_option('-r', '--repeat-number',
                  action='store', dest='repeat', type=int, default=1000,
                  help='repeat analogy solving between random strings REPEAT times (default: %default)')
	parser.add_option('-s', '--statistics',
                  action='store_true', dest='statistics', default=False,
                  help='output success rates and computation times '
				  		'for all values of vocabulary size and string lengths '
						'until the ones passed as arguments to the options')
	parser.add_option('-v', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='runs in verbose mode')
	parser.add_option('-T', '--test',
                  action='store_true', dest='test', default=False,
                  help='run all unitary tests')
						
	(options, args) = parser.parse_args()
	return options, args

###############################################################################

def random_word(alphabetsize, length):
	return ''.join([ chr(ord('a')+random.randint(0,alphabetsize-1)) for _ in range(length) ])

def is_analogy(s):
	A, B, _, C, D = [ str.strip() for str in s.split(':') ]
	return 1 == verifnlg(A, B, C, D)

def confirm_analogy(s):
	A, B, _, C, D = [ str.strip() for str in s.split(':') ]
	return D == solvenlg(A, B, C)

def _test():
   import doctest
   doctest.testmod()
   sys.exit(0)

def main(repeat=1000, vocsize=8, strlen=8):
	"""
	>>> solvenlg('aslama','muslim','arsala')
	'mursil'
	>>> solvenlg('abc','aabbcc','aaabbbccc')
	'aaaabbbbcccc'
	>>> '' == solvenlg('aaa','aa','a')
	True
	>>> None == solvenlg('aaa','aa','a')
	False
	>>> solvenlg('aaa','aa','a')
	''
	>>> print(solvenlg('aaa','aa','a'))
	<BLANKLINE>
	>>> None == solvenlg('aaac','aa','a')
	True
	>>> '' == solvenlg('aaac','aa','a')
	False
	>>> solvenlg('aaac','aa','a')

	>>> print(solvenlg('aaac','aa','a'))
	None
	>>> verifnlg('aslama','muslim','arsala','mursil')
	1
	>>> verifnlg('abc','aabbcc','aaabbbccc','aaaabbbbcccc')
	1
	>>> verifnlg('aaa','aa','a','')
	1
	>>> verifnlg('aaac','aa','a','')
	0
	
	The following instruction causes segmentation fault because None is not a character string.
	*** >>> verifnlg('aaac','aa','a',None)
	***	1
	
	*** LINGUISTIC EXAMPLES ***
	
	*** auf Deutsch ***
	
	>>> is_analogy( 'setzen : setzte :: lachen : lachte' )
	True
	>>> is_analogy( 'lang : längste :: scharf : schärfste' )
	True
	>>> is_analogy( 'sprechen : wir sprächen :: nehmen : wir nähmen' )
	True
	>>> is_analogy( 'sprechen : er spräche :: nehmen : er nähme' )
	True
	>>> is_analogy( 'sprechen : du sprächest :: nehmen : du nähmest'  )
	True
	>>> is_analogy( 'sprechen : ihr sprächet :: nehmen : ihr nähmet' )
	True
	>>> is_analogy( 'sprechen : ihr aussprächet :: nehmen : ihr ausnähmet' )
	True
	>>> is_analogy( 'fliehen : er floh :: schließen : er schloß' )
	True
	>>> is_analogy( 'sprechen : aussprächet :: nehmen : ausnähmet' )
	True

	*** bi llugha 'l 3arabiya ***
	
	>>> is_analogy( 'ضسمضكض : ضقسضمض :: كعسمهكعر : كعقسهمعر' )
	True
	>>> is_analogy( 'ضسمضكض : ضقسضمض :: كعسمهك : كعقسهم' )
	True
	>>> is_analogy( 'نضفضزض : نضضفهز :: سضنضوض : سضضنهر' )
	True
	>>> is_analogy( 'huzila : huzAl :: Sudi`a : SudA`' )
	True
	>>> is_analogy( 'kalb : kulaib :: masjid : musaijid' )
	True
	>>> is_analogy( 'yaSilu : yaSala :: yasimu : yasama' )
	True
	>>> is_analogy( 'aslama : arsala :: muslimun : mursilun' )
	True
	>>> is_analogy( 'aslama : arsala :: muslim : mursil' )
	True
	>>> is_analogy( 'kataba : kAtib :: sakana : sAkin' )
	True
	>>> is_analogy( 'huzila : huzAl :: Sudi`a : SudA`' )
	True

	*** Akkadien ***
	
	>>> is_analogy( 'ukaSSad : uktanaSSad :: uSakSad : uStanakSad' )
	True

	*** Hébreu ***
	
	>>> is_analogy( 'iahmod : mahmAd :: ia`abor : ma`abAr' )
	True

	*** Proto-sémitique ***
	
	>>> is_analogy( 'yaqtilu : qatil :: yuqtilu : qutil' )
	True
	>>> is_analogy( 'yasriqu : sariq :: yanqimu : naqim' )
	True

	*** 普通话 ***

	>>> is_analogy( '一年，是我国社会主义 : 一年是我国 :: ，社会主义 : ' )
	True
	>>> is_analogy( '科学 : 科学家 :: 政治 : 政治家' )
	True
	>>> is_analogy( '我 : 我们 :: 他 : 他们' )
	True
	>>> is_analogy( '今年 : 今天 :: 明年 : 明天' )
	True
	>>> is_analogy( '读 : 读者 :: 学 : 学者' )
	True
	>>> is_analogy( '勇 : 勇者 :: 强 : 强者' )
	True
	>>> is_analogy( '车 : 车行 :: 药 : 药行' )
	True
	>>> is_analogy( '学 : 学院 :: 医 : 医院' )
	True
	>>> is_analogy( '工程 : 工程师 :: 理发 : 理发师' )
	True
	>>> is_analogy( 'kexue : kexuejia :: zhengzhi : zhengzhijia' )
	True
	>>> is_analogy( 'wo : women :: ta : tamen' )
	True
	>>> is_analogy( 'jinnian : jintian :: mingnian : mingtian' )
	True
	>>> is_analogy( 'du : duzhe :: xue : xuezhe' )
	True
	>>> is_analogy( 'AduA : AduzheA :: AxueA : AxuezheA' )
	True
	>>> is_analogy( 'yong : yongzhe :: qiang : qiangzhe' )
	True
	>>> is_analogy( 'che : chehang :: yao : yaohang' )
	True
	>>> is_analogy( 'xue : xueyuan :: yi : yiyuan' )
	True
	>>> is_analogy( 'gongcheng : gongchengshi :: lifa : lifashi' )
	True

	*** en français ***

	>>> is_analogy( 'dues : indu :: nées : inné' )
	True
	>>> is_analogy( 'inné : nées :: indu : dues' )
	True
	>>> is_analogy( 'réaction : réactionnaire :: répression : répressionnaire' )
	True
	>>> is_analogy( 'aimer : ils aimaient :: marcher : ils marchaient' )
	True
	>>> is_analogy( 'pardonner : impardonnable :: décorer : imdécorable' )
	True
	>>> is_analogy( 'joindre : je joins :: oindre : je oins' )
	True
	>>> is_analogy( 'logique : logiciel :: ludique : ludiciel' )
	True
	>>> is_analogy( 'prendrai : prendre :: viendrai : viendre' )
	True
	>>> is_analogy( 'changer : tu changes :: observer : tu observes' )
	True
	>>> is_analogy( 'marcher : tu marches :: démenager : tu démenages' )
	True
	>>> is_analogy( 'préférer : je préfère :: vénérer : je vénère' )
	True
	>>> is_analogy( 'préférer : je préfère :: révérer : je révère' )
	True
	>>> is_analogy( 'préférer : je préfère :: zébrer : je zèbre' )
	True
	>>> is_analogy( 'fini : infini :: exact : inexact' )
	True
	>>> is_analogy( "recevoir : j'ai reçu :: percevoir : j'ai perçu" )
	True
	>>> is_analogy( "décevoir : j'ai déçu :: percevoir : j'ai perçu" )
	True
	>>> is_analogy( "concevoir : j'ai conçu :: percevoir : j'ai perçu" )
	True

	*** 日本語で ***

	>>> is_analogy( '食べる : 食べます :: 認める : 認めます' )
	True
	>>> is_analogy( '痛い : 痛む :: 親しい : 親しむ' )
	True
	>>> is_analogy( 'あれ : これ :: あっち : こっち' )
	True
	>>> is_analogy( '乗る : 乗せる :: 寄る : 寄せる' )
	True
	>>> is_analogy( '自由 : 不自由な :: 用意 : 不用意な' )
	True
	>>> is_analogy( '飛びます : 飛ぶ :: 選びます : 選ぶ' )
	True
	>>> is_analogy( '飲む : 飲みます :: 進む : 進みます' )
	True
	>>> is_analogy( '飲みます : 飲んでみます :: 進みます : 進んでみます' )
	True
	>>> is_analogy( '冷める : 冷まる :: 決める : 決まる' )
	True
	>>> is_analogy( '乗る : 乗せる :: 寄る : 寄せる' )
	True
	>>> is_analogy( '新しい : 新しかった :: 嬉しい : 嬉しかった' )
	True
	>>> is_analogy( '新しい : 新しかった :: きれい : きれかった' )
	True

	*** lingua latine ***

	>>> is_analogy( 'oratorem : orator :: honorem : honor' )
	True
	>>> is_analogy( 'facio : conficio :: capio : concipio' )
	True
	>>> is_analogy( 'amo : amas :: oro : oras' )
	True
	>>> is_analogy( 'amo : amat :: oro : orat' )
	True
	>>> is_analogy( 'amo : amamus :: oro : oramus' )
	True

	*** dalam bahasa melayu ***

	>>> is_analogy( 'tinggal : ketinggalan :: duduk : kedudukan' )
	True
	>>> is_analogy( 'pekerja : kerja :: pelawat : lawat' )
	True
	>>> is_analogy( 'kawan : mengawani :: keliling : mengelilingi' )
	True
	>>> is_analogy( 'isteri : beristeri :: ladang : berladang' )
	True
	>>> is_analogy( 'keras : mengeraskan :: kena : mengenakan' )
	True

	*** po polsku ***

	True
	>>> is_analogy( 'biorąc : bierzesz :: piorąc : pierzesz' )
	True
	>>> is_analogy( 'ubezpieczony : ubezpieczeni :: obrażony : obrażeni' )
	True
	>>> is_analogy( 'spiewać : spiewaczka :: łechtać : łechtaczka' )
	True
	>>> is_analogy( 'wyszedłem : wyszłaS :: poszedłem : poszłaS' )
	True
	>>> is_analogy( 'rozproszyć : rozpraszać :: rozmnożyć się : rozmnażać się' )
	True
	>>> is_analogy( 'stworzyć : stwarzać :: rozmnożyć się : rozmnażać się' )
	True
	>>> is_analogy( 'stworzyć : stwarzać :: mnożyć się : mnażać się' )
	True
	>>> is_analogy( 'wyszedłeś : wyszłaś :: poszedłeś : poszłaś' )
	True
	>>> is_analogy( 'zgubiony : zgubieni :: zmartwiony : zmartwieni' )
	True
	>>> is_analogy( 'ṥpiewać : ṥpiewaczka :: biegać : biegaczka' )
	True

	*** in English ***

	>>> is_analogy( 'wolf : wolves :: leaf : leaves' )
	True
	>>> is_analogy( 'wolf : wolves :: calf : calves' )
	True

	*** EXEMPLES FORMELS ***

	>>> is_analogy( 'bb : ab :: ba : aa' )
	True

	>>> is_analogy( 'a : aa :: aaa : aaaa' )
	True
	>>> is_analogy( 'b : ab :: aab : aaab' )
	True
	>>> is_analogy( 'b : ba :: baa : baaa' )
	True
	>>> is_analogy( 'ab : aabb :: aaabbb : aaaabbbb' )
	True
	>>> is_analogy( 'ab : abab :: ababab : abababab' )
	True
	>>> is_analogy( 'aab : aaaabb :: aaaaaabbb : aaaaaaaabbbb' )
	True
	>>> is_analogy( 'aba : aabbaa :: aaabbbaaa : aaaabbbbaaaa' )
	True
	>>> is_analogy( 'ab : aabb :: aaaaaaabbbbbbb : aaaaaaaabbbbbbbb' )
	True
	>>> is_analogy( 'abc : aabbcc :: aaabbbccc : aaaabbbbcccc' )
	True

	>>> is_analogy( 'a : aa :: aaaaaaa : aaaaaaaa' )
	True
	>>> is_analogy( 'b : ab :: aaaaaaab : aaaaaaaab' )
	True
	>>> is_analogy( 'ab : aabb :: aaaaaaabbbbbbb : aaaaaaaabbbbbbbb' )
	True
	>>> is_analogy( 'ab : abab :: ababababababab : abababababababab' )
	True
	>>> is_analogy( 'aab : aaaabb :: aaaaaaaaaaaaaabbbbbbb : aaaaaaaaaaaaaaaabbbbbbbb' )
	True
	>>> is_analogy( 'aba : aabbaa :: aaaaaaabbbbbbbaaaaaaa : aaaaaaaabbbbbbbbaaaaaaaa' )
	True
	>>> is_analogy( 'aab : aaaabb :: aaaaaaaaaaaaaabbbbbbb : aaaaaaaaaaaaaaaabbbbbbbb' )
	True
	>>> is_analogy( 'abc : aabbcc :: aaaaaaabbbbbbbccccccc : aaaaaaaabbbbbbbbcccccccc' )
	True

	*** CONTRE-EXEMPLES FORMELS ***

	>>> is_analogy( 'a : ab :: c : bc' )
	False
	>>> is_analogy( 'abcde : edcba :: abc : cba' )
	False
	>>> is_analogy( 'b : b :: ba : bb' )
	False
	>>> is_analogy( 'b : ab :: aab : abaa' )
	False
	>>> is_analogy( 'a : aa :: aaa : aaaaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aaabbbba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aaabbbab' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aaabbbaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aaabbabb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aabbbaba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aabbbaab' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbbbaaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aaababbb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aaababbb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aabbabba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aabbabab' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbbabaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbbaabb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbbaaba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : bbbbaaaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aababbba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aababbab' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbabbaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aabababb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbababa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : bbbabaaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : aabaabbb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbaabba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbaabab' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : bbbaabaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : abbaaabb' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : bbbaaaba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : bbabbbba' )
	False
	>>> is_analogy( 'ab : aabb :: aaabbb : bbabbbab' )
	False

	>>> is_analogy( 'ab : aabb :: aaabbb : bababbaa' )
	False

	>>> is_analogy( 'ab : aabb :: aaabbb : baaabbba' )
	False
	>>> is_analogy( 'ab : abab :: ababab : ababbaab' )
	False
	>>> is_analogy( 'ab : abab :: ababab : bbababaa' )
	False
	>>> is_analogy( 'aab : aaaabb :: aaaaaabbb : aaabaaaababb' )
	False
	>>> is_analogy( 'aba : aabbaa :: aaabbbaaa : aababbabaaaa' )
	False
	>>> is_analogy( 'ab : aabb :: aaaaaaabbbbbbb : aabaaaaababbbbbb' )
	False
	>>> is_analogy( 'abc : aabbcc :: aaabbbccc : aababcbbcacc' )
	False
	>>> is_analogy( 'ab : aabb :: ab : abba' )
	False
	>>> is_analogy( 'ab : ab :: aabb : abba' )
	False
	>>> is_analogy( 'ab : abab :: abab : abbaab' )
	False
	>>> is_analogy( 'abbaab : abab :: abab : ab' )
	False
	>>> is_analogy( 'ab : aabb :: aabb : aababb' )
	False
	
	*** Tests from Baptsite Jonglez (baptiste.jonglez@ens-lyon.fr). ***
	
	>>> confirm_analogy( 'eue : rue :: nous devons : nous drvons' )
	True
	>>> confirm_analogy( 'sue : rue :: nous devons : nous desons' )
	False
	>>> confirm_analogy( 'eue : rue :: nous devons : nous devons' )
	False
	>>> confirm_analogy( 'sus : vus :: nous devons : nous devons' )
	False
	
	>>> confirm_analogy( 'tata : tàtà :: haha : hàhà' )
	True
	>>> confirm_analogy( 'tété : tete :: héhé : hehe' )
	True
	>>> confirm_analogy( 'tete : tété :: hehe : héhé' )
	True
	>>> confirm_analogy( 'aaaa : à :: aaaàa : àà' )
	True
	>>> confirm_analogy( '決める : 決めます :: 食べる : 食べます' )
	True
	>>> confirm_analogy( '一年，是我国社会主义 : ，社会主义 :: 一年是我国 : ' )
	True
	"""

	successes, total_t = 0, 0
	for _ in range(repeat):
		lenA, lenB, lenC = random.randint(1,strlen), random.randint(1,strlen), random.randint(1,strlen)
		A, B, C = random_word(vocsize,lenA), random_word(vocsize, lenB), random_word(vocsize, lenC)
		t1 = time.time()
		D = solvenlg(A,B,C)
		total_t += time.time() - t1
		if None != D:
			if __verbose__: print(__nlg_fmt__ % (A,B,C,D), file=sys.stderr)
			successes += 1
	return int(round((100.0 * successes)) / repeat), int(round(1000*total_t))

if __name__ == '__main__':
	options, args = read_argv()
	if options.test: _test()
	__verbose__ = options.verbose
	if 127 < ord('a') + options.vocsize:
		options.vocsize = 127 - ord('a')
	if not options.statistics:
		success_result, time_result = main(options.repeat, options.vocsize, options.strlen)
		print('# Number of trials: %d' % options.repeat, file=sys.stderr)
		print('# Success rate: %d%%' % success_result, file=sys.stderr)
		print('# Processing time: %dms' % time_result, file=sys.stderr)
	else:
		success_table, time_table = dict(), dict()
		for maxlen in range(1,options.strlen+1):
			success_table[maxlen], time_table[maxlen] = dict(), dict()
			for vocsize in range(1,options.vocsize+1):
				success_table[maxlen][vocsize], time_table[maxlen][vocsize] = main(options.repeat, vocsize, maxlen)
		s = '# Success rate over random analogical equations (in percentage)\n'
		t = '# Computation time (in milliseconds)\n'
		msg  = '# Number of trials: %d\n' % options.repeat
		msg += '# First line in table: vocabulary size\n#'
		msg += '# First column in table: maximal length of strings\n#'
		msg += '\t'  +  '\t'.join([ '%d' % vocsize for vocsize in range(1,options.vocsize+1) ])  +  '\n'
		s += msg
		t += msg
		for maxlen in range(1,options.strlen+1):
			msg = '%d\t' % maxlen
			s += msg
			t += msg
			s += '\t'.join([ '%d' % success_table[maxlen][vocsize] for vocsize in range(1,options.vocsize+1) ])
			t += '\t'.join([ '%d' % time_table[maxlen][vocsize] for vocsize in range(1,options.vocsize+1) ])
			s += '\n'
			t += '\n'
		print(s)
		print(t)


