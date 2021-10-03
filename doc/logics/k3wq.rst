.. _K3WQ:

******************************************************
K3WQ - Weak Kleene Logic with alternate quantification
******************************************************

This is a version of :ref:`K3W` with a different treatment of the quantifiers
in terms of generalized conjunction/disjunction. This yeilds some interesting
rules for the quantifiers, given the behavior of those operators in :ref:`K3W`.

.. contents:: :local:

.. automodule:: logics.k3wq

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

        .. automethod:: value_of_existential(sentence)

        .. automethod:: value_of_universal(sentence)

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined just like in :ref:`CPL` and :ref:`K3`:

    * *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is :m:`T`
      are models where *C* also has the value :m:`T`.

    Notes
    =====

    - Standard interdefinability of the quantifiers is preserved.
