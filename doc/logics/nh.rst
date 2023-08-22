.. _NH:

********************************
NH - Paraconsistent Hybrid Logic
********************************

L{NH} is a three-valued predicate logic with values V{T}, V{F}, and V{B}.
It is the `glutty` dual of {@MH}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.nh

.. _nh-semantics:
.. _nh-model:

Semantics
=========

.. _nh-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/lp/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{NH} is: { V{T}, V{B} }

.. _nh-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction, Conditional

.. rubric:: Defined Operators

.. include:: include/bicond_define.rst

.. include:: include/bicond_table.rst

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{NH} does not have a separate `Assertion` operator, but we include a table
and rules for it, for cross-compatibility.

.. truth-tables::
  :operators: Assertion

.. _nh-predication:

Predication
-----------

.. include:: include/lp/predication.rst

.. _nh-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T}, V{B} }:

.. include:: include/fde/m.consequence.rst

.. _nh-system:

Tableaux
========

L{NH} tableaux are built similary to L{FDE}.

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

.. _nh-rules:

Rules
--------

.. include:: include/fde/rules_blurb.rst

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: Assertion

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: Assertion


Notes
=====


References
==========

- `Colin Caret`_. (2017). `Hybridized Paracomplete and Paraconsistent Logics`_.
  *The Australasian  Journal of Logic*, 14.


.. _Colin Caret: https://sites.google.com/view/colincaret
.. _Hybridized Paracomplete and Paraconsistent Logics: https://ojs.victoria.ac.nz/ajl/article/view/4035/3588

.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: