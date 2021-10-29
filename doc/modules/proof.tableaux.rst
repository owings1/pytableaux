***************
Tableaux Module
***************

.. contents:: :local:

.. automodule:: proof.tableaux

    .. autoclass:: Tableau

        .. autoattribute:: argument

        .. autoattribute:: branch_count

        .. autoattribute:: completed

        .. autoattribute:: current_step

        .. autoattribute:: finished

        .. autoattribute:: history

        .. autoattribute:: id

        .. autoattribute:: invalid

        .. autoattribute:: logic

        .. autoattribute:: open_branch_count

        .. autoattribute:: premature

        .. autoattribute:: tree

        .. autoattribute:: trunk_built

        .. autoattribute:: valid

        .. automethod:: build()

        .. automethod:: step

        .. automethod:: branches

        .. automethod:: open_branches

        .. automethod:: get_branch

        .. automethod:: get_branch_at

        .. automethod:: branch

        .. automethod:: add_branch

        .. automethod:: get_rule

        .. automethod:: closure_rules

        .. automethod:: add_closure_rule

        .. automethod:: add_rule_group

        .. automethod:: clear_rules
        
        .. automethod:: build_trunk

    .. autoclass:: Branch

    .. autoclass:: Node

    .. autoclass:: TableauxSystem