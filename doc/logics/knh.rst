.. _knh:

.. module:: pytableaux.logics.knh

***************************************
L{} - L{NH} with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _knh-semantics:
.. _knh-model:
.. _knh-frame:

Semantics
=========

.. include:: include/k/models_blurb.rst

The semantics for predication, quantification, and truth-functional operators are the
same as {@NH}.

.. _knh-modality:

Modal Operators
---------------

Although modal operators were not defined in Caret's original paper, here we apply
the idea of generalized disjunction & conjunction.

.. rubric:: Possibility

Since disjunction behaves just like {@K3}, possibility is the same.

.. include:: include/kfde/m.possibility.rst

.. rubric:: Necessity

Let :m:`M` be the set of values of :s:`A` at all :m:`w'` such that :m:`wRw'`.
The value of :m:`NA` at :m:`w` is:

* V{F} if V{F} is in :m:`M`.
* V{B} if both V{B} and V{T} are in :m:`M`.
* V{T} otherwise.

.. _knh-consequence:

Consequence
-----------

**Logical Consequence** is defined just as in {@KFDE}.

.. include:: include/kfde/m.consequence.rst

.. _knh-system:

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

The closure rules are the same as {@NH}.

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _knh-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@NH} counterparts, with
the addition of carrying over the world marker from the target node(s).

.. include:: include/kfde/rule_groups.rst

Notes
=====



References
==========

- `Colin Caret`_. (2017). `Hybridized Paracomplete and Paraconsistent Logics`_.
  *The Australasian  Journal of Logic*, 14.

- Doug Owings (2012). `Indeterminacy and Logical Atoms`_. *Ph.D. Thesis, University
  of Connecticut*.


.. _Colin Caret: https://sites.google.com/view/colincaret
.. _Hybridized Paracomplete and Paraconsistent Logics: https://ojs.victoria.ac.nz/ajl/article/view/4035/3588
.. _Indeterminacy and Logical Atoms: https://github.com/owings1/dissertation/raw/master/output/dissertation.pdf


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: