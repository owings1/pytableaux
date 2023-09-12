.. module:: pytableaux.logics.k3wq

.. _K3WQ:

*******************************************************************
L{} - Weak Kleene Logic with alternate quantification
*******************************************************************

This is a version of {@K3W} with a different treatment of the quantifiers
in terms of generalized conjunction/disjunction. This yields some interesting
rules for the quantifiers, given the behavior of those operators in {@K3W}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------


.. _k3wq-semantics:
.. _k3wq-model:

Semantics
=========

.. _k3wq-truth-values:

Truth Values
------------

.. include:: include/k3w/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{} is the singleton: { V{T} }

.. _k3wq-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{K3WQ} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

.. _k3wq-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

.. _k3wq-quantification:

Quantification
--------------

For L{} we give a treatment of quantification in terms of generalized disjunction &
conjunction, instead of the {@FDE} min/max fubctions.

.. rubric:: Existential

Let :m:`M` be the set of values of the sentences that result from replacing each
constant for the quantified variable of an existential sentence :m:`A`. The value
of :m:`A` is:

* V{N} if V{N} is in :m:`M`.
* V{T} if V{N} in not in :m:`M`, and V{T} is in :m:`M`.
* V{F} otherwise.

.. rubric:: Universal

For a universal sentence, the value is:

* V{N} if V{N} is in :m:`M`.
* V{F} if V{N} in not in :m:`M`, and V{F} is in :m:`M`.
* V{T} otherwise.

.. _k3wq-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T} }:

.. include:: include/fde/m.consequence.rst

.. _k3wq-system:

Tableaux
========

L{} tableaux are built similary to L{FDE}.

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
  :doc:

.. _k3wq-rules:

Rules
--------

.. include:: include/fde/rules_blurb.rst

.. tableau-rules::
  :docflags:
  :group: quantifier

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: non_native

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: non_native


Notes
=====

- Standard interdefinability of the quantifiers is preserved.

References
==========


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: