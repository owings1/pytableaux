==============================================
:mod:`pytableaux.lang.lex` — Lexical classes
==============================================

.. module:: pytableaux.lang.lex

.. contents:: Contents
    :local:

Base classes
==============

.. autoclass:: Lexical()
    :members:
    :special-members: __delattr__

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
    :special-members: __init__
    :exclude-members: Coords


.. autoclass:: Constant()
    :members:
    :special-members: __init__
    :show-inheritance:


.. autoclass:: Variable()
    :members:
    :special-members: __init__
    :show-inheritance:

Enum classes
------------

.. autoclass:: Quantifier()
    :members:
    :special-members: __init__
    :show-inheritance:


.. autoclass:: Operator()
    :members:
    :special-members: __init__
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

