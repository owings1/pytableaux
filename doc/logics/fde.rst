.. _FDE:

***************************************
L{FDE} - First Degree Entailment
***************************************

.. contents:: :local:

L{FDE} is a 4-valued logic (V{T}, V{F}, V{N} and V{B}). A common reading
of these values is:

- V{T}: just true
- V{F}: just false
- V{N}: neither true nor false
- V{B}: both true and false

.. automodule:: logics.fde

    Semantics
    =========

    .. _fde-model:

    .. autoclass:: Model

      .. autoclass:: logics.fde::Model.Value()
          :members: F, N, B, T
          :undoc-members:

      .. autoattribute:: designated_values

      .. autoattribute:: extensions

      .. autoattribute:: anti_extensions

      .. autoattribute:: atomics

    .. _fde-truth-tables:

    Truth Tables
    ------------

    .. include:: include/truth_table_blurb.rst

    //truth_tables//fde//

    .. _fde-predication:

    Predication
    -----------

    A sentence with *n*-ary predicate :math:`P` over parameters !{ntuple}
    has the value:

    * V{T} iff !{ntuple} is in the *extension* of :math:`P` and
      not in the *anti-extension* of :math:`P`.

    * V{F} iff !{ntuple} is in the *anti-extension* of :math:`P`
      and not in the *extension* of :math:`P`.

    * V{B} iff !{ntuple} is in *both* the extension and anti-extension
      of :math:`P`.

    * V{N} iff !{ntuple} is in *neither* in the extension nor the 
      anti-extension of :math:`P`.

    Note, for L{FDE}, there is no *exclusivity* nor *exhaustion* constraint on a
    predicate's extension and anti-extension. This means that !{ntuple} could
    be in *neither* the extension nor the anti-extension of a predicate, or it
    could be in *both* the extension and the anti-extension.

    .. _fde-quantification:

    Quantification
    --------------

    Existential
    ^^^^^^^^^^^

    The value of an existential sentence is the maximum value of the sentences that
    result from replacing each constant for the quantified variable. The ordering of
    the values from least to greatest is: V{F}, V{N}, V{B}, V{T}.

    Universal
    ^^^^^^^^^

    The value of an universal sentence is the minimum value of the sentences that
    result from replacing each constant for the quantified variable. The ordering of
    the values from least to greatest is: V{F}, V{N}, V{B}, V{T}.

    .. _fde-consequence:

    Consequence
    -----------

    **Logical Consequence** is defined in terms of the *designated* values V{T} and V{B}:

      .. include:: include/fde/m.consequence.rst

    .. _fde-system:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members:

    .. _fde-rules:

    .. autoclass:: TabRules
        :members:

    Notes
    =====

    Some notable features of L{FDE} include:

    * No logical truths. The means that the Law of Excluded Middle :s:`A V ~A`, and the
      Law of Non-Contradiction :s:`~(A & ~A)` fail, as well as Conditional Identity
      :s:`A $ A`.
  
    * Failure of Modus Ponens, Modus Tollens, Disjunctive Syllogism, and other Classical
      validities.

    * DeMorgan laws are valid, as well as Conditional Contraction (:s:`A $ (A $ B)`
      implies :s:`A $ B`).

    References
    ==========

    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and
      Many-valued Logic. United Kingdom, Oxford University Press, 2003.

    * Priest, Graham. `An Introduction to Non-Classical Logic`_: From If to Is.
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