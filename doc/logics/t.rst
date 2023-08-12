.. _T:

****************************************
L{T} - Reflexive Normal Modal Logic
****************************************

L{T} is an extension of {@K}, with a *reflexive* access relation.

.. contents::
    :local:
    :depth: 2

------------------------

.. module:: pytableaux.logics.t

.. _t-semantics:

Semantics
=========

L{T} semantics behave just like {@K semantics}.

Reflexivity
-----------

L{T} adds a *reflexive* restriction on the access relation for models.

.. include:: include/t/m.reflexivity.rst

.. _t-system:

Tableaux
========

L{T} tableaux are constructed just like {@K system} tableaux.

.. _t-rules:

Rules
-----

.. cssclass:: hidden

  .. class:: TabRules()

L{T} contains all the {@K rules} plus an additional Reflexive rule.

The Reflexive rule applies to an open branch *b* when there is a node *n*
on *b* with a world *w* but there is not a node where *w* accesses *w* (itself).

.. tableau::
  :rule: Reflexive
  :doc:

Notes
=====

References
==========
