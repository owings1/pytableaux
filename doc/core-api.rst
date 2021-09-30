************************
Core API
************************

.. contents:: :local:

The core API provides high-level methods for basic usage, with convience
wrappers for nested classes, that encapsulates things like parsing
sentences and building proofs for difference logics.

.. automodule:: logic

    Basic Usage
    -----------

    .. autoclass:: Argument

    .. autofunction:: tableau

    .. autofunction:: parse

    .. autofunction:: render

    Sentence Construction
    ---------------------

    .. autofunction:: atomic

    .. autofunction:: constant

    .. autofunction:: predicated

    .. autofunction:: variable

    .. autofunction:: quantify

    .. autofunction:: operate

    .. autofunction:: negate

    .. autofunction:: assertion

    .. autofunction:: negative

    Type Inspection
    ---------------

    .. autofunction:: is_constant

    .. autofunction:: is_variable

    .. autofunction:: is_predicate

    .. autofunction:: arity

    Utilities
    ---------

    .. autofunction:: create_parser

    .. autofunction:: get_logic

    .. autofunction:: get_system_predicate