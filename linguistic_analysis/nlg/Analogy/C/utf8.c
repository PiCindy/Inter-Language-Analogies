/* Copyright (c) 2013, 2014, Yves Lepage */
#define MODULE "utf8"
#define TRACE 0
/* extern int tracet ; */

/*
 * Encoding and decoding of utf8 strings into byte strings (= integer strings).
 * A dictionary is built that remembers the correspondence
 *    integer -> utf8 character
 * by copying the original utf8 characters into a dictionary.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/*
#include "usrlib.h"
#include "usrmath.h"
*/
#include "utf8.h"

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
 * Messages for warnings and errors
 */

#define ERR_MODULE_LABEL       " in module:   "
#define ERR_FUNCTION_LABEL     " in function: "
#define ERR_DIAGNOSTIC_LABEL   " diagnostic:  "

/*
 * Error, do not exit
 */

static void warning(char *module_name, char *function_name, char *msg)
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

static void error(char *module_name, char *function_name, char *msg)
{
	warning(module_name,function_name,msg) ;
	abort() ;
}


/*
 * Variables for traces, etc. for the programmer
 */

static int tracet	= 0 ;
static int debug	= 0 ;

/*
 * Various variables
 */

#define uchar			char

/*
 * size of UTF8 character or string in bytes
 */

static int utf8charsize(unsigned char *ss)
{
	int result = 1 ;
	
trace(("in  utf8charsize(%s)\n",ss))

	if (( *ss & 0x80 ) == 0 )			/* 0xxx xxxx lead bit == zero => single ascii */
		result = 1 ;
	else if (( *ss & 0xE0 ) == 0xC0 )	/* 110x xxxx => two-byte char */
		result = 2 ;
	else if (( *ss & 0xF0 ) == 0xE0 )	/* 1110 xxxx => three-byte char */
		result = 3 ;
	else if (( *ss & 0xF8 ) == 0xF0 )	/* 1111 0xxx => four-byte char */
		result = 4 ;
	else
		warning(MODULE,"utf8charsize","Unrecognized lead byte.\n") ;
		/* printf( "Unrecognized lead byte (%02x)\n", *ss ); */

trace(("out utf8charsize(%s) = %d\n",ss,result))

	return result ;
}

static int utf8stringsize(unsigned char *s)
{
	int result = 0 ;
	unsigned char *ss = s ;	/* iterator on string s */
	int bl = 0 ;			/* for length in bytes */
	
trace(("in  utf8stringsize(%s)\n",s))

	for ( ss = s ; *ss ; ss += bl )
	{
		bl = utf8charsize(ss) ;
		result += 1 ;
	} ;
	
trace(("out utf8stringsize(%s) = %d\n",s,result))

	return result ;
}

/*
 * Dictionary management.
 * initializecodedict is an interface function.
 * All other functions are static.
 */

/*
 * Variables for the dictionary.
 */

/* FIRST_CODE should be greater than 0 */
#if TRACE
#define FIRST_CODE	65		/* set to 65 = 'A' for trace */
#else
#define FIRST_CODE 	1		/* set to 1 for actual implementation */
#endif

#define LAST_CODE	255		/* Limited to the number of ascii characters */

static int nextindict = FIRST_CODE ;

#define UTFCHARMAXSIZE	4

static unsigned char codedict[LAST_CODE*UTFCHARMAXSIZE] ;
static int lenchar[LAST_CODE] = { 0 } ;

/*
 * Lookup of the dictionary
 * Addition of an entry into the dictionary
 * Conditional update of the dictionary for one utf8 char:
 *    if already present, return the code
 *    if was absent from the dictionary, add it and return new code
 * Except for the initialization of the dictionary,
 *   the input is utf8 character (a pointer to a utf8 string) with its length in bytes
 */

static int lookupcodedict(unsigned char *s, int len)
{
/*
	int result = -1 ;
*/
	int result = 0 ;
	int found = 0 ;
	
trace(("in  lookupcodedict(%.*s,%d)\n",len,s,len))

	for ( found = 0, result = FIRST_CODE ; (! found) && result < nextindict ; ++result )
	{
		unsigned char *cc = &codedict[result*UTFCHARMAXSIZE],
					  *ss = s ;
		int cclen = lenchar[result] ;
		int i = 0 ;

trace(("mid lookupcodedict(%.*s,%d, %.*s,%d)\n",len,s,len, cclen,cc,cclen))

		for ( i = 0 ; *(cc+i) == *(ss+i) && (i < len) && (i < cclen); ++i ) ;
		if ( i == len )
			found = 1 ;
	} ;
	if ( ! found )
		result = -1 ;
	else
		result -= 1 ;

trace(("out lookupcodedict(%.*s) = %d = %c\n",len,s,result,(-1==result)?'?':result))

	return result ;
}

static int addtocodedict(unsigned char *s, int len)
{
	int result = -1 ;
	
trace(("in  addtocodedict(%.*s,%d)\n",len,s,len))

	if ( nextindict < LAST_CODE )
	{
		int i = 0 ;
		
		result = nextindict ;
		for ( i = 0 ; i < len ; ++i )
			codedict[result*UTFCHARMAXSIZE+i] = s[i] ;
		lenchar[result] = len ;
		++nextindict ;
	}
	else
		warning("utf8","addtocodedict","Dictionary capacity exceeded. Continues with wrong encoding.") ;

trace(("out addtocodedict(%.*s) = %d = %c\n",len,s,result,result))

	return result ;
}

static int updatecodedict(unsigned char *s, int len)
{
	int result = 0 ;
	
trace(("in  updatecodedict(%.*s,%d)\n", len, s, len))

	result = lookupcodedict(s, len) ;
	if ( -1 == result )
		result = addtocodedict(s, len) ;

trace(("out updatecodedict(%.*s) = %d = %c\n", len, s, result, result))

	return result ;
}

/*
 * Find the smallest ascii char not used in ascii string
 */

static uchar lbchar(char *s)
{
	char result = 1 ;
	char *ss = s ;

trace(("in  lbchar(%s)\n",s))

	for ( ss = s ; *ss ; ++ss )
		if ( result < *ss )
			result = *ss ;
	if ( 1 < (int) result )
		result = (char) (((int) result) + 1) ;
	else
		error(MODULE,"lbchar","Lower bound char is 0.") ;

trace(("in  lbchar(%s) = %c\n",s,result))

	return result ;
}

/*
 * Interface functions:
 * replace the unicode characters in a unicode string by an ascii character
 * that is not used in a second ascii string
 */

uchar *maskunicodechar(unsigned char *s, unsigned char *aword)
{
	char *result = (char *) calloc(strlen(s)+1, sizeof(char *)) ;
	char c = lbchar(aword) ;
	char *ss = s ;			/* iterator on string s */
	int bl = 0, 			/* for length in bytes */
		i = 0 ;

trace(("in  maskunicodechar(%s,%s(%c))\n",s,aword,c))

	for ( ss = s, i = 0 ; *ss ; ss += bl, ++i )
	{
		bl = utf8charsize(ss) ;
		result[i] = ( 1 < bl ) ? c++ : (*ss) ;
		if ( 255 <= c )
		{
			c -= 1 ;
			warning(MODULE,"maskunicodechar","Character overflow: subsequent results may be false.") ;
		} ;
	} ;

trace(("out maskunicodechar(%s,%s) = %s,%d\n",s,aword,result,strlen(result)))

	return result ;
}

/*
 * Interface functions:
 * check whether a string is an ascii string or not
 * initialization of the dictionary
 * encoding or decoding of UTF8 strings using the dictionary
 */

int isasciistring(unsigned char *s)
{
	int result = 1 ;
	unsigned char *ss = s ;	/* iterator on string s */
	
trace(("in  isasciistring(%s)\n",s))
/*
	for ( ss = s ; *ss && result ; ++ss )
		result = ( 1 == utf8charsize(ss) ) ;
*/
	for ( ss = s ; *ss && result ; ++ss )
		result = ( 0 == ( *ss & 0x80 ) ) ; /* just check that first bit is not 1 for all chars */
	
trace(("out isasciistring(%s) = %d\n",s,result))

	return result ;
}

void initializecodedict(void)
{
	nextindict = FIRST_CODE ;
}

uchar *encode(unsigned char *s)
{
	uchar *result = NULL ;
	unsigned char *ss = s ;	/* iterator on string s */
	int bl = 0, 			/* for length in bytes */
		i = 0 ;

trace(("in  encode(%s)\n",s))

	result = (uchar *) calloc(utf8stringsize(s)+1,sizeof(uchar)) ;
	for ( ss = s, i = 0 ; *ss ; ss += bl, ++i )
	{
		bl = utf8charsize(ss) ;
		result[i] = updatecodedict(ss,bl) ;
	} ;
	
trace(("out encode(%s) = %s\n",s,result))

	return result ;
}

unsigned char *decode(uchar *s)
{
	unsigned char *result = NULL,
				  *rr = NULL ;
	uchar *ss = s ;
	int size = 0 ;

trace(("in  decode(%s)\n",s))

	size = 0 ;
	for ( ss = s ; *ss ; ++ss )
		size += lenchar[*ss] ;

trace(("mid decode(%s) size = %d\n",s,size))

	rr = result = (unsigned char *) calloc(size+1,sizeof(unsigned char)) ;
	if ( 0 != size )
	{
		for ( ss = s ; *ss ; ++ss )
		{
			int i = 0 ;
			
			for ( i = 0 ; i < lenchar[(int)*ss] ; ++i, ++rr )
				/* *rr = *(codedict[(int)*ss]+i) ;*/
				*rr = codedict[((int)*ss)*UTFCHARMAXSIZE+i] ;
		} ;
	} ;

trace(("out decode(%s) = %s\n",s,result))

	return result ;
}
