============================================
:mod:`pytableaux.proof`
============================================

.. contents:: Contents
  :local:
  :depth: 2

.. module:: pytableaux.proof

Classes
=======

.. autoclass:: Branch

.. autoclass:: Node

.. autoclass:: Target

.. autoclass:: Rule
    :members:

.. autoclass:: Tableau

    .. autoattribute:: argument

    .. autoattribute:: logic

    .. autoattribute:: finished

    .. autoattribute:: valid

    .. autoattribute:: invalid

    .. autoattribute:: completed

    .. autoattribute:: premature

    .. autoattribute:: id

    .. autoattribute:: history

    .. autoattribute:: rules

    .. autoattribute:: open

    .. autoattribute:: tree

    .. automethod:: build

    .. automethod:: step
    
    .. automethod:: stepiter

    .. automethod:: branch

    .. automethod:: add

    .. automethod:: finish

    .. automethod:: build_trunk

    .. automethod:: branching_complexity

.. autoclass:: System
    :members:


.. autoclass:: pytableaux.proof.tableaux::Tableau.Tree
    :members:

.. autoclass:: pytableaux.proof.tableaux::Rule.Helper
    :members:

.. autoclass:: RulesRoot
    :members:

.. autoclass:: RuleGroups
    :members:

.. autoclass:: RuleGroup
    :members:
