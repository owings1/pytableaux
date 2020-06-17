****************
RM3 - R-mingle 3
****************

R-mingle 3 (RM3) is a three-valued logic with values **T**, **F**, and **B**.
It is similar to `LP`_, with a different conditional operator.

.. contents:: :local:

.. automodule:: logics.rm3

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

    **Logical Consequence** is defined, just as in `FDE`_, in terms of *designated* values **T**
    and **B**:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a *desginated* value
      (**T** or **B**) are models where *C* also has a *designated* value.

    Notes
    =====

    * With the conditional operator, Modus Ponens (P{A}, P{A $ B}, therefore P{B}) is
      valid in RM3, but it fails in `LP`_.

    * The argument P{B}, therefore P{A $ B} is valid in `LP`_, but not in RM3.

    For further reading, see:

    * Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
      Vol. 38, No. 2. 1979.

.. _FDE: fde.html
.. _LP: lp.html
.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf