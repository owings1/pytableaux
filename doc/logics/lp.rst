.. _LP:

*****************************
L{LP} - Logic of Paradox
*****************************

L{LP} is a 3-valued logic (V{T}, V{F}, and V{B}). It can be understood as
{@FDE} without the V{N} value.

.. contents:: :local:

.. automodule:: logics.lp

    Semantics
    =========

    .. _lp-model:

    Model
    -----

    .. autoclass:: Model

      .. autoclass:: logics.lp::Model.Value()
          :members: F, B, T
          :undoc-members:

      .. autoattribute:: designated_values

      .. autoattribute:: extensions

      .. autoattribute:: anti_extensions

      .. autoattribute:: atomics

    .. _lp-truth-tables:

    Truth Tables
    ------------

    .. include:: include/truth_table_blurb.rst

    .. inject:: truth_tables LP

    .. _lp-predication:

    Predication
    -----------

    A sentence with predicate `P` with parameters !{ntuple} is assigned a
    value as follows:

    * V{T} iff !{ntuple} is in the extension of `P` and not in the
      anti-extension of `P`.

    * V{F} iff !{ntuple} is in the anti-extension of `P` and not
      in the extension of `P`.

    * V{B} iff !{ntuple} is in both the extension and anti-extension
      of `P`.

    Note, unlike {@FDE}, there is an *exhaustion constraint* on a predicate's
    extension/anti-extension. This means that !{ntuple} must be in either the
    extension and the anti-extension of `P`. Like L{FDE}, there is no exclusion
    restraint.

    .. _lp-consequence:

    Consequence
    -----------

    **Logical Consequence** is defined, just as in {@FDE}, in terms of *designated*
    values V{T} and V{B}:

    * *C* is a **Logical Consequence** of *A* iff all models where *A* has a
      *desginated* value (V{T} or V{B}) are models where *C* also has a *designated*
      value.

    .. _lp-system:

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. _lp-rules:

    .. autoclass:: TabRules
        :members:

    Notes
    =====

    Some notable features of L{LP} include:

    * Everything valid in {@FDE} is valid in L{LP}.

    * Like {@FDE}, the Law of Non-Contradiction fails :s:`~(A & ~A)`.

    * Unlike {@FDE}, L{LP} has some logical truths. For example, the Law of Excluded
      Middle (:s:`(A V ~A)`), and Conditional Identity (:s:`(A $ A)`).

    * Many classical validities fail, such as Modus Ponens, Modus Tollens,
      and Disjunctive Syllogism.

    * DeMorgan laws are valid.

    References
    ==========
    
    * Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and
      Many-valued Logic. United Kingdom, Oxford University Press, 2003.

    For futher reading see:

    * `Stanford Encyclopedia entry on paraconsistent logic
      <http://plato.stanford.edu/entries/logic-paraconsistent/>`_

.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en