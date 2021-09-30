*************************************
B3E - Bochvar 3-valued External Logic
*************************************

B3E is a three-valued logic with values **T**, **F**, and **N**. B3E is similar
to `K3W`_, with a special Assertion operator, that always results in a classical
value (**T** or **F**).

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

    **Logical Consequence** is defined just like in `CPL`_ and `K3`_:

    * *C* is a **Logical Consequence** of *A* iff all models where the value of *A* is **T**
      are models where *C* also has the value **T**.

    Notes
    =====

    * Unlike `K3W`_, B3E has some logical truths. For example :s:`(A $ B) V ~(A $ B)`.
      This logical truth is an instance of the Law of Excluded Middle.

    * The assertion operator can expression alternate versions of validities that
      fail in `K3W`_. For example, :s:`A` implies :s:`A V *B` in B3E, which fails in
      `K3W`_.

    * D. A. Bochvar published his paper in 1938. An English translation by Merrie
      Bergmann was published in 1981. *On a three-valued logical calculus and its
      application to the analysis of the paradoxes of the classical extended
      functional calculus.* History and Philosophy of Logic, 2(1-2):87–112, 1981.

    For further reading, see:

    * Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.

.. _CPL: cpl.html
.. _K3: k3.html
.. _K3W: k3w.html