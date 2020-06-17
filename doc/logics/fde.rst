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

    - Anderson, A., Belnap, N. D., et al. `Entailment`_: The Logic of Relevance and
      Necessity. United Kingdom, Princeton University Press, 1975.
    
    * Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
      Vol. 38, No. 2, 1979.

    - Priest, Graham. `An Introduction to Non-Classical Logic`_: From If to Is.
      Cambridge University Press, 2008.

    - `Stanford Encyclopedia on Paraconsistent Logic`_


.. _Stanford Encyclopedia on Paraconsistent Logic: http://plato.stanford.edu/entries/logic-paraconsistent/
.. _Entailment: https://www.google.com/books/edition/_/8LRGswEACAAJ?hl=en
.. _An Introduction to Non-Classical Logic: https://www.google.com/books/edition/_/rMXVbmAw3YwC?hl=en
.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf