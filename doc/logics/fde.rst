*****************************
FDE - First Degree Entailment
*****************************

FDE is a 4-valued logic (**T**, **F**, **N** and **B**). A common interpretation of these
values is:

- **T**: just true
- **F**: just false
- **N**: neither true nor false
- **B**: both true and false

.. contents:: :local:

.. automodule:: logics.fde

    Semantics
    =========

    .. autoclass:: Model
        :members:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members:

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined in terms of the *designated* values **T** and **B**:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a *desginated* value
      (**T** or **B**) are models where *C* also has a *designated* value.

    Notes
    =====

    Some notable features of FDE include:

    * No logical truths. The means that the Law of Excluded Middle P{A V ~A}, and the
      Law of Non-Contradiction P{~(A & ~A)} fail, as well as Conditional Identity P{A $ A}.
  
    * Failure of Modus Ponens, Modus Tollens, Disjunctive Syllogism, and other Classical validities.

    * DeMorgan laws are valid, as well as Conditional Contraction (P{A $ (A $ B)} implies P{A $ B}).

    For futher reading see:

    - `Stanford Encyclopedia on Paraconsistent Logic`_


.. _Stanford Encyclopedia on Paraconsistent Logic: http://plato.stanford.edu/entries/logic-paraconsistent/