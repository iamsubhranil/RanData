#ifndef KEYWORD
#define KEYWORD(name, length, argcount)
// argcount is -1 for varargs
#endif
// clang-format off
KEYWORD(append, 6, -1)
KEYWORD(lower, 5, 1)
KEYWORD(number_between, 14, 2)
KEYWORD(number_upto, 11, 1)
KEYWORD(one_of, 6, -1)
KEYWORD(one_of_unique, 13, -1)
KEYWORD(print, 5, 2)
// clang-format on
#undef KEYWORD
