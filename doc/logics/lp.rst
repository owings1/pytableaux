.. _LP:

*********************
LP - Logic of Paradox
*********************

LP is a 3-valued logic (:m:`T`, :m:`F`, and :m:`B`). It can be understood as :ref:`FDE` without
the :m:`N` value.

.. contents:: :local:

.. automodule:: logics.lp

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

        .. method:: value_of_predicated(sentence)

            A sentence with predicate `P` with parameters :m:`ntuple` has the value:

            * :m:`T` iff :m:`ntuple` is in the extension of `P` and not in the anti-extension of `P`.
            * :m:`F` iff :m:`ntuple` is in the anti-extension of `P` and not in the extension of `P`.
            * :m:`B` iff :m:`ntuple` is in both the extension and anti-extension of `P`.

            Note, unlike :ref:`FDE`, there is an exhaustion constraint on a predicate's
            extension/anti-extension. This means that :m:`ntuple` must be in either the
            extension and the anti-extension of `P`. Like :ref:`FDE`, there is no exclusion
            restraint.

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined, just as in :ref:`FDE`, in terms of *designated* values :m:`T`
    and :m:`B`:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a *desginated* value
      (:m:`T` or :m:`B`) are models where *C* also has a *designated* value.

    Notes
    =====

    Some notable features of LP include:

    * Everything valid in :ref:`FDE` is valid in LP.

    * Like :ref:`FDE`, the Law of Non-Contradiction fails :s:`~(A & ~A)`.

    * Unlike :ref:`FDE`, LP has some logical truths. For example, the Law of Excluded Middle (:s:`(A V ~A)`),
      and Conditional Identity (:s:`(A $ A)`).

    * Many classical validities fail, such as Modus Ponens, Modus Tollens, and Disjunctive Syllogism.

    * DeMorgan laws are valid.

    References
    ==========
    
    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and Many-valued Logic.
      United Kingdom, Oxford University Press, 2003.

    For futher reading see:

    * `Stanford Encyclopedia entry on paraconsistent logic <http://plato.stanford.edu/entries/logic-paraconsistent/>`_

.. _FDE: fde.html
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en