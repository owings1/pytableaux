============================================
:mod:`pytableaux.lang` package
============================================

.. contents:: Contents
  :local:
  :depth: 3

.. module:: pytableaux.lang

Lexical Base Classes
********************

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
************************

Predicate
----------
.. autoclass:: Predicate
    :members:
    :exclude-members: Coords

Constant
----------

.. autoclass:: Constant()
    :show-inheritance:

Variable
----------

.. autoclass:: Variable()
    :show-inheritance:

Operator
---------

.. autoclass:: Operator()
    :members:
    :show-inheritance:

Quantifier
----------

.. autoclass:: Quantifier()
    :members:
    :show-inheritance:

Atomic
------

.. autoclass:: Atomic()
    :members:
    :special-members: __init__
    :show-inheritance:

Predicated
----------

.. autoclass:: Predicated
    :members:
    :special-members: __init__
    :show-inheritance:

Quantified
----------

.. autoclass:: Quantified
    :members:
    :special-members: __init__
    :show-inheritance:

Operated
---------

.. autoclass:: Operated()
    :members:
    :special-members: __init__
    :show-inheritance:

Collection Classes
*******************

Argument
---------

.. autoclass:: Argument

.. autoclass:: Predicates

Parser Classes
**************

.. autoclass:: Parser
    :members: __call__, argument

.. autoclass:: DefaultParser()

.. autoclass:: PolishParser()

.. autoclass:: StandardParser()

Writer Classes
***************

.. autoclass:: LexWriter
    :members: __call__

.. autoclass:: DefaultLexWriter()

.. autoclass:: PolishLexWriter()

.. autoclass:: StandardLexWriter()

Utility Classes
***************

.. autoclass:: LexType()
    :members:

.. autoclass:: ParseTable()

.. autoclass:: StringTable
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