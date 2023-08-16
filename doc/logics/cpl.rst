.. _CPL:

*******************************
CPL - Classical Predicate Logic
*******************************

L{CPL} is the standard bivalent logic with values V{T} and V{F}.

.. contents::
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.cpl

.. _cpl-semantics:
.. _cpl-model:

Semantics
=========

.. _cpl-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/cpl/value-table.rst

.. _cpl-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{CPL} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

.. _cpl-predication:

Predication
-----------

The value of predicated sentences are handled in terms of a predicate's *extension*.

.. include:: include/cpl/predication.rst

.. Note:: CPL does not give a treatment of the quantifiers. Quantified sentences
    are treated as opaque (uninterpreted). See {@CFOL} for quantification.

.. _cpl-consequence:

Consequence
-----------

**Logical Consequence** is defined as follows:

  .. include:: include/cpl/m.consequence.rst

.. _cpl-system:

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
  :docs:

.. _cpl-rules:

Rules
--------

.. include:: include/cpl/rules_blurb.rst

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

References
==========

.. cssclass:: hidden

.. autoclass:: Rules()
    :members: