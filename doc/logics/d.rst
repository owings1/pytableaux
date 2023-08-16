.. _D:

******************************
D - Deontic Normal Modal Logic
******************************

L{D}, also known as the Logic of Obligation, is an extension of {@K}, with
a *serial* access relation.

.. contents::
    :local:
    :depth: 2

------------------------

.. module:: pytableaux.logics.d

.. _d-semantics:


Semantics
=========

L{D} semantics behave just like {@K semantics}.

Seriality
---------

L{D} adds a *serial* restriction on the access relation for models.

.. include:: include/d/m.seriality.rst

.. _d-system:

Tableaux
========

L{D} tableaux are constructed just like {@K system} tableaux.

.. _d-rules:

Rules
-----

L{D} contains all the {@K rules} plus an additional Serial rule.

The Serial rule applies to a an open branch *b* when there is a world *w*
that appears on *b*, but there is no world *w'* such that *w* accesses *w'*.

.. tableau::
  :rule: Serial
  :doc:

Notes
=====

References
==========

.. rubric:: Further Reading

* `Stanford Encyclopedia on Deontic Logic`_

.. _Stanford Encyclopedia on Deontic Logic: http://plato.stanford.edu/entries/logic-deontic/

.. cssclass:: hidden

.. autoclass:: Rules()
    :members: