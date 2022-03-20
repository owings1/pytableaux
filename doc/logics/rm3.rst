.. _RM3:

*********************
:m:`RM3` - R-mingle 3
*********************

R-mingle 3 (:m:`RM3`) is a three-valued logic with values :m:`T`, :m:`F`, and :m:`B`.
It is similar to :ref:`LP`, with a different conditional operator.

.. contents:: :local:

.. automodule:: logics.rm3

    Semantics
    =========

    .. autoclass:: Model

        .. autoclass:: logics.rm3::Model.Value()
            :members: F, B, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//rm3//

    Logical Consequence
    ===================

    Logical consequence is defined, just as in :ref:`FDE <FDE>`, in terms of
    *designated* values :m:`T` and :m:`B`:
    
    .. include:: include/fde/m.consequence.rst

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

    Notes
    =====

    * With the conditional operator, Modus Ponens (:s:`A`, :s:`A $ B`, therefore :s:`B`) is
      valid in :m:`RM3`, but it fails in:ref:`LP`.

    * The argument :s:`B`, therefore :s:`A $ B` is valid in :ref:`LP`, but not in :m:`RM3`.

    References
    ==========

    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and Many-valued Logic.
      United Kingdom, Oxford University Press, 2003.

    For further reading, see:

    * Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
      Vol. 38, No. 2. 1979.


.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en