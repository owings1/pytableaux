.. _T:

********************************
T - Reflexive Normal Modal Logic
********************************

Reflexive Modal Logic is an extension of :ref:`K <K>`, with a *reflexive*
accessibility relation, which states that for every world *w*,
*w* accesses *w* (itself).

.. contents:: :local:

.. automodule:: logics.t

    Semantics
    =========

    A T model uses :ref:`K Frames <k-frame>` to hold information about each world.

    .. autoclass:: logics.k.Frame
        :noindex:

        .. autoattribute:: world
            :noindex:

        .. autoattribute:: atomics
            :noindex:

        .. autoattribute:: extensions
            :noindex:

    .. autoclass:: Model

        .. autoclass:: logics.t::Model.Value()
            :members: F, T
            :undoc-members:

        .. include:: include/k/m.attributes.rst

    Reflexivity
    -----------

    T adds a *reflexivity* restriction on the access relation for models.

    .. include:: include/t/m.reflexivity.rst

    This is witnessed in the tableaux system through the :ref:`Reflexive Rule <reflexive-rule>`.

    Consequence
    -----------

    Logical Consequence is defined just as in :ref:`K <K>`:

    .. include:: include/k/m.consequence.rst

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TabRules
        :members:
