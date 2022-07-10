.. _CFOL:

********************************************
L{CFOL} - Classical First-Order Logic
********************************************

L{CFOL} adds quantification to {@CPL}.

.. contents::
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.cfol

.. _cfol-semantics:
.. _cfol-model:

Semantics
=========

.. _cfol-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/cpl/value-table.rst

.. _cfol-truth-tables:

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

L{CFOL} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :operators: Assertion, Conditional, Biconditional

.. _cfol-predication:

Predication
-----------

The value of predicated sentences are handled in terms of a predicate's *extension*.

.. include:: include/cpl/predication.rst

.. _cfol-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/cfol/m.existential.rst

.. rubric:: Universal

.. include:: include/cfol/m.universal.rst

.. _cfol-consequence:

Consequence
-----------

**Logical Consequence** is defined in the standard way:

  .. include:: include/cpl/m.consequence.rst

.. _cfol-system:

Tableaux
========

Nodes
-----

.. include:: include/cpl/nodes_blurb.rst

Trunk
-----

.. include:: include/cpl/trunk_blurb.rst

.. tableau::
  :build-trunk:
  :prolog:

Closure
-------

.. tableau::
  :rule: ContradictionClosure
  :legend:
  :doc:

.. tableau::
  :rule: SelfIdentityClosure
  :legend:
  :doc:

.. _cfol-rules:

Rules
--------

.. include:: include/cpl/rules_blurb.rst

Additional rules are given for the quantifiers.

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: Assertion, Conditional, Biconditional

.. tableau-rules::
  :docflags:
  :group: quantifier

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: Assertion, Conditional, Biconditional
