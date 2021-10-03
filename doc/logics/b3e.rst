.. _B3E:

*************************************
B3E - Bochvar 3-valued External Logic
*************************************

B3E is a three-valued logic with values :m:`T`, :m:`F`, and :m:`N`. B3E is similar
to :ref:`K3W`, with a special Assertion operator, that always results in a classical
value (:m:`T` or :m:`F`).

.. contents:: :local:

.. automodule:: logics.b3e

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Logical Consequence
    ===================

    **Logical Consequence** is defined just like in :ref:`CPL` and :ref:`K3`:

    * *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is :m:`T`
      are models where *C* also has the value :m:`T`.

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
