*************************************
B3E - Bochvar 3-valued External Logic
*************************************

B3E is a three-valued logic with values **T**, **F**, and **N**.
B3E is similar to `K3W`_, with a special Assertion operator, that always results in
a classical value (**T** or **F**).

.. contents:: :local:

.. automodule:: logics.b3e

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

    Notes
    =====

    * The assertion operator can expression alternate versions of validities that
      fail in `K3W`_. For example, P{A} implies P{A V \*B} in B3E, which fails in
      `K3W`_.

.. _CPL: cpl.html
.. _K3: k3.html
.. _K3W: k3w.html