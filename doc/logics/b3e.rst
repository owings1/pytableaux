.. _B3E:

******************************************
:m:`B3E` - Bochvar 3-valued External Logic
******************************************

:m:`B3E` is a three-valued logic with values :m:`T`, :m:`F`, and :m:`N`. :m:`B3E`
is similar to :ref:`K3W <K3W>`, with a special Assertion operator, that always
results in a classical value (:m:`T` or :m:`F`).

.. contents:: :local:

.. automodule:: logics.b3e

    Semantics
    =========

    .. _b3e-model:

    .. autoclass:: Model

        .. autoclass:: logics.b3e::Model.Value()
            :members: F, N, T
            :undoc-members:
            :noindex:

        .. include:: include/fde/m.attributes.rst

        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//b3e//

            Note that the conditional operator :s:`$` is definable in terms of the
            assertion operator :s:`*`:
            
            .. cssclass:: definition
            
                :s:`A $ B` :math:`:=` :s:`~*A V *B` 

            Bochvar also defined `external` versions of :s:`&` and :s:`V`
            using the assertion operator:

            .. cssclass:: definiendum
            
            External Conjunction

            .. cssclass:: definiens

            :s:`A` :s:`&`:sub:`ext` :s:`B` :math:`:=` :s:`*A & *B`

            .. cssclass:: definiendum

            External Disjunction

            .. cssclass:: definiens

            :s:`A` :s:`V`:sub:`ext` :s:`B` :math:`:=` :s:`*A V *B`

            These connectives always result in a classical value. For compatibility,
            we use the standard `internal` readings of :s:`$` and :s:`V`,
            and use the `internal` reading for :s:`$` and :s:`%`.

        .. method:: value_of_predicated(sentence)

            :m:`B3E` predication is defined just as in :m:`K3`:

            .. include:: include/k3/m.predication.rst

        .. method:: value_of_existential(sentence)

            Existential quantification is defined just as in :m:`K3`:

            .. include:: include/k3/m.existential.rst

        .. method:: value_of_universal(sentence)

            Universal quantification is defined just as in :m:`K3`:

            .. include:: include/k3/m.existential.rst
        
    Logical Consequence
    -------------------

    Logical consequence is defined just like in :m:`K3`:
    
    .. include:: include/k3/m.consequence.rst

    Tableaux System
    ===============

    .. _b3e-system:

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. cssclass:: tableaux-rules

    .. autoclass:: TabRules
        :members:

    Notes
    =====

    * Unlike :ref:`K3W`, :m:`B3E` has some logical truths. For example
      :s:`(A $ B) V ~(A $ B)`. This logical truth is an instance of the
      Law of Excluded Middle.

    * The assertion operator can express alternate versions of validities that
      fail in :ref:`K3W`. For example, :s:`A` implies :s:`A V *B` in :m:`B3E`,
      which fails in :ref:`K3W`.

    * D. A. Bochvar published his paper in 1938. An English translation by Merrie
      Bergmann was published in 1981. *On a three-valued logical calculus and its
      application to the analysis of the paradoxes of the classical extended
      functional calculus.* History and Philosophy of Logic, 2(1-2):87-112, 1981.

    For further reading, see:

    * Rescher, N. (1969). Many-valued Logic. McGraw-Hill.

    * Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic
      <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.
