.. _T:

********************************
T - Reflexive Normal Modal Logic
********************************

Reflexive Modal Logic is an extension of :ref:`K <K>`, with a *reflexive* accessibility relation,
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

    **Logical Consequence** is defined just as in :ref:`K <K>`: :

    - *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is :m:`T`
      at *w0* are models where *C* also has the value :m:`T` at *w0*.
