        

def test_truth_table_cpl_negation():
    tbl = logic.truth_table('cpl', 'Negation')
    assert len(tbl['inputs']) == 2
    assert len(tbl['outputs']) == 2
    assert tbl['inputs'][0][0] == 'F'
    assert tbl['outputs'][0] == 'T'

def test_truth_tables_cpl():
    tbls = logic.truth_tables('cpl')
    assert tbls['Negation']['outputs'][0] == 'T'

def test_get_logic_cpl_case_insensitive():
    assert get_logic('cpl') == get_logic('CPL')

def test_get_logic_none_bad_argument():
    with raises(logic.BadArgumentError):
        get_logic(None)
        
class TestModel(object):

    def test_not_impl_various(self):
        model = logic.Model()
        with raises(NotImplementedError):
            model.read_branch(None)
        with raises(NotImplementedError):
            model.truth_function(None, None)
        with raises(NotImplementedError):
            model.value_of_opaque(None)
        with raises(NotImplementedError):
            model.value_of_predicated(None)
        with raises(NotImplementedError):
            s = logic.negate(atomic(0, 0))
            model.value_of_operated(s)
        with raises(NotImplementedError):
            model.value_of_quantified(None)
        with raises(NotImplementedError):
            model.is_countermodel_to(None)
        with raises(NotImplementedError):
            model.value_of_atomic(None)

    def test_get_data_empty(self):
        model = logic.Model()
        res = model.get_data()
        assert len(res) == 0