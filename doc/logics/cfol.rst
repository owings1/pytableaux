.. _CFOL:

**********************************
CFOL - Classical First-Order Logic
**********************************

Classical First-Order Logic (CFOL) augments :ref:`CPL` with the quantifiers: Universal and Existential.

.. contents:: :local:

.. automodule:: logics.cfol

    Semantics
    =========

    .. autoclass:: Model

        .. method:: value_of_existential(sentence)

            An existential sentence is true just when the sentence resulting in the
            subsitution of some constant in the domain for the variable is true.  

        .. method:: value_of_universal(sentence)

            A universal sentence is true just when the sentence resulting in the
            subsitution of each constant in the domain for the variable is true.

        .. automethod:: value_of_operated(sentence)

        .. automethod:: is_sentence_opaque(sentence)

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined in the standard way:

    - *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is :m:`T`
      are models where *C* also has the value :m:`T`.
