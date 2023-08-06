# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.proof.writers.nodes
==============================

"""
from __future__ import annotations

from ... import proof
from ...lang import Sentence
from .. import Access, Tableau
from . import elements

__all__ = (
    'access',
    'child_wrapper',
    'clear',
    'designation',
    'document',
    'ellipsis',
    'flag',
    'horizontal_line',
    'node_props',
    'node_segment',
    'node',
    'sentence',
    'tree',
    'vertical_line',
    'world')

class document(elements.Element):

    @property
    def document(self):
        return self

class clear(elements.Block):
    pass

class ellipsis(elements.Inline):
    pass

class vertical_line(elements.Block):

    @classmethod
    def for_object(cls, step: int, /):
        return cls(**{'data-step': step})

class horizontal_line(elements.Block):

    @classmethod
    def for_object(cls, tree: Tableau.Tree, /):
        return cls(**dict(cls.get_obj_attributes(tree)))

    @classmethod
    def get_obj_attributes(cls, tree: Tableau.Tree, /):
        yield 'data-step', tree.branch_step
        width = 100 * tree.balanced_line_width
        margin_left = 100 * tree.balanced_line_margin
        yield 'style', _styleattr(
            width=_pctstr(width),
            margin_left=_pctstr(margin_left))

class child_wrapper(elements.Block):

    @classmethod
    def for_objects(cls, tree: Tableau.Tree, child: Tableau.Tree, /):
        return cls(**dict(cls.get_objs_attributes(tree, child)))

    @classmethod
    def get_objs_attributes(cls, tree: Tableau.Tree, child: Tableau.Tree, /):
        width = (100 / tree.width) * child.width
        yield 'data-step', child.step
        yield 'data-current-width-pct', _pctstr(width)
        yield 'style', _styleattr(width=_pctstr(width))

class tree(elements.Block):

    default_classes = ['structure']

    data_attrnames = (
        'depth',
        'width',
        'left',
        'right',
        'step')

    flag_classnames = (
        'has_open',
        'has_closed',
        'leaf',
        'open',
        'closed',
        'is_only_branch')

    @classmethod
    def for_object(cls, tree: Tableau.Tree, /):
        return cls(
            id=f'structure_{tree.id}',
            classes=cls.get_obj_classes(tree),
            **dict(cls.get_obj_attributes(tree)))

    @classmethod
    def get_obj_attributes(cls, tree: Tableau.Tree, /):
        for name in cls.data_attrnames:
            yield f'data-{name}', tree[name]
        if tree.closed:
            yield 'data-closed-step', tree.closed_step
        if tree.branch_id:
            yield 'data-branch-id', tree.branch_id
        if tree.model_id:
            yield 'data-model-id', tree.model_id
        
    @classmethod
    def get_obj_classes(cls, tree: Tableau.Tree, /):
        if tree.root:
            yield 'root'
        yield from filter(tree.get, cls.flag_classnames)

class node(elements.Block):

    @classmethod
    def for_objects(cls, node: proof.Node, tickstep: int, /):
        return cls(
            *cls.get_obj_inner_nodes(node),
            id=f'node_{node.id}',
            classes=cls.get_obj_classes(node),
            **dict(cls.get_objs_attributes(node, tickstep)))

    @classmethod
    def get_objs_attributes(cls, node: proof.Node, tickstep: int, /):
        yield 'data-node-id', node.id
        yield 'data-step', node.step
        if getattr(node, 'ticked', False):
            yield 'data-ticked-step', tickstep

    @classmethod
    def get_obj_classes(cls, node: proof.Node, /):
        if getattr(node, 'ticked', False):
            yield 'ticked'

    @classmethod
    def get_obj_inner_nodes(cls, node: proof.Node, /):
        yield node_props.for_object(node)

class node_segment(elements.Block):

    @classmethod
    def for_object(cls, tree: Tableau.Tree, /):
        return cls(*cls.get_obj_inner_nodes(tree))

    @classmethod
    def get_obj_inner_nodes(cls, tree: Tableau.Tree, /):
        if not tree.root:
            yield vertical_line.for_object(tree.step)
        for node_, step in zip(tree.nodes, tree.ticksteps):
            yield node.for_objects(node_, step)

class node_props(elements.Inline):

    @classmethod
    def for_object(cls, node: proof.Node, /):
        return cls(
            *cls.get_obj_inner_nodes(node),
            classes=cls.get_obj_classes(node))

    @classmethod
    def get_obj_classes(cls, node: proof.Node, /):
        if getattr(node, 'ticked', False):
            yield 'ticked'
    
    @classmethod
    def get_obj_inner_nodes(cls, node: proof.Node, /):
        if node.has('sentence'):
            yield sentence.for_object(node)
            if node.has('world'):
                yield world.for_object(node)
        if node.has('designated'):
            yield designation.for_object(node)
        if node.is_access:
            yield access.for_object(node)
        if node.has('ellipsis'):
            yield ellipsis()
        if node.has('is_flag'):
            yield flag.for_object(node)

class sentence(elements.Inline):

    @classmethod
    def for_object(cls, node: proof.Node, /):
        return cls(node['sentence'])

    def __init__(self, sentence: Sentence, /, **kw):
        super().__init__(**kw)
        self.sentence = sentence

class world(elements.Inline):

    @classmethod
    def for_object(cls, node: proof.Node, /):
        return cls(world=node['world'])

class designation(elements.Inline):

    @classmethod
    def for_object(cls, node: proof.Node, /):
        return cls(classes=cls.get_obj_classes(node))

    @classmethod
    def get_obj_classes(cls, node: proof.Node, /):
        if node.get('designated'):
            yield 'designated'
        else:
            yield 'undesignated'

class access(elements.Inline):

    @classmethod
    def for_object(cls, node: proof.Node, /):
        return cls(**dict(cls.get_obj_attributes(node)))

    @classmethod
    def get_obj_attributes(cls, node: proof.Node, /):
        return Access.fornode(node).tonode().items()


class flag(elements.Inline):

    @classmethod
    def for_object(cls, node: proof.Node, /):
        return cls(
            classes=cls.get_obj_classes(node),
            **dict(cls.get_obj_attributes(node)))

    @classmethod
    def get_obj_classes(cls, node: proof.Node, /):
        yield node['flag']

    @classmethod
    def get_obj_attributes(cls, node: proof.Node, /):
        yield 'title', node.get('info', '')

def _styleattr(*args, **kw):
    return ' '.join(
        f"{str(key).replace('_', '-')}: {value};"
        for key, value in dict(*args, **kw).items())

def _pctstr(n):
    return f'{n}%'