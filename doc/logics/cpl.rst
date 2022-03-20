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

    .. _cpl-model:

    .. autoclass:: Model

        .. autoclass:: logics.cpl::Model.Value()
            :members: F, T
            :undoc-members:
            :noindex:

        .. include:: include/cpl/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//cpl//

        .. method:: value_of_predicated(sentence)

            The value of predicated sentences are handled in terms of their *extension*:

                | A sentence with *n*-ary predicate :math:`P` over parameters :m:`ntuple`
                | has the value :m:`T` iff :m:`ntuple` is in the extension of :math:`P`.


        .. Note:: CPL does not give a treatment of the quantifiers. Quantified sentences
            are treated as opaque (uninterpreted). See :ref:`CFOL <CFOL>` for quantification.
              

    .. _cpl-consequence:

    Logical Consequence
    -------------------

    **Logical Consequence** is defined in the standard way:

        .. include:: include/cpl/m.consequence.rst

    .. _cfol-system:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

