.. include:: /_inc/attn-doc-freewheel.rsti

***************
Tableaux Module
***************

.. contents:: :local:

.. automodule:: pytableaux.proof.tableaux

    .. autoclass:: Tableau

        .. autoattribute:: argument

        .. autoattribute:: logic

        .. autoattribute:: finished

        .. autoattribute:: valid

        .. autoattribute:: invalid

        .. autoattribute:: completed

        .. autoattribute:: premature

        .. autoattribute:: id

        .. autoattribute:: history

        .. autoattribute:: rules

        .. autoattribute:: open

        .. autoattribute:: tree

        .. automethod:: build

        .. automethod:: step

        .. automethod:: branch

        .. automethod:: add

        .. automethod:: finish

    .. autoclass:: TreeStruct
        :members:

    .. autoclass:: Rule

    .. autoclass:: ClosingRule

    .. autoclass:: TabRules
    
    .. autoclass:: RuleGroups
    
    .. autoclass:: RuleGroup

    .. autoclass:: TableauxSystem
        :members: