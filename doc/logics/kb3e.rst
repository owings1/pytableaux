.. _kb3e:

.. module:: pytableaux.logics.kb3e

***************************************
L{} - L{B3E} with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _kb3e-semantics:
.. _kb3e-model:
.. _kb3e-frame:

Semantics
=========

.. include:: include/k/models_blurb.rst

The semantics for predication, quantification, and truth-functional operators are the
same as {@B3E}.

.. _kb3e-modality:

Modal Operators
---------------

.. rubric:: Possibility

.. include:: include/kfde/m.possibility.rst

.. rubric:: Necessity

.. include:: include/kfde/m.necessity.rst

.. _kb3e-consequence:

Consequence
-----------

**Logical Consequence** is defined just as in {@KFDE}.

.. include:: include/kfde/m.consequence.rst

.. _kb3e-system:

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

The closure rules are the same as {@B3E}.

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _kb3e-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@B3E} counterparts, with
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