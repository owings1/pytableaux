.. _K:

*****************************
K - Kripke Normal Modal Logic
*****************************

Kripke Logic (K) is the foundation of so-called normal modal logics. It is an extension of :ref:`CFOL`,
adding the modal operators for possibility and necessity.

.. contents:: :local:

.. automodule:: logics.k

    Semantics
    =========

    A K model makes use of *Frames* to hold information about each world.

    .. autoclass:: Frame

        .. autoattribute:: world

        .. autoattribute:: atomics
        
        .. autoattribute:: extensions

    .. autoclass:: Model

        .. autoattribute:: truth_values

        .. autoattribute:: frames

        .. autoattribute:: access

        .. autoattribute:: constants

        .. method:: value_of_operated(sentence)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//k//

        .. automethod:: value_of_predicated(sentence)

        .. automethod:: value_of_existential(sentence)

        .. automethod:: value_of_universal(sentence)

        .. automethod:: value_of_possibility(sentence)

        .. automethod:: value_of_necessity(sentence)





    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined similary as :ref:`CPL`, except with reference to a world:

    - *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is **T**
      at *w0* are models where *C* also has the value **T** at *w0*.

    Notes
    =====

    For further reading, see:

    - `Stanford Encyclopedia on Modal Logic`_

.. _Stanford Encyclopedia on Modal Logic: http://plato.stanford.edu/entries/logic-modal/
