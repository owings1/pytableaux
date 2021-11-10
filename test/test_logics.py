# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - logics test cases
from pytest import raises
from errors import *
from utils import StopWatch, get_logic
from lexicals import Predicates, Atomic, Constant, Predicate, Predicated, Quantified, \
    Operated, Variable, Argument, Operator, Quantifier, Quantifier as Quant, Operator as Oper
from proof.tableaux import Tableau, Branch
from proof.common import Node
from parsers import parse, parse_argument
from models import truth_table
from .tutils import BaseSuite, larg, using, skip
from enum import Enum
import examples
Existential = Quantifier.Existential
Universal = Quantifier.Universal
Identity = Predicates.SystemEnum.Identity.pred
Existence = Predicates.SystemEnum.Existence.pred

Designated = des = Node.Properties.Designation.Designated
Undesignated = undes = Node.Properties.Designation.Undesignated
Negated = 'Negated'

class BoolPropEnum(Enum):
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.__str__()
    def __bool__(self):
        return self.value
    def __eq__(self, other):
        return other is self or other in (self.value, self.name)
    def __hash__(self):
        return self.value

class Designation(BoolPropEnum):
    Designated = True
    Undesignated = False
# Designation.key = 'designated'
# Designation.attr = 'designation'

@using(logic = 'FDE')
class Test_FDE(BaseSuite):

    class Test_Tableaux(BaseSuite):

        class Test_Closure(BaseSuite):

            def test_DesignationClosure(self):
                self.rule_eg('DesignationClosure')

        class Test_Operators(BaseSuite):

            @larg(Oper.Negation)
            def test_Negation(self, o):
                assert self.logic.name == 'FDE'
                self.rule_eg('Double%s%s' % (o, Designated))
                self.rule_eg('Double%s%s' % (o, Undesignated))

            @larg(Oper.Assertion)
            def test_Assertion(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, des))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.valid_tab('Na', 'NTa')

            @larg(Oper.Conjunction)
            def test_Conjunction(self, o):
                rtd = self.rule_eg('%s%s' % (o, Designated))
                rtu = self.rule_eg('%s%s' % (o, Undesignated))
                rtnd = self.rule_eg('%s%s%s' % (o, Negated, Designated))
                rtnu = self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

                self.invalid_tab('LNC')

                n = rtnd[1].history[0].target.node; s = n['sentence']
                assert (s.operator, s.negatum.operator, n['designated']) \
                    == (Oper.Negation, Oper.Conjunction, True)


            @larg(Oper.Disjunction)
            def test_Disjunction(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.valid_tab('Addition')
                self.invalid_tab('LEM')

            @larg(Oper.MaterialConditional)
            def test_MaterialConditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.MaterialBiconditional)
            def test_MaterialBiconditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.invalid_tab('Material Biconditional Elimination 3')

            @larg(Oper.Conditional)
            def test_Conditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Biconditional)
            def test_Biconditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, des))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            class Test_Arguments(BaseSuite):

                def test_DeMorgan(self):
                    self.valid_tab('DeMorgan 1')
                    self.valid_tab('DeMorgan 2')
                    self.valid_tab('DeMorgan 3')
                    self.valid_tab('DeMorgan 4')

        class Test_Quantification(BaseSuite):

            @larg(Quant.Existential)
            def test_Existential(self, q):
                rtd = self.rule_eg('%s%s' % (q, Designated))
                rtu = self.rule_eg('%s%s' % (q, Undesignated))
                rtnd = self.rule_eg('%s%s%s' % (q, Negated, Designated))
                rtnu = self.rule_eg('%s%s%s' % (q, Negated, Undesignated))

                b = rtu[1][0]
                assert b.has(
                    {'sentence': Quantified.first(q), 'designated': False}
                )

            @larg(Quant.Universal)
            def test_Universal(self, q):
                self.rule_eg('%s%s' % (q, Designated))
                self.rule_eg('%s%s' % (q, Undesignated))
                self.rule_eg('%s%s%s' % (q, Negated, Designated))
                self.rule_eg('%s%s%s' % (q, Negated, Undesignated))

            def test_arguments(self):
                self.valid_tab('Quantifier Interdefinability 4')
                self.invalid_tab('Universal from Existential')

            def test_invalid_existential_inside_univ_max_steps(self):
                tab = self.invalid_tab('b', 'VxUFxSyFy', max_steps=100, is_build_models=True)
                assert len(tab.history) < 100

        class Test_BranchingComplexity(BaseSuite):

            def nodecase(s, des):
                def wrap(fn):
                    def testfn(self):
                        tab = self.tab()
                        tab.branch().add({'sentence': self.p(s), 'designated': des})
                        fn(self, tab[0][0], tab)
                    return testfn
                return wrap

            @nodecase('a', False)
            def test_branching_complexity_undes_0_1(self, node, tab):
                assert tab.branching_complexity(node) == 0

            @nodecase('Kab', False)
            def test_branching_complexity_undes_1_1(self, node, tab):
                assert tab.branching_complexity(node) == 1

            @nodecase('NAaNKbc', False)
            def test_branching_complexity_undes_1_2(self, node, tab):
                assert node['sentence'].operators == (
                    Oper.Negation, Oper.Disjunction, Oper.Negation, Oper.Conjunction)
                assert tab.branching_complexity(node) == 1

            @nodecase('NAab', False)
            def test_branching_complexity_undes_1_3(self, node, tab):
                assert node['sentence'].operators == (Oper.Negation, Oper.Disjunction)
                assert tab.branching_complexity(node) == 1

            @nodecase('KaKab', False)
            def test_branching_complexity_undes_2_1(self, node, tab):
                assert node['sentence'].operators == ('Conjunction', 'Conjunction')
                assert tab.branching_complexity(node) == 2

    class Test_Models(BaseSuite):

        def mb(self, *nitems):
            b = Branch()
            for s, d in nitems:
                b.add({'sentence': self.p(s), 'designated': d})
            m = self.Model()
            m.read_branch(b)
            return (m,b)

        def test_countermodels(self):
            self.cm('LEM')
            m = self.cm('LNC')
            assert m.value_of(Atomic.first()) == 'B'

        def test_model_a_thus_b_is_countermodel_to_false(self):
            arg = self.parg('b', 'a')
            model = self.logic.Model()
            model.set_literal_value(arg.premises[0], 'F')
            model.set_literal_value(arg.conclusion, 'F')
            assert not model.is_countermodel_to(arg)

        def test_model_b_value_atomic_branch(self):
            s1 = self.p('a')
            m, b = self.mb(('a', True), ('Na', True))
            assert m.value_of(s1) == 'B'

        def test_model_univ_t_value_branch(self):
            s1, s2 = self.pp('Fm', 'VxFx')
            m,b = self.mb((s1, True))
            assert m.value_of(s2) == 'T'

        def test_model_exist_b_value_branch(self):
            s1, s2, s3 = self.pp('Fm', 'Fn', 'SxFx')
            m,b = self.mb(
                (s1, True),
                (s1.negate(), True),
                (s2, False),
                (s2.negate(), False)
            )
            assert m.value_of(s3) == 'B'

        def test_model_necessity_opaque_des_value_branch(self):
            s1 = self.p('La')
            b = Branch().add({'sentence': s1, 'designated': True})
            m = self.Model().read_branch(b)
            assert m.value_of(s1) in ('B', 'T')

        def test_model_necessity_opaque_b_value_branch(self):
            s1 = self.p('La')
            b = Branch().extend((
                {'sentence': s1         , 'designated': True},
                {'sentence': s1.negate(), 'designated': True},
            ))
            m = self.Model().read_branch(b)
            assert m.value_of(s1) == 'B'

        def test_model_atomic_undes_value_branch(self):
            s1 = self.p('a')
            b = Branch().add({'sentence': s1, 'designated': False})
            m = self.Model().read_branch(b)
            assert m.value_of(s1) in ('F', 'N')

        def test_model_atomic_t_value_branch(self):
            branch = Branch()
            s = self.p('a')
            branch.extend([
                {'sentence': s         , 'designated': True},
                {'sentence': s.negate(), 'designated': False},
            ])
            model = self.Model().read_branch(branch)
            assert model.value_of(s) == 'T'

        def test_model_atomic_f_value_branch(self):
            branch = Branch()
            s = self.p('a')
            branch.extend([
                {'sentence': s         , 'designated': False},
                {'sentence': s.negate(), 'designated': True},
            ])
            model = self.Model().read_branch(branch)
            assert model.value_of(s) == 'F'

        def test_model_get_data_various(self):
            s1 = self.p('a')
            s2 = self.p('Imn')
            model = self.logic.Model()
            model.set_literal_value(s1, 'B')
            model.set_literal_value(s2, 'F')
            res = model.get_data()
            assert 'Atomics' in res

        def test_model_not_impl_various(self):
            s1 = self.p('Aab')
            model = self.logic.Model()
            with raises(NotImplementedError):
                model.set_literal_value(s1, 'T')
            with raises(NotImplementedError):
                model.value_of_quantified(s1)
            with raises(NotImplementedError):
                model.truth_function('Foomunction', 'F')

        def test_model_value_of_atomic_unassigned(self):
            s = self.p('a')
            model = self.logic.Model()
            res = model.value_of(s)
            assert res == model.unassigned_value

        def test_model_value_of_opaque_unassigned(self):
            s = self.p('La')
            model = self.logic.Model()
            res = model.value_of(s)
            assert res == model.unassigned_value

        def test_model_value_error_various(self):
            s1 = self.p('La')
            s2 = self.p('a')
            s3 = self.p('Imn')
            model = self.logic.Model()
            model.set_opaque_value(s1, 'T')
            with raises(ModelValueError):
                model.set_opaque_value(s1, 'B')
            model = self.logic.Model()
            model.set_atomic_value(s2, 'T')
            with raises(ModelValueError):
                model.set_atomic_value(s2, 'B')
            model = self.logic.Model()
            model.set_predicated_value(s3, 'T')
            with raises(ModelValueError):
                model.set_predicated_value(s3, 'N')
            model = self.logic.Model()
            model.set_predicated_value(s3, 'B')
            with raises(ModelValueError):
                model.set_predicated_value(s3, 'T')
            model = self.logic.Model()
            model.set_predicated_value(s3, 'B')
            with raises(ModelValueError):
                model.set_predicated_value(s3, 'F')
            model = self.logic.Model()
            model.set_predicated_value(s3, 'F')
            with raises(ModelValueError):
                model.set_predicated_value(s3, 'N')

        def test_model_read_branch_with_negated_opaque_then_faithful(self):
            arg = parse_argument('a', premises=['NLa', 'b'])
            proof = Tableau(self.logic, arg, is_build_models=True)
            proof.build()
            model = proof[0].model
            assert model.value_of(parse('a')) == 'F'
            assert model.value_of(parse('La')) == 'F'
            assert model.value_of(parse('NLa')) == 'T'
            assert model.is_countermodel_to(arg)

        def test_observed_value_of_universal_with_diamond_min_arg_is_an_empty_sequence(self):
            arg = self.parg('b', 'VxUFxSyMFy')
            proof = Tableau(self.logic, arg, is_build_models=False, max_steps=100).build()
            assert proof.invalid
            branch = proof[-1]
            model = self.logic.Model()
            model.read_branch(branch)
            s1 = arg.premises[0]
            assert model.value_of(s1) in model.designated_values

        def test_observed_as_above_reconstruct1(self):
            # solution was to add all constants in set_opaque_value
            s1, s2, s3, s4, s5, s6 = self.pp(
                'MFs',          # designated
                'MFo',          # designated
                'MFn',          # designated
                'b',            # undesignated
                'SyMFy',        # designated
                'VxUFxSyMFy',   # designated
            )
            model = self.logic.Model()
            model.set_opaque_value(s1, 'T')
            model.set_opaque_value(s2, 'T')
            model.set_opaque_value(s3, 'T')
            model.set_literal_value(s4, 'F')
            assert model.value_of(s3) == 'T'
            assert s3 in model.opaques
            assert model.value_of(s5) in model.designated_values

@using(logic = 'K3')
class TestK3(BaseSuite):

        class Test_Closure(BaseSuite):

            def test_GlutClosure(self):
                self.rule_eg('GlutClosure')

        class Test_Operators(BaseSuite):

            @larg(Oper.Negation)
            def test_Negation(self, o):
                assert self.logic.name == 'K3'
                self.rule_eg('Double%s%s' % (o, Designated))
                self.rule_eg('Double%s%s' % (o, Undesignated))

            @larg(Oper.Assertion)
            def test_Assertion(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, des))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Conjunction)
            def test_Conjunction(self, o):
                rtd = self.rule_eg('%s%s' % (o, Designated))
                rtu = self.rule_eg('%s%s' % (o, Undesignated))
                rtnd = self.rule_eg('%s%s%s' % (o, Negated, Designated))
                rtnu = self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.valid_tab('LNC')

            @larg(Oper.Disjunction)
            def test_Disjunction(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.invalid_tab('LEM')

            @larg(Oper.MaterialConditional)
            def test_MaterialConditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.MaterialBiconditional)
            def test_MaterialBiconditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Conditional)
            def test_Conditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Biconditional)
            def test_Biconditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, des))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.valid_tab('Biconditional Elimination 1')

            class Test_Arguments(BaseSuite):

                def test_DeMorgan(self):
                    self.valid_tab('DeMorgan 1')
                    self.valid_tab('DeMorgan 2')
                    self.valid_tab('DeMorgan 3')
                    self.valid_tab('DeMorgan 4')

@using(logic = 'K3W')
class TestK3W(BaseSuite):

    class Test_Tableaux(BaseSuite):

        class Test_Closure(BaseSuite):

            def test_GlutClosure(self):
                self.rule_eg('GlutClosure')

        class Test_Operators(BaseSuite):

            @larg(Oper.Negation)
            def test_Negation(self, o):
                assert self.logic.name == 'K3W'
                self.rule_eg('Double%s%s' % (o, Designated))
                self.rule_eg('Double%s%s' % (o, Undesignated))

            @larg(Oper.Assertion)
            def test_Assertion(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, des))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Conjunction)
            def test_Conjunction(self, o):
                rtd = self.rule_eg('%s%s' % (o, Designated))
                rtu = self.rule_eg('%s%s' % (o, Undesignated))
                rtnd = self.rule_eg('%s%s%s' % (o, Negated, Designated))
                rtnu = self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.valid_tab('LNC')

            @larg(Oper.Disjunction)
            def test_Disjunction(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))
                self.invalid_tab('LEM')

            @larg(Oper.MaterialConditional)
            def test_MaterialConditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.MaterialBiconditional)
            def test_MaterialBiconditional(self, o):
                rtd = self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Conditional)
            def test_Conditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            @larg(Oper.Biconditional)
            def test_Biconditional(self, o):
                self.rule_eg('%s%s' % (o, Designated))
                self.rule_eg('%s%s' % (o, Undesignated))
                self.rule_eg('%s%s%s' % (o, Negated, Designated))
                self.rule_eg('%s%s%s' % (o, Negated, Undesignated))

            def test_arguments(self):

                self.valid_tab('Conditional Contraction')
                self.invalid_tab('Addition')
                self.invalid_tab('ANAabNa', 'Na')
                self.invalid_tab('AaTb', 'a')
                self.valid_tab('DeMorgan 1')
                self.valid_tab('DeMorgan 2')
                self.valid_tab('DeMorgan 3')
                self.valid_tab('DeMorgan 4')
                self.invalid_tab('AUabNUab')

            def bt(self, *nitems):
                tab = self.tab()
                b = tab.branch()
                b.extend({'sentence': self.p(s), 'designated': d}
                    for s,d in nitems
                )
                return (tab, b)

            def test_rule_MaterialBiconditionalDesignated_step(self):
                s1, s2 = self.pp('Eab', 'KCabCba')
                tab, b = self.bt((s1, True))
                tab.step()
                assert b.has({'sentence': s2, 'designated': True})

            def test_rule_MaterialBiconditionalNegatedDesignated_step(self):
                s1, s2 = self.pp('NEab', 'NKCabCba')
                tab, b = self.bt((s1, True))
                tab.step()
                rule = tab.history[0].rule
                assert rule.name == 'MaterialBiconditionalNegatedDesignated'
                assert b.has({'sentence': s2, 'designated': True})

            def test_rule_ConjunctionNegatedUndesignated_step(self):
                tab, b = self.bt(('NKab', False))
                tab.step()
                b1, b2, b3 = tab
                assert b1.has({'sentence': parse('a'), 'designated': False})
                assert b1.has({'sentence': parse('Na'), 'designated': False})
                assert b2.has({'sentence': parse('b'), 'designated': False})
                assert b2.has({'sentence': parse('Nb'), 'designated': False})
                assert b3.has({'sentence': parse('a'), 'designated': True})
                assert b3.has({'sentence': parse('b'), 'designated': True})

        class Test_Optimizations(BaseSuite):
            def test_optimize1(self):
                tab = self.tab()
                tab.branch().extend([
                    {'sentence': parse('ANaUab'), 'designated': False},
                    {'sentence': parse('NANaUab'), 'designated': False},
                ])
                step = tab.step()
                assert step.rule.name == 'DisjunctionNegatedUndesignated'

    class Test_Models(BaseSuite):

        def test_truth_table_conjunction(self):
            tbl = truth_table(self.logic, 'Conjunction')
            assert tbl['outputs'][0] == 'F'
            assert tbl['outputs'][3] == 'N'
            assert tbl['outputs'][8] == 'T'

        def test_models_with_opaques_observed_fail(self):
            # this was because sorting of constants had not been implemented.
            # it was only observed when we were sorting predicated sentences
            # that ended up in the opaques of a model.
            arg = parse_argument('VxMFx', ['VxUFxSyMFy', 'Fm'], vocab=self.vocab)
            proof = Tableau(self.logic, arg, is_build_models=True, max_steps=100)
            proof.build()
            assert proof.invalid
            for branch in proof.open:
                model = branch.model
                model.get_data()

@using(logic = 'K3WQ')
class TestK3WQ(BaseSuite):

    def test_valid_quantifier_interdefinability_1(self):
        self.valid_tab('Quantifier Interdefinability 1')

    def test_valid_quantifier_interdefinability_2(self):
        self.valid_tab('Quantifier Interdefinability 2')
        
    def test_valid_quantifier_interdefinability_3(self):
        self.valid_tab('Quantifier Interdefinability 3')

    def test_valid_quantifier_interdefinability_4(self):
        self.valid_tab('Quantifier Interdefinability 4')

    def test_valid_existential_to_if_a_then_a(self):
        self.valid_tab('CFmFm', 'SxFx')

    def test_model_existential_from_predicate_sentence_countermodel(self):
        s1, s2, s3 = self.pp('SxFx', 'Fm', 'Fn')
        arg = self.parg(s1, s2)
        m, = self.tab(arg, is_build_models = True).models
        assert m.value_of(s1) in {'F', 'N'}
        assert m.value_of(s2) == 'T'
        assert m.value_of(s3) == 'N'
        assert m.is_countermodel_to(arg)

    def test_model_universal_from_predicate_sentence_countermodel(self):
        s1, s2 = self.pp('VxFx', 'Fm')
        arg = self.parg(s1, s2)
        m, = self.tab(arg, is_build_models = True).models
        assert m.value_of(s1) in ('F', 'N')
        assert m.value_of(s2) == 'T'
        assert m.is_countermodel_to(arg)

@using(logic = 'B3E')
class TestB3E(BaseSuite):

    def test_truth_table_assertion(self):
        tbl = truth_table(self.logic, 'Assertion')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][2] == 'T'

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][3] == 'T'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][7] == 'F'

    def test_truth_table_biconditional(self):
        tbl = truth_table(self.logic, 'Biconditional')
        assert tbl['outputs'][2] == 'F'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][7] == 'F'
        
    def test_valid_cond_contraction(self):
        self.valid_tab('Conditional Contraction')

    def test_valid_bicond_elim_1(self):
        self.valid_tab('Biconditional Elimination 1')

    def test_valid_bicond_elim_3(self):
        self.valid_tab('Biconditional Elimination 3')

    def test_valid_bicond_intro_1(self):
        self.valid_tab('Biconditional Introduction 1')

    def test_invalid_lem(self):
        self.invalid_tab('Law of Excluded Middle')

    def test_invalid_prior_rule_defect(self):
        arg = self.parg('ANAabNa', 'Na')
        assert Tableau(self.logic, arg).build().invalid

    def test_valid_prior_rule_defect2(self):
        arg = self.parg('AANaTbNa', 'Na')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_asserted_addition(self):
        arg = self.parg('AaTb', 'a')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_cond_lem(self):
        arg = self.parg('AUabNUab')
        assert Tableau(self.logic, arg).build().valid

@using(logic = 'L3')
class TestL3(BaseSuite):
        
    def test_valid_cond_identity(self):
        self.valid_tab('Conditional Identity')

    def test_valid_cond_mp(self):
        self.valid_tab('Conditional Modus Ponens')

    def test_valid_bicond_elim_1(self):
        self.valid_tab('Biconditional Elimination 1')

    def test_valid_bicond_elim_3(self):
        self.valid_tab('Biconditional Elimination 3')

    def test_valid_bicond_intro_3(self):
        self.valid_tab('Biconditional Introduction 3')

    def test_valid_bicond_ident(self):
        self.valid_tab('Biconditional Identity')

    def test_valid_bicond_from_mat_bicond(self):
        self.valid_tab('Bab', 'Eab')

    def test_invalid_material_identify(self):
        self.invalid_tab('Material Identity')

    def test_invalid_cond_contraction(self):
        self.invalid_tab('Conditional Contraction')

    def test_invalid_cond_pseudo_contraction(self):
        self.invalid_tab('Conditional Pseudo Contraction')

    def test_invalid_mat_bicon_from_bicond(self):
        self.invalid_tab('Eab', 'Bab')

    def test_invalid_cond_lem(self):
        self.invalid_tab('AUabNUab')

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][3] == 'N'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][6] == 'F'

@using(logic = 'G3')
class TestG3(BaseSuite):

    def test_invalid_demorgan_8_model(self):
        tab = self.invalid_tab('DeMorgan 8')
        model = tab.open.first().model
        assert model.is_countermodel_to(tab.argument)

    def test_valid_demorgan_6(self):
        self.valid_tab('DeMorgan 6')

    def test_invalid_lem(self):
        self.invalid_tab('Law of Excluded Middle')

    def test_invalid_not_not_a_arrow_a(self):
        # Rescher p.45
        arg = self.parg('UNNaa')
        assert Tableau(self.logic, arg).build().invalid

    def test_invalid_not_a_arrow_not_b_arrow_b_arrow_a(self):
        # Rescher p.45
        arg = self.parg('UUNaNbUba')
        assert Tableau(self.logic, arg).build().invalid

    def test_valid_a_arrow_b_or_b_arrow_a(self):
        # Rescher p.45
        arg = self.parg('AUabUba')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_not_not_a_arrow_a_arrow_a_or_not_a(self):
        # Rescher p.45
        arg = self.parg('UUNNaaAaNa')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_a_dblarrow_a(self):
        arg = self.parg('Baa')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_a_dblarrow_b_thus_a_arrow_b_and_b_arrow_a(self):
        arg = self.parg('KUabUba', 'Bab')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_a_arrow_b_and_b_arrow_a_thus_a_dblarrow_b(self):
        arg = self.parg('Bab', 'KUabUba')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_not_a_arrow_b_or_not_b_arrow_a_thus_not_a_dblarrow_b(self):
        arg = self.parg('NBab', 'ANUabNUba')
        assert Tableau(self.logic, arg).build().valid

    def test_valid_not_a_dblarrow_b_thus_not_a_arrow_b_or_not_b_arrow_a(self):
        arg = self.parg('ANUabNUba', 'NBab')
        assert Tableau(self.logic, arg).build().valid

@using(logic = 'LP')
class TestLP(BaseSuite):

    def test_rule_GapClosure_eg(self):
        self.rule_eg('GapClosure')

    def test_valid_material_ident(self):
        assert self.tab('Material Identity').valid

    def test_case_model_not_a_countermodel(self):
        arg = self.parg('NBab', 'c', 'BcNUab')
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'F')
        model.set_literal_value(parse('b'), 'T')
        model.set_literal_value(parse('c'), 'B')
        assert model.value_of(arg.premises[1]) == 'B'

    def test_case_bad_rule_neg_bicond_undes(self):
        arg = self.parg('NBab', 'NBab')
        proof = Tableau(self.logic, arg)
        rule = proof.rules.BiconditionalNegatedUndesignated
        assert rule.get_target(proof[0])

    def test_invalid_lnc(self):
        assert self.tab('Law of Non-contradiction').invalid

    def test_valid_b_then_a_arrow_b(self):
        arg = self.parg('Uab', 'b')
        assert Tableau(self.logic, arg).build().valid

    def test_invalid_cond_modus_ponens(self):
        assert self.tab('Conditional Modus Ponens').invalid

    def test_valid_a_not_a_not_b_thus_not_a_arrow_b(self):
        proof = Tableau(self.logic, parse_argument('NUab', ['a', 'Na', 'Nb'])).build()
        assert proof.valid

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_a_arrow_b(self):
        proof = Tableau(self.logic, parse_argument('NUab', ['a', 'UaNUbc'])).build()
        assert not proof.valid

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_b_arrow_c(self):
        # this is an instance of modus ponens
        proof = Tableau(self.logic, parse_argument('NUbc', ['a', 'UaNUbc'])).build()
        assert not proof.valid

    def test_invalid_mp_with_neg_bicon(self):
        arg = self.parg('NBab', 'c', 'BcNUab')
        assert Tableau(self.logic, arg).build().invalid

@using(logic = 'RM3')
class TestRM3(BaseSuite):

    def test_truth_table_conditional(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'T'
        assert tbl['outputs'][2] == 'T'
        assert tbl['outputs'][3] == 'F'
        assert tbl['outputs'][4] == 'B'
        assert tbl['outputs'][5] == 'T'
        assert tbl['outputs'][6] == 'F'
        assert tbl['outputs'][7] == 'F'
        assert tbl['outputs'][8] == 'T'

    def test_model_value_of_biconditional(self):
        model = self.logic.Model()
        model.set_literal_value(parse('a'), 'B')
        model.set_literal_value(parse('b'), 'F')
        assert model.value_of(parse('Bab')) == 'F'

    def test_valid_cond_mp(self):
        proof = self.tab('Conditional Modus Ponens')
        assert proof.valid

    def test_valid_demorgan_1(self):
        proof = self.tab('DeMorgan 1')
        assert proof.valid

    def test_valid_demorgan_2(self):
        proof = self.tab('DeMorgan 2')
        assert proof.valid

    def test_valid_demorgan_3(self):
        proof = self.tab('DeMorgan 3')
        assert proof.valid

    def test_valid_demorgan_4(self):
        proof = self.tab('DeMorgan 4')
        assert proof.valid

    def test_invalid_b_then_a_arrow_b(self):
        arg = parse_argument('Uab', premises=['b'])
        proof = Tableau(self.logic, arg).build()
        assert not proof.valid

    def test_valid_cond_modus_ponens(self):
        proof = self.tab('Conditional Modus Ponens')
        assert proof.valid

    def test_invalid_a_a_arrow_not_b_arrow_c_thus_not_a_arrow_b(self):
        proof = Tableau(self.logic, parse_argument('NUab', ['a', 'UaNUbc'])).build()
        assert not proof.valid

    def test_valid_a_a_arrow_not_b_arrow_c_thus_not_b_arrow_c(self):
        # this is an instance of modus ponens
        proof = Tableau(self.logic, parse_argument('NUbc', ['a', 'UaNUbc'])).build()
        assert proof.valid

    def test_valid_bicond_thus_matbicond(self):
        arg = parse_argument('Eab', premises=['Bab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

    def test_invalid_matbicon_thus_bicond(self):
        arg = parse_argument('Bab', premises=['Eab'])
        proof = Tableau(self.logic, arg).build()
        assert not proof.valid

    def test_valid_mp_with_neg_bicon(self):
        arg = parse_argument('NBab', premises=['c', 'BcNUab'])
        proof = Tableau(self.logic, arg).build()
        assert proof.valid

@using(logic = 'GO')
class TestGO(BaseSuite):

    def test_truth_table_assertion(self):
        tbl = truth_table(self.logic, 'Assertion')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][2] == 'T'

    def test_truth_table_negation(self):
        tbl = truth_table(self.logic, 'Negation')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'N'
        assert tbl['outputs'][2] == 'F'

    def test_truth_table_disjunction(self):
        tbl = truth_table(self.logic, 'Disjunction')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][2] == 'T'

    def test_truth_table_conjunction(self):
        tbl = truth_table(self.logic, 'Conjunction')
        assert tbl['outputs'][0] == 'F'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][8] == 'T'

    def test_truth_table_mat_cond(self):
        tbl = truth_table(self.logic, 'Material Conditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'T'
        assert tbl['outputs'][4] == 'F'

    def test_truth_table_mat_bicond(self):
        tbl = truth_table(self.logic, 'Material Biconditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][1] == 'F'
        assert tbl['outputs'][4] == 'F'

    def test_truth_table_cond(self):
        tbl = truth_table(self.logic, 'Conditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][3] == 'F'
        assert tbl['outputs'][4] == 'T'

    def test_truth_table_bicond(self):
        tbl = truth_table(self.logic, 'Biconditional')
        assert tbl['outputs'][0] == 'T'
        assert tbl['outputs'][4] == 'T'
        assert tbl['outputs'][7] == 'F'

    def test_MaterialConditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NCab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('Na'), 'designated': False})
        assert branch.has({'sentence': parse('b'), 'designated': False})

    def test_MaterialBionditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('NEab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        assert b1.has({'sentence': parse('Na'), 'designated': False})
        assert b1.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('a'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConditionalDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('Uab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        assert b1.has({'sentence': parse('ANab'), 'designated': True})
        assert b2.has({'sentence': parse('a'), 'designated': False})
        assert b2.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': False})

    def test_ConditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('NUab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        assert b1.has({'sentence': parse('a'), 'designated': True})
        assert b1.has({'sentence': parse('b'), 'designated': False})
        assert b2.has({'sentence': parse('Na'), 'designated': False})
        assert b2.has({'sentence': parse('Nb'), 'designated': True})

    def test_BiconditionalDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Bab'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('Uab'), 'designated': True})
        assert branch.has({'sentence': parse('Uba'), 'designated': True})

    def test_BiconditionalNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        proof.branch().add({'sentence': parse('NBab'), 'designated': True})
        proof.step()
        b1, b2 = proof
        assert b1.has({'sentence': parse('NUab'), 'designated': True})
        assert b2.has({'sentence': parse('NUba'), 'designated': True})

    def test_AssertionUndesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Ta'), 'designated': False})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_AssertionNegatedDesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NTa'), 'designated': True})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': False})

    def test_AssertionNegatedUndesignated_step(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('NTa'), 'designated': False})
        proof.step()
        assert branch.has({'sentence': parse('a'), 'designated': True})

    def test_valid_neg_exist_from_univ(self):
        proof = self.tab('Quantifier Interdefinability 1')
        assert proof.valid

    def test_valid_neg_univ_from_exist(self):
        proof = self.tab('Quantifier Interdefinability 3')
        assert proof.valid

    def test_valid_demorgan_3(self):
        proof = self.tab('DeMorgan 3')
        assert proof.valid

    def test_invalid_demorgan_1(self):
        proof = self.tab('DeMorgan 1')
        assert not proof.valid

    def test_invalid_exist_from_neg_univ(self):
        proof = self.tab('Quantifier Interdefinability 2')
        assert not proof.valid

    def test_invalid_univ_from_neg_exist(self):
        proof = self.tab('Quantifier Interdefinability 4')
        assert not proof.valid

    def test_valid_prior_b3e_rule_defect2(self):
        arg = parse_argument('AANaTbNa', premises=['Na'], notn='polish')
        proof = Tableau(self.logic, arg)
        proof.build()
        assert proof.valid

    def test_branching_complexity_inherits_branchables(self):
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': parse('Kab'), 'designated': False})
        node = branch[0]
        assert self.logic.TableauxSystem.branching_complexity(node) == 0

@using(logic = 'MH')
class TestMH(BaseSuite):

    def test_valid_hmh_ax1(self):
        self.valid_tab('UaUba')

    def test_valid_hmh_ax2(self):
        self.valid_tab('UUaUbcUUabUac')

    def test_valid_hmh_ax3(self):
        self.valid_tab('UKaba')

    def test_valid_hmh_ax4(self):
        self.valid_tab('UKabb')

    def test_valid_hmh_ax5(self):
        self.valid_tab('UUabUUacUaKbc')

    def test_valid_hmh_ax6(self):
        self.valid_tab('UaAab')

    def test_valid_hmh_ax7(self):
        self.valid_tab('UbAab')

    def test_valid_hmh_ax8(self):
        self.valid_tab('UUacUUbcUAabc')

    def test_valid_hmh_ax9(self):
        self.valid_tab('BNNaa')

    def test_valid_hmh_ax10(self):
        self.valid_tab('AAaNaNAaNa')

    def test_valid_hmh_ax11(self):
        self.valid_tab('AUabNUab')

    def test_valid_hmh_ax12(self):
        self.valid_tab('UAaNaUUabUNbNa')

    def test_valid_hmh_ax13(self):
        self.valid_tab('BNKabANaNb')

    def test_valid_hmh_ax14(self):
        self.valid_tab('BNAabAKNaNbKNAaNaNAbNb')

    def test_valid_hmh_ax15(self):
        self.valid_tab('UANaNAaNaUab')

    def test_valid_hmh_ax16(self):
        self.valid_tab('UKaANbNAbNbNUab')

    def test_valid_mp(self):
        self.valid_tab('Conditional Modus Ponens')

    def test_valid_inden(self):
        self.valid_tab('Uaa')

    def test_valid_ifn(self):
        self.valid_tab('BNAaNaNANaNNa')

    def test_valid_adj(self):
        self.valid_tab('Kab', 'a', 'b')

    def test_invalid_p(self):
        self.invalid_tab('UNbNa', 'NAaNa', 'Uab')

@using(logic = 'NH')
class TestNH(BaseSuite):

    logic = get_logic('NH')

    def test_valid_hnh_ax1(self):
        self.valid_tab('UaUba')

    def test_valid_hnh_ax2(self):
        self.valid_tab('UUaUbcUUabUac')

    def test_valid_hnh_ax3(self):
        self.valid_tab('UKaba')

    def test_valid_hnh_ax4(self):
        self.valid_tab('UKabb')

    def test_valid_hnh_ax5(self):
        self.valid_tab('UUabUUacUaKbc')

    def test_valid_hnh_ax6(self):
        self.valid_tab('UaAab')

    def test_valid_hnh_ax7(self):
        self.valid_tab('UbAab')

    def test_valid_hnh_ax8(self):
        self.valid_tab('UUacUUbcUAabc')

    def test_valid_hnh_ax9(self):
        self.valid_tab('BNNaa')

    def test_valid_hnh_ax17(self):
        self.valid_tab('NKKaNaNKaNa')

    def test_valid_hnh_ax18(self):
        self.valid_tab('NKUabNUab')

    def test_valid_hnh_ax19(self):
        self.valid_tab('UNKaNaUUbaUNaNb')

    def test_valid_hnh_ax20(self):
        self.valid_tab('BKNaNbNAab')

    def test_valid_hnh_ax21(self):
        self.valid_tab('BANaNbANKabKKaNaKbNb')

    def test_valid_hnh_ax22(self):
        self.valid_tab('UKNKaNaNaUab')

    def test_valid_hnh_ax23(self):
        self.valid_tab('UKaKNKbNbNbNUab')

    def test_invalid_efq(self):
        self.invalid_tab('b', 'KaNa')

    def test_valid_lem(self):
        self.valid_tab('AbNb', 'a')

    def test_invalid_dem(self):
        self.invalid_tab('NAab', 'ANaNb')

@using(logic = 'P3')
class TestP3(BaseSuite):

    logic = get_logic('P3')

    def test_rule_DoubleNegationDesignated_eg(self):
        rule, tab = self.rule_eg('DoubleNegationDesignated')
        assert tab[0].has_all([
            {'sentence': parse('a'), 'designated': False},
            {'sentence': parse('Na'), 'designated': False},
        ])

    def test_rule_ConjunctionUndesignated_eg(self):
        self.rule_eg('ConjunctionUndesignated')

    def test_rule_MaterialConditionalDesignated_eg(self):
        self.rule_eg('MaterialConditionalDesignated')

    def test_rule_UniversalNegatedDesignated_eg(self):
        self.rule_eg('UniversalNegatedDesignated')

    def test_invalid_lem(self):
        proof = self.tab('Law of Excluded Middle')
        assert proof.invalid

    def test_invalid_demorgan_1(self):
        assert self.tab('DeMorgan 1').invalid

    def test_invalid_demorgan_2(self):
        assert self.tab('DeMorgan 2').invalid

    def test_invalid_demorgan_3(self):
        assert self.tab('DeMorgan 3').invalid

    def test_invalid_demorgan_4(self):
        assert self.tab('DeMorgan 4').invalid

    def test_invalid_demorgan_5(self):
        assert self.tab('DeMorgan 5').invalid

    def test_valid_demorgan_6(self):
        assert self.tab('DeMorgan 6').valid

@using(logic = 'CPL')
class TestCPL(BaseSuite):
  
    def test_valid_simplification(self):
        self.valid_tab('Simplification')

    def test_valid_optimize_group_score_from_candidate_score(self):
        tab = self.valid_tab('Na', ('Cab', 'Nb', 'Acd'))
        assert len(tab) == 2

    def test_invalid_syllogism(self):
        self.invalid_tab('Syllogism')

    def test_rule_ContradictionClosure_eg(self):
        self.rule_eg('ContradictionClosure')

    def test_rule_SelfIdentityClosure_eg(self):
        self.rule_eg('SelfIdentityClosure')

    def test_rule_NonExistenceClosure_eg(self):
        self.rule_eg('NonExistenceClosure')

    def test_rule_IdentityIndiscernability_eg(self):
        self.rule_eg('IdentityIndiscernability')

    def test_rule_IdentityIndiscernability_not_applies(self):
        vocab = Predicates()
        vocab.add((0, 0, 2))
        proof = Tableau(self.logic)
        s1 = parse('Fmn', vocab=vocab)
        s2 = parse('Io1o2')
        branch = proof.branch()
        branch.extend([
            {'extend': s1, 'world': 0},
            {'sentence': s2, 'world': 0},
        ])
        rule = proof.rules.IdentityIndiscernability
        assert not rule.get_target(branch)

    def test_model_branch_deny_antec(self):
        proof = self.tab('Denying the Antecedent')
        model = self.logic.Model()
        branch = proof.open.first()
        model.read_branch(branch)
        s = Atomic(0, 0)
        assert model.value_of(s) == 'F'
        assert model.value_of(s.negate()) == 'T'

    def test_model_branch_extract_disj_2(self):
        proof = self.tab('Extracting a Disjunct 2')
        model = self.logic.Model()
        branch = proof.open.first()
        model.read_branch(branch)
        s = Atomic(0, 0)
        assert model.value_of(s) == 'T'
        assert model.value_of(s.negate()) == 'F'

    def test_model_branch_no_proof_predicated(self):
        branch = Branch()
        s1 = parse('Fm', vocab=examples.vocabulary)
        branch.add({'sentence': s1})
        model = self.logic.Model()
        model.read_branch(branch)
        assert model.value_of(s1) == 'T'
        
    def test_model_add_access_not_impl(self):
        model = self.logic.Model()
        with raises(NotImplementedError):
            model.add_access(0, 0)

    def test_model_value_of_operated_opaque(self):
        # coverage
        model = self.logic.Model()
        s = parse('La')
        model.set_opaque_value(s, 'T')
        assert model.value_of_operated(s) == 'T'
        
    def test_model_set_literal_value_predicated1(self):
        model = self.logic.Model()
        m = Constant(0, 0)
        n = Constant(1, 0)
        s = Predicated('Identity', [m, n])
        model.set_literal_value(s, 'T')
        res = model.value_of(s)
        assert res == 'T'

    def test_model_opaque_necessity_branch_make_model(self):
        s = parse('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s})
        model = self.logic.Model().read_branch(branch)
        assert model.value_of(s) == 'T'

    def test_model_opaque_neg_necessity_branch_make_model(self):
        s = parse('La')
        proof = Tableau(self.logic)
        branch = proof.branch()
        branch.add({'sentence': s.negate()})
        model = self.logic.Model().read_branch(branch)
        assert model.value_of(s) == 'F'

    def test_model_get_data_triv(self):
        s = parse('a')
        model = self.logic.Model()
        model.set_literal_value(s, 'T')
        model.finish()
        data = model.get_data()
        assert 'Atomics' in data

    def test_model_value_of_operated_opaque1(self):
        s1 = parse('La')
        model = self.logic.Model()
        model.set_opaque_value(s1, 'F')
        res = model.value_of_operated(s1.negate())
        assert res == 'T'

    def test_model_value_of_opaque_unassigned(self):
        s = parse('La')
        model = self.logic.Model()
        res = model.value_of(s)
        assert res == model.unassigned_value

    def test_model_set_predicated_false_value_error_on_set_to_true(self):
        s = parse('Fm', vocab=examples.vocabulary)
        model = self.logic.Model()
        model.set_literal_value(s, 'F')
        with raises(ModelValueError):
            model.set_literal_value(s, 'T')

    def test_model_get_anti_extension(self):
        # coverage
        s = self.p('Fm')
        model = self.logic.Model()
        pred = s.predicate
        anti_extension = model.get_anti_extension(pred)
        assert len(anti_extension) == 0
        model.set_literal_value(s, 'F')
        assert s.params in anti_extension

@using(logic = 'CFOL')
class TestCFOL(BaseSuite):

    def test_valid_syllogism(self):
        self.valid_tab('Syllogism')

    def test_invalid_possibility_addition(self):
        self.invalid_tab('Possibility Addition')

    def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
        self.valid_tab('b', 'VxKFxKaNa')

    def test_invalid_existential_inside_univ_max_steps(self):
        self.invalid_tab('b', 'VxUFxSyFy', max_steps = 100)

    def test_model_get_data_triv(self):
        m = self.logic.Model()
        s1 = self.p('a')
        m.set_literal_value(s1, 'T')
        m.finish()
        assert 'Atomics' in m.get_data()

    def test_model_value_of_operated_opaque1(self):
        m = self.logic.Model()
        s1 = self.p('La')
        m.set_opaque_value(s1, 'F')
        assert m.value_of_operated(s1.negate()) == 'T'

    def test_model_value_of_operated_opaque2(self):
        m = self.logic.Model()
        s1 = self.p('La')
        m.set_opaque_value(s1, 'T')
        assert m.value_of_operated(s1) == 'T'

    def test_model_read_node_opaque(self):
        m = self.logic.Model()
        s1 = self.p('La')
        m.read_node(Node({'sentence': s1}))
        assert m.value_of(s1) == 'T'

    def test_model_add_access_not_impl(self):
        m = self.logic.Model()
        with raises(NotImplementedError):
            m.add_access(0, 0)

    def test_model_read_branch_with_negated_opaque_then_faithful(self):
        tab = self.tab('a', ('NLa', 'b'), is_build_models = True)
        m, = tab.models
        s1, s2, s3 = self.pp('a', 'La', 'NLa')
        assert m.value_of(s1) == 'F'
        assert m.value_of(s2) == 'F'
        assert m.value_of(s3) == 'T'
        assert m.is_countermodel_to(tab.argument)

    def test_model_quantified_opaque_is_countermodel(self):
        # For this we needed to add constants that occur within opaque sentences.
        # The use of the existential is important given the way the K model
        # computes quantified values (short-circuit), as opposed to FDE (min/max).
        tab = self.tab('b', 'SxUNFxSyMFy', is_build_models = True)
        arg = tab.argument
        assert len(tab) == 2
        assert len(tab.models) == 2
        m1, m2 = tab.models
        assert m1.is_countermodel_to(arg)
        assert m2.is_countermodel_to(arg)

    def test_model_identity_predication1(self):
        m = self.logic.Model()
        s1, s2, s3 = self.pp('Fm', 'Imn', 'Fn')
        for s in (s1, s2):
            m.set_literal_value(s, 'T')
        m.finish()
        assert m.value_of(s3) == 'T'

    def test_model_identity_predication2(self):
        m = self.logic.Model()
        s1, s2, s3 = self.pp('Fm', 'Imn', 'Fn')
        for s in (s1, s2):
            m.set_literal_value(s, 'T')
        m.finish()
        assert m.value_of(s3) == 'T'

    def test_model_self_identity1(self):
        m = self.logic.Model()
        s1, s2 = self.pp('Fm', 'Imm')
        # here we make sure the constant m is registered
        m.set_literal_value(s1, 'F')
        m.finish()
        assert m.value_of(s2) == 'T'

    def test_model_raises_denotation_error(self):
        m = self.logic.Model()
        s1 = self.p('Imm')
        m.finish()
        with raises(DenotationError):
            m.value_of(s1)

    def test_model_get_identicals_singleton_two_identical_constants(self):
        m = self.logic.Model()
        s1 = self.p('Imn')
        c1, c2 = s1.params
        m.set_literal_value(s1, 'T')
        m.finish()
        identicals = m.get_identicals(c1)
        assert len(identicals) == 1
        assert c2 in identicals

    def test_model_singleton_domain_two_identical_constants(self):
        m = self.logic.Model()
        s1 = self.p('Imn')
        m.set_literal_value(s1, 'T')
        m.finish()
        d = m.get_domain()
        assert len(d) == 1

    def test_model_same_denotum_two_identical_constants(self):
        m = self.logic.Model()
        s1 = self.p('Imn')
        m.set_literal_value(s1, 'T')
        m.finish()
        d1, d2 = (m.get_denotum(c) for c in s1.params)
        assert d1 is d2

@using(logic = 'K')
class Test_K(BaseSuite):
    
    class Test_Tableaux(BaseSuite):

        class Test_Closure(BaseSuite):

            def test_ContradictionClosure(self):
                self.rule_eg('ContradictionClosure')
                self.valid_tab('EFQ')

            def test_SelfIdentityClosure(self):
                self.rule_eg('SelfIdentityClosure')
                self.valid_tab('Self Identity 1')

            def test_NonExistenceClosure(self):
                self.rule_eg('NonExistenceClosure')
                self.valid_tab('b', 'NJm')

        class Test_Operators(BaseSuite):

            def test_Assertion(self):
                rule, tab = self.rule_eg('Assertion')
                rule, tab = self.rule_eg('AssertionNegated')

                self.valid_tab('Assertion Elimination 1')
                self.valid_tab('Assertion Elimination 2')

            def test_Negation(self):
                rule, tab = self.rule_eg('DoubleNegation')

            def test_Conjunction(self):
                rule, tab = self.rule_eg('Conjunction')
                rule, tab = self.rule_eg('ConjunctionNegated')

                self.valid_tab('Conjunction Introduction')

            def test_Disjunction(self):
                rule, tab = self.rule_eg('Disjunction')
                rule, tab = self.rule_eg('DisjunctionNegated')

                rule, tab = self.rule_eg('DisjunctionNegated', step = False)
                node = tab[0][0]
                assert node['sentence'].operator == Oper.Negation
                self.valid_tab('Addition')
                self.valid_tab('LEM')
                self.valid_tab('Disjunctive Syllogism')
                self.valid_tab('Disjunctive Syllogism 2')

            def test_MaterialConditional(self):
                rule, tab = self.rule_eg('MaterialConditional')
                rule, tab = self.rule_eg('MaterialConditionalNegated')
                self.valid_tab('MMP')
                self.valid_tab('MMT')

            def test_MaterialBiconditional(self):
                rule, tab = self.rule_eg('MaterialBiconditional')
                rule, tab = self.rule_eg('MaterialBiconditionalNegated')
                self.valid_tab('Material Biconditional Elimination 1')
                self.valid_tab('Material Biconditional Introduction 1')

            def test_Conditional(self):
                rule, tab = self.rule_eg('Conditional')
                rule, tab = self.rule_eg('ConditionalNegated')
                self.valid_tab('MP')
                self.valid_tab('MT')
                self.invalid_tab('Denying the Antecedent')

            def test_Biconditional(self):
                rule, tab = self.rule_eg('Biconditional')
                rule, tab = self.rule_eg('BiconditionalNegated')

        class Test_ModalOperators(BaseSuite):

            def test_Necessity(self):
                srule, tab = self.rule_eg('Necessity')
                srule, tab = self.rule_eg('NecessityNegated')
                self.invalid_tab('Necessity Elimination')

            def test_Possibility(self):
                srule, tab = self.rule_eg('Possibility')
                srule, tab = self.rule_eg('PossibilityNegated')
                rule, tab = self.rule_eg('Possibility', step = False)
                node = tab[0][0]
                assert node['world'] == 0

            def test_modal_transformation(self):
                self.valid_tab('Modal Transformation 2')

            @skip
            def test_invalid_nested_diamond_within_box1(self):
                self.invalid_tab('KMNbc', ('LCaMNb', 'Ma'))

            @skip
            def test_Arguments_2(self):
                self.valid_tab('Necessity Distribution 1')
                self.invalid_tab('S4 Conditional Inference 2')

        class Test_Quantifiers(BaseSuite):

            def test_Universal(self):
                rule, tab = self.rule_eg('Universal')
                rule, tab = self.rule_eg('UniversalNegated')

            def test_Existential(self):
                rule, tab = self.rule_eg('Existential')
                rule, tab = self.rule_eg('ExistentialNegated')
                rule, tab = self.rule_eg('Existential', step = False)
                node = tab[0][0]
                assert node['sentence'].quantifier == Existential

            def test_valid_regression_efq_univeral_with_contradiction_no_constants(self):
                self.valid_tab('b', 'VxKFxKaNa')

            def test_invalid_existential_inside_univ_max_steps(self):
                self.invalid_tab('b', 'VxUFxSyFy', max_steps = 100)

        class Test_Identity(BaseSuite):

            def test_regresion(self):
                rule, tab = self.rule_eg('IdentityIndiscernability')
                self.valid_tab('Identity Indiscernability 1')
                self.valid_tab('Identity Indiscernability 2')

            def test_IdentityIndiscernability(self):
                rule, tab = self.rule_eg('IdentityIndiscernability')
                b = tab.branch().extend((
                    {'sentence': self.p('Imm'), 'world': 0},
                    {'sentence': self.p('Fs'),  'world': 0},
                ))
                assert not rule.get_target(b)

    class Test_Models(BaseSuite):

        class Test_RefatorBugs(BaseSuite):

            def test_model_branch_proof_deny_antec(self):
                tab = self.tab('Denying the Antecedent')
                model = self.logic.Model()
                branch = tab.open.first()
                model.read_branch(branch)
                s = Atomic(0, 0)
                assert model.value_of(s, world=0) == 'F'
                assert model.value_of(s.negate(), world=0) == 'T'

        class TestModel_Atomics(BaseSuite):

            def test_model_value_of_atomic_unassigned(self):
                model = self.logic.Model()
                s = Atomic(0, 0)
                res = model.value_of_atomic(s)
                assert res == model.unassigned_value

            def test_model_branch_no_proof_atomic(self):
                model = self.logic.Model()
                branch = Branch()
                branch.add({'sentence': Atomic(0, 0), 'world': 0})
                model.read_branch(branch)
                assert model.value_of(Atomic(0, 0), world=0) == 'T'

        class TestModel_Opaques(BaseSuite):

            def test_finish_every_opaque_has_value_in_every_frame(self):
                s1, s2 = self.pp('a', 'b')
                # s2 = self.p('b')
                model = self.logic.Model()
                model.set_opaque_value(s1, 'T', world=0)
                model.set_opaque_value(s2, 'T', world=1)
                model.finish()
                f1 = model.world_frame(0)
                f2 = model.world_frame(1)
                assert s2 in f1.opaques
                assert s1 in f2.opaques

        class TestModel_Predication(BaseSuite):

            def test_branch_no_proof_predicated(self):
                model = self.logic.Model()
                branch = Branch()
                s1 = parse('Imn')
                branch.add({'sentence': s1, 'world': 0})
                model.read_branch(branch)
                assert model.value_of(s1, world=0) == 'T'

            def test_set_predicated_value1(self):
                model = self.logic.Model()
                s = Identity(tuple(Constant.gen(2)))
                model.set_predicated_value(s, 'T', world=0)
                res = model.value_of(s, world=0)
                assert res == 'T'

            def test_get_extension_adds_predicate_to_predicates(self):
                # coverage
                s1 = self.p('Fm')
                model = self.logic.Model()
                res = model.get_extension(s1.predicate)
                assert len(res) == 0
                assert s1.predicate in model.predicates

            def test_model_identity_extension_non_empty_with_sentence(self):
                s = self.p('Imn')
                model = self.logic.Model()
                model.set_predicated_value(s, 'T', world=0)
                extension = model.get_extension(Identity, world=0)
                assert len(extension) > 0
                assert (Constant(0, 0), Constant(1, 0)) in extension

        class TestModel_ModalAccess(BaseSuite):

            def test_model_branch_no_proof_access(self):
                model = self.logic.Model()
                branch = Branch()
                branch.add({'world1': 0, 'world2': 1})
                model.read_branch(branch)
                assert model.has_access(0, 1)

            def test_model_add_access_sees(self):
                model = self.logic.Model()
                model.add_access(0, 0)
                assert 0 in model.visibles(0)

            def test_model_possibly_a_with_access_true(self):
                model = self.logic.Model()
                a = Atomic(0, 0)
                model.add_access(0, 1)
                model.set_atomic_value(a, 'T', world=1)
                res = model.value_of(Oper.Possibility(a), world=0)
                assert res == 'T'

            def test_model_possibly_a_no_access_false(self):
                model = self.logic.Model()
                a = Atomic(0, 0)
                model.set_atomic_value(a, 'T', world=1)
                res = model.value_of(Operated('Possibility', a), world=0)
                assert res == 'F'

            def test_model_nec_a_no_access_true(self):
                model = self.logic.Model()
                a = Atomic(0, 0)
                res = model.value_of(Operated('Necessity', a), world=0)
                assert res == 'T'

            def test_model_nec_a_with_access_false(self):
                model = self.logic.Model()
                a = Atomic(0, 0)
                model.set_atomic_value(a, 'T', world=0)
                model.set_atomic_value(a, 'F', world=1)
                model.add_access(0, 1)
                model.add_access(0, 0)
                res = model.value_of(Operated('Necessity', a), world=0)
                assert res == 'F'

            def test_model_get_data_with_access_has_2_frames(self):
                model = self.logic.Model()
                model.set_literal_value(self.p('a'), 'T', world=0)
                model.add_access(0, 1)
                model.finish()
                data = model.get_data()
                assert len(data['Frames']['values']) == 2

        class TestModel_Quantification(BaseSuite):

            def test_model_existence_user_pred_true(self):
                pred, x = Predicate.first(), Variable.first()
                s1, s2 = pred(Constant.first()), pred(x)
                s3 = Existential(x, s2)
                model = self.logic.Model()
                model.set_predicated_value(s1, 'T', world=0)
                res = model.value_of(s3, world=0)
                assert res == 'T'

            def test_model_existense_user_pred_false(self):
                pred = Predicate(0, 0, 1)
                m = Constant(0, 0)
                x = Variable(0, 0)
                s1 = Predicated(pred, [m])
                s2 = Predicated(pred, [x])
                s3 = Quantified('Existential', x, s2)

                model = self.logic.Model()
                res = model.value_of(s3, world=0)
                assert res == 'F'

            def test_model_universal_user_pred_true(self):
                pred = Predicate(0, 0, 1)
                m = Constant(0, 0)
                x = Variable(0, 0)
                s1 = Predicated(pred, [m])
                s2 = Predicated(pred, [x])
                s3 = Quantified('Universal', x, s2)

                model = self.logic.Model()
                model.set_predicated_value(s1, 'T', world=0)
                res = model.value_of(s3, world=0)
                assert res == 'T'

            def test_model_universal_false(self):
                s1 = self.p('VxFx')
                s2 = self.p('Fm')
                model = self.logic.Model()
                model.set_predicated_value(s2, 0, world=0)
                res = model.value_of(s1, world=0)
                assert res == 'F'

            def test_model_universal_user_pred_false(self):
                pred = Predicate(0, 0, 1)
                m = Constant(0, 0)
                n = Constant(1, 0)
                x = Variable(0, 0)
                s1 = Predicated(pred, [m])
                s2 = Predicated(pred, [x])
                s3 = Predicated(pred, [n])
                s4 = Quantified('Universal', x, s2)
            
                model = self.logic.Model()
                model.set_predicated_value(s1, 'T', world=0)
                model.set_predicated_value(s3, 'F', world=0)
                res = model.value_of(s4, world=0)
                assert res == 'F'

        class TestModel_Frame(BaseSuite):

            def test_difference_atomic_keys_diff(self):
                model = self.logic.Model()
                model.set_literal_value(self.p('a'), 'T', world=0)
                model.set_literal_value(self.p('b'), 'T', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert not frame_a.is_equivalent_to(frame_b)
                assert not frame_b.is_equivalent_to(frame_a)

            def test_difference_atomic_values_diff(self):
                model = self.logic.Model()
                s1 = self.p('a')
                model.set_literal_value(s1, 'T', world=0)
                model.set_literal_value(s1, 'F', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert not frame_a.is_equivalent_to(frame_b)
                assert not frame_b.is_equivalent_to(frame_a)

            def test_difference_atomic_values_equiv(self):
                model = self.logic.Model()
                s1 = self.p('a')
                model.set_literal_value(s1, 'T', world=0)
                model.set_literal_value(s1, 'T', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert frame_a.is_equivalent_to(frame_b)
                assert frame_b.is_equivalent_to(frame_a)

            def test_difference_opaque_keys_diff(self):
                model = self.logic.Model()
                model.set_opaque_value(self.p('Ma'), 'T', world=0)
                model.set_opaque_value(self.p('Mb'), 'T', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert not frame_a.is_equivalent_to(frame_b)
                assert not frame_b.is_equivalent_to(frame_a)

            def test_difference_opaque_values_diff(self):
                s1 = self.p('Ma')
                model = self.logic.Model()
                model.set_opaque_value(s1, 'T', world=0)
                model.set_opaque_value(s1, 'F', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert not frame_a.is_equivalent_to(frame_b)
                assert not frame_b.is_equivalent_to(frame_a)

            def test_difference_opaque_values_equiv(self):
                model = self.logic.Model()
                model.set_opaque_value(parse('Ma'), 'T', world=0)
                model.set_opaque_value(parse('Ma'), 'T', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert frame_a.is_equivalent_to(frame_b)
                assert frame_b.is_equivalent_to(frame_a)

            def test_difference_extension_keys_diff(self):
                vocab = Predicates((0, 0, 1), (1, 0, 2))
                s1, s2 = self.pp('Fm', 'Gmn', vocab)
                model = self.logic.Model()
                model.set_predicated_value(s1, 'T', world=0)
                model.set_predicated_value(s2, 'T', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert not frame_a.is_equivalent_to(frame_b)
                assert not frame_b.is_equivalent_to(frame_a)

            def test_difference_extension_values_diff(self):
                s1 = self.p('Fm')
                s2 = self.p('Fn')
                model = self.logic.Model()
                model.set_predicated_value(s1, 'T', world=0)
                model.set_predicated_value(s2, 'T', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert not frame_a.is_equivalent_to(frame_b)
                assert not frame_b.is_equivalent_to(frame_a)

            def test_difference_extension_values_equiv(self):
                s1 = self.p('Fm')
                s2 = self.p('Fn')
                model = self.logic.Model()
                model.set_predicated_value(s1, 'T', world=0)
                model.set_predicated_value(s2, 'F', world=0)
                model.set_predicated_value(s1, 'T', world=1)
                model.set_predicated_value(s2, 'F', world=1)
                frame_a = model.world_frame(0)
                frame_b = model.world_frame(1)
                assert frame_a.is_equivalent_to(frame_b)
                assert frame_b.is_equivalent_to(frame_a)

            def test_not_equals(self):
                s = self.p('a')
                model1 = self.logic.Model()
                model2 = self.logic.Model()
                model1.set_literal_value(s, 'T', world=0)
                model2.set_literal_value(s, 'F', world=0)
                f1 = model1.world_frame(0)
                f2 = model2.world_frame(0)
                assert f1 != f2

            def test_not_equals(self):
                s = self.p('a')
                model1 = self.logic.Model()
                model2 = self.logic.Model()
                model1.set_literal_value(s, 'T', world=0)
                model2.set_literal_value(s, 'T', world=0)
                f1 = model1.world_frame(0)
                f2 = model2.world_frame(0)
                assert f1 == f2

            def test_ordering(self):
                s = self.p('a')
                model = self.logic.Model()
                model.set_literal_value(s, 'T', world=0)
                model.set_literal_value(s, 'F', world=1)
                f1 = model.world_frame(0)
                f2 = model.world_frame(1)
                assert f2 > f1
                assert f1 < f2
                assert f2 >= f1
                assert f1 <= f2

            def test_data_has_identity_with_sentence(self):
                s = self.p('Imn')
                model = self.logic.Model()
                model.set_predicated_value(s, 'T', world=0)
                model.finish()
                data = model.get_data()
                assert len(data['Frames']['values']) == 1
                fdata = data['Frames']['values'][0]['value']
                assert len(fdata['Predicates']['values']) == 2
                pdata = fdata['Predicates']['values'][1]
                assert pdata['values'][0]['input'].name == 'Identity'

        class TestModeCounterModel(BaseSuite):

            def test_countermodel_to_false1(self):
                arg = self.parg('b', 'a')
                s1, = arg.premises
                model = self.logic.Model()
                model.set_literal_value(s1, 'F')
                model.set_literal_value(arg.conclusion, 'T')
                assert not model.is_countermodel_to(arg)

        class TestModel_Error(BaseSuite):

            def test_not_impl_various(self):
                s1 = self.p('Aab')
                model = self.logic.Model()
                with raises(NotImplementedError):
                    model.set_literal_value(s1, 'T')
                with raises(NotImplementedError):
                    model.value_of_modal(s1)
                with raises(NotImplementedError):
                    model.value_of_quantified(s1)

            def test_value_error_various(self):
                s1, s2 = self.pp('a', 'Fm')
                model = self.logic.Model()
                model.set_opaque_value(s1, 'T')
                with raises(ModelValueError):
                    model.set_opaque_value(s1, 'F')
                model = self.logic.Model()
                model.set_atomic_value(s1, 'T')
                with raises(ModelValueError):
                    model.set_atomic_value(s1, 'F')
                model.set_predicated_value(s2, 'T')
                with raises(ModelValueError):
                    model.set_predicated_value(s2, 'F')

@using(logic = 'D')
class TestD(BaseSuite):

    logic = get_logic('D')

    def test_valid_long_serial_max_steps_50(self):
        self.valid_tab('MMMMMa', 'LLLLLa', max_steps = 50)

    def test_valid_serial_inf_1(self):
        self.valid_tab('Serial Inference 1')

    def test_invalid_reflex_inf_1(self):
        self.invalid_tab('Reflexive Inference 1')

    def test_invalid_optimize_nec_rule1_max_steps_50(self):
        self.invalid_tab('NLVxNFx', 'LMSxFx', max_steps = 50)

    def test_invalid_s4_cond_inf_2(self):
        self.invalid_tab('S4 Conditional Inference 2')

    def test_rule_Serial_eg(self):
        self.rule_eg('Serial')

    def test_rule_Serial_not_applies_to_branch_empty(self):
        tab = self.tab()
        rule = tab.rules.Serial
        assert not rule.get_target(tab.branch())

    def test_verify_core_bugfix_branch_should_not_have_w1_with_more_than_one_w2(self):
        tab = self.tab('CaLMa')
        # sanity check
        assert len(tab) == 1
        b = tab[0]
        # use internal properties just to be sure, since the bug was with the .find method
        access = {}
        for node in b:
            if 'world1' in node:
                w1 = node['world1']
                w2 = node['world2']
                if w1 not in access:
                    # use a list to also make sure we don't have redundant nodes
                    access[w1] = list()
                access[w1].append(w2)
        for w1 in access:
            assert len(access[w1]) == 1
        assert len(access) == (b.world_count - 1)
        # sanity check
        assert b.world_count > 2

@using(logic = 'T')
class TestT(BaseSuite):

    logic = get_logic('T')

    def test_valid_np_collapse_1(self):
        self.valid_tab('NP Collapse 1')

    def test_invalid_s4_material_inf_1(self):
        self.invalid_tab('S4 Material Inference 1')

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx', 'LMSxFx', build_timeout = 1000)

    def test_invalid_s4_cond_inf_2(self):
        self.invalid_tab('S4 Conditional Inference 2')

    def test_rule_Reflexive_eg(self):
        rule, tab = self.rule_eg('Reflexive')
        b, = tab
        assert b.has({'world1': 0, 'world2': 0})

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):
        # Rule ordering benchmark result:
        
        #           [# non-branching rules]
        #                 [S4:Transitive]
        #           [Necessity, Possibility]
        #                 [T:Reflexive]
        #           [# branching rules]
        #         - [Existential, Universal]
        #                 [S5:Symmetric]
        #             [D:Serial],
        #       S5: 8 branches, 142 steps
        #       S4: 8 branches, 132 steps
        #        T: 8 branches, 91 steps
        #        D: 8 branches, 57 steps

        # 200 might be agressive
        self.invalid_tab('b', 'LVxSyUFxLMGy', max_steps = 200)

@using(logic = 'S4')
class TestS4(BaseSuite):

    logic = get_logic('S4')

    def test_valid_s4_material_inf_1(self):
        self.valid_tab('S4 Material Inference 1')

    def test_valid_np_collapse_1(self):
        self.valid_tab('NP Collapse 1')

    def test_valid_s4_complex_possibility_with_max_steps(self):
        self.valid_tab('MNb', ['LCaMMMNb', 'Ma'], max_steps = 200)

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx', 'LMSxFx', build_timeout = 1000)

    def test_valid_s4_cond_inf_2(self):
        self.valid_tab('S4 Conditional Inference 2')

    def test_invalid_s5_cond_inf_1(self):
        self.invalid_tab('S5 Conditional Inference 1')

    def test_invalid_problematic_1_with_timeout(self):
        self.invalid_tab('b', 'LMa', build_timeout = 2000)

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc', ['LCaMNb', 'Ma'])

    def test_rule_Transitive_eg(self):
        rule, tab = self.rule_eg('Transitive')
        b, = tab
        assert b.has({'world1': 0, 'world2': 2})

    def test_model_finish_transitity_visibles(self):
        model = self.logic.Model()
        model.add_access(0, 1)
        model.add_access(1, 2)
        model.finish()
        assert 2 in model.visibles(0)

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):

        # Rule ordering benchmark result:
        
        #           [# non-branching rules]
        #                 [S4:Transitive]
        #           [Necessity, Possibility]
        #                 [T:Reflexive]
        #           [# branching rules]
        #         - [Existential, Universal]
        #                 [S5:Symmetric]
        #             [D:Serial],
        #       S5: 8 branches, 142 steps
        #       S4: 8 branches, 132 steps
        #        T: 8 branches, 91 steps
        #        D: 8 branches, 57 steps

        # 200 might be agressive
        self.invalid_tab('b', 'LVxSyUFxLMGy', max_steps = 200)

@using(logic = 'S5')
class TestS5(BaseSuite):

    logic = get_logic('S5')

    def test_valid_s4_cond_inf_2(self):
        self.valid_tab('S4 Conditional Inference 2')

    def test_valid_s5_cond_inf_1(self):
        self.valid_tab('S5 Conditional Inference 1')

    def test_valid_s4_complex_possibility_with_max_steps(self):
        self.valid_tab('MNb', ('LCaMMMNb', 'Ma'), max_steps = 200)

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx', 'LMSxFx', build_timeout = 1000)

    def test_valid_intermediate_mix_modal_quantifiers1(self):

        # For this we needed to put Universal and Existential rules
        # in the same group, and toward the end.

        self.valid_tab('MSxGx', ('VxLSyUFxMGy', 'Fm'), max_steps = 100)

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc', ('LCaMNb', 'Ma'))

    def test_rule_Symmetric_eg(self):
        rule, tab = self.rule_eg('Symmetric', bare = True)
        b, = tab
        assert b.has({'world1': 1, 'world2': 0})

    def test_model_finish_symmetry_visibles(self):
        model = self.logic.Model()
        model.add_access(0, 1)
        model.finish()
        assert 0 in model.visibles(1)

    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):

        # Rule ordering benchmark result:
        
        #           [# non-branching rules]
        #                 [S4:Transitive]
        #           [Necessity, Possibility]
        #                 [T:Reflexive]
        #           [# branching rules]
        #         - [Existential, Universal]
        #                 [S5:Symmetric]
        #             [D:Serial],
        #       S5: 8 branches, 142 steps
        #       S4: 8 branches, 132 steps
        #        T: 8 branches, 91 steps
        #        D: 8 branches, 57 steps
        # 200 might be agressive
        self.invalid_tab('b', 'LVxSyUFxLMGy', max_steps = 200)
