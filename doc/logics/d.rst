******************************
D - Deontic Normal Modal Logic
******************************

Deontic logic, also known as the Logic of Obligation, is an extension of `K`_, with
a *serial* accessibility relation, which states that for every world *w*, there is
a world *w'* such that *w* accesses *w'*.

.. contents:: :local:

.. automodule:: logics.d

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

    Notes
    =====

    For further reading, see

    * `Stanford Encyclopedia on Deontic Logic`_

.. _K: k.html

.. _Stanford Encyclopedia on Deontic Logic: http://plato.stanford.edu/entries/logic-deontic/