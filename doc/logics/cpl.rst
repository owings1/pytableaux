.. _CPL:

*******************************
CPL - Classical Predicate Logic
*******************************

Classical Predicate Logic (CPL) is the standard bivalent logic with
values V{T} and V{F}, commonly interpretated as 'true' and 'false',
respectively.

.. contents:: :local:

.. automodule:: pytableaux.logics.cpl

    Semantics
    =========

    .. _cpl-model:

    .. autoclass:: Model

        .. autoclass:: pytableaux.logics.cpl::Model.Value()
            :members: F, T
            :undoc-members:
            :noindex:

        .. include:: include/cpl/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            .. truth-tables:: cpl

        .. method:: value_of_predicated(sentence)

            The value of predicated sentences are handled in terms of their *extension*:

                | A sentence with *n*-ary predicate :math:`P` over parameters :m:`!{ntuple}`
                | has the value V{T} iff :m:`!{ntuple}` is in the extension of :math:`P`.


        .. Note:: CPL does not give a treatment of the quantifiers. Quantified sentences
            are treated as opaque (uninterpreted). See {@CFOL} for quantification.
              

    .. _cpl-consequence:

    Consequence
    -----------

    **Logical Consequence** is defined in the standard way:

        .. include:: include/cpl/m.consequence.rst

    .. _cfol-system:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

