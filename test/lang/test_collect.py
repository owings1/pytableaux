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
# pytableaux.lang.collect tests
from copy import copy

from pytableaux import examples
from pytableaux.lang import *

from ..utils import BaseCase


class TestArgument(BaseCase):

    def test_self_equality(self):
        a = self.parg('Addition')
        self.assertEqual(a, a)

    def test_lt_sentence_not_implemented(self):
        a = self.parg('Addition')
        s = Atomic.first()
        self.assertIs(a.__lt__(s), NotImplemented)
        
    def test_keystr_examples_restore(self):
        for a1 in examples.arguments():
            keystr = a1.keystr()
            a2 = Argument.from_keystr(keystr)
            self.assertEqual(a1, a2)

    def test_for_json_has_keys_coverage(self):
        a = self.parg('Addition')
        res = a.for_json()
        self.assertIn('premises', res)
        self.assertIn('conclusion', res)

    def test_repr_str_coverage(self):
        a = self.parg('a')
        r = repr(a)
        self.assertIs(type(r), str)

    def test_set_attr_locked(self):
        a = self.parg('a')
        with self.assertRaises(AttributeError):
            a.premises = ()

class TestPredicates(BaseCase):

    def test_errors(self):
        with self.assertRaises((TypeError,ValueError)):
            Predicates().add('foo')
        with self.assertRaises((TypeError,ValueError)):
            Predicates([('foo', 4)])
        with self.assertRaises(TypeError):
            Predicates()['nonIndexKey']
        with self.assertRaises(TypeError):
            Predicates()[(-1, 2)]
        with self.assertRaises(KeyError):
            Predicates().get('NonExistentPred')
        with self.assertRaises(KeyError):
            Predicates().get((-1, 2))
        with self.assertRaises(KeyError):
            Predicates().get((1, 2))
        with self.assertRaises((TypeError,ValueError)):
            Predicates().add((0, 0, 2, 'Identity'))
        with self.assertRaises((TypeError,ValueError)): # bad arity
            Predicates().add((0, 0, None))
        with self.assertRaises((TypeError,ValueError)): # bad arity
            Predicates().add((0, 0,))
        with self.assertRaises((TypeError,ValueError)): # bad arity
            Predicates().add((0, 0, 0))
        with self.assertRaises(ValueError): # index too large
            Predicates().add((Predicate.TYPE.maxi + 1, 0, 1))
        preds = Predicates({(0, 0, 1)})
        with self.assertRaises(ValueError): # arity mismatch
            preds.add((0, 0, 2))

    def test_get_predicate_by_index_subscript_sys_identity(self):
        self.assertEqual(Predicates().get((-1, 0)).name, 'Identity')

    def test_get_pred_coords_tuple(self):
        pred, = Predicates({(1, 1, 1)})
        self.assertEqual(pred.spec, (1, 1, 1))
        self.assertEqual(pred.bicoords, (1, 1))

    def test_pred_no_name(self):
        v = Predicates()
        p = Predicate((1, 0, 1))
        v.add(p)
        p1 = v.get((1, 0))
        self.assertEqual(p, p1)
        p = Predicate((1, 1, 2))
        v.add(p)
        p2 = v.get((1, 1))
        self.assertEqual(p, p2)

    def test_declare1(self):
        p, = Predicates({(0, 0, 1)})
        self.assertEqual(p.index, 0)
        self.assertEqual(p.subscript, 0)
        self.assertEqual(p.arity, 1)

    def test_copy_get_predicate(self):
        v = Predicates()
        spec = (0, 0, 1)
        v.add(spec)
        pred = v.get(spec)
        v2 = copy(v)
        self.assertEqual(v2.get(spec), pred)
        self.assertIsNot(v, v2)

    def test_compare_id_with_user_pred(self):
        pred, = Predicates({(0, 0, 1)})
        self.assertLess(Predicate.Identity, pred)
        self.assertLessEqual(Predicate.Identity, pred)
        self.assertGreater(pred, Predicate.Identity)
        self.assertGreaterEqual(pred, Predicate.Identity)

    def test_lookup_refs(self):
        v = Predicates(((0, 0, 1),))
        self.assertIn((0, 0), v)
        self.assertIn((0, 0, 1), v)

    def test_init_iter_types(self):
        v = Predicates([(0, 0, 2)])
        p = v.get((0, 0))
        self.assertEqual(p.arity, 2)
        v = Predicates(((0, 0, 3),))
        p = v.get((0, 0))
        self.assertEqual(p.arity, 3)
        v = Predicates(Predicate.gen(4))
        self.assertEqual(len(v), 4)
        v2 = Predicates(v)
        self.assertEqual(v, v2)
        self.assertEqual(len(v2), 4)
        self.assertIsNot(v, v2)

    def test_copy_preds(self):
        p1, p2, p3 = Predicate.gen(3)
        v1 = Predicates((p1, p2))
        v2 = copy(v1)
        self.assertEqual(v1, v2)
        self.assertIsNot(v1, v2)
        self.assertNotIn(p3, v1)
        v1.add(p3)
        self.assertIn(p3, v1)
        self.assertNotIn(p3, v2)

    def test_conflict_leaves_collection_as_is(self):
        p1 = Predicate(0,0,1)
        p2 = Predicate(0,0,2)
        v = Predicates()
        v.add(p1)
        with self.assertRaises(ValueError):
            v.add(p2)
        self.assertIn(p1, v)
        self.assertNotIn(p2, v)
        self.assertNotIn(p2, v._set_)
        self.assertNotIn(p2, v._seq_)
        self.assertEqual(len(v), 1)

    def test_deletion(self):
        p1 = Predicate(0,0,1)
        p2 = Predicate(0,0,2)
        v = Predicates()
        v.add(p1)
        self.assertEqual(set(v), {p1})
        v.remove(p1)
        self.assertEqual(set(v), set())
        v.discard(p1)
        v.add(p2)
        self.assertEqual(set(v), {p2})

    def test_overwrite_with_conflicting_value(self):
        p1 = Predicate(0,0,1)
        p2 = Predicate(0,0,2)
        v = Predicates()
        v.append(p1)
        self.assertEqual(v[0], p1)
        v[0] = p2
        self.assertEqual(v[0], p2)
        self.assertEqual(len(v), 1)

    def test_get_returns_default(self):
        v = Predicates()
        o = object()
        self.assertIs(v.get('', o), o)

    def test_clear_removes_lookup(self):
        v = Predicates(Predicate.System)
        self.assertIn('Identity', v)
        v.clear()
        self.assertEqual(len(v), 0)
        self.assertNotIn('Identity', v)
