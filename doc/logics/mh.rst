.. _MH:

******************************
MH - Paracomplete Hybrid Logic
******************************

.. contents:: :local:

.. automodule:: logics.mh

    Semantics
    =========

    .. autoclass:: Model

        .. autoclass:: logics.mh::Model.Value()
            :members: F, N, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            .. truth-tables:: MH

    Consequence
    -----------

    Logical consequence is defined just like in L{K3}:
    
    .. include:: include/k3/m.consequence.rst

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:


..
    - Maximal Weakly-Intuitionistic Logics: https://www.jstor.org/stable/20015812
