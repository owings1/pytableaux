.. _K3W:

****************************
:m:`K3W` - Weak Kleene Logic
****************************

:m:`K3W` is a 3-valued logic with values :m:`T`, :m:`F`, and :m:`N`. The logic is
similar to :ref:`K3 <K3>`, but with slightly different behavior of the :m:`N` value.
This logic is also known as Bochvar Internal (:m:`B3`). A common interpretation of
these values is:

- :m:`T`: just true
- :m:`F`: just false
- :m:`N`: meaningless (or senseless)

.. contents:: :local:

.. automodule:: logics.k3w

    Semantics
    =========

    .. _k3w-model:

    .. autoclass:: Model

        .. autoclass:: logics.k3w::Model.Value()
            :members: F, N, T
            :undoc-members:

        .. include:: include/fde/m.attributes.rst
        
        .. method:: truth_function(operator, a, b)

            The value of a sentence with a truth-functional operator is determined by
            the values of its operands according to the following tables.

            //truth_tables//k3w//

            Note that, for the binary connectives, if either operand has the value :m:`N`,
            then the whole sentence has the value :m:`N`. To (re-)quote a Chinese proverb,
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

        .. Note:: For an alternate interpretation of the quantifiers in :m:`K3W`, see
            :ref:`K3WQ <k3wq-model>`. There we apply the notion of *generalized*
            conjunction and disjunction to :s:`L` and :s:`X`.


    Logical Consequence
    -------------------

    Logical consequence is defined just like in :m:`K3`:
    
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

    Addition fails in :m:`K3W`. That is :s:`A` does not imply :s:`A V B`.

    For further reading, see:

    * Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.
