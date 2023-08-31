.. _KFDE:

.. module:: pytableaux.logics.kfde

***************************************
L{} - FDE with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _kfde-semantics:
.. _kfde-model:
.. _kfde-frame:

Semantics
=========

A L{} `frame` comprises the interpretation of sentences and predicates at a world.
A L{} `model` comprises a non-empty collection of L{} frames, a world access
relation :m:`R`, and a set of constants (the domain).

The semantics for predication, quantification, and truth-functional operators are the
same as {@FDE}.

.. _kfde-modality:

Modal Operators
---------------

.. rubric:: Possibility

.. include:: include/kfde/m.possibility.rst

.. rubric:: Necessity

.. include:: include/kfde/m.necessity.rst

.. _kfde-consequence:

Consequence
-----------

**Logical Consequence** is defined similary as {@FDE}, except with
reference to a world:

.. include:: include/kfde/m.consequence.rst

.. _kfde-system:

Tableaux
========

Nodes
-----

.. include:: include/kfde/nodes_blurb.rst

Trunk
-----

.. include:: include/kfde/trunk_blurb.rst

.. tableau::
  :build-trunk:
  :prolog:

Closure
-------

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _kfde-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@FDE} counterparts, with
the addition of carrying over the world marker from the target node(s).

.. include:: include/kfde/rule_groups.rst

Notes
=====

* Like L{FDE}, there are no logical truths.

* The standard modal operator interdefinabilities hold: :s:`NA` |<=>| :s:`~P~A`
  and :s:`~NA` |<=>| :s:`P~A`.

* Modal forms of modus ponens fail, e.g. :s:`N(A $ B)`, :s:`PA` |!=>| :s:`PB`.

References
==========

* Priest, Graham. `An Introduction to Non-Classical Logic`_: From If to Is.
  Cambridge University Press, 2008.

.. _An Introduction to Non-Classical Logic: https://www.google.com/books/edition/_/rMXVbmAw3YwC?hl=en


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: