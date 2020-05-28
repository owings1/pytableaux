*****************************
K - Kripke Normal Modal Logic
*****************************

Kripke Logic (K) is the foundation of so-called normal modal logics. It is an extension of `CFOL`_,
adding the modal operators for possibility and necessity.

.. contents:: :local:

.. automodule:: logics.k

    Semantics
    =========

    .. autoclass:: Model
        :members:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined similary as `CPL`_, except with reference to a world:

    - *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is **T**
      at *w0* are models where *C* also has the value **T** at *w0*.

    Notes
    =====

    For further reading, see:

    - `Stanford Encyclopedia on Modal Logic`_

.. _Stanford Encyclopedia on Modal Logic: http://plato.stanford.edu/entries/logic-modal/
.. _CPL: cpl.html
.. _CFOL: cfol.html