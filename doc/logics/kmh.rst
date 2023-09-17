.. _kmh:

.. module:: pytableaux.logics.kmh

***************************************
L{} - L{MH} with K Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _kmh-semantics:
.. _kmh-model:
.. _kmh-frame:

Semantics
=========

.. include:: include/k/models_blurb.rst

The semantics for predication, quantification, and truth-functional operators are the
same as {@MH}.

.. _kmh-modality:

Modal Operators
---------------

Although modal operators were not defined in Caret's original paper, here we apply
the idea of generalized disjunction & conjunction.

.. rubric:: Possibility

Let :m:`M` be the set of values of :s:`A` at all :m:`w'` such that :m:`wRw'`.
The value of :m:`PA` at :m:`w` is:

* V{T} if V{T} is in :m:`M`.
* V{N} if both V{N} and V{F} are in :m:`M`.
* V{F} otherwise.

.. rubric:: Necessity

Since conjunction behaves just like {@K3}, necessity is the same.

.. include:: include/kfde/m.necessity.rst

.. _kmh-consequence:

Consequence
-----------

**Logical Consequence** is defined just as in {@KFDE}.

.. include:: include/kfde/m.consequence.rst

.. _kmh-system:

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

The closure rules are the same as {@MH}.

.. tableau-rules::
  :docflags:
  :group: closure
  :title: -

.. _kmh-rules:

Rules
--------

Non-modal rules for L{} are exactly like their {@MH} counterparts, with
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