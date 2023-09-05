.. _TK3:

.. module:: pytableaux.logics.tk3

***************************************
L{} - L{K3} with T Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _tk3-semantics:
.. _tk3-model:
.. _tk3-frame:

Semantics
=========

L{} semantics behave just like {@KK3 semantics}.

L{} includes the {@T} *reflexive* restriction on the access relation for models.

.. include:: include/t/m.reflexivity.rst

.. _tk3-system:

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

.. _tk3-rules:

Rules
--------

L{} contains all the {@KFDE rules} plus the {@T} Reflexive rule.

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