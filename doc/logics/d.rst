.. _D:

******************************
D - Deontic Normal Modal Logic
******************************

Deontic logic, also known as the Logic of Obligation, is an extension of :ref:`K <K>`, with
a *serial* accessibility relation, which states that for every world *w*, there is
a world *w'* such that *w* accesses *w'*.

.. contents:: :local:

.. automodule:: logics.d

    Semantics
    =========

    A D model uses :ref:`K Frames <k-frame>` to hold information about each world.

    .. autoclass:: logics.k.Frame
        :noindex:

        .. autoattribute:: world
            :noindex:

        .. autoattribute:: atomics
            :noindex:

        .. autoattribute:: extensions
            :noindex:

    .. class:: Model

        .. include:: include/k/m.attributes.rst

    Seriality
    ---------

    D adds a *serial* restriction on the access relation for models.

    .. cssclass:: definiendum smallcaps

    Seriality

    .. cssclass:: definiens

    In every model, for each world :m:`w`, there is *some world* :m:`w'` such
    that :m:`<w,w'>` is in the access relation.

    This is witnessed in the tableaux system through the :ref:`Serial Rule <serial-rule>`.

    Logical Consequence
    -------------------

    Logical Consequence is defined just as in :ref:`K <K>`:

    .. include:: include/k/m.consequence.rst

    Tableaux System
    ===============

    .. autoclass:: TableauxSystem
        :members: build_trunk

    .. autoclass:: TableauxRules
        :members:

    Notes
    -----

    .. rubric:: Further Reading

    * `Stanford Encyclopedia on Deontic Logic`_

.. _Stanford Encyclopedia on Deontic Logic: http://plato.stanford.edu/entries/logic-deontic/