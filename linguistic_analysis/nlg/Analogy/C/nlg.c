/* Copyright (c) 1999, Yves Lepage */
#define MODULE "nlg"
#define TRACE 0
#define CONTIGUITY 0
/* extern int tracet ; */

/*
 * Compute the solution of an analogy.
 * An analogy is an equation on words : u:v = w:x
 * where u, v and w are known and x is the unknown.
 *
 * For instance:
 *   arsala : aslama = mursil : x  =>  x = muslim
 *
 * Method:
 *
 * compute strings x
 * by computation of pseudo-distance matrices
 * and longest common subsequence algorithm,
 * stop if analogy constraint is not verified.
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/*
#include "usrlib.h"
#include "usrmath.h"
*/
#include "utf8.h"
#include "nlg.h"

/*
 * REPLACES #include "usrlib.h"
 * macro for trace:
 * use:
 * trace((string))
 * in C code not followed by semi-colon
 */

#define ytrace(x) { printf x ; fflush(stderr) ; fflush(stdout) ; }
#define ntrace(x)

#if TRACE
/* #define trace(x) { ytrace(x) ; if ( iscgiuse() ) printf("<br>\n") ; fflush(stdout) ; } */
#define trace(x) { ytrace(x) ; }
#else
#define trace(x)
#endif

/*
 * Exit on error
 */

#define ERR_MODULE_LABEL       " in module:   "
#define ERR_FUNCTION_LABEL     " in function: "
#define ERR_DIAGNOSTIC_LABEL   " diagnostic:  "

/*
 * Error, do not exit
 */

void warning(char *module_name, char *function_name, char *msg)
{
   fprintf(stderr,
          "\n#"
          "\n#" ERR_MODULE_LABEL     "%s"
          "\n#" ERR_FUNCTION_LABEL   "%s"
          "\n#" ERR_DIAGNOSTIC_LABEL "%s"
          "\n#"
          "\n",
          module_name,function_name,msg) ;
   fflush(stderr) ;
}

/*
 * Exit on error
 */

void error(char *module_name, char *function_name, char *msg)
{
   warning(module_name,function_name,msg) ;
	abort() ;
}


/*
 * Variables for traces, etc. for the programmer
 */

static int tracet	= 0 ;
static int debug	= 0 ;
static int count	= 0 ;
static int bytenbr	= 1 ;
static int resolution	= 0 ;

/*
 * Numbering of analogy arguments
 */
 
#define TERM_MIN	0
#define A       	0
#define B       	1
#define C       	2
#define D       	3
#define TERM_MAX	4

#define oppterm(X)	(TERM_MAX-1-X)

#define Termname(X)\
   (X==A)?"A":\
   (X==B)?"B":\
   (X==C)?"C":\
   (X==D)?"D":"?"

/*
 * Various variables
 */

#define uchar			char
#define MAXWORD		256
#define MAXALPHABET	256*256
/* #define MAXSYMBOLS	128 */

/*
 * Trace macros
 */

#define S_NLGFMT	"%s : %s :: %s : %s"
#define L_NLGFMT	"%d : %d :: %d : %d"

#define verif_arg(s)	s[A],s[B],s[C],s[D]
#define solve_arg(s)	s[A],s[B],s[C]
 
#define tw(X,i)		tword((uchar *) s[X],i[X])
#define nlg_arg(s,i)	tw(A,i),tw(B,i),tw(C,i),tw(D,i)


/*
 * Variables
 */

int matrix12[MAXWORD+1][MAXWORD+1] ;
int matrix13[MAXWORD+1][MAXWORD+1] ;

int maxsymbols = 0 ;
int convsymbols[MAXALPHABET] ;
uchar *anticonv = NULL ;

int ****matrix123 ;
int **matrix4 ;

/*
 * Local functions
 */

static int charconstraint(uchar *, uchar *, uchar *) ;
static uchar *solveanalogy(uchar *, uchar *, uchar *) ;
static int verifanalogy(uchar *, uchar *, uchar *, uchar *) ;

/*
 * Macros for matrix computation
 */

#define HORCOST 0
#define VERCOST 1

#define M(i,j)          matrix ## i ## j
#define W(i)            word ## i

/* i,j can be: 1,2 or 1,3 or 4,2 or 4,3 */
#define diag(i,j,ki,kj)   (M(i,j)[ki  ][kj  ] + 2 * (W(i)[ki-1] != W(j)[kj-1]))
#define hori(i,j,ki,kj)   (M(i,j)[ki+1][kj  ] + HORCOST)
#define vert(i,j,ki,kj)   (M(i,j)[ki  ][kj+1] + VERCOST)

#define isdiag(i,j,ki,kj)	(M(i,j)[ki+1][kj+1] == diag(i,j,ki,kj))
#define ishori(i,j,ki,kj)	(M(i,j)[ki+1][kj+1] == hori(i,j,ki,kj))
#define isvert(i,j,ki,kj)	(M(i,j)[ki+1][kj+1] == vert(i,j,ki,kj))

#define t3words   tword((uchar *)word1,i1,i1),\
                  tword((uchar *)word2,i2,i2),\
                  tword((uchar *)word3,i3,i3)

/*
 * Compute the minimum of three integers.
 */

int min3(int i, int j, int k)
{
	if ( i < j )
	{
		if ( i < k ) return i ;
		else         return k ;
	}
	else
	{
		if ( j < k ) return j ;
		else         return k ;
	} ;
}

/*
 * Creation of matrix123.
 */

int ****newmatrix123(int l1, int l2, int l3, int maxsymbols)
{
   int ****result = NULL ;
   int i1 = 0, i2 = 0, i3 = 0 ;

trace(("in  newmatrix123(%d,%d,%d, %d)\n",l1,l2,l3,maxsymbols))

   result = (int ****) calloc(l1+2,sizeof(int ***)) ;
   for ( i1 = 0 ; i1 <= l1+1 ; ++i1 )
   {
      result[i1] = (int ***) calloc(l2+2,sizeof(int **)) ;
      for ( i2 = 0 ; i2 <= l2+1 ; ++i2 )
      {
         result[i1][i2] = (int **) calloc(l3+2,sizeof(int *)) ;
         for ( i3 = 0 ; i3 <= l3+1 ; ++i3 )
         {
            result[i1][i2][i3] = (int *) calloc(maxsymbols,sizeof(int)) ;
         } ;
      } ;
   } ;

trace(("out newmatrix123(%d,%d,%d, %d)\n",l1,l2,l3,maxsymbols))

   return result ;
}

/*
 * Free matrix123.
 */

void freematrix123(int ****result, int l1, int l2, int l3)
{
   int i1 = 0, i2 = 0, i3 = 0 ;

trace(("in  freematrix123(%d,%d,%d)\n",l1,l2,l3))

   for ( i1 = 0 ; i1 <= l1+1 ; ++i1 )
   {
      for ( i2 = 0 ; i2 <= l2+1 ; ++i2 )
      {
         for ( i3 = 0 ; i3 <= l3+1 ; ++i3 )
         {
            free(result[i1][i2][i3]) ;
         } ;
         free(result[i1][i2]) ;
      } ;
      free(result[i1]) ;
   } ;
   free(result) ;

trace(("out freematrix123(%d,%d,%d)\n",l1,l2,l3))
}

/*
 * Creation of matrix4.
 */

int **newmatrix4(int l4, int maxsymbols)
{
   int **result = NULL ;
   int i4 = 0 ;

trace(("in  newmatrix4(%d,%d)\n",l4,maxsymbols))

   if ( l4 > 0 )
   {
      result = (int **) calloc(l4+1,sizeof(int *)) ;
      for ( i4 = 0 ; i4 <= l4+1 ; ++i4 )
      {
         result[i4] = (int *) calloc(maxsymbols,sizeof(int)) ;
      } ;
   } ;

trace(("out newmatrix4(%d,%d)\n",l4,maxsymbols))

   return result ;
}

/*
 * Free matrix4.
 */

void freematrix4(int **result, int l4)
{
   int i4 = 0 ;

trace(("in  freematrix4(%d)\n",l4))

   for ( i4 = 0 ; i4 <= l4+1 ; ++i4 )
   {
      free(result[i4]) ;
   } ;
   free(result) ;

trace(("out freematrix4(%d)\n",l4))
}


/*
 * Management of the solutions.
 */

static int equalSolns(uchar **solns1, uchar **solns2)
{
   int result = 1 ;

   if ( solns1 && solns2 )
   {
      int j = 0 ;

      for ( j = 0 ; result && solns1[j] && solns2[j] ; ++j )
			result = ( 0 == strcmp((uchar *)solns1[j],(uchar *)solns2[j]) ) ;
      result = ! ( (solns1[j] && ! solns2[j]) || (! solns1[j] && solns2[j]) ) ;
   }
   else
      result = ! ( (solns1 && ! solns2) || (! solns1 && solns2) ) ;
   return result ;
}

static void freeSolns(uchar **solns)
{
	if ( solns )
	{
		int j = 0 ;

		for ( j = 0 ; solns[j] ; ++j )
			free(solns[j]) ;
		free(solns) ;
	} ;
}

/*
 * Verify the contiguity constraint.
 */

int contiguityconstraint(int i1, int i2, int i3)
{
	int result = 0 ;
	int i4 = i2+i3-i1 ;
	int is = 0 ;

trace(("in  contiguityconstraint\n"))

	if ( i4 > 0 )
	{
		result = 1 ;
		for ( is = 0 ; is < maxsymbols && result ; ++is )
		{
			result = ( matrix123[i1][i2][i3][is] == matrix4[i4][is] ) ;
trace(("mid contiguityconstraint: matrix123\\[%d\\]\\[%d\\]\\[%d\\]\\[%c\\]=%d %s matrix4\\[%d\\]\\[%c\\]=%d\n",i1,i2,i3,anticonv[is],matrix123[i1][i2][i3][is],((result)?"==":"!="),i4,anticonv[is],matrix4[i4][is]))
		} ;
	} ;

trace(("out contiguityconstraint\n"))

	return result ;
}

/*
 * Verify the similarity constraint
 */

int similarityconstraint(int i1, int i2, int i3, int com)
{
	int result = 0 ;

	result = ( i1 == matrix12[i1+1][i2+1] + matrix13[i1+1][i3+1] + com ) ;

	return result ;
            
}

/*
 * Verify the full constraint
 */

int fullconstraint(int i1, int i2, int i3, int com)
{
	int result = 0 ;

trace(("in  fullconstraint\n"))

	result = similarityconstraint(i1,i2,i3,com)
#if CONTIGUITY         
			&& contiguityconstraint(i1,i2,i3)
#endif
			;

trace(("out fullconstraint = %s\n",result?"true":"false"))

	return result ;
}

/*
 * Trace symbols
 */

void traceanticonv(void)
{
	int is = 0 ;

	for ( is = 0 ; is < maxsymbols ; ++is )
		fprintf(stderr,"%d symbol = %c\n",is,anticonv[is]) ;
}

/*
 * Trace a word
 */

static uchar *tword(uchar *word, int i, int j)
{
	uchar *result = (uchar *) calloc(MAXWORD,sizeof(uchar)) ;
	uchar *traceword = result ;

	if ( i > strlen((uchar *) word) )
		i = strlen((uchar *) word) ;
	if ( j < i )
		j = i ;
	if ( j > strlen((uchar *) word) )
		j = strlen((uchar *) word) ;
	if ( i == 0 )
	{
		traceword[0] = '[' ;
		strncpy(traceword+1,word,j) ;
		traceword[j+1] = ']' ;
		strcpy(traceword+j+2,word+j) ;
	}
	else
	{
		strncpy(traceword,word,i-1) ;
		traceword[i-1] = '[' ;
		strncpy(traceword+i,word+i-1,j-i+1) ;
		traceword[j+1] = ']' ;
		strcpy(traceword+j+2,word+j) ;
	} ;
	return result ;
}


/*
 * Trace matrices
 */

static void tracematrices(uchar *word1, uchar *word2, uchar *word3, int j1, int j2, int j3, int j4, int l1, int l2, int l3)
{
	int i1 = 0, i2 = 0, i3 = 0, i4 = 0 ;
/*  j1 = min(j1,l1) ; */
	j1 = ( j1 <= l1 ) ? j1 : l1 ;

	fprintf(stderr,"  ") ;
	for ( i2 = l2 ; i2 >= 1 ; --i2 )
		fprintf(stderr,"%c  ",word2[i2-1]) ;
	fprintf(stderr,"     ") ;
	for ( i3 = 1 ; i3 <= l3 ; ++i3 )
		fprintf(stderr,"%c  ",word3[i3-1]) ;
	fprintf(stderr,"\n") ;
   
	fprintf(stderr,"  ") ;
	for ( i2 = l2 ; i2 >  j2 ; --i2 )
		fprintf(stderr,"   ") ;
	fprintf(stderr,"v") ;
	for ( i2 = j2 -1 ; i2 >= 0 ; --i2 )
		fprintf(stderr,"   ") ;
	fprintf(stderr," ") ;
	for ( i3 = 0 ; i3 <  j3 ; ++i3 )
		fprintf(stderr,"   ") ;
	fprintf(stderr,"v\n") ;
   
	for ( i1 = 1 ; i1 <= j1 ; ++i1 )
	{
		for ( i2 = l2 ; i2 >= 1 ; --i2 )
			fprintf(stderr,"%3d",matrix12[i1+1][i2+1]) ;
		fprintf(stderr,"   %c ",word1[i1-1]) ;
		for ( i3 = 1 ; i3 <= l3 ; ++i3 )
			fprintf(stderr,"%3d",matrix13[i1+1][i3+1]) ;
		fprintf(stderr,"\n") ;
	} ;
	fprintf(stderr,"\n") ;
} ;

/*
 * Intialise matrices
 */

/*
#define VERIFY(x) trace(("mid %c\n",x)) if ((x)>=MAXALPHABET) return result ;
*/
#define VERIFY(x) trace(("mid %c\n",x))

static int initialisation(uchar *word1, uchar *word2, uchar *word3, int l1, int l2, int l3)
{
	int result = 0 ;
	int i1 = 0, i2 = 0, i3 = 0, i4 = 0 ;
	int is = 0 ;

	int ll = (l2+l3-l1) ;
	int l4 = (ll < 0) ? 0 : ll ;

trace(("in  initialisation(%s(%d),%s(%d),%s(%d))\n",word1,l1,word2,l2,word3,l3))

#if CONTIGUITY
	maxsymbols = 0 ;
	for ( i1 = 0 ; i1 < MAXALPHABET ; ++i1 )
		convsymbols[i1] = 0 ;
#endif
	for ( i1 = 0 ; i1 <= l1+1 ; ++i1 )
	{
		VERIFY(word1[i1]) ;
#if CONTIGUITY
		if ( 0 <= i1 && i1 < l1 && ! convsymbols[word1[i1]] )
			convsymbols[word1[i1]] = ++maxsymbols ;
#endif
		matrix12[i1+1][1] = matrix13[i1+1][1] = i1 * VERCOST ;
	} ;
	for ( i2 = 0 ; i2 <= l2+1 ; ++i2 )
	{
		VERIFY(word2[i2]) ;
#if CONTIGUITY
		if ( 0 <= i2 && i2 < l2 && ! convsymbols[word2[i2]] )
			convsymbols[word2[i2]] = ++maxsymbols ;
#endif
		matrix12[1][i2+1] = i2 * HORCOST ;
	} ;
	for ( i3 = 0 ; i3 <= l3+1 ; ++i3 )
	{
		VERIFY(word3[i3]) ;
#if CONTIGUITY
		if ( 0 <= i3 && i3 < l3 && ! convsymbols[word3[i3]] )
			convsymbols[word3[i3]] = ++maxsymbols ;
#endif
		matrix13[1][i3+1] = i3 * HORCOST ;
	} ;

	for ( i1 = 1 ; i1 <= l1+1 ; ++i1 )
	{
		for ( i2 = 1 ; i2 <= l2+1 ; ++i2 )
			matrix12[i1+1][i2+1] = min3(diag(1,2,i1,i2),hori(1,2,i1,i2),vert(1,2,i1,i2)) ;
		for ( i3 = 1 ; i3 <= l3+1 ; ++i3 )
			matrix13[i1+1][i3+1] = min3(diag(1,3,i1,i3),hori(1,3,i1,i3),vert(1,3,i1,i3)) ;
	} ;
#if CONTIGUITY
	anticonv = (uchar *) calloc(maxsymbols+1,sizeof(uchar)) ;
	for ( is = 0 ; is < MAXALPHABET ; ++is )
		if ( convsymbols[is] )
			anticonv[convsymbols[is]-1] = is ;
	traceanticonv() ;

	matrix123 = newmatrix123(l1,l2,l3,maxsymbols) ;
	matrix4   = newmatrix4(l2+l3-l1,maxsymbols) ;

	traceanticonv() ;

	for ( i1 = 0 ; i1 <= l1+1 ; ++i1 )
	for ( i2 = 0 ; i2 <= l2+1 ; ++i2 )
	for ( i3 = 0 ; i3 <= l3+1 ; ++i3 )
	for ( is = 0 ; is < maxsymbols ; ++is )
		matrix123[i1][i2][i3][is] = 0 ; ; ;

	for ( i1 = l1 ; i1 >= 1 ; --i1 )
	{
		int c1 = convsymbols[word1[i1]] ;

		for ( i2 = l2 ; i2 >= 1 ; --i2 )
		{
			int c2 = convsymbols[word2[i2]] ;
   
			for ( i3 = l3 ; i3 >= 1 ; --i3 )
			{
				int c3 = convsymbols[word3[i3]] ;

				for ( is = 0 ; is < maxsymbols ; ++is )
				{
					matrix123[i1][i2][i3][is] = matrix123[i1+1][i2][i3][is] + (is == c1) ;
					matrix123[i1][i2][i3][is] = matrix123[i1][i2+1][i3][is] + (is == c2) ;
					matrix123[i1][i2][i3][is] = matrix123[i1][i2][i3+1][is] + (is == c3) ;
				} ;
			} ;
		} ;
	} ;
#endif
	result = 1 ;

	traceanticonv() ;

trace(("out initialisation(%s,%s,%s) = %d\n",word1,word2,word3,result))

	return result ;
}

#undef VERIFY


/*
 * Old character inclusion constraint (prog by Jean-François Morreeuw)
 * Does not work. Problem of architecture with long int?
 */

static int old_charconstraint(uchar *word1, uchar *word2, uchar *word3)
{
   int result = 0 ;
   unsigned long int memory[3][8] =
      { 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0 } ; /* 8*32=256 bits */
   uchar *word[3] = { (uchar *)word1, (uchar *)word2, (uchar *)word3 };
   int i = 0; /* index of word: 0, 1 ou 2 */
   int j = 0; /* position in word i */

trace(("in  charconstraint(%s,%s,%s)\n",word1,word2,word3))

	for ( i = 0 ; i < 3 ; ++i )
	{
		int li = strlen((uchar *)word[i]) ;

		for ( j = 0 ; j < li ; ++j )
			memory[i][word[i][j] >> 5] |= (0x1 << (word[i][j] % 32)) ;
    } ;
	for ( j = 0 ; j < 8 ; ++j )
	{
		memory[0][j] |= (memory[1][j] |= memory[2][j]) ;
		memory[0][j] ^= memory[1][j] ;
    } ;
    for ( j = 0 ; j < 7 ; ++j )
		memory[0][j+1] |= memory[0][j] ;
    result = (int) (memory[0][7] == 0L) ;

trace(("out charconstraint(%s,%s,%s) = %d\n",word1,word2,word3,result))

   return result ;
}

/*
 * Character inclusion constraint (prog by Yves Lepage)
 */

static int charconstraint(uchar *word1, uchar *word2, uchar *word3)
{
   int result = 0 ;
   uchar *word[3] = { (uchar *)word1, (uchar *)word2, (uchar *)word3 };
   int len[4] = { 0 } ;
   int alphabet[256] = { 0 } ;
   int min = 0, max = 256 ; /* first and last character used in alphabet */

trace(("in  charconstraint(%s,%s,%s)\n",word1,word2,word3))

	result = ( 0 <= len[3] ) ;
	if ( result )
	{
		int i = 0; /* index of word: 0, 1 ou 2 */
		uchar *si = NULL ; /* character iterator in word i */
		int j = 0; /* position in word i */
		
		/* add char numbers from B and C */
		for ( i = 1 ; i < 3 ; ++i )
		{
			for ( si = word[i] ; *si ; ++si )
			{				
				int c = *si ;
			
				alphabet[c] += 1 ;
				if ( c < min )
					min = c ;
				if ( max < c+1 )
					max = c+1 ;
			} ;
			len[i] = (si - word[i]) ;
trace(("mid charconstraint(%s,%s,%s) len = %d\n",word1,word2,word3,len[i]))
		} ;
		/* subtract char numbers from A */
		for ( si = word[0] ; *si ; ++si )
		{
			int c = *si ;
			
			alphabet[c] -= 1 ;
			result = ( 0 <= alphabet[c] ) ;
trace(("mid charconstraint(%s,%s,%s) memory[%c] = %d result = %d\n",word1,word2,word3,c,alphabet[c],result))
			if ( ! result )
				break ;
		} ;
		len[0] = (si - word[0]) ; /* maybe incorrect if result == 0 */
		len[3] = len[1] + len[2] - len[0] ;
trace(("mid charconstraint(%s,%s,%s) = %d\n",word1,word2,word3,result))
		if ( result )
		{
			int sum = 0 ;
			int i = 0; /* character in alphabet */

			for ( i = min ; i < max ; ++i )
				sum += alphabet[i] ;
			if ( sum != len[3] )
				result = 0 ;
		} ;
	} ;

trace(("out charconstraint(%s,%s,%s) = %d\n",word1,word2,word3,result))

   return result ;
}

/*
 * Update the matrix for the contiguity constraint
 */

void updatematrix4(uchar *word4, int i4, int l4)
{
	int c4 = convsymbols[word4[i4]] ;
	int is = 0 ;

trace(("in  updatematrix4(word4[%d]=%c)\n",i4,c4))

	if ( l4 > i4 && i4 > 0 )
	{
		for ( is = 0 ; is < maxsymbols ; ++is )
		{
			matrix4[i4][is] = matrix4[i4+1][is] + (is == c4) ;
trace(("matrix4[%d][%c] = %d\n",i4,anticonv[is],matrix4[i4][is]))
		} ;
	} ;

trace(("out updatematrix4(word4[%d]=%c)\n",i4,c4))
}


/*
 * Compute a solution of the analogy
 */

#define VERIFY(x,msg) trace(("mid %s\n",msg)) if (!(x)) goto ENDOFMOVE ;

static uchar *pr_mov(uchar *word1, uchar *word2, uchar *word3, uchar *word4, int l1, int l2, int l3)
{
   int ll = (l2+l3-l1) ;
   int l4 = (ll < 0) ? 0 : ll ;
   uchar *result = (uchar *) calloc(l4+1,sizeof(uchar)) ;

   int i1 = 0, i2 = 0, i3 = 0, i4 = 0 ;
   int j1 = 0, j2 = 0, j3 = 0, j4 = 0 ;
   int com = 0 ;

trace(("in  pr_mov(%s(%d),%s(%d),%s(%d),%s(%d))\n",word1,l1,word2,l2,word3,l3,"?",l4))

   traceanticonv() ;
   if ( l4 > MAXWORD )
   {
      warning(MODULE,"pr_mov","TOO LONG!") ;
      free(result) ;
      result = (uchar *) "" ;
      return result ;
   } ;

   i1 = l1 ;
   i2 = l2 ;
   i3 = l3 ;
   i4 = l4 ;
   com = l1 - matrix12[l1+1][l2+1] - matrix13[l1+1][l3+1] ;

   if ( resolution )
      word4 = result ;

   if ( l4 > 0 /* && (resolution || l4 == strlen((uchar *)word4)) */ )
   {
      while ( ! (i1 <= 0 && i2 <= 0 && i3 <= 0 && i4 <= 0)
             /* && (word4[i4] == result[i4]) */ )
      {
trace(("mid 1 pr_mov(%s,%s,%s) = %s\n", t3words, result+i4))
   
if ( tracet )
{
   fprintf(stderr,"constraint: %d = %d + %d + %d\n",i1,matrix12[i1+1][i2+1],matrix13[i1+1][i3+1],com) ;
   tracematrices((uchar *)word1,(uchar *)word2,(uchar *)word3,i1,i2,i3,i4, l1,l2,l3) ;
} ;
/**/
         VERIFY(! (j1==i1 && j2==i2 && j3==i3), "check progress") ;
         j1 = i1 ;
         j2 = i2 ;
         j3 = i3 ;
/**/

         updatematrix4(word4,i4,l4) ;
	 if ( ! fullconstraint(i1,i2,i3,com) )
	    break ;
	    
	 if ( isdiag(1,2,i1,i2) && isdiag(1,3,i1,i3) )
	 {
            VERIFY((i4-1) >= 0,"diag 2 && 3") ;
	    if ( i1 > 0 /* was i1 != 0 2004/8/11 */ && word1[i1-1] == word2[i2-1] && word1[i1-1] == word3[i3-1] ) 
	    {
	       result[i4-1] = word1[i1-1] ; com-- ;
	    }
	    else if ( (i3 > 0) /* was i3 != 0 2004/8/11 */ && word1[i1-1] == word2[i2-1] )
	       result[i4-1] = word3[i3-1] ;
	    else if ( (i2 > 0) /* was i2 != 0 2004/8/11 */ && word1[i1-1] == word3[i3-1] )
	       result[i4-1] = word2[i2-1] ;
	    else
	       break ;
	    i1 = i1 - 1 ; i2 = i2 - 1 ; i3 = i3 - 1 ; i4 = i4 - 1 ;
	 }
	 else if ( isdiag(1,2,i1,i2) && (! isdiag(1,3,i1,i3)) )
	 {
		VERIFY((i4-1) >= 0,"diag 2 && !3") ;
	    if ( i3 > 0 && ishori(1,3,i1,i3) )
	       result[i4-- -1] = word3[i3-- -1] ;
	    else if ( i2 > 0 )
	    {
	       i1-- ; i2-- ;
	    } ;
	 }
	 else if ( (! isdiag(1,2,i1,i2)) && isdiag(1,3,i1,i3) )
	 {
		VERIFY((i4-1) >= 0,"diag !2 && 3") ;
	    if ( i2 > 0 && ishori(1,2,i1,i2) )
	       result[i4-- -1] = word2[i2-- -1] ;
	    else if ( i3 > 0 )
	    {
	       i1-- ; i3-- ;
	    } ;
	 }

	 else if ( (! isdiag(1,2,i1,i2)) && (! isdiag(1,3,i1,i3)) )
	 {
		VERIFY((i4-1) >= 0,"diag !2 && !3") ;
		if ( i2 > 0 && i3 > 0 )
	    {
			if ( isvert(1,2,i1,i2) && isvert(1,3,i1,i3) )
				i1-- ;
			else if ( isvert(1,2,i1,i2) && ! isvert(1,3,i1,i3) )
				result[i4-- -1] = word3[i3-- -1] ;
			else if ( ! isvert(1,2,i1,i2) && isvert(1,3,i1,i3) )
			result[i4-- -1] = word2[i2-- -1] ;
			else
			{
trace(("mid 2 pr_mov(%s,%s,%s) %d,%d,%d,%d mat=%d,%d\n", t3words,i1,i2,i3,i4, matrix12[i1+1][i2+1],matrix13[i1+1][i3+1]))
				if ( matrix12[i1+1][i2+1] < matrix13[i1+1][i3+1] )
					result[i4-- -1] = word2[i2-- -1] ;
				else if ( matrix12[i1+1][i2+1] > matrix13[i1+1][i3+1] )
					result[i4-- -1] = word3[i3-- -1] ;
				else if ( i1 == 0 && i2 < i3 ) /* should be last copied */
					result[i4-- -1] = word2[i2-- -1] ;
				else
					result[i4-- -1] = word3[i3-- -1] ;
			} ;
		}
		else if ( i2 > 0 && i3 == 0 )
		{
			result[i4-- -1] = word2[i2-- -1] ;
			i1-- ; i2-- ;
	    }
	    else if ( i2 == 0 && i3 > 0 )
	    {
	       result[i4-- -1] = word3[i3-- -1] ;
	       i1-- ; i3-- ;
	    }
	    else if ( i2 == 0 && i3 == 0 )
	       break ;
	 }
	 else
	    break ;
      } ;
   } ;

trace(("mid 3 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))


ENDOFMOVE:
trace(("mid 4 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))
	if ( (i1 == 0 || (i3==0 && i1==1)) && (i2 > 1) )
	{
		for ( ; i1 > 0 && i2 > 0 && word1[i1-1] == word2[i2-1] ; )
		{ i1 = i1 - 1 ; i2 = i2 - 1 ; }
		for ( i2 = i2 ; i2 > 0 ; )
		{
			VERIFY((i4-1) >= 0,"step in 2") ;
			result[i4-- -1] = word2[i2-- -1] ;
		} ;
	}
	else if ( (i1 == 0 || (i2==0 && i1==1)) && (i3 > 1) )
	{
		for ( ; i1 > 0 && i3 > 0 && word1[i1-1] == word3[i3-1] ; )
		{ i1 = i1 - 1 ; i3 = i3 - 1 ; }
		for ( i3 = i3 - 1 ; i3 > 0 ; )
		{
			VERIFY((i4-1) >= 0,"step in 3") ;
			result[i4-- -1] = word3[i3-- -1] ;
		} ;
	} ;
trace(("mid 5 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))
	for ( ; i1 > 0 && i2 > 0 && word1[i1-1] == word2[i2-1] ; )
	{ i1 = i1 - 1 ; i2 = i2 - 1 ; }
	for ( ; i1 > 0 && i3 > 0 && word1[i1-1] == word3[i3-1] ; )
	{ i1 = i1 - 1 ; i3 = i3 - 1 ; }
	if ( (i1 == 0 && i3 == 0 && i2 == i4) || (i1 == 0 && i2 == 0 && i3 == i4) )
	{
		if (i1 == 0 && i3 == 0 && i2 == i4)
		{
			for ( i2 = i2 ; i2 > 0 ; )
			{
				VERIFY((i4-1) >= 0,"step in 2") ;
				result[i4-- -1] = word2[i2-- -1] ;
			} ;
		}
		else if (i1 == 0 && i2 == 0 && i3 == i4)
		{
			for ( i3 = i3 - 1 ; i3 > 0 ; )
			{
				VERIFY((i4-1) >= 0,"step in 3") ;
				result[i4-- -1] = word3[i3-- -1] ;
			} ;
		} ;
	} ;

trace(("mid 6 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))

	if ( i1 == i2 && strncmp((uchar *)word1,(uchar *)word2,i1) == 0 )
	{
trace(("mid 7 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))
		for ( ; i4 > 0 ; )
		{
			VERIFY((i4-1) >= 0,"copy in 7") ;
			result[i4-- -1] = word2[i3-- -1] ;
		} ;
	}
	else if ( i1 == i3 && strncmp((uchar *)word1,(uchar *)word3,i1) == 0 )
	{
trace(("mid 8 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))
		for ( ; i4 > 0 ; )
		{
			VERIFY((i4-1) >= 0,"copy in 8") ;
			result[i4-- -1] = word2[i2-- -1] ;
		} ;
	}
	else if ( i1 > 0 || i2 > 0 || i3 > 0 || i4 > 0 )
	{
		free(result) ;
trace(("mid 9 pr_mov(%s,%s,%s) %d,%d,%d,%d\n", t3words,i1,i2,i3,i4))
		if ( 0 == l4 )
			result = (uchar *) "" ;
		else
			result = (uchar *) NULL ;
	} ;

trace(("out pr_mov(%s(%d),%s(%d),%s(%d)) = %s(%d)\n", word1,l1,word2,l2,word3,l3,result,l4))

	return result ;
}

#undef VERIFY

/*
 * Call to solve an analogy
 * (with C strings of characters)
 */

uchar *asciisolvenlg(uchar *word1, uchar *word2, uchar *word3)
{
	int l1 = strlen((uchar *)word1),
		l2 = strlen((uchar *)word2),
		l3 = strlen((uchar *)word3) ;
	uchar *result = (uchar *) NULL ;

trace(("in  asciisolvenlg(%s,%s,%s)\n", (uchar *)word1,(uchar *)word2,(uchar *)word3))

	if ( l1 > MAXWORD || l2 > MAXWORD || l3 > MAXWORD )
	{
		/*error(MODULE,"asciisolveanalogy",ERR_STRLEN) ;*/
		return result ;
	} ;
	if ( l3 > l2 )
	{
		uchar *wordtmp = word2 ;
		int ltmp = l2 ;

		word2 = word3 ;
		l2 = l3 ;
		word3 = wordtmp ;
		l3 = ltmp ;
	} ;

	if ( charconstraint(word1,word2,word3) )
	{
/*
trace(("mid pdist(%s,%s) = %d, pdist(%s,%s) = %d\n", word1,word2,matrix12[l1+1][l2+1],word1,word3,matrix13[l1+1][l3+1]))
	if ( matrix12[l1+1][l2+1] < matrix13[l1+1][l3+1] )
		initialisation(word1,word3,word2) ;
*/
		if ( initialisation(word1,word2,word3,l1,l2,l3) )
		{

if ( tracet )
	tracematrices((uchar *)word1,(uchar *)word2,(uchar *)word3,l1,0,0,0, l1,l2,l3) ;

			resolution = 1 ;
			result = pr_mov(word1,word2,word3,NULL,l1,l2,l3) ;
/*
			if ( ! (result && strcmp((uchar *) result,"")) )
				result = (uchar *) "" ;
*/
#if CONTIGUITY
			freematrix123(matrix123,l1,l2,l3) ;
			freematrix4(matrix4,l2+l3-l1) ;
#endif
		} ;
	}
	else
	{
trace(("no soln: charconstraint false\n"))
		return (char *) NULL ;
	} ;

trace(("out asciisolvenlg(%s,%s,%s) = %s\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,(NULL==result)?"NULL":result))

	return result ;
}
/*
 * Call to verify an analogy
 * (with C strings of characters)
 */

int asciiverifnlg(uchar *word1, uchar *word2, uchar *word3, uchar *word4)
{
	int l1 = strlen((uchar *)word1),
		l2 = strlen((uchar *)word2),
		l3 = strlen((uchar *)word3) ;
	uchar *result = (uchar *) NULL ;
	int xresult = 0 ;

trace(("in  asciiverifnlg(%s,%s,%s,%s)\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,(uchar *)word4))

	if ( l1 > MAXWORD || l2 > MAXWORD || l3 > MAXWORD )
	{
		/* error(MODULE,"asciiverifnlg","length overflow") ; */
		return xresult ;
	} ;

	if ( charconstraint(word1,word2,word3) )
	{
		if ( initialisation(word1,word2,word3,l1,l2,l3) )
		{
/*
trace(("mid pdist(%s,%s) = %d, pdist(%s,%s) = %d\n", word1,word2,matrix12[l1+1][l2+1],word1,word3,matrix13[l1+1][l3+1]))
			if ( matrix12[l1+1][l2+1] < matrix13[l1+1][l3+1] )
				initialisation(word1,word3,word2) ;
*/

if ( tracet )
   tracematrices((uchar *)word1,(uchar *)word2,(uchar *)word3,l1,0,0,0, l1,l2,l3) ;

			resolution = 0 ;
			result = pr_mov(word1,word2,word3,word4,l1,l2,l3) ;
/*
			if ( result && strcmp((uchar *) result,"") )
*/
			if ( result && ! strcmp((uchar *) result,(uchar *) word4) )
			{
				xresult = 1 ;
				if ( "" != result )
					free(result) ;
			} ;
#if CONTIGUITY
			freematrix123(matrix123,l1,l2,l3) ;
			freematrix4(matrix4,l2+l3-l1) ;
#endif
		} ;
	} ;

trace(("out asciiverifnlg(%s,%s,%s,%s) = %d\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,(uchar *)word4,xresult))

	return xresult ;
}

/*
 * Call to solve an analogy with utf8 strings
 * assume total number of characters in all strings is less than 256
 */

unsigned char *utf8solvenlg(char *uword1, char *uword2, char *uword3)
{
	unsigned char *result = NULL ;
	uchar *word1 = NULL,
		  *word2 = NULL,
		  *word3 = NULL,
		  *word4 = NULL ;

	initializecodedict() ;
	word1 = encode((unsigned char *) uword1) ;
	word2 = encode((unsigned char *) uword2) ;
	word3 = encode((unsigned char *) uword3) ;
	word4 = asciisolvenlg(word1,word2,word3) ;
trace(("mid utf8solvenlg(%s,%s,%s,%s)\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,NULL==word4?"NULL":"not NULL"))
trace(("mid utf8solvenlg(%s,%s,%s,%s)\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,""==word4?"epsilon":"not epsilon"))
	if ( NULL != word4 )
		result = decode(word4) ;

	free(word1) ;
	free(word2) ;
	free(word3) ;
	/*
		Caution with free(word4).
		Doing free(word4) without a test in cases where word4 = ""
		will give error 'pointer was not allocated'
		because result is initialized to constant "" in asciisolvenlg.
	*/
trace(("mid utf8solvenlg(%s,%s,%s,%s)\n", (char *)uword1,(char *)uword2,(char *)uword3,NULL==result?"NULL":"not NULL"))
trace(("mid utf8solvenlg(%s,%s,%s,%s)\n", (char *)uword1,(char *)uword2,(char *)uword3,""==result?"epsilon":"not epsilon"))

	if ( NULL != word4 && "" != word4 )
/*	if ( word4 && ( strcmp((uchar *) word4,"")) ) */
		free(word4) ;

	return result ;
}

/*
 * Call to verify an analogy with utf8 strings
 * assume total number of characters in all strings is less than 256
 */

int utf8verifnlg(char *uword1, char *uword2, char *uword3, char *uword4)
{
	int result = 0 ;
	uchar *word1 = NULL,
		  *word2 = NULL,
		  *word3 = NULL,
		  *word4 = NULL ;

trace(("in utf8verifnlg(%s,%s,%s,%s)\n", (char *)uword1,(char *)uword2,(char *)uword3,NULL==word4?"NULL":"not NULL"))
trace(("mid utf8verifnlg(%s,%s,%s,%s)\n", (char *)uword1,(char *)uword2,(char *)uword3,""==word4?"epsilon":"not epsilon"))

	initializecodedict() ;
	word1 = encode((unsigned char *) uword1) ;
	word2 = encode((unsigned char *) uword2) ;
	word3 = encode((unsigned char *) uword3) ;
	word4 = encode((unsigned char *) uword4) ;
	result = asciiverifnlg(word1,word2,word3,word4) ;
trace(("mid utf8solvenlg(%s,%s,%s,%s)\n", (char *)uword1,(char *)uword2,(char *)uword3,NULL==result?"NULL":"not NULL"))
trace(("mid utf8solvenlg(%s,%s,%s,%s)\n", (char *)uword1,(char *)uword2,(char *)uword3,""==result?"epsilon":"not epsilon"))
	free(word1) ;
	free(word2) ;
	free(word3) ;
	free(word4) ;

	return result ;
}

/*
 * Call to solve an analogy
 */

char *solvenlg(char *word1, char *word2, char *word3)
{
	char *result = NULL ;
		  
trace(("in  solvenlg(%s,%s,%s)\n", (uchar *)word1,(uchar *)word2,(uchar *)word3))

	if ( isasciistring((unsigned char *) word1)
	  && isasciistring((unsigned char *) word2)
	  && isasciistring((unsigned char *) word3) )
		result = asciisolvenlg(word1,word2,word3) ;
	else
		result = utf8solvenlg(word1,word2,word3) ;

trace(("out solvenlg(%s,%s,%s) = %s\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,(char *)result))

	return result ;
}

/*
 * Call to verify an analogy
 */

int verifnlg(char *word1, char *word2, char *word3, char *word4)
{
	int result = 0 ;
		  
trace(("in  verifnlg(%s,%s,%s,%s)\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,(uchar *)word4))

	if ( isasciistring((unsigned char *) word1)
	  && isasciistring((unsigned char *) word2)
	  && isasciistring((unsigned char *) word3)
	  && isasciistring((unsigned char *) word4) )
		result = asciiverifnlg(word1,word2,word3,word4) ;
	else
		result = utf8verifnlg(word1,word2,word3,word4) ;

trace(("out verifnlg(%s,%s,%s,%s) = %d\n", (uchar *)word1,(uchar *)word2,(uchar *)word3,(uchar *)word4,result))

	return result ;
}





