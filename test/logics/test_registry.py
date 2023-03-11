from pytableaux import logics
from pytableaux.logics import Registry, registry

from unittest import TestCase as Base

class TestRegistry(Base):

    def test_construct(self):
        self.assertIsInstance(Registry(), Registry)

    def test_add_package(self):
        reg = Registry()
        reg.packages.add('pytableaux.logics')
        self.assertIs(reg('cpl'), registry('cpl'))

    def test_get(self):
        self.assertIs(registry.get('cpl'), registry('cpl'))

    def test_get_default(self):
        self.assertIs(registry.get('??', None), None)

    def test_call_raises(self):
        with self.assertRaises(ModuleNotFoundError):
            registry('??')

    def test_get_no_default_raises(self):
        with self.assertRaises(ModuleNotFoundError):
            registry.get('??')

    def test_locate(self):
        logic = registry('cpl')
        self.assertIs(registry.locate(logic.TableauxSystem), logic)

    def test_locate_default(self):
        self.assertIs(registry.locate(type(self), None), None)

    def test_locate_no_default_raises(self):
        with self.assertRaises(ValueError):
            registry.locate(type(self))

    def test_all_package_all(self):
        reg = Registry()
        reg.packages.add('pytableaux.logics')
        res = list(reg.all())
        self.assertEqual(set(res), set(f'pytableaux.logics.{x}' for x in logics.__all__))
        self.assertEqual(res, list(registry.package_all('pytableaux.logics')))
