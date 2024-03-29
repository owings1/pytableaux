.. _K:

******************************************
L{K} - Kripke Normal Modal Logic
******************************************

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

.. include:: include/k/models_blurb.rst

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

.. _k-modality:

Modal Operators
---------------

.. rubric:: Possibility

.. include:: include/k/m.possibility.rst

.. rubric:: Necessity

.. include:: include/k/m.necessity.rst

.. _k-consequence:

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
  :docflags:
  :title: -

.. _k-rules:

Rules
--------

.. include:: include/cpl/rules_blurb.rst

Additional rules are given for the quantifiers.

.. include:: include/k/rule_groups.rst

Notes
=====

References
==========

.. rubric:: Futher Reading

- `Stanford Encyclopedia on Modal Logic`_

.. _Stanford Encyclopedia on Modal Logic: http://plato.stanford.edu/entries/logic-modal/


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members:
