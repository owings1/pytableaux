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
#
# ------------------
#
# pytableaux.proof.common tests
from __future__ import annotations

from types import MappingProxyType as MapProxy

from pytableaux.errors import IllegalStateError
from pytableaux.lang import *
from pytableaux.logics import registry
from pytableaux.proof import *
from pytableaux.proof import rules

from ..utils import BaseCase as Base


class TestNode(Base):

    def test_construct_non_mapping_raises_type_error(self):
        with self.assertRaises(TypeError):
            Node(1)

    def test_init_self(self):
        n1 = Node()
        m1 = n1._cov_mapping
        n1.__init__(n1)
        self.assertIs(n1._cov_mapping, m1)
    
    def test_copy(self):
        n1 = Node({'a': 1})
        n2 = n1.copy()
        self.assertIsNot(n1, n2)
        self.assertEqual(dict(n1), dict(n2))
    
    def test_has(self):
        n = Node({'a': 1, 'b': None})
        self.assertTrue(n.has('a'))
        self.assertFalse(n.has('b'))
        self.assertFalse(n.has('a', 'b'))

    def test_any(self):
        n = Node({'a': 1, 'b': None})
        self.assertTrue(n.any('a'))
        self.assertFalse(n.any('b'))
        self.assertTrue(n.any('a', 'b'))

    def test_repr_coverage(self):
        r = repr(Node({}))
        self.assertIs(type(r), str)

    def test_for_mapping(self):
        n = Node.for_mapping({'world': 0})
        self.assertIsInstance(n, WorldNode)
        n = Node.for_mapping({'flag': 'closure', 'is_flag': True})
        self.assertIsInstance(n, ClosureNode)
        n = Node.for_mapping({'flag': 'quit', 'is_flag': True})
        self.assertIsInstance(n, QuitFlagNode)
        n = Node.for_mapping({'flag': 'other', 'is_flag': True})
        self.assertIsInstance(n, FlagNode)

    def test_worlds_contains_worlds(self):
        node = Node.for_mapping({'world1': 0, 'world2': 1})
        res = set(node.worlds())
        self.assertIn(0, res)
        self.assertIn(1, res)

    def test_clousre_flag_node_has_is_flag(self):
        branch = Branch()
        branch.close()
        node = branch[0]
        assert node.has('is_flag')

    def test_create_node_with_various_types(self):
        exp = {}
        exp.update({'a':1,'b':2,'c':3})
        for inp in [
            dict(zip(('a', 'b', 'c'), (1, 2, 3))),
            MapProxy(exp),
        ]:
            self.assertEqual(dict(Node(inp)), exp)

    def test_or_ror_operators(self):
        pa = dict(world = None, designated = None)
        pb = pa.copy()
        pa.update(a=1,b=3,C=3,x=1)
        pb.update(A=1,b=2,c=4,y=3)
        exp1 = pa | pb
        exp2 = pb | pa
        n1, n2 = map(Node, (pa, pb))
        self.assertEqual(n1 | n2, exp1)
        self.assertEqual(n1 | dict(n2), exp1)
        self.assertEqual(dict(n1) | n2, exp1)
        self.assertEqual(dict(n1) | dict(n2), exp1)
        self.assertEqual(n2 | n1, exp2)
        self.assertEqual(n2 | dict(n1), exp2)
        self.assertEqual(dict(n2) | n1, exp2)
        self.assertEqual(dict(n2) | dict(n1), exp2)


class TestBranch(Base):

    def test_close_twice_raises(self):
        b = Branch()
        b.close()
        with self.assertRaises(IllegalStateError):
            b.close()

    def test_append_when_closed_raises(self):
        b = Branch()
        b.close()
        with self.assertRaises(IllegalStateError):
            b.append({'a': 1})

    def test_or_returns_branch(self):
        b1 = Branch()
        b1 += {'a': 1}
        b2 = Branch()
        b2 += {'b': 2}
        b3 = b1 | b2
        self.assertIsInstance(b3, Branch)
        self.assertTrue(b3.has({'a': 1}))
        self.assertTrue(b3.has({'b': 2}))

    def test_any(self):
        b = Branch()
        b += map(Node, [{'a': 1, 'b': 2}, {'b': 2, 'a': 4}])
        self.assertTrue(b.any([{'a': 0}, {'b': 5}, {'a': 4}]))

    def test_set_parent_twice_raises(self):
        b1 = Branch()
        b2 = Branch(b1)
        with self.assertRaises(AttributeError):
            b2.parent = Branch()

    def test_set_parent_self_raises(self):
        b1 = Branch()
        del(b1._parent)
        with self.assertRaises(ValueError):
            b1.parent = b1

    def test_set_model_twice_raises(self):
        b = Branch()
        m1 = registry('cpl').Model()
        b.model = m1
        m2 = registry('cpl').Model()
        with self.assertRaises(AttributeError):
            b.model = m2

    def test_next_world_returns_w0(self):
        self.assertEqual(Branch().new_world(), 0)

    def test_new_constant_returns_m(self):
        self.assertEqual(Branch().new_constant(), Constant(0, 0))

    def test_new_constant_returns_m1_after_s0(self):
        b = Branch()
        i = 0
        while i <= Constant.TYPE.maxi:
            c = Constant(i, 0)
            sen = Predicated('Identity', (c, c))
            b.append({'sentence': sen})
            i += 1
        self.assertEqual(b.new_constant(), Constant(0, 1))

    def test_repr_contains_closed(self):
        self.assertIn('closed', Branch().__repr__())

    def test_has_all_true_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{'sentence': s1}, {'sentence': s2}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        self.assertTrue(b.all(check))

    def test_has_all_false_1(self):
        b = Branch()
        s1, s2, s3 = Atomic.gen(3)
        b.extend([{'sentence': s1}, {'sentence': s3}])
        check = [{'sentence': s1, 'sentence': s2}]
        self.assertFalse(b.all(check))

    def test_branch_has_world1(self):
        proof = Tableau()
        branch = proof.branch().append({'world1': 4, 'world2': 1})
        self.assertTrue(branch.has({'world1': 4}))


    def test_regression_branch_has_works_with_newly_added_node_on_after_node_add(self):

        class MyRule(rules.NoopRule):

            __slots__ = 'should_be', 'shouldnt_be'

            def __init__(self, *args, **opts):
                self.should_be = False
                self.shouldnt_be = True
                super().__init__(*args, **opts)
                def after_node_add(node: Node, branch: Branch):
                    self.should_be = branch.has({'world1': 7})
                    self.shouldnt_be = branch.has({'world1': 6})
                self.tableau.on(Tableau.Events.AFTER_NODE_ADD, after_node_add)

        proof = Tableau()
        proof.rules.append(MyRule)
        rule = proof.rules.get(MyRule)
        proof.branch().append({'world1': 7})

        self.assertTrue(rule.should_be)
        self.assertFalse(rule.shouldnt_be)


    def test_select_index_non_indexed_prop(self):
        branch = Branch()
        branch.append({'foo': 'bar'})
        idx = branch._index.select({'foo': 'bar'}, branch)
        self.assertEqual(list(idx), list(branch))

    def test_select_index_access(self):
        b = Branch()
        b.extend((
            {'world1': 0, 'world2': 1},
            *({'foo': 'bar'} for _ in range(len(b._index))),
        ))
        base = b._index.select({'world1': 0, 'world2': 1}, b)
        self.assertEqual(set(base), {b[0]})

    def test_close_adds_flag_node(self):
        b = Branch()
        b.close()
        self.assertTrue(b.has({'is_flag': True, 'flag': 'closure'}))
        self.assertEqual(len(b), 1)

    def nn1(self, n = 3):
        return tuple(Node({'i': i}) for i in range(n))

    def case1(self, n = 3, nn = None):
        b = Branch()
        if not any ((n, nn)):
            return b
        if nn is None:
            nn = self.nn1(n)
        b.extend(nn)
        return (b, nn)

    def test_for_in_iter_nodes(self):
        b, nn = self.case1()
        npp = tuple(dict(n) for n in nn)
        self.assertEqual(tuple(b), nn)
        self.assertEqual(tuple(iter(b)), nn)
        self.assertEqual(tuple(map(dict, b)), npp)
        self.assertEqual(tuple(map(dict, iter(b))), npp)

    def gcase1(self, *a, **k):
        b, nn = self.case1(*a, *k)
        def gen(*subs):
            for i in subs:
                if not isinstance(i, int):
                    i = slice(*i)
                yield b[i], nn[i]
        return gen, b, nn

    def test_subscript_1(self):
        size = 5
        gen, branch, nodes = self.gcase1(size)

        self.assertEqual(len(branch), len(nodes))
        self.assertEqual(len(branch), size)

        # indexes
        it = gen(
            0, -1
        )

        for a, b in it:
            self.assertIs(a, b)
            self.assertEqual(branch.index(a), nodes.index(b))

        # slices
        it = gen(
            (0, 1), (2, -1), (3, None)
        )

        for a, b in it:
            self.assertEqual(list(a), list(b))


    def test_create_list_tuple_set_from_branch(self):
        b, nn = self.case1(5)
        nodes = list(b)
        self.assertEqual(tuple(b), nn)
        self.assertEqual(set(b), set(nn))
        self.assertEqual(nodes, list(nn))
        self.assertEqual(len(nodes), len(b))
        self.assertEqual(len(nodes), 5)

    def case2(self, n = 2):
        return Branch().extend(self.nn1(n=n))

    def test_subscript_errors(self):
        b = self.case2()
        with self.assertRaises(TypeError):
            b['0']
        with self.assertRaises(IndexError):
            b[2]

    def test_len_0_6(self):
        self.assertEqual(len(self.case2(0)), 0)
        self.assertEqual(len(self.case2(6)), 6)

class TestTarget(Base):

    def test_missing_branch_raises(self):
        with self.assertRaises(ValueError):
            Target()

    def test_type_nodes(self):
        n1 = Node()
        n2 = Node()
        b = Branch()
        b += n1, n2
        t = Target(branch=b, node=n1, nodes=(n1, n2))
        self.assertEqual(t.type, 'Nodes')

    def test_type_node(self):
        n1 = Node()
        n2 = Node()
        b = Branch()
        b += n1, n2
        t = Target(branch=b, node=n1)
        self.assertEqual(t.type, 'Node')

    def test_type_branch(self):
        t = Target(branch=Branch())
        self.assertEqual(t.type, 'Branch')

    def test_repr_coverage(self):
        r = repr(Target(branch=Branch()))
        self.assertIs(type(r), str)
    
    def test_dir_names(self):
        t = Target(branch=Branch(), node=Node())
        self.assertEqual(dir(t), ['branch', 'node'])
    
    def test_setitem_conflict_raises(self):
        t = Target(branch=Branch())
        with self.assertRaises(ValueError):
            t['branch'] = Branch()
    
    def test_setitem_no_conflict(self):
        b = Branch()
        t = Target(branch=b)
        t['branch'] = b
    
    def test_setitem_reserved_raises(self):
        t = Target(branch=Branch())
        with self.assertRaises((AttributeError, KeyError)):
            t['or'] = 1
    
    def test_setitem_non_str_raises(self):
        t = Target(branch=Branch())
        with self.assertRaises(TypeError):
            t[0] = 1
    
    def test_type_raises_if_missing_branch(self):
        t = Target(branch=Branch())
        dict.__delitem__(t, 'branch')
        with self.assertRaises(ValueError):
            t.type
