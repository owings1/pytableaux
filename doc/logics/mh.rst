.. _MH:

******************************
MH - Paracomplete Hybrid Logic
******************************

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

L{MH} does not have a separate `Assertion` operator, but we include a table
and rules for it, for cross-compatibility.

.. truth-tables::
  :operators: Assertion

.. _mh-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

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

.. tableau::
  :rule: DesignationClosure
  :legend:
  :doc:

.. tableau::
  :rule: GlutClosure
  :legend:
  :doc:

.. _mh-rules:

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
