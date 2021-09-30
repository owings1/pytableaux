************************
Python API
************************

The *logic* module is the base module for the Python API.

.. contents:: :local:

Core API
==========

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