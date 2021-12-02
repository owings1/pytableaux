.. _CFOL:

**********************************
CFOL - Classical First-Order Logic
**********************************

Classical First-Order Logic (CFOL) augments :ref:`CPL <CPL>` with the quantifiers:
Universal (:s:`L`) and Existential (:s:`X`).

.. contents:: :local:

.. automodule:: logics.cfol

    Semantics
    =========

    .. autoclass:: Model

        .. include:: include/cpl/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//cfol//

        .. method:: value_of_existential(sentence)

            An existential sentence is true just when the sentence resulting in the
            subsitution of some constant in the domain for the variable is true.  

        .. method:: value_of_universal(sentence)

            A universal sentence is true just when the sentence resulting in the
            subsitution of each constant in the domain for the variable is true.

    Logical Consequence
    -------------------

    **Logical Consequence** is defined in the standard way:

        .. include:: include/cpl/m.consequence.rst

    Tableaux System
    ===============

    .. _cfol-system:

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:


