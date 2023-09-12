.. _S4K3WQ:

.. module:: pytableaux.logics.s4k3wq

***************************************
L{} - L{K3WQ} with S4 Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _s4k3wq-semantics:
.. _s4k3wq-model:
.. _s4k3wq-frame:

Semantics
=========

L{} semantics behave just like {@KK3WQ semantics}.

L{} includes the access relation restrictions on models of {@S4}:

.. include:: include/t/m.reflexivity.rst

.. include:: include/s4/m.transitivity.rst

.. _s4k3wq-system:

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

.. _s4k3wq-rules:

Rules
--------

L{} contains all the {@KK3WQ rules} plus the {@S4} access rules.

.. include:: include/s4/access_rules_group.rst

.. include:: include/kfde/rule_groups.rst

Notes
=====


References
==========



.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: