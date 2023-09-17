.. _S4NH:

.. module:: pytableaux.logics.s4nh

***************************************
L{} - L{NH} with S4 Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _s4nh-semantics:
.. _s4nh-model:
.. _s4nh-frame:

Semantics
=========

L{} semantics behave just like {@KNH semantics}.

L{} includes the access relation restrictions on models of {@S4}:

.. include:: include/t/m.reflexivity.rst

.. include:: include/s4/m.transitivity.rst

.. _s4nh-system:

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

.. _s4nh-rules:

Rules
--------

L{} contains all the {@KNH rules} plus the {@S4} access rules.

.. include:: include/s4/access_rules_group.rst

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