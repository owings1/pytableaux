.. _S4GO:

.. module:: pytableaux.logics.s4go

***************************************
L{} - L{GO} with S4 Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _s4go-semantics:
.. _s4go-model:
.. _s4go-frame:

Semantics
=========

The semantics for predication, quantification, and truth-functional operators are the
same as {@GO}.

Modal Operators
---------------

For modality, we reuse the `crunch` function from {@GO quantification}:

.. include:: include/go/crunch.rst

.. rubric:: Possibility

.. include:: include/go/m.possibility.rst

.. rubric:: Necessity

.. include:: include/go/m.necessity.rst

L{} includes the access relation restrictions on models of {@S4}:

.. include:: include/t/m.reflexivity.rst

.. include:: include/s4/m.transitivity.rst

.. _s4go-system:

Tableaux
========

L{} tableaux are constructed just like {@KFDE system} tableaux.

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

L{} includes the {@K3} and {@FDE} closure rules.

.. tableau-rules::
  :group: closure
  :docflags:
  :title: -

.. _s4go-rules:

Rules
--------

L{} contains all the {@GO rules}, and adds modal operator rules,
as well as the {@S4} access rules.

.. tableau-rules::
  :docflags:
  :title: Modal Operator Rules
  :group: operator
  :include: modal

.. include:: include/s4/access_rules_group.rst

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: modal

.. tableau-rules::
  :docflags:
  :group: quantifier


Notes
=====


References
==========

- Doug Owings (2012). `Indeterminacy and Logical Atoms`_. *Ph.D. Thesis, University
  of Connecticut*.

.. _Indeterminacy and Logical Atoms: https://github.com/owings1/dissertation/raw/master/output/dissertation.pdf


.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: