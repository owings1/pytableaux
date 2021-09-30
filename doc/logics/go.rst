***********************
GO - Gappy Object Logic
***********************

GO is a 3-valued logic (**T**, **F**, and **N**) with non-standard readings of
disjunction and conjunction, as well as different behavior of the quantifiers.

.. contents:: :local:

.. automodule:: logics.go

    Semantics
    =========

    .. autoclass:: Model

        .. automethod:: value_of_operated(sentence)

        .. automethod:: value_of_existential(sentence)

        .. automethod:: value_of_universal(sentence)

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

    - GO has some similarities to `K3`_. Material Identity :s:`A $ A` and the
      Law of Excluded Middle :s:`A V ~A` fail.

    - Unlike `K3`_, there are logical truths, e.g. The Law of Non Contradiction :s:`~(A & ~A)`.

    - GO contains an additional conditional operator besides the material conditional,
      which is similar to `L3`_. However, this conditional is *non-primitive*, unlike `L3`_,
      and it obeys contraction (:s:`A $ (A $ B)` implies :s:`A $ B`).

    - This logic was developed as part of this author's dissertation, `Indeterminacy and Logical Atoms`_
      at the University of Connecticut, under `Professor Jc Beall`_.


    Further Reading
    ===============

    - Doug Owings (2012). `Indeterminacy and Logical Atoms`_. *Ph.D. Thesis, University of Connecticut*.

    - `Colin Caret`_. (2017). `Hybridized Paracomplete and Paraconsistent Logics`_. *The Australasian 
      Journal of Logic*, 14.

.. _Professor Jc Beall: http://entailments.net
.. _Colin Caret: https://sites.google.com/view/colincaret
.. _Indeterminacy and Logical Atoms: https://github.com/owings1/dissertation/raw/master/output/dissertation.pdf
.. _K3: k3.html
.. _K3 Predication: k3.html#predication
.. _L3: l3.html
.. _B3E: b3e.html
.. _FDE: fde.html
.. _CPL: cpl.html
.. _Hybridized Paracomplete and Paraconsistent Logics: https://ojs.victoria.ac.nz/ajl/article/view/4035/3588