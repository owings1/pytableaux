.. _K3WQ:

************************************************************
:m:`K3WQ` - Weak Kleene Logic with alternate quantification
************************************************************

This is a version of :ref:`K3W <K3W>` with a different treatment of the quantifiers
in terms of generalized conjunction/disjunction. This yields some interesting
rules for the quantifiers, given the behavior of those operators in :ref:`K3W <K3W>`.

.. contents:: :local:

.. automodule:: logics.k3wq

    Semantics
    =========

    .. _k3wq-model:

    .. autoclass:: Model

        .. autoclass:: logics.k3wq::Model.Value()
            :members: F, N, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//k3wq//

        .. automethod:: value_of_existential(sentence)

        .. automethod:: value_of_universal(sentence)

    Consequence
    -----------

    Logical consequence is defined just like in :m:`K3`:
    
    .. include:: include/k3/m.consequence.rst

    Tableaux System
    ===============

    .. _k3wq-system:

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

    Notes
    -----

    - Standard interdefinability of the quantifiers is preserved.
