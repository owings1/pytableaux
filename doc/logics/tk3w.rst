.. _TK3W:

.. module:: pytableaux.logics.tk3w

***************************************
L{} - L{K3W} with T Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _tk3w-semantics:
.. _tk3w-model:
.. _tk3w-frame:

Semantics
=========

L{} semantics behave just like {@KK3W semantics}.

L{} includes the {@T} *reflexive* restriction on the access relation for models.

.. include:: include/t/m.reflexivity.rst

.. _tk3w-system:

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

.. _tk3w-rules:

Rules
--------

L{} contains all the {@KK3W rules} plus the {@T} Reflexive rule.

.. include:: include/t/reflexive_rule_blurb.rst

.. include:: include/t/access_rules_group.rst

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