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

from types import MappingProxyType as MapProxy
from typing import TypeVar

from ... import proof
from .. import Access, NodeAttr, NodeKey, Tableau
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

_T = TypeVar('_T')

class document(elements.Document):
    pass

class clear(elements.Block):
    pass

class ellipsis(elements.Inline, elements.ObjectBuilder[proof.Node]):
    pass

class vertical_line(elements.Block, elements.ObjectBuilder[int]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield 'data-step', obj

class horizontal_line(elements.Block, elements.ObjectBuilder[Tableau.Tree]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield 'data-step', obj.branch_step
        width = 100 * obj.balanced_line_width
        margin_left = 100 * obj.balanced_line_margin
        yield 'style', _styleattr(
            width=_pctstr(width),
            margin_left=_pctstr(margin_left))

class child_wrapper(elements.Block, elements.ObjectBuilder[tuple[Tableau.Tree, Tableau.Tree]]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        tree, child = obj
        width = (100 / tree.width) * child.width
        yield 'data-step', child.step
        yield 'data-current-width-pct', _pctstr(width)
        yield 'style', _styleattr(width=_pctstr(width))

class sentence(elements.Inline, elements.ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield NodeKey.sentence, obj[NodeKey.sentence]

class world(elements.Inline, elements.ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield NodeKey.world, obj[NodeKey.world]

class designation(elements.Inline, elements.ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_classes(cls, obj, /):
        if obj.get(NodeKey.designation):
            yield 'designated'
        else:
            yield 'undesignated'

class access(elements.Inline, elements.ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield from Access.fornode(obj).tonode().items()

class flag(elements.Inline, elements.ObjectBuilder[proof.Node]):

    @classmethod
    def get_obj_classes(cls, obj, /):
        yield obj[NodeKey.flag]

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield NodeKey.info, obj.get(NodeKey.info, '')

class node_props(elements.Inline, elements.ObjectBuilder[proof.Node]):

    node_types = MapProxy({
        NodeKey.sentence: sentence,
        NodeKey.world: world,
        NodeKey.designation: designation,
        NodeAttr.is_access: access,
        NodeKey.ellipsis: ellipsis,
        NodeKey.is_flag: flag})

    @classmethod
    def get_obj_classes(cls, obj, /):
        if getattr(obj, NodeAttr.ticked, False):
            yield 'ticked'
    
    @classmethod
    def get_obj_children(cls, obj, /):
        types = cls.node_types
        if obj.has(NodeKey.sentence):
            yield types[NodeKey.sentence].for_object(obj)
            if obj.has(NodeKey.world):
                yield types[NodeKey.world].for_object(obj)
        if obj.has(NodeKey.designation):
            yield types[NodeKey.designation].for_object(obj)
        if getattr(obj, NodeAttr.is_access):
            yield types[NodeAttr.is_access].for_object(obj)
        if obj.has(NodeKey.ellipsis):
            yield types[NodeKey.ellipsis].for_object(obj)
        if obj.has(NodeKey.is_flag):
            yield types[NodeKey.is_flag].for_object(obj)

class node(elements.Block, elements.ObjectBuilder[tuple[proof.Node, int]]):

    node_types = MapProxy(dict(node_props=node_props))

    @classmethod
    def get_obj_attributes(cls, obj, /):
        node, tickstep = obj
        yield 'id', f'node_{node.id}'
        yield 'data-node-id', node.id
        yield 'data-step', node.step
        if getattr(node, NodeAttr.ticked, False):
            yield 'data-ticked-step', tickstep

    @classmethod
    def get_obj_classes(cls, obj, /):
        if getattr(obj[0], NodeAttr.ticked, False):
            yield 'ticked'

    @classmethod
    def get_obj_children(cls, obj, /):
        yield cls.node_types['node_props'].for_object(obj[0])

class node_segment(elements.Block, elements.ObjectBuilder[Tableau.Tree]):

    node_types = MapProxy(dict(
        (cls.__name__, cls) for cls in (
            node,
            vertical_line)))

    @classmethod
    def get_obj_children(cls, obj, /):
        types = cls.node_types
        if not obj.root:
            yield types['vertical_line'].for_object(obj.step)
        yield from map(types['node'].for_object, zip(obj.nodes, obj.ticksteps))

class tree(elements.Block, elements.ObjectBuilder[Tableau.Tree]):

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

    node_types = MapProxy(dict(
        (cls.__name__, cls) for cls in (
            node_segment,
            vertical_line,
            horizontal_line,
            child_wrapper)))

    @classmethod
    def get_obj_attributes(cls, obj, /):
        yield 'id', f'structure_{obj.id}'
        for name in cls.data_attrnames:
            yield f'data-{name}', obj[name]
        if obj.closed:
            yield 'data-closed-step', obj.closed_step
        if obj.branch_id:
            yield 'data-branch-id', obj.branch_id
        if obj.model_id:
            yield 'data-model-id', obj.model_id
        
    @classmethod
    def get_obj_classes(cls, obj, /):
        if obj.root:
            yield 'root'
        yield from filter(obj.get, cls.flag_classnames)

    @classmethod
    def get_obj_children(cls, obj, /):
        types = cls.node_types
        node = types['node_segment'].for_object(obj)
        if obj.children:
            node += types['vertical_line'].for_object(obj.branch_step)
            node += types['horizontal_line'].for_object(obj)
            for child in obj.children:
                wrap = types['child_wrapper'].for_object((obj, child))
                wrap += cls.for_object(child)
                node += wrap
        return node

def _styleattr(*args, **kw):
    return ' '.join(
        f"{str(key).replace('_', '-')}: {value};"
        for key, value in dict(*args, **kw).items())

def _uscore(s: str):
    return s.replace('-', '_')

def _endash(s: str):
    return s.replace('_', '-')

def _pctstr(n):
    return f'{n}%'