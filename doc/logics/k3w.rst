.. _K3W:

**********************************
L{K3W} - Weak Kleene Logic
**********************************

L{K3W} is a 3-valued logic with values V{T}, V{F}, and V{N}. The logic is
similar to {@K3}, but with slightly different behavior of the V{N} value.
This logic is also known as Bochvar Internal (L{B3}).

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.k3w

.. _k3w-semantics:
.. _k3w-model:

Semantics
=========

.. _k3w-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/k3w/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{K3W} is the singleton: { V{T} }

.. _k3w-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{K3W} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

.. _k3w-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

.. _k3w-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/fde/m.existential.rst

.. rubric:: Universal

.. include:: include/fde/m.universal.rst

.. Note:: For an alternate interpretation of the quantifiers in L{K3W}, see
    {@K3WQ}. There we apply the notion of *generalized*
    conjunction and disjunction to :s:`L` and :s:`X`.

.. _k3w-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T} }:

.. include:: include/fde/m.consequence.rst

.. _k3w-system:

Tableaux
========

L{K3W} tableaux are built similary to L{FDE}.

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

.. _k3w-rules:

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

- :term:`Addition` fails in L{K3W}. That is :s:`A` does not imply :s:`A V B`.

For further reading, see:

* Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.

References
==========


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: