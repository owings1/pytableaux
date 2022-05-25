.. _GO:

***********************
GO - Gappy Object Logic
***********************

GO is a 3-valued logic (V{T}, V{F}, and V{N}) with non-standard readings of
disjunction and conjunction, as well as different behavior of the quantifiers.

.. contents:: :local:

.. automodule:: pytableaux.logics.go

    Semantics
    =========

    .. autoclass:: Model

        .. autoclass:: pytableaux.logics.go::Model.Value()
            :members: F, N, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst

        .. method:: truth_function(operator, a, b)

              The value of a sentence with a truth-functional operator is determined
              by the values of its operands according to the following tables.

              .. truth-tables::

              Note that, given the tables above, conjunctions and disjunctions
              always have a classical value (V{T} or V{F}). This means that
              only atomic sentences (with zero or more negations) can have the
              non-classical V{N} value.

              This property of "classical containment" means, that we can define
              a conditional operator that satisfies Identity :s:`A $ A`. It also
              allows us to give a formal description of a subset of sentences
              that obey all principles of classical logic. For example, although
              the Law of Excluded Middle fails for atomic sentences :s:`A V ~A`,
              complex sentences -- those with at least one binary connective --
              do obey the law: :s:`(A V A) V ~(A V A)`.

        .. automethod:: value_of_existential(sentence)

        .. automethod:: value_of_universal(sentence)

    Consequence
    -----------

    Logical consequence is defined just like in L{K3}:
    
    .. include:: include/k3/m.consequence.rst

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. cssclass:: tableauxrules

    .. autoclass:: TabRules
        :members:

    Notes
    -----

    - GO has some similarities to L{K3}. Material Identity :s:`A $ A` and the
      Law of Excluded Middle :s:`A V ~A` fail.

    - Unlike L{K3}, there are logical truths, e.g. The Law of Non-Contradiction
      :s:`~(A & ~A)`.

    - GO contains an additional conditional operator besides the material conditional,
      which is similar to L{L3}. However, this conditional is *non-primitive*,
      unlike L{L3}, and it obeys contraction (:s:`A $ (A $ B)` implies :s:`A $ B`).

    .. rubric:: Further Reading

    - Doug Owings (2012). `Indeterminacy and Logical Atoms`_. *Ph.D. Thesis, University
      of Connecticut*.

    - `Colin Caret`_. (2017). `Hybridized Paracomplete and Paraconsistent Logics`_.
      *The Australasian  Journal of Logic*, 14.

.. _Professor Jc Beall: http://entailments.net
.. _Colin Caret: https://sites.google.com/view/colincaret
.. _Indeterminacy and Logical Atoms: https://github.com/owings1/dissertation/raw/master/output/dissertation.pdf
.. _Hybridized Paracomplete and Paraconsistent Logics: https://ojs.victoria.ac.nz/ajl/article/view/4035/3588