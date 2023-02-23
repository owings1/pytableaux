==============================================
:mod:`pytableaux.lang.lex` 
==============================================

.. module:: pytableaux.lang.lex

.. contents:: Contents
    :local:

Base classes
==============

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


Concrete classes
=================

.. autoclass:: Predicate
    :members:
    :exclude-members: Coords

.. autoclass:: Constant()
    :show-inheritance:

.. autoclass:: Variable()
    :show-inheritance:

Enum classes
------------

.. autoclass:: Quantifier()
    :members:
    :show-inheritance:

.. autoclass:: Operator()
    :members:
    :show-inheritance:

Sentence classes
----------------

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


Special classes
=================

.. autoclass:: LexType()
    :members:
    :special-members: __init__

