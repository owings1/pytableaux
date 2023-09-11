.. _MH:

******************************
MH - Paracomplete Hybrid Logic
******************************

L{MH} is a three-valued predicate logic with values V{T}, V{F}, and V{N}.
It is the `gappy` dual of {@NH}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.mh

.. _mh-semantics:
.. _mh-model:

Semantics
=========

.. _mh-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/k3/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{MH} is the singleton: { V{T} }

.. _mh-truth-tables:

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

L{MH} does not have a separate `Assertion` operator, but we include a table
and rules for it, for cross-compatibility.

.. truth-tables::
  :operators: Assertion

.. _mh-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

.. _mh-quantification:

Quantification
--------------

Although quantification was not defined in Caret's original paper, here we apply
the idea of generalized disjunction & conjunction.

.. rubric:: Existential

Let :m:`M` be the set of values of the sentences that result from replacing each
constant for the quantified variable of an existential sentence :m:`A`. The value
of :m:`A` is:

* V{T} if V{T} is in :m:`M`.
* V{N} if both V{N} and V{F} are in :m:`M`.
* V{F} otherwise.

.. rubric:: Universal

Since conjunction behaves just like {@K3}, universal quantification is the same.

.. include:: include/k3/m.universal.rst

.. _mh-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T} }:

.. include:: include/fde/m.consequence.rst

.. _mh-system:

Tableaux
========

L{MH} tableaux are built similary to L{FDE}.

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

.. _mh-rules:

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