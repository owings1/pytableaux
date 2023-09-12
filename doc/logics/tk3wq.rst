.. _TK3WQ:

.. module:: pytableaux.logics.tk3wq

***************************************
L{} - L{K3WQ} with T Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _tk3wq-semantics:
.. _tk3wq-model:
.. _tk3wq-frame:

Semantics
=========

L{} semantics behave just like {@KK3WQ semantics}.

L{} includes the {@T} *reflexive* restriction on the access relation for models.

.. include:: include/t/m.reflexivity.rst

.. _tk3wq-system:

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

.. _tk3wq-rules:

Rules
--------

L{} contains all the {@KK3WQ rules} plus the {@T} Reflexive rule.

.. include:: include/t/reflexive_rule_blurb.rst

.. include:: include/t/access_rules_group.rst

.. include:: include/kfde/rule_groups.rst

Notes
=====


References
==========



.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: