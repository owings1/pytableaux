.. _GO:

***********************
GO - Gappy Object Logic
***********************

GO is a 3-valued logic with values V{T}, V{F}, and V{N}. It has non-standard readings of
disjunction and conjunction, as well as different behavior of the quantifiers.


.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.go

.. _go-semantics:
.. _go-model:

Semantics
=========

.. _go-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/k3/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{GO} is the singleton: { V{T} }

.. _go-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

An `Assertion` :s:`*` operator is definable in terms of :s:`&`:

.. sentence::

  *A := A & A

.. truth-tables::
  :operators: Assertion

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

The `Conditional` :s:`$` is definable as follows:

.. sentence::

  A $ B := (A > B) V (~(A V ~A) & ~(B V ~B))

This can be read as: either :s:`A > B` or both :s:`A` and :s:`B` are
`gappy` (i.e. have the value T{N}).

.. include:: include/bicond_define.rst

.. truth-tables::
  :operators: Conditional, Biconditional

.. _go-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

.. _go-quantification:

Quantification
--------------

For quantification, we introduce a `crunch` function:

.. include:: include/go/crunch.rst

.. rubric:: Existential

.. include:: include/go/m.existential.rst

.. rubric:: Universal

.. include:: include/go/m.universal.rst

.. _go-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T} }:

.. include:: include/fde/m.consequence.rst

.. _go-system:

Tableaux
========

L{GO} tableaux are built similary to L{FDE}.

Nodes
-----

.. include:: include/fde/nodes_blurb.rst

Trunk
-----

.. include:: include/fde/trunk_blurb.rst

.. tableau::
  :build-trunk:
  :prolog:

Closure
-------

.. tableau-rules::
  :group: closure
  :titles:
  :legend:
  :docs:

Rules
-----

.. include:: include/fde/rules_blurb.rst

.. tableau-rules::
  :docflags:
  :group: operator

.. tableau-rules::
  :docflags:
  :group: quantifier


Notes
=====

- GO has some similarities to L{K3}. :term:`Material Identity` :s:`A > A` and the
  :term:`Law of Excluded Middle` :s:`A V ~A` fail.

- Unlike L{K3}, there are logical truths, e.g. the :term:`Law of Non-Contradiction`
  :s:`~(A & ~A)`.

- GO contains an additional conditional operator besides the material conditional,
  which is similar to L{L3}. However, this conditional is *non-primitive*,
  unlike L{L3}, and it obeys contraction (:s:`A $ (A $ B)` !{conseq} :s:`A $ B`).

- Conjunctions and Disjunctions always have a classical value (V{T} or V{F}).
  This means that only atomic sentences (with zero or more negations) can have
  the non-classical V{N} value.

  This property of "classical containment" means that we can define
  a conditional operator that satisfies :term:`Conditional Identity` :s:`A $ A`.
  It also allows us to give a formal description of a subset of sentences
  that obey all principles of classical logic. For example, although
  the :term:`Law of Excluded Middle` fails for atomic sentences :s:`A V ~A`,
  complex sentences -- those with at least one binary connective --
  do obey the law: !{conseq} :s:`(A V A) V ~(A V A)`.

References
==========

- Doug Owings (2012). `Indeterminacy and Logical Atoms`_. *Ph.D. Thesis, University
  of Connecticut*.

.. rubric:: Further Reading

- `Colin Caret`_. (2017). `Hybridized Paracomplete and Paraconsistent Logics`_.
  *The Australasian  Journal of Logic*, 14.

.. _Professor Jc Beall: http://entailments.net
.. _Colin Caret: https://sites.google.com/view/colincaret
.. _Indeterminacy and Logical Atoms: https://github.com/owings1/dissertation/raw/master/output/dissertation.pdf
.. _Hybridized Paracomplete and Paraconsistent Logics: https://ojs.victoria.ac.nz/ajl/article/view/4035/3588

.. cssclass:: hidden

.. autoclass:: Rules()
    :members: