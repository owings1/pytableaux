.. _S5MH:

.. module:: pytableaux.logics.s5mh

***************************************
L{} - L{MH} with S5 Modal
***************************************

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. _s5mh-semantics:
.. _s5mh-model:
.. _s5mh-frame:

Semantics
=========

L{} semantics behave just like {@KMH semantics}.

L{} includes the access relation restrictions on models of {@S5}:

.. include:: include/t/m.reflexivity.rst

.. include:: include/s4/m.transitivity.rst

.. include:: include/s5/m.symmetry.rst

.. _s5mh-system:

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

.. _s5mh-rules:

Rules
--------

L{} contains all the {@KMH rules} plus the {@S5} access rules.

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