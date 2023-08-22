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

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{CFOL} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

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

.. tableau-rules::
  :group: closure
  :titles:
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
  :exclude: non_native

.. tableau-rules::
  :docflags:
  :group: quantifier

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: non_native

Notes
=====

References
==========

.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members:
