.. _RM3:

***************************
L{RM3} - R-mingle 3
***************************

L{RM3} is a three-valued logic with values V{T}, V{F}, and V{B}.
It is similar to {@LP}, with a different conditional operator. It can be
considered as the `glutty` dual of {@L3}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.rm3

.. _rm3-semantics:
.. _rm3-model:

Semantics
=========

.. _rm3-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/lp/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{RM3} is: { V{T}, V{B} }

.. _rm3-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction, Conditional

.. rubric:: Defined Operators

The `Biconditional` :s:`%` is defined in the usual way:

.. sentence::

  A % B := (A $ B) & (B $ A)

The `Material Conditional` :s:`>` is definable in terms of disjunction:

.. sentence::

  A > B := ~A V B

Likewise the `Material Biconditional` :s:`<` is defined in terms of :s:`>`
and :s:`&`:

.. sentence::

  A < B := (A > B) & (B > A)

.. truth-tables::
  :operators: Biconditional, MaterialConditional, MaterialBiconditional

.. rubric:: Compatibility Tables

L{RM3} does not have a separate `Assertion` operator, but we include a table
and rules for it, for cross-compatibility.

.. truth-tables::
  :operators: Assertion

.. _rm3-predication:

Predication
-----------

.. include:: include/lp/predication.rst

.. _rm3-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/fde/m.existential.rst

.. rubric:: Universal

.. include:: include/fde/m.universal.rst

.. _rm3-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T}, V{B} }:

  .. include:: include/fde/m.consequence.rst

.. _rm3-system:

Tableaux
========

L{RM3} tableaux are built similary to L{FDE}.

Nodes
-----

.. include:: include/fde/nodes_blurb.rst

Trunk
-----

.. include:: include/fde/trunk_blurb.rst

.. tableau::
  :build-trunk:
  :prolog:

Closure
-------

.. tableau::
  :rule: DesignationClosure
  :legend:
  :doc:

.. tableau::
  :rule: GapClosure
  :legend:
  :doc:

.. _rm3-rules:

Rules
--------

.. include:: include/fde/rules_blurb.rst

There are no rules that apply to quantified sentences.

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: Assertion

.. tableau-rules::
  :docflags:
  :group: quantifier

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: Assertion


Notes
=====

* With the Conditional operator :s:`$`, Modus Ponens (:s:`A`, :s:`A $ B` !{conseq} :s:`B`) is
  valid in L{RM3}, which fails in {@LP}.

* The argument :s:`B`, therefore :s:`A $ B` is invalid in L{RM3}, which is valid in L{LP}.

References
==========

* Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and Many-valued Logic.
  United Kingdom, Oxford University Press, 2003.

.. rubric:: Further Reading

* Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
  Vol. 38, No. 2. 1979.


.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en

