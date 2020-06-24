Random Value Generator
=====================

This project is mainly created because I need some random input data for my 
dbms projects, and I didn't find manual insertion fun. Even if this is the 
first time I'm commiting this, this version is a complete rewrite of the 
previous one, which was pretty limited in both configurability and 
functionality.

To generate random data, you first create a file which describes the format 
of the data. See 'bootstrap.format'. Each statement of the format file is 
either a print statement or an assignment.

## Print
```
print(<number_of_times>, <rule>)
```
A print statement is the only statement which actually triggers the execution. 
Nothing is actually executed before a 'print', they are merely parsed and 
mapped. A print statement evaluates the specified rule for the given number 
of times, and returns back the whole result as an array to the driver.

## Assignment Statement
```
rule = <expression>
```
Assignment statements basically maps a rule to a given expression. When a rule 
is encountered in either a print statement or in another expression, it's 
corresponding definiton is looked for in the rule map. If found, the engine 
re-evalutes the rule, and returns the result. Otherwise, an error is triggered.

## Expression
```
STRING | INTEGER | function_name(expression)
```
An expression is the atomic unit of execution. All RHS's of assignment 
statements have to be a valid expression. Available functions to use in RanData 
are listed below.

## Available functions

1. append(arg (, arg)*) : joins all the arguments in a string
2. one_of(arg, (, arg)*) : returns one random value from the arguments
3. one_of_unique(arg, (, arg)*) : returns one random, but unique, value 
                        at subsequent calls from the arguments
4. number_between(x, y) : returns a number between (x, y)
5. number_upto(x) : returns a number between [0, x]
6. lower(x) : converts the argument into lowercase

## Available default rules

1. first_name
2. last_name
3. full_name
4. address
5. area
6. gender
7. domain   // email domains
8. email
9. year     // between 1990-2020
10. day     // between 1-28
11. month   // between 1-12
12. date    // in YYYY-MM-DD
