============================================
:mod:`pytableaux.lang`
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
  :members: arity
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

.. autoclass:: Argument()
  :members:
  :special-members: __init__
  :exclude-members: for_json

Predicates
----------

.. autoclass:: Predicates()
  :members: get
  :show-inheritance:
  :special-members: __init__

Parser Classes
**************

Parser
------

.. autoclass:: Parser
  :members: __call__, argument

.. autoclass:: DefaultParser()
  :show-inheritance:

.. autoclass:: PolishParser()
  :show-inheritance:

.. autoclass:: StandardParser()
  :show-inheritance:

Writer Classes
***************

LexWriter
---------

.. autoclass:: LexWriter
  :members: __call__, canwrite

.. autoclass:: PolishLexWriter()
  :show-inheritance:

.. autoclass:: StandardLexWriter()
  :show-inheritance:

Utility Classes
***************

.. autoclass:: LexType()
  :members:

.. autoclass:: ParseTable()
  :members:
  :show-inheritance:

.. autoclass:: StringTable
  :members:
  :show-inheritance:

.. autoclass:: Notation
  :members: formats, writers, DefaultWriter, Parser, get_common_formats

.. autoclass:: Marking

.. autoclass:: BiCoords
  :members:

.. autoclass:: TriCoords
  :members: