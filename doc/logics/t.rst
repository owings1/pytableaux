.. _T:

.. module:: pytableaux.logics.t

****************************************
L{} - Reflexive Normal Modal Logic
****************************************

L{} is an extension of {@K}, with a *reflexive* access relation.

.. contents::
  :local:
  :depth: 2

------------------------

.. _t-semantics:

Semantics
=========

L{} semantics behave just like {@K semantics}.

Reflexivity
-----------

L{} adds a *reflexive* restriction on the access relation for models.

.. include:: include/t/m.reflexivity.rst

.. _t-system:

Tableaux
========

L{} tableaux are constructed just like {@K system} tableaux.

Nodes
-----

.. include:: include/k/nodes_blurb.rst

Trunk
-----

.. include:: include/k/trunk_blurb.rst

.. tableau::
  :build-trunk:
  :prolog:

Closure
-------

.. tableau-rules::
  :group: closure
  :docflags:
  :title: -

.. _t-rules:

Rules
-----

L{} contains all the {@K rules} plus an additional Reflexive rule.

.. include:: include/t/reflexive_rule_blurb.rst

.. include:: include/t/access_rules_group.rst

.. include:: include/k/rule_groups.rst

Notes
=====

References
==========

.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: