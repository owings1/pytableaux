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

    Logical consequence is defined just like in :m:`K3`:
    
    .. include:: include/k3/m.consequence.rst


..
    - Maximal Weakly-Intuitionistic Logics: https://www.jstor.org/stable/20015812
