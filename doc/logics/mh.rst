.. _MH:

******************************
MH - Paracomplete Hybrid Logic
******************************

.. contents:: :local:

.. automodule:: logics.mh

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined just like in :ref:`CPL` and :ref:`K3`:

    * *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is **T**
      are models where *C* also has the value **T**.


..
    - Maximal Weakly-Intuitionistic Logics: https://www.jstor.org/stable/20015812
