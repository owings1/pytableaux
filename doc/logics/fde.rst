.. _FDE:

*****************************
FDE - First Degree Entailment
*****************************

.. contents:: :local:

FDE is a 4-valued logic (:m:`T`, :m:`F`, :m:`N` and :m:`B`). A common interpretation of these
values is:

- :m:`T`: just true
- :m:`F`: just false
- :m:`N`: neither true nor false
- :m:`B`: both true and false

.. automodule:: logics.fde

    Semantics
    =========

    .. autoclass:: Model

        .. autoattribute:: truth_values

        .. autoattribute:: designated_values

        .. autoattribute:: extensions

        .. autoattribute:: anti_extensions

        .. autoattribute:: atomics

        .. method:: value_of_operated(sentence)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//fde//

        .. method:: value_of_predicated(sentence)

            A sentence with *n*-ary predicate :math:`P` over parameters :m:`ntuple`
            has the value:

            * :m:`T` iff :m:`ntuple` is in the *extension* of :math:`P` and
              not in the *anti-extension* of :math:`P`.

            * :m:`F` iff :m:`ntuple` is in the *anti-extension* of :math:`P`
              and not in the *extension* of :math:`P`.

            * :m:`B` iff :m:`ntuple` is in **both** the extension and anti-extension
              of :math:`P`.

            * :m:`N` iff :m:`ntuple` is in **neither** in the extension nor the 
              anti-extension of :math:`P`.

            Note, for FDE, there is no *exclusivity* nor *exhaustion* constraint on a predicate's
            extension and anti-extension. This means that :m:`ntuple` could be in *neither*
            the extension nor the anti-extension of a predicate, or it could be in *both* the extension
            and the anti-extension.

    .. _fde-consequence:

    Logical Consequence
    ===================

    **Logical Consequence** is defined in terms of the *designated* values :m:`T` and :m:`B`:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a *desginated* value
      (:m:`T` or :m:`B`) are models where *C* also has a *designated* value.

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members:

    .. autoclass:: TableauxRules
        :members:

    Notes
    =====

    Some notable features of FDE include:

    * No logical truths. The means that the Law of Excluded Middle :s:`A V ~A`, and the
      Law of Non-Contradiction :s:`~(A & ~A)` fail, as well as Conditional Identity :s:`A $ A`.
  
    * Failure of Modus Ponens, Modus Tollens, Disjunctive Syllogism, and other Classical validities.

    * DeMorgan laws are valid, as well as Conditional Contraction (:s:`A $ (A $ B)` implies :s:`A $ B`).

    References
    ==========

    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and Many-valued Logic.
      United Kingdom, Oxford University Press, 2003.

    * Priest, Graham. `An Introduction to Non-Classical Logic`_: From If to Is.
      Cambridge University Press, 2008.

    For futher reading see:

    * Anderson, A., Belnap, N. D., et al. `Entailment`_: The Logic of Relevance and
      Necessity. United Kingdom, Princeton University Press, 1975.
    
    * Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
      Vol. 38, No. 2, 1979.

    * `Stanford Encyclopedia on Paraconsistent Logic`_


.. _Stanford Encyclopedia on Paraconsistent Logic: http://plato.stanford.edu/entries/logic-paraconsistent/
.. _Entailment: https://www.google.com/books/edition/_/8LRGswEACAAJ?hl=en
.. _An Introduction to Non-Classical Logic: https://www.google.com/books/edition/_/rMXVbmAw3YwC?hl=en
.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en