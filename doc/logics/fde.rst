.. _FDE:

***************************************
L{FDE} - First Degree Entailment
***************************************

L{FDE} is a 4-valued `relevance logic`_ logic with values V{T}, V{F}, V{N} and V{B}.

.. contents:: Contents
  :local:
  :depth: 2

------------------------

.. module:: pytableaux.logics.fde

.. _fde-semantics:
.. _fde-model:

Semantics
=========

.. _fde-truth-values:

Truth Values
------------

Common labels for the values include:

.. include:: include/fde/value-table.rst

.. rubric:: Designated Values

The set of *designated values* for L{FDE} is: { V{T}, V{B} }

.. _fde-truth-tables:

Truth Tables
------------

.. include:: include/truth_table_blurb.rst

.. truth-tables::
  :operators: Negation, Conjunction, Disjunction

.. rubric:: Defined Operators

.. include:: include/material_defines.rst

.. include:: include/material_tables.rst

.. rubric:: Compatibility Tables

L{FDE} does not have separate `Assertion` or `Conditional` operators,
but we include tables and rules for them, for cross-compatibility.

.. truth-tables::
  :include: non_native

.. _fde-predication:

Predication
-----------

.. include:: include/fde/predication.rst

Note, for L{FDE}, there is no *exclusivity* nor *exhaustion* constraint on a
predicate's extension and anti-extension. This means that !{ntuple} could
be in *neither* the extension nor the anti-extension of a predicate, or it
could be in *both* the extension and the anti-extension.

.. _fde-quantification:

Quantification
--------------

.. rubric:: Existential

.. include:: include/fde/m.existential.rst

.. rubric:: Universal

.. include:: include/fde/m.universal.rst

.. _fde-consequence:

Consequence
-----------

**Logical Consequence** is defined in terms of the set of *designated* values
V{T, B}:

.. include:: include/fde/m.consequence.rst

.. _fde-system:

Tableaux
========

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

A branch is **closed** iff the same sentence appears on both a designated node,
and undesignated node.

.. tableau-rules::
  :group: closure
  :titles:
  :legend:
  :docs:

This allows for both a sentence and its negation to appear as *designated*
on an open branch (or both as *undesignated*).

.. _fde-rules:

Rules
--------

.. include:: include/fde/rules_blurb.rst

.. tableau-rules::
  :docflags:
  :group: operator
  :exclude: non_native

.. tableau-rules::
  :docflags:
  :group: quantifier

.. tableau-rules::
  :docflags:
  :title: Compatibility Rules
  :group: operator
  :include: non_native


Notes
=====

Some notable features of L{FDE} include:

* No logical truths. The means that the :term:`Law of Excluded Middle` :s:`A V ~A`, and the
  :term:`Law of Non-Contradiction` :s:`~(A & ~A)` fail, as well as :term:`Conditional Identity`
  :s:`A $ A`.

* Failure of :term:`Modus Ponens`, :term:`Modus Tollens`, :term:`Disjunctive Syllogism`,
  and other Classical validities.

* :term:`DeMorgan laws` are valid, as well as :term:`Conditional Contraction` (:s:`A $ (A $ B)`
  !{conseq} :s:`A $ B`).

References
==========

* Beall, Jc, et al. `Possibilities and Paradox`_: An Introduction to Modal and
  Many-valued Logic. United Kingdom, Oxford University Press, 2003.

* Priest, Graham. `An Introduction to Non-Classical Logic`_: From If to Is.
  Cambridge University Press, 2008.

For futher reading see:

* Anderson, A., Belnap, N. D., et al. `Entailment`_: The Logic of Relevance and
  Necessity. United Kingdom, Princeton University Press, 1975.

* Belnap, N. D., McRobbie, M. A. `Relevant Analytic Tableaux`_.  Studia Logica,
  Vol. 38, No. 2, 1979.

* Stanford Encyclopedia on `Paraconsistent Logic`_ and `Relevance Logic`_.


.. _Paraconsistent Logic: http://plato.stanford.edu/entries/logic-paraconsistent/
.. _Relevance logic: https://plato.stanford.edu/entries/logic-relevance/
.. _Entailment: https://www.google.com/books/edition/_/8LRGswEACAAJ?hl=en
.. _An Introduction to Non-Classical Logic: https://www.google.com/books/edition/_/rMXVbmAw3YwC?hl=en
.. _Relevant Analytic Tableaux: http://www.pitt.edu/~belnap/77relevantanalytictableaux.pdf
.. _Possibilities and Paradox: https://www.google.com/books/edition/_/aLZvQgAACAAJ?hl=en


.. cssclass:: hidden

.. autoclass:: Rules()
    :members: