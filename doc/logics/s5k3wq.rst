
.. _S5K3WQ:

.. module:: pytableaux.logics.s5k3wq

***************************************
L{} - L{K3WQ} with S5 Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _s5k3wq-semantics:
.. _s5k3wq-model:
.. _s5k3wq-frame:

Semantics
=========

L{} semantics behave just like {@KK3WQ semantics}.

L{} includes the access relation restrictions on models of {@S5}:

.. include:: include/t/m.reflexivity.rst

.. include:: include/s4/m.transitivity.rst

.. include:: include/s5/m.symmetry.rst

.. _s5k3wq-system:

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

.. _s5k3wq-rules:

Rules
--------

L{} contains all the {@KK3WQ rules} plus the {@S5} access rules.

.. include:: include/s5/access_rules_group.rst

.. include:: include/kfde/rule_groups.rst

Notes
=====


References
==========



.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: