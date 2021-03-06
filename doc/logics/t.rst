********************************
T - Reflexive Normal Modal Logic
********************************

Reflexive Modal Logic is an extension of `K`_, with a *reflexive* accessibility relation,
which states that for every world *w*, *w* accesses *w* (itself).

.. contents:: :local:

.. automodule:: logics.t

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

    **Logical Consequence** is defined just as in `K`_:

    - *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is **T**
      at *w0* are models where *C* also has the value **T** at *w0*.

.. _K: k.html