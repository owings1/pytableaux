.. _B3E:

*************************************************
L{B3E} - Bochvar 3-valued External Logic
*************************************************

.. figure:: /res/img/Dmitry_Anatolevich_Bochvar.jpg
    :alt: Photo of Dmitry Bochvar
    :align: right
    :scale: 50 %
    :target: https://ineos.ac.ru/images/stories/oldschool/bochvar.jpg

    Dmitry Bochvar

L{B3E} is a three-valued logic with values V{T}, V{F}, and V{N}. L{B3E}
is similar to {@K3W}, but with a special Assertion operator that
always results in a classical value (V{T} or V{F}).

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.b3e

.. _b3e-semantics:
.. _b3e-model:

Semantics
=========

.. _b3e-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/k3w/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{B3E} is the singleton: { V{T} }

.. _b3e-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Assertion, Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

The Conditional operator :s:`$` is definable in terms of
the Assertion operator :s:`*`:

.. sentence::

  A $ B := ~*A V *B

.. truth-tables::
  :operators: Conditional, Biconditional

.. include:: include/material_defines.rst

.. truth-tables::
  :operators: MaterialConditional, MaterialBiconditional

.. _b3e-external-connectives:

.. rubric:: External Connectives

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
For compatibility, we use the standard `internal` readings of :s:`&`
and :s:`V`, and use the `external` reading for :s:`$` and :s:`%`.

.. _b3e-predication:

Predication
-----------

.. include:: include/k3/m.predication.rst

.. _b3e-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/fde/m.existential.rst

.. rubric:: Universal

.. include:: include/fde/m.universal.rst

.. _b3e-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
{ V{T} }:

.. include:: include/fde/m.consequence.rst

.. _b3e-system:

Tableaux
========

L{B3E} tableaux are built similary to L{FDE}.

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

.. _b3e-rules:

Rules
--------

.. cssclass:: hidden

  .. class:: TabRules()

.. include:: include/fde/rules_blurb.rst

.. tableau-rules::
  :docflags:
  :group: operator

.. tableau-rules::
  :docflags:
  :group: quantifier

Notes
=====

* Unlike L{K3W}, L{B3E} has some logical truths. For example
  :s:`(A $ B) V ~(A $ B)`. This logical truth is an instance of the
  Law of Excluded Middle.

* The Assertion operator :s:`*` can express alternate versions of validities
  that fail in L{K3W}. For example, :s:`A` !{conseq} :s:`A V *B` in L{B3E},
  which fails in L{K3W}.

References
==========

* D. A. Bochvar published his paper in 1938. An English translation by Merrie
  Bergmann was published in 1981. *On a three-valued logical calculus and its
  application to the analysis of the paradoxes of the classical extended
  functional calculus.* History and Philosophy of Logic, 2(1-2):87-112, 1981.

For further reading, see:

* Rescher, N. (1969). Many-valued Logic. McGraw-Hill.

* Beall, Jc `Off-topic: a new interpretation of Weak Kleene logic
  <http://entailments.net/papers/beall-ajl-wk3-interp.pdf>`_. 2016.
