/* File : example.i */
%module nlg
%{
#include "nlg.h"
/* An analogy can be solved or verified */
extern char *solvenlg(char *, char *, char *) ;
extern int   verifnlg(char *, char *, char *, char *) ;
%}
extern char *solvenlg(char *, char *, char *) ;
extern int   verifnlg(char *, char *, char *, char *) ;

