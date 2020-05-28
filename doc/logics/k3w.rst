***********************
K3W - Weak Kleene Logic
***********************

K3W is a 3-valued logic with values **T**, **F**, and **N**. The logic is similar
to `K3`_, but with slightly different behavior of the **N** value. This logic is also
known as Bochvar Internal (B3).

.. contents:: :local:

.. automodule:: logics.k3w

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

    **Logical Consequence** is defined just like in `CPL`_ and `K3`_:

    * *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is **T**
      are models where *C* also has the value **T**.

.. _CPL: cpl.html
.. _K3: k3.html
.. _FDE: fde.html