.. _krm3:

.. module:: pytableaux.logics.krm3

***************************************
L{} - L{RM3} with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _krm3-semantics:
.. _krm3-model:
.. _krm3-frame:

Semantics
=========

.. include:: include/k/models_blurb.rst

The semantics for predication, quantification, and truth-functional operators are the
same as {@RM3}.

.. _krm3-modality:

Modal Operators
---------------

.. rubric:: Possibility

.. include:: include/kfde/m.possibility.rst

.. rubric:: Necessity

.. include:: include/kfde/m.necessity.rst

.. _krm3-consequence:

Consequence
-----------

**Logical Consequence** is defined just as in {@KFDE}.

.. include:: include/kfde/m.consequence.rst

.. _krm3-system:

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

The closure rules are the same as {@RM3}.

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _krm3-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@RM3} counterparts, with
the addition of carrying over the world marker from the target node(s).

.. include:: include/kfde/rule_groups.rst

Notes
=====



References
==========

* Priest, Graham. `An Introduction to Non-Classical Logic`_: From If to Is.
  Cambridge University Press, 2008.

.. _An Introduction to Non-Classical Logic: https://www.google.com/books/edition/_/rMXVbmAw3YwC?hl=en


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: