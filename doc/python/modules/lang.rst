============================================
:mod:`pytableaux.lang` package
============================================

.. contents:: Contents
  :local:
  :depth: 2

.. module:: pytableaux.lang

Lexical Base Classes
====================

.. autoclass:: Lexical()
    :members:
    :exclude-members: identitem, hashitem, for_json

.. autoclass:: LexicalEnum()
    :members:
    :show-inheritance:

.. autoclass:: CoordsItem()
    :members:
    :exclude-members: Coords

.. autoclass:: Parameter()
    :members:
    :show-inheritance:

.. autoclass:: Sentence()
    :members:
    :show-inheritance:


Concrete Lexical Classes
========================

.. autoclass:: Predicate
    :members:
    :exclude-members: Coords

.. autoclass:: Constant()
    :show-inheritance:

.. autoclass:: Variable()
    :show-inheritance:

Enum types
----------

.. autoclass:: Quantifier()
    :members:
    :show-inheritance:

.. autoclass:: Operator()
    :members:
    :show-inheritance:

Sentence types
--------------

.. autoclass:: Atomic()
    :members:
    :special-members: __init__
    :show-inheritance:

.. autoclass:: Predicated
    :members:
    :special-members: __init__
    :show-inheritance:


.. autoclass:: Quantified
    :members:
    :special-members: __init__
    :show-inheritance:


.. autoclass:: Operated()
    :members:
    :special-members: __init__
    :show-inheritance:


Collection Classes
==================

.. autoclass:: Argument

.. autoclass:: Predicates


Parser Classes
==============

.. autoclass:: Parser
    :members: __call__, argument

.. autoclass:: DefaultParser()

.. autoclass:: PolishParser()

.. autoclass:: StandardParser()


Writer Classes
==============

.. autoclass:: LexWriter
    :members: __call__

.. autoclass:: DefaultLexWriter()

.. autoclass:: PolishLexWriter()

.. autoclass:: StandardLexWriter()


Utility Classes
===============

.. autoclass:: LexType()
    :members:


.. autoclass:: TableStore
    :members:

.. autoclass:: ParseTable()

.. autoclass:: RenderSet
    :members:
    :show-inheritance:
    :inherited-members: Mapping

.. autoclass:: Notation
    :members:

.. autoclass:: Marking
    :members:

.. autoclass:: BiCoords
    :members:

.. autoclass:: TriCoords
    :members: