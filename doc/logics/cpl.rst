.. _CPL:

*******************************
CPL - Classical Predicate Logic
*******************************

Classical Predicate Logic (CPL) is the standard bivalent logic with
values :m:`T` and :m:`F`, commonly interpretated as 'true' and 'false',
respectively.

.. contents:: :local:

.. automodule:: logics.cpl

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

        .. method:: value_of_predicated(sentence)

            A sentence for predicate `P` is true iff the tuple of the parameters
            is in the extension of `P`.

        .. automethod:: is_sentence_opaque(sentence)

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    .. _cpl-consequence:

    Logical Consequence
    ===================

    **Logical Consequence** is defined in the standard way:

    - *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is :m:`T`
      are models where *C* also has the value :m:`T`.