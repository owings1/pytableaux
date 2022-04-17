.. _K3W:

**********************************
L{K3W} - Weak Kleene Logic
**********************************

L{K3W} is a 3-valued logic with values V{T}, V{F}, and V{N}. The logic is
similar to {@K3}, but with slightly different behavior of the V{N} value.
This logic is also known as Bochvar Internal (L{B3}). A common interpretation of
these values is:

- V{T}: just true
- V{F}: just false
- V{N}: meaningless (or senseless)

.. contents:: :local:

.. automodule:: pytableaux.logics.k3w

    Semantics
    =========

    .. _k3w-model:

    .. autoclass:: Model

        .. autoclass:: pytableaux.logics.k3w::Model.Value()
            :members: F, N, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst
        
        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            .. truth-tables:: k3w

            Note that, for the binary connectives, if either operand has the value V{N},
            then the whole sentence has the value V{N}. To (re-)quote a Chinese proverb,
            "a single jot of rat's dung spoils the soup."

        .. method:: value_of_predicated(sentence)

            Predication is the same as :ref:`K3 <k3-model>`, defined in terms of a
            predicate's *extenstion* and *anti-extension*.

            .. include:: include/k3/m.predication.rst

        .. method:: value_of_existential(sentence)

            Existential quantification is defined just as in :ref:`K3 <k3-model>`:

            .. include:: include/k3/m.existential.rst

        .. method:: value_of_universal(sentence)

            Universal quantification is defined just as in :ref:`K3 <k3-model>`:

            .. include:: include/k3/m.existential.rst

        .. Note:: For an alternate interpretation of the quantifiers in L{K3W}, see
            :ref:`K3WQ <k3wq-model>`. There we apply the notion of *generalized*
            conjunction and disjunction to :s:`L` and :s:`X`.


    Consequence
    -----------

    Logical consequence is defined just like in L{K3}:
    
    .. include:: include/k3/m.consequence.rst

    .. _k3w-system:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:

    Notes
    -----

    Addition fails in L{K3W}. That is :s:`A` does not imply :s:`A V B`.

    For further reading, see:

    * Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.
