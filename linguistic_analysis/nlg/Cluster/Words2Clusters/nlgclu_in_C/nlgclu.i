/* File: nlgclu.i */
%module nlgclu

%{
#include "nlgclu.h"
extern void nlgclu_in_C(char *fileA, char *fileB, char *clufile, int minsize, int maxsize, int verbose, int lineout, int focus) ;
%}
extern void nlgclu_in_C(char *fileA, char *fileB, char *clufile, int minsize, int maxsize, int verbose, int lineout, int focus) ;
