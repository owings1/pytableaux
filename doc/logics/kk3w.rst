.. _kk3w:

.. module:: pytableaux.logics.kk3w

***************************************
L{} - L{K3W} with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _kk3w-semantics:
.. _kk3w-model:
.. _kk3w-frame:

Semantics
=========

.. include:: include/k/models_blurb.rst

The semantics for predication, quantification, and truth-functional operators are the
same as {@K3W}.

.. _kk3w-modality:

Modal Operators
---------------

.. rubric:: Possibility

.. include:: include/kfde/m.possibility.rst

.. rubric:: Necessity

.. include:: include/kfde/m.necessity.rst

.. _kk3w-consequence:

Consequence
-----------

**Logical Consequence** is defined just as in {@KFDE}.

.. include:: include/kfde/m.consequence.rst

.. _kk3w-system:

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

The closure rules are the same as {@K3W}.

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _kk3w-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@K3W} counterparts, with
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