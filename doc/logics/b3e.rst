.. _B3E:

*************************************
B3E - Bochvar 3-valued External Logic
*************************************

B3E is a three-valued logic with values :m:`T`, :m:`F`, and :m:`N`. B3E is similar
to :ref:`K3W <K3W>`, with a special Assertion operator, that always results in a classical
value (:m:`T` or :m:`F`).

.. contents:: :local:

.. automodule:: logics.b3e

    Semantics
    =========

    .. autoclass:: Model

        .. method:: value_of_operated(sentence)

        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        Note that the conditional operator :oper:`Conditional` is definable in terms of the
        assertion operator :oper:`Assertion`:
        
        * :s:`A $ B` is equivalent to :s:`~*A V *B` 

        //truth_tables//b3e//

        Bochvar also defined `external` versions of :oper:`Conjunction` and :oper:`Disjunction`
        using the assertion operator:

        * External conjunction: :s:`*A & *B`
        * External disjunction: :s:`*A V *B`

        These connectives always result in a classical value. For compatibility,
        we use the standard `internal` readings of :oper:`Conjunction` and :oper:`Disjunction`,
        and use the `internal` reading for :oper:`Conditional` and :oper:`Biconditional`.

    Logical Consequence
    ===================

    **Logical Consequence** is defined just like in :ref:`CPL <CPL>` and :ref:`K3 <K3>`:

    * *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is :m:`T`
      are models where *C* also has the value :m:`T`.
 
    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:


    Notes
    =====

    * Unlike :ref:`K3W`, B3E has some logical truths. For example :s:`(A $ B) V ~(A $ B)`.
      This logical truth is an instance of the Law of Excluded Middle.

    * The assertion operator can expression alternate versions of validities that
      fail in :ref:`K3W`. For example, :s:`A` implies :s:`A V *B` in B3E, which fails in
      :ref:`K3W`.

    * D. A. Bochvar published his paper in 1938. An English translation by Merrie
      Bergmann was published in 1981. *On a three-valued logical calculus and its
      application to the analysis of the paradoxes of the classical extended
      functional calculus.* History and Philosophy of Logic, 2(1-2):87–112, 1981.

    For further reading, see:

    * Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.
