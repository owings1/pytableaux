***************
Tableaux Module
***************

.. contents:: :local:

.. automodule:: proof.tableaux

    .. autoclass:: Tableau

        .. autoattribute:: argument

        .. autoattribute:: completed

        .. autoattribute:: current_step

        .. autoattribute:: finished

        .. autoattribute:: history

        .. autoattribute:: id

        .. autoattribute:: invalid

        .. autoattribute:: logic

        .. autoattribute:: premature

        .. autoattribute:: open

        .. autoattribute:: tree

        .. autoattribute:: trunk_built

        .. autoattribute:: valid

        .. automethod:: build()

        .. automethod:: step

        .. automethod:: branch

        .. automethod:: add

        .. automethod:: get_rule

        .. automethod:: closure_rules

        .. automethod:: add_closure_rule

        .. automethod:: add_rule_group

        .. automethod:: clear_rules
        
        .. automethod:: build_trunk

    .. autoclass:: Branch

    .. autoclass:: Node

    .. autoclass:: TableauxSystem