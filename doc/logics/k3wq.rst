.. _K3WQ:

*******************************************************************
L{K3WQ} - Weak Kleene Logic with alternate quantification
*******************************************************************

This is a version of {@K3W} with a different treatment of the quantifiers
in terms of generalized conjunction/disjunction. This yields some interesting
rules for the quantifiers, given the behavior of those operators in {@K3W}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.k3wq

.. _k3wq-semantics:
.. _k3wq-model:

Semantics
=========

.. _k3wq-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/k3w/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{K3WQ} is the singleton: { V{T} }

.. _k3wq-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

The `Material Conditional` :s:`>` is definable in terms of disjunction:

.. sentence::

  A > B := ~A V B

Likewise the `Material Biconditional` :s:`<` is defined in terms of :s:`>`
and :s:`&`:

.. sentence::

  A < B := (A > B) & (B > A)

.. truth-tables::
  :operators: MaterialConditional, MaterialBiconditional

.. rubric:: Compatibility Tables

L{K3WQ} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native_operators

.. _k3wq-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

.. _k3wq-quantification:

Quantification
--------------

.. rubric:: Existential

An existential sentence is interpreted in terms of `generalized disjunction`.
If we order the values least to greatest as V{N}, V{T}, V{F}, then we
can define the value of an existential in terms of the `maximum` value of
the set of values for the substitution of each constant in the model for
the variable.

.. rubric:: Universal

A universal sentence is interpreted in terms of `generalized conjunction`.
If we order the values least to greatest as V{N}, V{F}, V{T}, then we
can define the value of a universal in terms of the `minimum` value of
the set of values for the substitution of each constant in the model for
the variable.

.. _k3wq-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T} }:

.. include:: include/fde/m.consequence.rst

.. _k3wq-system:

Tableaux
========

L{K3WQ} tableaux are built similary to L{FDE}.

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

.. tableau-rules::
  :group: closure
  :titles:
  :legend:
  :docs:

.. _k3wq-rules:

Rules
--------

.. cssclass:: hidden

  .. class:: TabRules()

.. include:: include/fde/rules_blurb.rst

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: non_native_operators

.. tableau-rules::
  :docflags:
  :group: quantifier

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: non_native_operators


Notes
=====

- Standard interdefinability of the quantifiers is preserved.
