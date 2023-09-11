.. _LP:

*****************************
L{LP} - Logic of Paradox
*****************************

L{LP} is a 3-valued logic with value V{T}, V{F}, and V{B}. It can be understood as
{@FDE} without the V{N} value.

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.lp

.. _lp-semantics:
.. _lp-model:

Semantics
=========

.. _lp-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/lp/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{LP} is: { V{T}, V{B} }

.. _lp-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{LP} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

.. _lp-predication:

Predication
-----------

Like L{FDE}, L{LP} predication defines a predicate's *extenstion* and
*anti-extension*. The value of a predicated sentence is determined as
follows:

.. include:: include/lp/predication.rst

Note, unlike {@FDE}, there is an *exhaustion constraint* on a predicate's
extension/anti-extension. This means that !{ntuple} must be in either the
extension and the anti-extension of `P`.

Like L{FDE}, there is no *exclusion restraint*: there are permissible L{LP}
models where some tuple !{ntuple} is in *both* the extension and anti-extension
of a predicate.

.. _lp-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/lp/m.existential.rst

.. rubric:: Universal

.. include:: include/lp/m.universal.rst

.. _lp-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T}, V{B} }:

.. include:: include/fde/m.consequence.rst

.. _lp-system:

Tableaux
========

L{LP} tableaux are built similary to L{FDE}.

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

L{LP} includes an additional `gap` closure rule. This means a branch closes
when a sentence and its negation both appear as undesignated nodes on the branch.

.. tableau::
  :rule: GapClosure
  :legend:
  :doc:

L{LP} includes the L{FDE} closure rule.

.. tableau::
  :rule: DesignationClosure
  :legend:
  :doc:

.. _lp-rules:

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

Some notable features of L{LP} include:

* Everything valid in {@FDE} is valid in L{LP}.

* Like {@FDE}, the :term:`Law of Non-Contradiction` fails :s:`~(A & ~A)`.

* Unlike {@FDE}, L{LP} has some logical truths. For example, the :term:`Law of Excluded Middle`
  (:s:`(A V ~A)`), and :term:`Conditional Identity` (:s:`(A $ A)`).

* Many classical validities fail, such as :term:`Modus Ponens`, :term:`Modus Tollens`,
  and :term:`Disjunctive Syllogism`.

* :term:`DeMorgan laws` are valid.

References
==========

* Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and
  Many-valued Logic. United Kingdom, Oxford University Press, 2003.

For futher reading see:

* `Stanford Encyclopedia entry on paraconsistent logic
  <http://plato.stanford.edu/entries/logic-paraconsistent/>`_

.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en

.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: