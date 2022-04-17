.. _B3E:

*************************************************
L{B3E} - Bochvar 3-valued External Logic
*************************************************

L{B3E} is a three-valued logic with values V{T}, V{F}, and V{N}. L{B3E}
is similar to :ref:`K3W <K3W>`, with a special Assertion operator, that
always results in a classical value (V{T} or V{F}).

.. contents:: :local:

.. automodule:: pytableaux.logics.b3e

    Semantics
    =========

    .. _b3e-model:

    .. autoclass:: Model

      .. autoclass:: pytableaux.logics.b3e::Model.Value()
          :members: F, N, T
          :undoc-members:
          :noindex:

      .. include:: include/fde/m.attributes.rst

    .. _b3e-truth-tables:

    Truth Tables
    ------------

    .. include:: include/truth_table_blurb.rst

    .. truth-tables:: B3E

    Note that the Conditional operator :s:`$` is definable in terms of
    the Assertion operator :s:`*`:
    
    .. cssclass:: definition
    
      :s:`A $ B` :math:`:=` :s:`~*A V *B`

    .. _b3e-external-connectives:

    External Connectives
    --------------------

    Bochvar also defined `external` versions of :s:`&` and :s:`V`
    using :s:`*`:

    .. cssclass:: definiendum
    
    External Conjunction

    .. cssclass:: definiens

    :s:`A` :s:`&`:sub:`ext` :s:`B` :math:`:=` :s:`*A & *B`

    .. cssclass:: definiendum

    External Disjunction

    .. cssclass:: definiens

    :s:`A` :s:`V`:sub:`ext` :s:`B` :math:`:=` :s:`*A V *B`

    These connectives always result in a classical value (V{T} or V{F}).
    For compatibility, we use the standard `internal` readings of :s:`$`
    and :s:`V`, and use the `internal` reading for :s:`$` and :s:`%`.

    .. _b3e-predication:

    Predication
    -----------

    L{B3E} predication is defined just as in L{K3}:

    .. include:: include/k3/m.predication.rst

    .. _b3e-quantification:

    Quantification
    --------------

    The quantifiers :s:`X` and :s:`L` are interpreted just as in L{K3}.

    Existential
    ^^^^^^^^^^^

    .. include:: include/k3/m.existential.rst

    Universal
    ^^^^^^^^^

    .. include:: include/k3/m.universal.rst

    .. _b3e-consequence:
        
    Consequence
    -----------

    Logical consequence is defined just like in L{K3}:
    
    .. include:: include/k3/m.consequence.rst

    .. _b3e-system:

    Tableaux
    ========

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. _b3e-rules:

    Rules
    -----

    .. cssclass:: tableaux-rules

    .. autoclass:: TabRules
        :members:

    Notes
    =====

    * Unlike L{K3W}, L{B3E} has some logical truths. For example
      :s:`(A $ B) V ~(A $ B)`. This logical truth is an instance of the
      Law of Excluded Middle.

    * The Assertion operator :s:`*` can express alternate versions of validities
      that fail in L{K3W}. For example, :s:`A` implies :s:`A V *B` in L{B3E},
      which fails in L{K3W}.

    * D. A. Bochvar published his paper in 1938. An English translation by Merrie
      Bergmann was published in 1981. *On a three-valued logical calculus and its
      application to the analysis of the paradoxes of the classical extended
      functional calculus.* History and Philosophy of Logic, 2(1-2):87-112, 1981.

    For further reading, see:

    * Rescher, N. (1969). Many-valued Logic. McGraw-Hill.

    * Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic
      <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.
