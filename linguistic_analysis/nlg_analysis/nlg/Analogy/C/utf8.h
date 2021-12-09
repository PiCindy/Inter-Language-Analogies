/* Copyright (c) 2013, Yves Lepage */
/*
 * Analogy functions
 */

#include <stddef.h>
#include <stdio.h>

/*
 * check whether a string is an ascii string or not
 */

int isasciistring(unsigned char *s) ;

/*
 * mask unicode chars in a string by ascii char not in second ascii string
 */

char *maskunicodechar(unsigned char *s, unsigned char *aword) ;

/*
 * initialization of the dictionary of codes
 * the subsequent calls of the encoding and decoding functions
 * will all use the same dictionary until new initialization
 */

void initializecodedict(void) ;

/*
 * encoding function
 * input:
 *    a string in unicode of type unsigned char *
 * output:
 *    a string of bytes (= a string of integers < 256)
 *    encoded using a hidden dictionary (one utf8 char = one integer)
 */

char *encode(unsigned char *s) ;

/*
 * decoding function:
 * input:
 *    a string of bytes (= a string of integers < 256)
 * output:
 *    a string in unicode of type unsigned char *
 *    decoded using the hidden dictionary (one integer = one utf8 char)
 */

unsigned char *decode(char *s) ;
