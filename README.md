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
Two predefined rules are there, namely 'number' and 'value'. They don't 
directly evalute to anything, but methods can be called upon them.

## Expression
```
STRING | INTEGER | rule.method_name(expression)
```
An expression is the atomic unit of execution. For a string or an integer, 
their corresponding value is wrapped in a Value class and that is returned. 
For a method call, first, the object is looked up to be a rule, and is 
evaluted correspondingly. If the object is 'number' or 'value', then the 
method is directly called, if exists. Otherwise the rule is evaluted, and 
then the method is dispatched upon the returned object.

## Default methods

1. value.append(arg (, arg)*) : appends the arguments to the value
2. value.one_of(arg, (, arg)*) : returns one random value from the arguments
3. value.one_of_unique(arg, (, arg)*) : returns one random, but unique, value 
                        at subsequent calls from the arguments
4. number.between(x, y) : returns a number between (x, y)
5. number.upto(x) : returns a number between [0, x]