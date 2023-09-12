.. _kk3wq:

.. module:: pytableaux.logics.kk3wq

***************************************
L{} - L{K3WQ} with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _kk3wq-semantics:
.. _kk3wq-model:
.. _kk3wq-frame:

Semantics
=========

.. include:: include/k/models_blurb.rst

The semantics for predication, quantification, and truth-functional operators are the
same as {@K3WQ}.

.. _kk3wq-modality:

Modal Operators
---------------

.. rubric:: Possibility

... todo

.. rubric:: Necessity

... todo

.. _kk3wq-consequence:

Consequence
-----------

**Logical Consequence** is defined just as in {@KFDE}.

.. include:: include/kfde/m.consequence.rst

.. _kk3wq-system:

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

The closure rules are the same as {@K3WQ}.

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _kk3wq-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@K3WQ} counterparts, with
the addition of carrying over the world marker from the target node(s).

.. include:: include/kfde/rule_groups.rst

Notes
=====



References
==========



.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: