.. _NH:

.. module:: pytableaux.logics.nh

*********************************************
L{} - Paraconsistent Hybrid Logic
*********************************************

L{} is a three-valued predicate logic with values V{T}, V{F}, and V{B}.
It is the `glutty` dual of {@MH}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------


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

The set of *designated values* for L{} is: { V{T}, V{B} }

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

L{} does not have a separate `Assertion` operator, but we include a table
and rules for it, for cross-compatibility.

.. truth-tables::
  :operators: Assertion

.. _nh-predication:

Predication
-----------

.. include:: include/lp/predication.rst

.. _nh-quantification:

Quantification
--------------

Although quantification was not defined in Caret's original paper, here we apply
the idea of generalized disjunction & conjunction.

.. rubric:: Existential

Since disjunction behaves just like {@LP}, existential quantification is the same.

.. include:: include/lp/m.existential.rst

.. rubric:: Universal

Let :m:`M` be the set of values of the sentences that result from replacing each
constant for the quantified variable of a universal sentence :m:`A`. The value
of :m:`A` is:

* V{F} if V{F} is in :m:`M`.
* V{B} if both V{B} and V{T} are in :m:`M`.
* V{T} otherwise.

.. _nh-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T}, V{B} }:

.. include:: include/fde/m.consequence.rst

.. _nh-system:

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

.. _nh-rules:

Rules
--------

.. include:: include/fde/rules_blurb.rst

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

- `Colin Caret`_. (2017). `Hybridized Paracomplete and Paraconsistent Logics`_.
  *The Australasian  Journal of Logic*, 14.


.. _Colin Caret: https://sites.google.com/view/colincaret
.. _Hybridized Paracomplete and Paraconsistent Logics: https://ojs.victoria.ac.nz/ajl/article/view/4035/3588

.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: