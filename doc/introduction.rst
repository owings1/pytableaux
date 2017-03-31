************
Introduction
************

pytableaux is a multi-logic tableau proof generator. It supports full first-order 
sentences (predication and quantification), with standard operators (negation, 
conjunction, etc.), as well as modal operators (possibility, necessity). It is 
designed to compare logical validities across various 'nonclassical' logics, 
focusing on many-valued and modal logics.

Project History & Goals
=======================

I started this project when I was supposed to be writing my dissertation_ on 
non-classical logic. I wanted a proof generator for a new logic I was developing,
and writing that generator myself would allow me to procrastinate heavily with
somewhat-reduced guilt. I eventually finished the paper, but have continued with
this project in various forms.

The goals of this project are:

1. A tool for researchers in non-classical logics to quickly check inferences.

2. Demonstrate the simplicity and parsimony of describing and conceptualizing 
   various logics with only a few basic concepts.
   
The module and class structure of the code attempt to mirror the presentation of
logical given in Beall's and van Fraassen's `Possibilities and Paradox`_, as
well as Beall's graduate lectures at the University of Connecticut.

Language
========

In order to compare inferences across logics, there is a **shared vocabulary 
across logics** of atomic symbols, operators, quantifiers, predicates, variables 
and constants. This allows any sentence to be processed by the proof system of 
any logic, even if that proof system does not have any particular rules for 
handling a sentence of a particular form. 

For example, Classical logic has one conditional operator, the Material 
Conditional. Lukasiewicz logic also has a distinct Conditional operator,
which attempts to work around the failure of some classical inferences for the
Material Conditional. Another example is Free Logic, which has a special 
Existence predicate meant to allow for the possibility that nothing exists.

Since operators, quantifiers and special predicates are defined 
globally, every logic will 'recognize' a sentence containing any of these 
tokens, and will successfully construct a tableau with them. However, Classical 
logic has no rules related to either an Existence predicate or a Conditional 
operator (separate from the Material Conditional), and so these sentences would 
not get 'broken down' in the proof process. 

This can be mitigated somewhat by adding rules, or broadening the application 
of existing rules. This was done in the implementation of Classical logic, for 
example, by applying Material Conditional rules to Conditional operators as 
well (likewise for the bi-conditional counterparts). This gives the appearance 
of Classical logic 'translating' the Conditional operator into the Material 
Conditional. I have taken this approach in clear cases where it makes sense, 
but I have tried not to take too many liberties with canonical presentations of 
the logics (e.g. there is no special rule for the Existence predicate in 
Classical logic).

The selection of operators and special predicates is thus maintained carefully 
with two (sometimes competing) goals: (1) flexible support for many logics, some 
of which contain special operators or predicates, and (2) consolidation of 
similarities among logics, in order to maximize translatability.

Atomics
--------

Atomic sentences are represented by an atomic symbol and a subscript integer.

Predicates
----------

Predicates are identified by a unique label (name), and have a fixed number of 
parameters (arity).

There are two system-defined or 'special' predicates:

+------------------+----------------------------------+-------+
| Predicate        | Common Translation               | Arity |
+==================+==================================+=======+
| Existence        | ... *exists*                     |   1   |
+------------------+----------------------------------+-------+
| Identity         | ... *is identical to* ...        |   2   |
+------------------+----------------------------------+-------+
    
Note that *existence* is typically expressed using the Existential
Quantifier. The Existence Predicate is used only in Free Logics.

Any number of user-defined predicates of any arity >= 1 can be added.

Constants & Variables
---------------------

Constants and variables are the parameters for predicate sentences, and are 
represented by a symbol and a subscript integer. A quantifier *binds* a 
variable to an inner sentence. At parsing time, every variable in a predicate 
sentence must be bound by a quantifier (no free variables allowed), and every 
variable that is bound by a quantifier must appear as a parameter somewhere in 
the inner sentence (no superfluous variables allowed).

Quantifiers
-----------


+-----------------+------------------------------------------------+
| Quantifier      | Common Translation                             |
+=================+================================================+
| Existential     | *there exists an x, such that* ...             |
+-----------------+------------------------------------------------+
| Universal       | *for all x*, ...                               |
+-----------------+------------------------------------------------+


Operators
---------

Sentential operators are identified internally by a unique name and have a 
fixed number of sentences (arity):

+-------------------------+----------------------------------+-------+
| Operator                | Common Translation               | Arity |
+=========================+==================================+=======+
| Assertion               | it is true that ...              |   1   |
+-------------------------+----------------------------------+-------+
| Negation                | *not* ...                        |   1   |
+-------------------------+----------------------------------+-------+
| Conjunction             | ... *and* ...                    |   2   |
+-------------------------+----------------------------------+-------+
| Disjunction             | ... *or* ...                     |   2   |
+-------------------------+----------------------------------+-------+
| Material Conditional    | *if* ... *then* ...              |   2   |
+-------------------------+----------------------------------+-------+
| Material Biconditional  | ... *if and only if* ...         |   2   |
+-------------------------+----------------------------------+-------+
| Conditional             | *if* ... *then* ...              |   2   |
+-------------------------+----------------------------------+-------+
| Biconditional           | ... *if and only if* ...         |   2   |
+-------------------------+----------------------------------+-------+
| Possibility             | *possibly,* ...                  |   1   |
+-------------------------+----------------------------------+-------+
| Necessity               | *necessarily,* ...               |   1   |
+-------------------------+----------------------------------+-------+

Form many logics, the *Conditional* operator is the same as the *Material Conditional*
operator (and likewise, the *Biconditional* is equivalent to the *Material Biconditional*).
This comes from the fact that the *Material Conditional* is defined in terms of a
disjunction, i.e. P{(A > B)} is equivalent to P{(~A V B)}. However, some logics, like L3,
define a separate *Conditional* operator, intended to better preserve intuitive
classical inferences such as *Identity* (P{(A > A)}). For this reason, the *Conditional*
is treated as a separate operator. Thus, in logics that do not define a distinct *Conditional*,
it will be equivalent to the *Material Conditional*.

Similar reasoning motivates the *Assertion* operator. Most logics do not define an *Assertion*
operator, but given that some do (e.g. Bochvar), we introduce it to the vocabulary, treating
it as a transparent operator (P{\*A} == P{A}) in logics that do not traditionally define it.

Installation
============

The program contains the following interfaces:

    - An API to use in Python scripts.
    
    - A web interface with a built-in server, which runs on any machine with Python installed.
    
    - [in progress] A CLI for evaluating arguments from the command line.
    
To install natively:

    1. Download the source, for example::

        cd ~/git
        git clone https://bitbucket.org/owings1/pytableaux
    
    2. Install dependencies, for example::

        pip install jinja2 cherrypy Sphinx

    3. Launch the web interface, for example::

        cd ~/git/pytableaux
        python src/web.py

    4. Then access http://localhost:8080

To install using docker:

    1. Run the following commands::

        cd ~/git/pytableaux

        # build the image
        docker build -t owings1/pytableaux:latest docker

        # set container parameters, choose different host port, container name if desired.
        REPO_HOME=`pwd`
        HOST_PORT=8080
        CONT_NAME=pytableaux

        # create the container
        docker create --name $CONT_NAME -v $REPO_HOME:/mnt/repo -p $HOST_PORT:8080 -e PY_HOST=0.0.0.0 owings1/pytableaux

        # start the container
        docker start pytableaux

    2. Access the web interface on the HOST_PORT (e.g. 8080) of your docker IP.

Parsing
=======

There are two parsers available: Polish notation, and Standard notation.

Proof output
============

Currently the output formats are plain text (ASCII), and HTML.

Contributing
============

To contribute in any way (documentation, code, testing, suggestions, etc.), contact
Doug Owings at doug at dougowings dot net. You can also submit issues and merge requests
on `Bitbucket`_.


.. _dissertation: https://bytebucket.org/owings1/dissertation/raw/master/output/dissertation.pdf

.. _Possibilities and Paradox: https://global.oup.com/academic/product/possibilities-and-paradox-9780199259878?q=Possibilities%20and%20Paradox

.. _Bitbucket: https://bitbucket.org/owings1/pytableaux