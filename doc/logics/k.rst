.. _K:

*****************************
K - Kripke Normal Modal Logic
*****************************

L{K} is the foundation of so-called normal modal logics. It adds
modal operators :s:`N` and :s:`P` to L{CFOL}.

.. contents::
    :local:
    :depth: 2

------------------------

.. module:: pytableaux.logics.k

.. _k-semantics:
.. _k-model:
.. _k-frame:

Semantics
=========

A L{K} `frame` comprises the interpretation of sentences and predicates at a world.
A L{K} `model` comprises a non-empty collection of K frames, a world access
relation :m:`R`, and a set of constants (the domain).

.. _k-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/cpl/value-table.rst

.. _k-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{K} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

.. _k-predication:

Predication
-----------

The value of predicated sentences are handled in terms of a predicate's *extension*.

.. include:: include/cpl/predication.rst

.. _k-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/cfol/m.existential.rst

.. rubric:: Universal

.. include:: include/cfol/m.universal.rst

.. _k-consequence:

Modal Operators
---------------

.. rubric:: Possibility

.. include:: include/k/m.possibility.rst

.. rubric:: Necessity

.. include:: include/k/m.necessity.rst

Consequence
-----------

**Logical Consequence** is defined similary as {@CPL}, except with
reference to a world:

.. include:: include/k/m.consequence.rst

.. _k-system:

Tableaux
========

Nodes
-----

.. include:: include/k/nodes_blurb.rst

Trunk
-----

.. include:: include/k/trunk_blurb.rst

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

.. _k-rules:

Rules
--------

.. include:: include/cpl/rules_blurb.rst

Additional rules are given for the quantifiers.

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: non_native modal

.. tableau-rules::
  :docflags:
  :title: Modal Operator Rules
  :group: operator
  :include: modal_
  :exclude: non_native

.. tableau-rules::
  :docflags:
  :group: predicate

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

.. rubric:: Futher Reading

- `Stanford Encyclopedia on Modal Logic`_

.. _Stanford Encyclopedia on Modal Logic: http://plato.stanford.edu/entries/logic-modal/


.. cssclass:: hidden

.. autoclass:: TabRules()
    :members:
