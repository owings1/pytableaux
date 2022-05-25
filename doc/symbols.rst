.. include:: /_inc/note-doc-stub.rsti

***************
Lexical Tables
***************

.. contents:: :local:

.. _operators-table:

Symbols Sets
==============

.. csv-table::
    :header-rows: 4
    :widths: auto
    :generator: oper-sym-table


.. _lexical-item-specs-table:

Python attributes
==================

Comparison of some attributes that are shared across all
lexical types.

Comparison across types is aided by some shared creation
methods like ``.first()``, as well a the ``LexType`` class,
which contains bookkeeping information such as a list of
all lexical classes. For example, we can examine the
``spec`` attribute for an item of each lexical type with
this code::

    rows = [
        (item, item.spec)
        for item in (
            member.cls.first()
            for member in LexType
        )
    ]


spec
-----

A ``spec`` is a tuple built from integers, strings. These
can nest to become complex, but only with tuples built
from integers and strings, and so on. The spec should
contain all the information to recreate the object, so
long as you know its original type.

.. csv-table::
    :header-rows: 1
    :widths: auto
    :generator: lex-eg-table
    :generator-args: spec
    :classes: lex-eg-table flex-last spec-table

.. _lexical-item-idents-table:


ident
-------

The ``ident`` attribute is similar to ``spec``, but also
contains the `type` information. This an ``ident`` attribute
is just a `2tuple`, or `ordered pair` of the type name, and
the spec.

.. csv-table::
    :header-rows: 1
    :widths: auto
    :generator: lex-eg-table
    :generator-args: ident
    :classes: lex-eg-table flex-last ident-table

.. _lexical-item-sort_tuple-table:

sort tuple
----------

A ``sort_tuple`` is a flat tuple of integers that encodes
less information overall, but should still be unique for 
distinct items. It might not contain enough information to
recreate an object, but provides a conenient method of comparing,
sorting, and hash items. The works across different types,
for example between a `predicate` and a `quantifier`, without
the risk of confusing one for the other.

.. csv-table::
    :header-rows: 1
    :widths: auto
    :generator: lex-eg-table
    :generator-args: sort_tuple
    :classes: lex-eg-table flex-last sort-tuple-table

