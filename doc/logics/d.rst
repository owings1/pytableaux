.. _D:

.. module:: pytableaux.logics.d

****************************************
L{} - Deontic Normal Modal Logic
****************************************

L{}, also known as the Logic of Obligation, is an extension of {@K}, with
a *serial* access relation.

.. contents::
    :local:
    :depth: 2

------------------------

.. _d-semantics:

Semantics
=========

L{} semantics behave just like {@K semantics}.

Seriality
---------

L{} adds a *serial* restriction on the access relation for models.

.. include:: include/d/m.seriality.rst

.. _d-system:

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

.. _d-rules:

Rules
-----

L{} contains all the {@K rules} plus an additional Serial rule.

.. include:: include/d/serial_rule_blurb.rst

.. include:: include/d/access_rules_group.rst

.. include:: include/k/rule_groups.rst

Notes
=====

References
==========

.. rubric:: Further Reading

* `Stanford Encyclopedia on Deontic Logic`_

.. _Stanford Encyclopedia on Deontic Logic: http://plato.stanford.edu/entries/logic-deontic/

.. cssclass:: hidden

.. autoclass:: Rules()
  :members:
  :undoc-members: