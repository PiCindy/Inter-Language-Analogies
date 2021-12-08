/* File : nlgclu.c */
/* Copyright (c) 2014, 2015, Yves Lepage */

#define MODULE "nlgclu.c"
#define TRACE 0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <time.h>

#include "nlgclu.h"

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

const int SHIFT = 4;
const char *BLANKS = "                                       ";
int length = 0;

/*
 * Exit on error
 */

#define ERR_MODULE_LABEL       " in module:   "
#define ERR_FUNCTION_LABEL     " in function: "
#define ERR_DIAGNOSTIC_LABEL   " diagnostic:  "

/*
 * Warning, do not exit
 */

void warning(char *module_name, char *function_name, char *msg)
{
    fprintf(stderr,
            "\n#"
            "\n#" ERR_MODULE_LABEL "%s"
            "\n#" ERR_FUNCTION_LABEL "%s"
            "\n#" ERR_DIAGNOSTIC_LABEL "%s"
            "\n#"
            "\n",
            module_name, function_name, msg) ;
    fflush(stderr) ;
}

/*
 * Exit on error
 */

void error(char *module_name, char *function_name, char *msg)
{
    warning(module_name, function_name, msg) ;
    abort() ;
}

/*
 * Print a list of integers.
 */

int intsize(int n)
{
    int result = 0;
    int m = n;

ntrace(("in  intsize(%d)\n", n))

    if ( m )
	{
		if ( m < 0 )
		{
			result += 1 ;
			m = -m ;
		} ;
        for ( m = n ; m ; ++result, m = m / 10 );
    }
	else
        result = 1 ;

ntrace(("out intsize(%d) = %d\n", n, result))

    return result ;
}

char *li2s(int length, int *list)
{
    int strlen = 0 ;
    int i = 0 ; /* Index on list. */
    static char *result = NULL ;
	char *xresult = NULL ; /* Iterator on result. */

	if ( ! result )
	{
		free(result) ;
		result = NULL ;
    } ;
	for (i = 0; i < length; ++i)
        strlen += intsize(list[i]) ;
    strlen += 2 * length + 2 + 1 ;
    result = (char *) calloc(strlen, sizeof(char)) ;
    xresult = result ;

    *xresult = '[' ;
    xresult += 1 ;
    for (i = 0 ; i < length ; ++i)
	{
        if (0 != i)
		{
            sprintf(xresult, ", ") ;
            xresult += 2 ;
		};
        sprintf(xresult, "%d", list[i]) ;
        xresult += intsize(list[i]) ;
    };
    *xresult = ']' ;

    return result ;
}

/*
 * Boolean values
 */

#define TRUE	1
#define FALSE	0

/*
 * The two feature trees are global variables.
 * A feature tree is just a list of integers,
 * more precisely of list of sequences of NODESIZE integers.
 * Each position divided by NODESIZE in a feature tree is the index of a node.
 */

int VERBOSE = 0;
int LINEOUT = 0;
int symmetry = FALSE;
int *treeA = NULL; /* The first  feature tree structure */
int *treeB = NULL; /* The second feature tree structure */
int last_level = 0;
char **linetableA = NULL; /* The starting point of each line in the first list of lines */
char **linetableB = NULL; /* The starting point of each line in the second list of lines */

/*
 * A well-formed cluster is considered degenerated if its length is less than the following threshold.
 */

int CLUSTER_MINIMAL_LENGTH = 2;			/* 2 for all theoretically possible clusters */
int CLUSTER_MAXIMAL_LENGTH = INT_MAX;	/* INT_MAX for all theoretically possible clusters */

/*
 * Structure of a node in a feature tree.
 */

#define NODESIZE						7					/* size of the node in the feature tree structure */

#define level(tree,i)					tree[NODESIZE*i+0]
#define width(tree,i)					tree[NODESIZE*i+1]
#define object(tree,i)					tree[NODESIZE*i+2]
#define value(tree,i)					tree[NODESIZE*i+3]	/* value of the feature for this interval [begin:end] */
#define is_empty_rest(tree,i)			tree[NODESIZE*i+4]	/* for a node of width 1, whether all the lower values are 0, i.e., no other char is present */
#define next_level_begin_node(tree,i)	tree[NODESIZE*i+5]	/* beginning of the next level */
#define next_level_end_node(tree,i)		tree[NODESIZE*i+6]	/* end of the next level */

/*
 * Values for the number of values and the number of pairs.
 */

int _VALMIN = 32;
int _VALNBR = 32;

/*
 * For trace only
 */

void print_node(int *tree, int i)
{
    printf("----- Node %2d -----\n", i);
    printf("level(tree,%d) 					= %d\n", i, level(tree, i));
    printf("width(tree,%d) 					= %d\n", i, width(tree, i));
    printf("object(tree,%d) 				= %d\n", i, object(tree, i));
    printf("value(tree,%d) 					= %d\n", i, value(tree, i));
    printf("is_empty_rest(tree,%d) 			= %d\n", i, is_empty_rest(tree, i));
    printf("next_level_begin_node(tree,%d)	= %d\n", i, next_level_begin_node(tree, i));
    printf("next_level_end_node(tree,%d)	= %d\n", i, next_level_end_node(tree, i));
    printf("------------------\n");
}

/*
 * Structure for the data contained in the temporary file.
 */

typedef struct FEATURES_T
{
  int length;
  int *thetree;
  char *thelines;
}
FEATURES ;

/*
 * Temporary file for the clusters.
 */

FILE *cluout = NULL ;

/*
 * Compute the minimal possible value
 */

int minvalueA = 0;
int maxvalueA = 0;
int maxsizeA = 0;

int minvalueB = 0;
int maxvalueB = 0;
int maxsizeB = 0;

void gettreeparams(int lengthA, int *treeA)
{
    int i = 0;
    int sizeA = 1;

trace(("in  gettreeparams(lengthA = %d)\n", lengthA))

    minvalueA = maxvalueA = value(treeA, 0);
    maxsizeA = next_level_end_node(treeA, 0) - next_level_begin_node(treeA, 0) + 1;

    for (i = 0; i < (lengthA / NODESIZE) - 1; ++i)
	{
        int valueA = value(treeA, i);
        int nextbeginA = next_level_begin_node(treeA, i),
			nextendA = next_level_end_node(treeA, i);

        if (valueA < minvalueA)
            minvalueA = valueA;
        if (maxvalueA < valueA)
            maxvalueA = valueA;

        sizeA = nextendA - nextbeginA + 1;

        if (maxsizeA < sizeA)
            maxsizeA = sizeA;
    };

trace(("out gettreeparams(lengthA = %d) minvalueA = %d, maxvalueA = %d, maxziseA = %d\n", lengthA, minvalueA, maxvalueA, maxsizeA))
}

void getmatrixparams(int lengthA, int lengthB, int *treeA, int *treeB)
{
trace(("in  getmatrixparams(lengthA = %d, lengthB = %d)\n", lengthA, lengthB))

    gettreeparams(lengthB, treeB);
    minvalueB = minvalueA;
    maxvalueB = maxvalueA;
    maxsizeB = maxsizeA;
    gettreeparams(lengthA, treeA);

    _VALMIN = minvalueA - maxvalueB;
    _VALNBR = maxvalueA - minvalueB - _VALMIN + 1;

trace(("out getmatrixparams(lengthA = %d, lengthB = %d) _VALMIN = %d, _VALNBR = %d\n", lengthA, lengthB, _VALMIN, _VALNBR))
}

/*
 * Creating matrix of integers
 * in refine_down for feature difference values and indices in A and B
 * on the next level.
 */

int **newmatrix(void)
{
    int **result = NULL;

ntrace(("in  newmatrix(%d)\n", _VALNBR))

    result = (int **) calloc(_VALNBR + 1, sizeof (int *));

ntrace(("out newmatrix(%d) done\n", _VALNBR))

    return result;
}

/*
 * Free matrix of integers.
 */

void freematrix(int **matrix)
{
    int i = 0;

ntrace(("in  freematrix(%d)\n", _VALNBR))

    for (i = 0; i < _VALNBR; ++i)
		if (! matrix[i])
        	free(matrix[i]);
    free(matrix);

ntrace(("out freematrix(%d) done\n", _VALNBR))
}

/*
 * Creating table of pointers to line.
 */

void newlinetable(char *s) {
    char *ss = NULL;
    int size = 0;
    int i = 0;

ntrace(("in  newlinetable(%s)\n", s))

	/* Counting the number of lines. */
    for (ss = s, size = 0; *ss; ++ss)
	{
        if ('\n' == *ss)
            size += 1;
    };

ntrace(("out newlinetable() size = %d\n", size))

	/* Creating linetableA. */
	linetableA = (char **) calloc(size + 2, sizeof (char *));
	/* Filling in linetableA and cutting linesA into lines at the same time. */
	linetableA[0] = s;
	for (ss = s, i = 0; *ss; ++ss) {
		if ('\n' == *ss) {
			i += 1;
			linetableA[i] = ss + 1;
		};
	};
	i += 1;
	linetableA[i] = ss;
	
ntrace(("out newlinetable(%s)\n", s))
}

/*
 * Freeing table of pointers to line.
 */

void freelinetable(char **linetable)
{
ntrace(("in  freelinetable()\n"))

    free(linetable);

ntrace(("out freelinetable()\n"))
}

/*
 * Print a cluster.
 */

void print_cluster(int length, int *nodesA, int *nodesB)
{
    static int clu_nbr = 0;
    int i = 0;
    char cA = ' ',
		 cB = ' ';

ntrace(("in  print_cluster(%d, %s, %s)\n", length, li2s(length, nodesA), li2s(length, nodesB)))

	if (VERBOSE) fprintf(stderr, "\r# %d clusters... ", ++clu_nbr);
	for (i = 0; i < length; ++i)
	{
		int iA = 0,
			iB = 0;

ntrace(("mid print_cluster(%d, %d)\n", object(treeA, nodesA[i]), object(treeB, nodesB[i])))

		if (0 != i)
		{
			fprintf(cluout, " :: ");
			if ( LINEOUT )
				fprintf(stderr, " :: ");
		} ;
		
		iA = object(treeA, nodesA[i]);
		iB = object(treeB, nodesB[i]);
		fprintf(cluout, "%d : %d", iA, iB);
		
ntrace(("mid print_cluster() 1 iA = %d, iB = %d\n", iA, iB))

		if ( LINEOUT )
		{
			cA = *(linetableA[iA + 1] - 1); /* Should be '\n' */
			cB = *(linetableB[iB + 1] - 1); /* Should be '\n' */
			*(linetableA[iA + 1] - 1) = '\0';
			*(linetableB[iB + 1] - 1) = '\0';
			fprintf(stderr, "%s : %s", linetableA[iA], linetableB[iB]);
			*(linetableA[iA + 1] - 1) = cA;
			*(linetableB[iB + 1] - 1) = cB;
		} ;
	};

	fprintf(cluout, "\n");
	fflush(cluout);
	if ( LINEOUT )
	{
		fprintf(stderr, "\n");
		fflush(stderr);
	} ;

ntrace(("out print_cluster(%d, %s, %s)\n", length, li2s(length, nodesA), li2s(length, nodesB)))
}

/*
 * Test for degenerated clusters.
 * A degenerated list is a list of pairs of intervals that contain only one pair of intervals,
 * and such that one of the intervals in the pair contains only one object.
 * A degenerated list cannot lead to any analogical cluster
 * because an analogical cluster contains necessarily at least 4 objects, whereas there are only 2 objects here.
 * The purpose of spotting degenerated lists is to eliminate them as soon as possible
 * so as to speed up the computation.
 */

int is_degenerated(int length, int *nodesA, int *nodesB)
{
    int result = FALSE;

ntrace(("in  is_degenerated(%d, %s, %s)\n", length, li2s(length, nodesA), li2s(length, nodesB)))

    result = ( (1 == length) && ((1 == width(treeA, nodesA[0])) || (1 == width(treeB, nodesB[0]))) ) ;

ntrace(("out is_degenerated(%d, %s, %s) = %s\n", length, li2s(length, nodesA), li2s(length, nodesB), result ? "TRUE" : "FALSE"))

    return result;
}

/*
 * Recognize the trivial cluster A : A :: B : B :: C : C :: ...
 */

int is_singleton_pair(int length, int nodeAi, int nodeBi)
{
	int result = FALSE ;
	
trace(("in  is_singleton_pair(%d, %d, %d)\n", length, nodeAi, nodeBi))

	result = (1 == width(treeA, nodeAi)) && (1 == width(treeB, nodeBi))
				&& object(treeA, nodeAi) == object(treeB, nodeBi) ;

trace(("out is_singleton_pair(%d, %d, %d) = %s\n", length, nodeAi, nodeBi, result ? "TRUE" : "FALSE"))

	return result ;
}

int is_trivial(int length, int *nodesA, int *nodesB)
{
    int result = FALSE;

trace(("in  is_trivial(%d, %s, %s)\n", length, li2s(length, nodesA), li2s(length, nodesB)))

	if ( symmetry )
	{
        int i = 0;
		
        for ( i = 0 ; i < length && is_singleton_pair(length, nodesA[i], nodesB[i]) ; ++i ) ;
		result = (i == length) ;
	} ;

trace(("out is_trivial(%d, %s, %s) = %s\n", length, li2s(length, nodesA), li2s(length, nodesB), result ? "TRUE" : "FALSE"))

    return result;
}

/*
 * Check whether
 * 	1/ this is already a list of pairs of only one object and
 * 	2/ there are no more chars on the levels below.
 * In that case, this is a cluster and we can output it.
 */

int is_finished_singleton_pair(int length, int nodeAi, int nodeBi)
{
	int result = FALSE ;
	
trace(("in  is_finished_singleton_pair(%d, %d, %d)\n", length, nodeAi, nodeBi))

	result = (1 == width(treeA, nodeAi)) && (1 == width(treeB, nodeBi))
				&& is_empty_rest(treeA, nodeAi)  && is_empty_rest(treeB, nodeBi) ;

trace(("out is_finished_singleton_pair(%d, %d, %d) = %s\n", length, nodeAi, nodeBi, result ? "TRUE" : "FALSE"))

	return result ;
}

static int rest_n = 0 ;

int is_empty_rest_cluster(int length, int *nodesA, int *nodesB)
{
    int result = FALSE;

trace(("in  is_empty_rest_cluster(%d, %s, %s)\n", length, li2s(length, nodesA), li2s(length, nodesB)))

	if ( symmetry )
	{
        int i = 0;
		
        for ( i = 0 ; i < length && is_finished_singleton_pair(length, nodesA[i], nodesB[i]) ; ++i ) ;
		result = (i == length) ;
	} ;

trace(("out is_empty_rest_cluster(%d, %s, %s) = %s\n", length, li2s(length, nodesA), li2s(length, nodesB), result ? "TRUE" : "FALSE"))

	if (result)
		rest_n += 1 ;
    return result;
}

/*
 * Compute the surface of a cluster
 * by adding up the products
 * of widths along A and B.
 */

int surface(int length, int *nodesA, int *nodesB)
{
	int result = 0 ;
	int i = 0;
	
trace(("in  surface(%d, %s, %s)\n", length, li2s(length, nodesA), li2s(length, nodesB)))
	
	for ( i = 0 ; i < length ; ++i )
		result += width(treeA, nodesA[i]) * width(treeB, nodesB[i]) ;

trace(("out surface(%d, %s, %s) = %d\n", length, li2s(length, nodesA), li2s(length, nodesB), result))

	return result ;
}

/*
 * Analogical clustering proper.
 * NodesA and nodesB have the same length, length.
 * The two nodes of same index in nodesA and nodesB correspond one to each other.
 * Precondition:
 *    all nodeA x nodeB have the same feature difference value on level n.
 * The purpose of this function is to split further each node and compute their differences on the next level.
 * In this function, we go from level n to level n+1.
 * Postcondition:
 *    the matrix contains the feature difference value for each subnode in A corresponding to each subnode in B
 */


static int MAXPAIRNBR = 0 ;

void xrefine_down(int length, int *nodesA, int *nodesB, int diffvalue, int level)
{
    int i = 0; /* indices in nodesA and nodesB on the current level */
    int *indexvector = NULL ; /* Vector of number of indices on the next level. */
    int *maxindexvector = NULL ; /* Vector of max number of indices on the next level. */
	int **nextnodeAmatrix = NULL , /* Matrix of indices for nodeA on the next level. */
		**nextnodeBmatrix = NULL ; /* Matrix of indices for nodeB on the next level. */
    int v = 0 ;

    void refine_down(int length, int *nodesA, int *nodesB, int diffvalue, int level) ;

trace(("%.*sin  xrefine_down(level=%d, diffvalue=%d, length=%d, %s, %s)\n", SHIFT*level, BLANKS, level, diffvalue, length, li2s(length, nodesA), li2s(length, nodesB)))

trace(("mid xrefine_down() Creating matrices and index vectors...\n"))

    indexvector = (int *) calloc(_VALNBR + 1, sizeof (int)) ;
	maxindexvector = (int *) calloc(_VALNBR + 1, sizeof (int)) ;
    nextnodeAmatrix = newmatrix()  ;
    nextnodeBmatrix = newmatrix() ;

trace(("mid xrefine_down() Matrices and index vector created.\n"))
trace(("mid xrefine_down() Filling matrices and index vector...\n"))

    for (i = 0 ; i < length ; ++i)
	{
        int nodeA = nodesA[i],
			nodeB = nodesB[i] ;
        int nextbeginA = next_level_begin_node(treeA, nodeA),
			nextendA = next_level_end_node(treeA, nodeA) ;
        int nextbeginB = next_level_begin_node(treeB, nodeB),
			nextendB = next_level_end_node(treeB, nodeB) ;
        int nextnodeA = 0, /* nodes on the next level */
			nextnodeB = 0 ;

        for ( nextnodeA = nextbeginA ; nextnodeA <= nextendA ; ++nextnodeA )
            for ( nextnodeB = nextbeginB ; nextnodeB <= nextendB ; ++nextnodeB )
                if ( ! ( symmetry && object(treeA, nextnodeA) > object(treeB, nextnodeB) ) )
				{
                    int v = value(treeA, nextnodeA) - value(treeB, nextnodeB) - _VALMIN ;

					if ( _VALNBR <= v )
					{
                        fprintf(stderr, "*** Too big value: %d...\n", v) ;
                        fflush(stderr) ;
                    };
					if ( 0 == indexvector[v] )
					{
						maxindexvector[v] = 256 ;
						nextnodeAmatrix[v] = (int *) calloc(maxindexvector[v], sizeof (int));
						nextnodeBmatrix[v] = (int *) calloc(maxindexvector[v], sizeof (int));
                    } ;
					if ( maxindexvector[v] <= indexvector[v] )
					{
						maxindexvector[v] = 2 * indexvector[v] ;
trace(("mid xrefine_down() nextnodeAmatrix[%d] extended to size %d.\n",v,maxindexvector[v]))
						nextnodeAmatrix[v] = (int *) realloc(nextnodeAmatrix[v], maxindexvector[v] * sizeof (int));
						nextnodeBmatrix[v] = (int *) realloc(nextnodeBmatrix[v], maxindexvector[v] * sizeof (int));
					} ;
                    nextnodeAmatrix[v][indexvector[v]] = nextnodeA ;
                    nextnodeBmatrix[v][indexvector[v]] = nextnodeB ;
                    indexvector[v] += 1 ;
					
					if ( MAXPAIRNBR < indexvector[v] )
						MAXPAIRNBR = indexvector[v] ;

                } ;
    } ;

trace(("mid xrefine_down() Matrices and index vector filled.\n"))
trace(("mid xrefine_down() Processing by feature difference value...\n"))

    for (v = 0; v < _VALNBR; ++v)
	{
trace(("mid xrefine_down() %d pairs with value = %d\n", indexvector[v], v))

        if (0 < indexvector[v])
		{
            refine_down(indexvector[v], nextnodeAmatrix[v], nextnodeBmatrix[v], v, level + 1);
			free(nextnodeAmatrix[v]);
			free(nextnodeBmatrix[v]);
		};
    };

trace(("mid xrefine_down() Processing by feature difference value done.\n"))
trace(("mid xrefine_down() Freeing matrices and vector of different values...\n"))

    freematrix(nextnodeAmatrix);
	freematrix(nextnodeBmatrix);
    free(indexvector);
    free(maxindexvector);

trace(("mid xrefine_down() Vector and matrices freeed.\n"))

trace(("%.*sout xrefine_down(level=%d, diffvalue=%d, length=%d, %s, %s)\n", SHIFT*level, BLANKS, level, diffvalue, length, li2s(length, nodesA), li2s(length, nodesB)))
}

/*
 * The following function wraps the previous function xrefine_down.
 * It prevents exploring possibly degenerated clusters,
 * or too small well-formed clusters.
 */

void refine_down(int length, int *nodesA, int *nodesB, int diffvalue, int level)
{
trace(("%.*sin  refine_down(length=%d, diffvalue=%d, level=%d, %s, %s)\n", SHIFT*level, BLANKS, length, diffvalue, level, li2s(length, nodesA), li2s(length, nodesB)))

	if ((3*last_level < 4*level) && (surface(length, nodesA, nodesB) < CLUSTER_MINIMAL_LENGTH))
	{
trace(("%.*smid refine_down(level=%d) CLUSTER TOO SMALL: DO NOT CONTINUE\n", SHIFT*level, BLANKS, level))
	}
    else if (is_degenerated(length, nodesA, nodesB))
	{
trace(("%.*smid refine_down(level=%d) DEGENERATED CLUSTER: DO NOT CONTINUE\n", SHIFT*level, BLANKS, level))
    }
	else if (is_empty_rest_cluster(length, nodesA, nodesB) || last_level == level)
/*	else if (last_level == level) */
	{
		if ( surface(length, nodesA, nodesB) > CLUSTER_MAXIMAL_LENGTH )
		{
trace(("%.*smid refine_down(level=%d) CLUSTER TOO BIG: DO NOT PRINT\n", SHIFT*level, BLANKS, level))
		}
		else if (is_trivial(length, nodesA, nodesB))
		{
trace(("%.*smid refine_down(level=%d) TRIVIAL CLUSTER: DO NOT PRINT\n", SHIFT*level, BLANKS, level))
		}
		else
		{
trace(("%.*smid refine_down(level=%d, last_level=%d) OUTPUT CLUSTER\n", SHIFT*level, BLANKS, level, last_level))
			print_cluster(length, nodesA, nodesB);
		} ;
    }
	else
	{
        xrefine_down(length, nodesA, nodesB, diffvalue, level);
    };

trace(("%.*sout refine_down(level=%d, diffvalue=%d, %d, %s, %s)\n", SHIFT*level, BLANKS, level, diffvalue, length, li2s(length, nodesA), li2s(length, nodesB)))
}

/*
 * Analogical clustering
 * The list of integers should be a list of NODESIZE-tuples of integers (see above).
 * 		n is the number of integers in the list of integers representing the tree.
 */

void analogical_clustering(int verbose, int lengthA, int lengthB, int *thetreeA, int *thetreeB, char *thelinesA, char *thelinesB)
{
    int nodesA = 0,
		nodesB = 0;
    int last_node = 0;
    /*int i = 0;*/

trace(("in  analogical_clustering(%d, %d, %s, %s)\n", lengthA, lengthB, li2s(lengthA, thetreeA), li2s(lengthB, thetreeB)))

    /* Initialize the global variables VERBOSE and symmetry. */
    VERBOSE = verbose;
/*
    if (thetreeA == thetreeB)
        symmetry = TRUE;
*/

    /* Initialize the global variables treeA and treeB. */
	treeA = thetreeA ;
	treeB = thetreeB ;

	if ( LINEOUT )
	{
		/* Creating the table of lines. */
		/* CAUTION: lines and linetable are global variables */
		newlinetable(thelinesB);
		linetableB = linetableA;
		if (!symmetry)
			newlinetable(thelinesA);
	} ;

trace(("mid analogical_clustering() symmetry = %s\n", symmetry ? "true" : "false"))

    /* n = NODESIZE * number of nodes and we start with 0, thus last node has the number (n/NODESIZE)-1 */
    last_node = (lengthA / NODESIZE) - 1;
    /* CAUTION: last_level is a global variable */
    last_level = level(treeA, last_node);
    /* Compute the possible minimal value. */
    getmatrixparams(lengthA, lengthB, treeA, treeB);

trace(("mid analogical_clustering() last_level = %d\n", last_level))

    /* Call the analogical clustering function. */
    refine_down(1, &nodesA, &nodesB, 0, 0);

    if (VERBOSE)
        fprintf(stderr, "\n");

    /* Freeing the lines. */
    /*
		if ( LINEOUT )
		{
            freelinetable(linetableB) ;
            if ( ! symmetry )
                    freelinetable(linetableA) ;
		} ;
     */
trace(("out analogical_clustering(%d, %d, %s, %s)\n", lengthA, lengthB, li2s(lengthA, treeA), li2s(lengthB, treeB)))
}

/*
 * Reading the data from the temporary file.
 */

FEATURES *read_features(char *fileA)
{
	FEATURES *result = (FEATURES *) calloc(1, sizeof(FEATURES)) ;
	FILE *fA = NULL ;
    char temp_char = '\0' ;
	int i = 0 ;

trace(("in  read_features(%s)\n", fileA))

	/* Open the temporray file. */
    fA = fopen(fileA, "r");

    fscanf(fA, "%d", &(result->length));
	
    result->thetree = (int *) calloc(result->length+1, sizeof(int)) ;
    for (i = 0; i < result->length; ++i)
	{
        fscanf(fA, "%d", &(result->thetree[i]));
    } ;
	
	if ( LINEOUT )
	{
		result->thelines = (char *) calloc(1000000, sizeof(char));
		i = 0;
		getc(fA);
		while (EOF != fscanf(fA, "%c", &temp_char))
		{
			*(result->thelines + i) = temp_char;
			i++;
		}
		*(result->thelines + i) = '\0';
	} ;
	
	/* Close the temporary file. */
    fclose(fA);
	
trace(("out read_features(%s) = (%d, %s)\n", fileA, result->length, li2s(result->length, result->thetree)))
	
	return result ;
}

/*
 * Interface with the Python program.
 * 	First, read the data contained in the input temporary file(s).
 * 	Then, call the clustering program.
 * 	The clustering program will write the clusters
 *		with the objects encoded as integers
 * 		onto the temporary output file.
 */

extern void nlgclu_in_C(char *fileA, char *fileB, char *clufile, int minsize, int maxsize, int verbose, int lineout)
{
	FEATURES *featuresA = NULL,
			 *featuresB = NULL ;
    clock_t t1, t2 ;

trace(("in  nlgclu_in_C(%s, %s, %s, min=%d, max=%d, %s, %s)\n", fileA, fileB, clufile, minsize, maxsize, verbose?"VERBOSE":"NOT verbose", lineout?"LINEOUT":"NOT lineout"))

	CLUSTER_MINIMAL_LENGTH = minsize;
	CLUSTER_MAXIMAL_LENGTH = maxsize;
	if ( -1 == CLUSTER_MAXIMAL_LENGTH )
		CLUSTER_MAXIMAL_LENGTH = INT_MAX ;

	VERBOSE = verbose;
	LINEOUT = lineout;
	
	t1 = clock() ;
	featuresA = read_features(fileA);
	if ( 0 == strcmp(fileA,fileB) )
	{
		featuresB = featuresA ;
		symmetry = TRUE ;
	}
	else
		featuresB = read_features(fileB);
	cluout = fopen(clufile, "w") ;

	if (VERBOSE )
    	fprintf(stderr, "## [C old version] Reading time: %.2fs\n",
			(double) (clock() - t1) / CLOCKS_PER_SEC) ;

trace(("mid nlgclu_in_C(%s, %s, %s, min=%d, max=%d, %s, %s)\n", fileA, fileB, clufile, minsize, maxsize, verbose?"VERBOSE":"NOT verbose", lineout?"LINEOUT":"NOT lineout"))

	t2 = clock() ;
	analogical_clustering(VERBOSE,
		featuresA->length, featuresB->length,
		featuresA->thetree, featuresB->thetree,
		featuresA->thelines, featuresB->thelines) ;

	if (VERBOSE)
		fprintf(stderr, "## Max number of pairs: %d\n",
			MAXPAIRNBR) ;

	if (VERBOSE)
		fprintf(stderr, "## _VALNBR: %d\n",
			_VALNBR) ;

	if (VERBOSE)
		fprintf(stderr, "## Number of early outputs of clusters: %d\n",
			rest_n) ;

	if (VERBOSE )
    	fprintf(stderr, "## [C] Clustering time: %.2fs\n",
			(double) (clock() - t2) / CLOCKS_PER_SEC) ;
	fflush(stderr) ;

trace(("out nlgclu_in_C(%s, %s, %s, min=%d, max=%d, %s, %s)\n", fileA, fileB, clufile, minsize, maxsize, verbose?"VERBOSE":"NOT verbose", lineout?"LINEOUT":"NOT lineout"))
}


