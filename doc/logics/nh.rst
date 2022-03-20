.. _NH:

********************************
NH - Paraconsistent Hybrid Logic
********************************

.. contents:: :local:

.. automodule:: logics.nh

    Semantics
    =========

    .. autoclass:: Model

        .. autoclass:: logics.nh::Model.Value()
            :members: F, B, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//nh//

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined, just as in :ref:`FDE <FDE>` and :ref:`LP`, in
    terms of *designated* values :m:`T` and :m:`B`:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a *desginated* value
      (:m:`T` or :m:`B`) are models where *C* also has a *designated* value.
