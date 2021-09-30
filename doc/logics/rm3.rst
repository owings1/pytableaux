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

    * With the conditional operator, Modus Ponens (:s:`A`, :s:`A $ B`, therefore :s:`B`) is
      valid in RM3, but it fails in `LP`_.

    * The argument :s:`B`, therefore :s:`A $ B` is valid in `LP`_, but not in RM3.

    References
    ==========

    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and Many-valued Logic.
      United Kingdom, Oxford University Press, 2003.

    For further reading, see:

    * Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
      Vol. 38, No. 2. 1979.

.. _FDE: fde.html
.. _LP: lp.html
.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en