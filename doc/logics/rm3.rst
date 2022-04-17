.. _RM3:

***************************
L{RM3} - R-mingle 3
***************************

R-mingle 3 (L{RM3}) is a three-valued logic with values V{T}, V{F}, and V{B}.
It is similar to {@LP}, with a different conditional operator.

.. contents:: :local:

.. automodule:: logics.rm3

    Semantics
    =========

    .. _rm3-model:

    .. autoclass:: Model

        .. autoclass:: logics.rm3::Model.Value()
            :members: F, B, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst

    .. _rm3-truth-tables:

    Truth Tables
    ------------

    .. include:: include/truth_table_blurb.rst

    .. truth-tables:: RM3

    .. _rm3-consequence:

    Consequence
    -----------

    Logical consequence is defined, just as in L{FDE}, in terms of
    *designated* values V{T} and V{B}:
    
    .. include:: include/fde/m.consequence.rst

    .. _rm3-system:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. _rm3-rules:

    .. autoclass:: TabRules
        :members:

    Notes
    =====

    * With the Conditional operator :s:`$`, Modus Ponens (:s:`A`, :s:`A $ B`, therefore :s:`B`) is
      valid in L{RM3}, but it fails in {@LP}.

    * The argument :s:`B`, therefore :s:`A $ B` is valid in L{LP}, but not in L{RM3}.

    References
    ==========

    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and Many-valued Logic.
      United Kingdom, Oxford University Press, 2003.

    For further reading, see:

    * Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
      Vol. 38, No. 2. 1979.


.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en