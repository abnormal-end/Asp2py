
## Introduction

The goal of this project is to convert ASP VbScript code to Python 3 code (source-to-source conversion).

This project is a work in progress. It'll contain 3 parts:

* Lexer: convert ASP VbScript to tokens
* Parser: convert tokens to an internal representation of the code (code structure)
* Transpiler: output the code structure to Python 3

## Scope

The target:

* most ASP VbScript features should be handled
* the outputted Python 3 source should produce the same result as the original 

The target is not about:

* transpilation speed
* refactoring or beatifying the code

## Status

* Lexer: first iteration done
* Parser:
    * basic reading and validation of:
        * if / then / elseif / else / end if
        * for each / next
        * do while / loop

Next steps:
* function and sub
* internal representation of code

## Examples

The following ASP VbScript code:

    <%
        if true then
            test = "true"
        else
            test = "false"
        else
            test = "false"
        end if
    %>

Produce the following errors:

    Line 6, column 1, token 'else': not valid for close because parent 'else' doesn't allow it


For more examples, please check /unittests folder.
