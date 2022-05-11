.. _K:

*****************************
K - Kripke Normal Modal Logic
*****************************

Kripke Logic (K) is the foundation of so-called normal modal logics. It is an extension
of :ref:`CFOL <CFOL>`, adding the modal operators for possibility and necessity.

.. contents:: :local:

.. automodule:: pytableaux.logics.k

    Semantics
    =========

    A K model makes use of *Frames* to hold information about each world.

    .. _k-frame:

    .. autoclass:: Frame

        .. autoattribute:: world

        .. autoattribute:: atomics

        .. autoattribute:: extensions

        .. autoattribute:: anti_extensions

    .. _k-model:

    .. autoclass:: Model

        .. autoclass:: pytableaux.logics.k::Model.Value()
            :members: F, T
            :undoc-members:

        .. include:: include/k/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            .. truth-tables::

        .. automethod:: value_of_predicated(sentence)

        .. automethod:: value_of_existential(sentence)

        .. automethod:: value_of_universal(sentence)

        .. automethod:: value_of_possibility(sentence)

        .. automethod:: value_of_necessity(sentence)

    Consequence
    -----------

    .. _k-consequence:

    Logical consequence is defined similary as :ref:`CPL <CPL>`, except with
    reference to a world:

    .. include:: include/k/m.consequence.rst

    Tableaux System
    ===============

    .. _k-system:

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

    Notes
    -----

    For further reading, see:

    - `Stanford Encyclopedia on Modal Logic`_

.. _Stanford Encyclopedia on Modal Logic: http://plato.stanford.edu/entries/logic-modal/
