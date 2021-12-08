/* Copyright (c) 1999, Yves Lepage */
/*
 * Analogy functions
 */

#include <stddef.h>
#include <stdio.h>

/*
 * solvenlg function:
 * input:
 *    three objects of type char *
 * output:
 *    an array of solutions of the analogy
 *    each solution is of type char *
 */

char *solvenlg(char *, char *, char *) ;

/*
 * verifnlg function:
 * input:
 *    four objects of type char *
 * output:
 *    1 if analogy is verified, 0 else
 */

int   verifnlg(char *, char *, char *, char *) ;
