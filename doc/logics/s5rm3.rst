.. _S5RM3:

.. module:: pytableaux.logics.s5rm3

***************************************
L{} - L{RM3} with S5 Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _s5rm3-semantics:
.. _s5rm3-model:
.. _s5rm3-frame:

Semantics
=========

L{} semantics behave just like {@KRM3 semantics}.

L{} includes the access relation restrictions on models of {@S5}:

.. include:: include/t/m.reflexivity.rst

.. include:: include/s4/m.transitivity.rst

.. include:: include/s5/m.symmetry.rst

.. _s5rm3-system:

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

L{} includes the {@LP} and {@FDE} closure rules.

.. tableau-rules::
  :group: closure
  :docflags:
  :title: -

.. _s5rm3-rules:

Rules
--------

L{} contains all the {@KRM3 rules} plus the {@S5} access rules.

.. include:: include/s5/access_rules_group.rst

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