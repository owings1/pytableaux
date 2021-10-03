.. _NH:

********************************
NH - Paraconsistent Hybrid Logic
********************************

.. contents:: :local:

.. automodule:: logics.nh

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined, just as in :ref:`FDE` and :ref:`LP`, in
    terms of *designated* values **T** and **B**:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a *desginated* value
      (**T** or **B**) are models where *C* also has a *designated* value.
