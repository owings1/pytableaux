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
# pytableaux.tools.lazy tests
from ..utils import BaseCase as Base

from pytableaux.tools import lazy

class TestLazyGet(Base):

    def test_default_decorator(self):

        class A:
            spam_calls = 0
            @lazy.get
            def spam(self):
                __class__.spam_calls +=1
                return 'spam'
        a = A()
        self.assertEqual(a.spam(), 'spam')
        self.assertEqual(a._spam, 'spam')
        a.spam()
        self.assertEqual(A.spam_calls, 1)

    def test_attr_name_decorator(self):

        class A:
            spam_calls = 0
            @lazy.get(attr='_realspam')
            def spam(self):
                __class__.spam_calls +=1
                return 'spam'
        a = A()
        self.assertEqual(a.spam(), 'spam')
        self.assertEqual(a._realspam, 'spam')
        a.spam()
        self.assertEqual(A.spam_calls, 1)


    def test_default_non_decorator(self):
        lg = lazy.get()
        class A:
            spam_calls = 0
            @lg
            def spam(self):
                __class__.spam_calls += 1
                return 'spam'
        
        a = A()
        self.assertEqual(a.spam(), 'spam')
        self.assertEqual(a._spam, 'spam')
        a.spam()
        self.assertEqual(A.spam_calls, 1)

    def test_attr_name_non_decorator(self):
        lg = lazy.get(attr='_realspam')
        class A:
            spam_calls = 0
            @lg
            def spam(self):
                __class__.spam_calls += 1
                return 'spam'
        
        a = A()
        self.assertEqual(a.spam(), 'spam')
        self.assertEqual(a._realspam, 'spam')
        a.spam()
        self.assertEqual(A.spam_calls, 1)

    def test_reusable_setname(self):
        lg = lazy.get()
        class A:
            spam_calls = 0
            eggs_calls = 0
            @lg
            def spam(self):
                __class__.spam_calls += 1
                return 'spam'
            @lg
            def eggs(self):
                __class__.eggs_calls += 1
                return 'eggs'
        
        a = A()
        self.assertEqual(a.spam(), 'spam')
        self.assertEqual(a._spam, 'spam')
        self.assertEqual(a.eggs(), 'eggs')
        self.assertEqual(a._eggs, 'eggs')
        a.spam()
        a.eggs()
        self.assertEqual(A.spam_calls, 1)
        self.assertEqual(A.eggs_calls, 1)

class TestLazyProp(Base):

    def test_default_decorator(self):

        class A:
            spam_calls = 0
            @lazy.prop
            def spam(self):
                __class__.spam_calls +=1
                return 'spam'
        a = A()
        self.assertEqual(a.spam, 'spam')
        self.assertEqual(a._spam, 'spam')
        a.spam
        self.assertEqual(A.spam_calls, 1)

    def test_attr_name_decorator(self):

        class A:
            spam_calls = 0
            @lazy.prop(attr='_realspam')
            def spam(self):
                __class__.spam_calls +=1
                return 'spam'
        a = A()
        self.assertEqual(a.spam, 'spam')
        self.assertEqual(a._realspam, 'spam')
        a.spam
        self.assertEqual(A.spam_calls, 1)


    def test_default_non_decorator(self):
        lp = lazy.prop()
        class A:
            spam_calls = 0
            @lp
            def spam(self):
                __class__.spam_calls += 1
                return 'spam'
        
        a = A()
        self.assertEqual(a.spam, 'spam')
        self.assertEqual(a._spam, 'spam')
        a.spam
        self.assertEqual(A.spam_calls, 1)

    def test_attr_name_non_decorator(self):
        lp = lazy.prop(attr='_realspam')
        class A:
            spam_calls = 0
            @lp
            def spam(self):
                __class__.spam_calls += 1
                return 'spam'
        
        a = A()
        self.assertEqual(a.spam, 'spam')
        self.assertEqual(a._realspam, 'spam')
        a.spam
        self.assertEqual(A.spam_calls, 1)
