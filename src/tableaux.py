from fixed import num_const_symbols
from lexicals import Constant
from utils import get_logic, StopWatch

from errors import BranchClosedError, ProofTimeoutError, \
    TableauStateError, TrunkAlreadyBuiltError, TrunkNotBuiltError

from inspect import isclass

class TableauxSystem(object):

    @classmethod
    def build_trunk(cls, tableau, argument):
        raise NotImplementedError()

    @classmethod
    def branching_complexity(cls, node):
        return 0

    @classmethod
    def add_rules(cls, tableau, opts):
        TabRules = tableau.logic.TableauxRules
        for Rule in TabRules.closure_rules:
            tableau.add_closure_rule(Rule)
        for Rules in TabRules.rule_groups:
            tableau.add_rule_group(Rules)

class Tableau(object):
    """
    Represents a tableau proof of an argument for the given logic.
    """

    #: A tableau is finished when no more rules can apply.
    finished = False

    #: An argument is proved (valid) when its finished tableau has no
    #: open branches.
    valid = None

    #: An argument is disproved (invalid) when its finished tableau has
    #: at least one open branch, and it was not ended prematurely.
    invalid = None

    #: Whether the tableau ended prematurely. This can happen when the
    #: `max_steps` or `build_timeout` options are exceeded.
    is_premature = False

    #: The branches on the tableau. The branches are stored as list to
    #: maintain a consistent ordering. Since a tableau really consists of
    #: a `set`, and are represented internally as such, this will always
    #: be a list of unique branches.
    branches = list()

    #: The history of rule applications. Each application is a map (`dict`)
    #: with the following keys:
    #:
    #: - `rule` - The :class:`~logic.Rule` instance that was applied.
    #:
    #: - `target` - A `dict` containing information about the elements to
    #:    which the rule was applied, as well as any auxilliary information
    #:    that may be tracked for various rules and optimizations. There is
    #:    no hard constraint on what keys are in a target, but all current
    #:    implementations at least provide a `branch` key.
    #:
    #: - `duration_ms` - The duration in milliseconds of the application,
    #:    or `0` if no step timer was associated.
    history = list()

    #: A tree structure of the tableau. This is generated only after the
    #: proof is finished.
    tree = dict()

    models = None

    default_opts = {
        'is_group_optim'  : True,
        'is_build_models' : False,
        'build_timeout'   : None,
        'max_steps'       : None,
    }

    def __init__(self, logic, argument=None, **opts):

        self.finished = False
        self.valid = None
        self.invalid = None
        self.is_premature = False

        self.branches = []
        self.history = []

        self.tree = dict()

        #: A reference to the logic, if given. To set the logic after
        #: constructing, it is recommended to use ``set_logic()`` instead
        #: of setting this property directly.
        self.logic = None

        #: The argument of the tableau, if given. To set the argument after
        #: constructing, it is recommended to use ``set_argument()`` instead
        #: of setting this property directly.
        self.argument = None

        # Rules
        self.all_rules = []
        self.closure_rules = []
        self.rule_groups = []

        # build timers
        self.build_timer = StopWatch()
        self.trunk_build_timer = StopWatch()
        self.tree_timer = StopWatch()
        self.models_timer = StopWatch()

        # opts
        self.opts = dict(self.default_opts)
        self.opts.update(opts)

        self.open_branchset = set()
        self.branch_dict = dict()
        self.trunk_built = False
        self.current_step = 0

        # Cache for the branching complexities
        self.branching_complexities = dict()

        if logic != None:
            self.set_logic(logic)

        if argument != None:
            self.set_argument(argument)

    def build(self, **opts):
        """
        Build the tableau. Returns self.
        """
        self.opts.update(opts)
        with self.build_timer:
            while not self.finished:
                self.__check_timeout()
                self.step()
        self.finish()
        return self

    def set_logic(self, logic):
        """
        Set the logic for the tableau. Assumes building has not started.
        Returns self.
        """
        self.__check_not_started()
        self.logic = get_logic(logic)
        self.clear_rules()
        self.logic.TableauxSystem.add_rules(self, self.opts)
        return self

    def set_argument(self, argument):
        """
        Set the argument for the tableau. Return self.

        If the tableau has a logic set, then ``build_trunk()`` is automatically
        called.
        """
        self.argument = argument
        if self.logic != None:
            self.build_trunk()
        return self

    def clear_rules(self):
        """
        Clear the rules. Assumes building has not started. Returns self.
        """
        self.__check_not_started()
        self.closure_rules = []
        self.rule_groups = []
        self.all_rules = []
        return self

    def add_closure_rule(self, rule):
        """
        Add a closure rule. The ``rule`` parameter can be either a class
        or instance. Returns self.
        """
        self.__check_not_started()
        if isclass(rule):
            rule = rule(self, **self.opts)
        self.closure_rules.append(rule)
        self.all_rules.append(rule)
        return self

    def add_rule_group(self, rules):
        """
        Add a rule group. The ``rules`` parameter should be list of rule
        instances or classes. Returns self.
        """
        self.__check_not_started()
        group = []
        for rule in rules:
            if isclass(rule):
                rule = rule(self, **self.opts)
            group.append(rule)
        self.rule_groups.append(group)
        self.all_rules.extend(group)
        return self

    def step(self):
        """
        Find, execute, and return the next rule application. If no rule can
        be applied, the ``finish()`` method is called, and ``None`` is returned.
        If the tableau is already finished when this method is called, return
        ``False``.

        Internally, this calls the ``get_application()`` method to get the
        rule application, and, if non-empty, calls the ``do_application()``
        method.
        """
        if self.finished:
            return False
        self.__check_trunk_built()
        application = None
        with StopWatch() as step_timer:
            res = None
            if self.__is_max_steps_exceeded():
                self.is_premature = True
            else:
                res = self.get_application()
            if res:
                rule, target = res
                application = self.do_application(rule, target, step_timer)
            else:
                self.finish()
        return application

    def get_application(self):
        """
        Find and return the next available rule application. If no rule
        cal be applied, return ``None``. This iterates over the open
        branches and calls ``get_branch_application()``, returning the
        first non-empty result.
        """
        for branch in self.open_branches():
            res = self.get_branch_application(branch)
            if res:
                return res

    def get_branch_application(self, branch):
        """
        Find and return the next available rule application for the given
        open branch. This first checks the closure rules, then iterates
        over the rule groups. The first non-empty result is returned.
        """
        res = self.get_group_application(branch, self.closure_rules)
        if res:
            return res
        for rules in self.rule_groups:
            res = self.get_group_application(branch, rules)
            if res:
                return res

    def get_group_application(self, branch, rules):
        """
        Find and return the next available rule application for the given
        open branch and rule group. The ``rules`` parameter is a list of
        rules, and is assumed to be either the closure rules, or one of the
        rule groups of the tableau. This calls the ``get_target()`` method
        on the rules.

        If the ``is_group_optim`` option is **disabled**, then the first
        non-empty target returned by a rule is selected. The target is
        updated with the keys `group_score` = ``None``, `total_group_targets` = `1`,
        and `min_group_score` = ``None``.

        If the ``is_group_optim`` option is **enabled**, then all non-empty
        targets from the rules are collected, and the ``select_optim_group_application()``
        method is called to select the result.

        The return value is either a non-empty list of results, or ``None``.
        Each result is a pair (tuple). The first element is the rule, and
        the second element is the target returned by the rule's `get_target()`
        method.
        """
        results = []
        for rule in rules:
            with rule.search_timer:
                target = rule.get_target(branch)
            if target:
                if not self.opts['is_group_optim']:
                    target.update({
                        'group_score'         : None,
                        'total_group_targets' : 1,
                        'min_group_score'     : None,
                        'is_group_optim'      : False,
                    })
                    return (rule, target)
                results.append((rule, target))
        if results:
            return self.select_optim_group_application(results)

    def select_optim_group_application(self, results):
        """
        Choose the best rule to apply from among the list of results. The
        ``results`` parameter is assumed to be a non-empty list, where each
        element is a pair (tuple) of rule, target.

        Internally, this calls the ``group_score()`` method on each rule,
        passing it the target that the rule returned by its ``get_target()``
        method. The target with the max score is selected. If there is a tie,
        the the first target is selected.

        The target is updated with the following keys:
        
        - group_score
        - total_group_targets
        - min_group_score
        - is_group_optim

        The return value an element of ``results``, which is a (rule, target)
        pair.
        """
        group_scores = [rule.group_score(target) for rule, target in results]
        max_group_score = max(group_scores)
        min_group_score = min(group_scores)
        for i in range(len(results)):
            if group_scores[i] == max_group_score:
                rule, target = results[i]
                target.update({
                    'group_score'         : max_group_score,
                    'total_group_targets' : len(results),
                    'min_group_score'     : min_group_score,
                    'is_group_optim'      : True,
                })
                return (rule, target)

    def do_application(self, rule, target, step_timer):
        """
        Perform the application of the rule. This calls ``rule.apply()``
        with the target. The ``target`` should be what was returned by the
        rule's ``get_target()`` method.

        Internally, this creates an entry in the tableau's history, and
        increments the ``current_step`` property. The history entry is
        a dictionary with `rule`, `target`, and `duration_ms` keys, and
        is the return value of this method.

        This method is called internally by the ``step()`` method, which
        creates a ``StopWatch`` to track the combined time it takes to
        complete both the ``get_target()`` and ``apply()`` methods. The
        elapsed time is then stored in the history entry. This method will
        accept ``None`` for the ``step_timer`` parameter, however, this means
        the timing statistics will be inaccurate.
        """
        rule.apply(target)
        application = {
            'rule'        : rule,
            'target'      : target,
            'duration_ms' : step_timer.elapsed() if step_timer else 0,
        }
        self.history.append(application)
        self.current_step += 1
        return application

    def open_branches(self):
        """
        Return the set of open branches on the tableau. This does **not** make
        a copy of the set, and so should be copied by the caller if modifications
        may occur.
        """
        return self.open_branchset

    def get_rule(self, rule):
        """
        Get a rule instance by name or class reference. Returns first occurrence.
        """
        for r in self.all_rules:
            if r.__class__ == rule or r.name == rule or r.__class__.__name__ == rule:
                return r

    def branch(self, parent = None):
        """
        Create a new branch on the tableau, as a copy of ``parent``, if given.
        This calls the ``after_branch_add(`` callback on all the rules of the
        tableau.
        """
        if parent == None:
            branch = Branch(self)
        else:
            branch = parent.copy()
            branch.parent = parent
        self.add_branch(branch)
        return branch

    def add_branch(self, branch):
        """
        Add a new branch to the tableau. Returns self.
        """
        branch.index = len(self.branches)
        self.branches.append(branch)
        if not branch.closed:
            self.open_branchset.add(branch)
        self.branch_dict[branch.id] = branch
        self.__after_branch_add(branch)
        return self

    def build_trunk(self):
        """
        Build the trunk of the tableau. Delegates to the ``build_trunk()`` method
        of the logic's ``TableauxSystem``. This is called automatically when the
        tableau is instantiated with a logic and an argument, or when instantiated
        with a logic, and the ``set_argument()`` method is called.
        """
        self.__check_trunk_not_built()
        with self.trunk_build_timer:
            self.logic.TableauxSystem.build_trunk(self, self.argument)
            self.trunk_built = True
            self.current_step += 1
            self.__after_trunk_build()
        return self

    def get_branch(self, branch_id):
        """
        Get a branch by its id. Raises ``KeyError`` if not found.
        """
        return self.branch_dict[branch_id]

    def finish(self):
        """
        Mark the tableau as finished. Computes the ``valid``, ``invalid``,
        and ``stats`` properties, and builds the structure into the ``tree``
        property. Returns self.

        This is safe to call multiple times. If the tableau is already finished,
        this will be a no-op.
        """
        if self.finished:
            return self

        self.finished = True
        self.valid    = len(self.open_branches()) == 0
        self.invalid  = not self.valid and not self.is_premature

        with self.models_timer:
            if self.opts['is_build_models'] and not self.is_premature:
                self.__build_models()

        with self.tree_timer:
            self.tree = make_tree_structure(self.branches)

        self.stats = self.__compute_stats()

        return self

    def branching_complexity(self, node):
        """
        Convenience caching method for the logic's ``TableauxSystem.branching_complexity()``
        method. If the tableau has no logic, then ``0`` is returned.
        """
        if node.id not in self.branching_complexities:
            if self.logic != None:
                self.branching_complexities[node.id] = self.logic.TableauxSystem.branching_complexity(node)
            else:
                return 0
        return self.branching_complexities[node.id]

    # Callbacks called from other classes

    def after_branch_close(self, branch):
        # Called from the branch instance in the close method.
        branch.closed_step = self.current_step
        self.open_branchset.remove(branch)
        # Propagate event to rules
        for rule in self.all_rules:
            rule._after_branch_close(branch)

    def after_node_add(self, node, branch):
        # Called from the branch instance in the add/update methods.
        node.step = self.current_step
        # Propagate event to rules
        for rule in self.all_rules:
            rule._after_node_add(node, branch)

    def after_node_tick(self, node, branch):
        # Called from the branch instance in the tick method.
        if node.ticked_step == None or self.current_step > node.ticked_step:
            node.ticked_step = self.current_step
        # Propagate event to rules
        for rule in self.all_rules:
            rule._after_node_tick(node, branch)

    # Callbacks called internally

    def __after_branch_add(self, branch):
        # Called from ``add_branch()``
        # Propagate event to rules
        for rule in self.all_rules:
            rule._after_branch_add(branch)

    def __after_trunk_build(self):
        # Called from ``build_trunk()``
        # Propagate event to rules
        for rule in self.all_rules:
            rule._after_trunk_build(self.branches)

    # Interal util methods

    def __compute_stats(self):
        # Compute the stats property after the tableau is finished.
        num_open = len(self.open_branches())
        return {
            'result'            : self.__result_word(),
            'branches'          : len(self.branches),
            'open_branches'     : num_open,
            'closed_branches'   : len(self.branches) - num_open,
            'rules_applied'     : len(self.history),
            'distinct_nodes'    : self.tree['distinct_nodes'],
            'rules_duration_ms' : sum((application['duration_ms'] for application in self.history)),
            'build_duration_ms' : self.build_timer.elapsed(),
            'trunk_duration_ms' : self.trunk_build_timer.elapsed(),
            'tree_duration_ms'  : self.tree_timer.elapsed(),
            'models_duration_ms': self.models_timer.elapsed(),
            'rules_time_ms'     : sum([
                sum([rule.search_timer.elapsed(), rule.apply_timer.elapsed()])
                for rule in self.all_rules
            ]),
            'rules' : [
                self.__compute_rule_stats(rule)
                for rule in self.all_rules
            ],
        }

    def __compute_rule_stats(self, rule):
        # Compute the stats for a rule after the tableau is finished.
        return {
            'name'            : rule.name,
            'queries'         : rule.search_timer.times_started(),
            'search_time_ms'  : rule.search_timer.elapsed(),
            'search_time_avg' : rule.search_timer.elapsed_avg(),
            'apply_count'     : rule.apply_count,
            'apply_time_ms'   : rule.apply_timer.elapsed(),
            'apply_time_avg'  : rule.apply_timer.elapsed_avg(),
            'timers'          : {
                name : {
                    'duration_ms'   : rule.timers[name].elapsed(),
                    'duration_avg'  : rule.timers[name].elapsed_avg(),
                    'times_started' : rule.timers[name].times_started(),
                }
                for name in rule.timers
            },
        }

    def __check_timeout(self):
        timeout = self.opts['build_timeout']
        if timeout != None and timeout >= 0:
            if self.build_timer.elapsed() > timeout:
                self.build_timer.stop()
                raise ProofTimeoutError(
                    'Timeout of {0}ms exceeded.'.format(str(timeout))
                )

    def __is_max_steps_exceeded(self):
        max_steps = self.opts['max_steps']
        return max_steps != None and len(self.history) >= max_steps

    def __check_trunk_built(self):
        if self.argument != None and not self.trunk_built:
            raise TrunkNotBuiltError("Trunk is not built.")

    def __check_trunk_not_built(self):
        if self.trunk_built:
            raise TrunkAlreadyBuiltError("Trunk is already built.")

    def __check_not_started(self):
        if self.current_step > 0:
            raise TableauStateError("Proof has already started building.")

    def __result_word(self):
        if self.valid:
            return 'Valid'
        if self.invalid:
            return 'Invalid'
        return 'Unfinished'

    def __build_models(self):
        self.models = set()
        # Build models for the open branches
        for branch in list(self.open_branches()):
            self.__check_timeout()
            self.models.add(branch.make_model())
        
    def __repr__(self):
        return {
            'argument'      : self.argument,
            'branches'      : len(self.branches),
            'rules_applied' : len(self.history),
            'finished'      : self.finished,
            'valid'         : self.valid,
            'invalid'       : self.invalid,
            'is_premature'  : self.is_premature,
        }.__repr__()

class Branch(object):
    """
    Represents a tableau branch.
    """

    def __init__(self, tableau=None):
        # Make sure properties are copied if needed in copy()
        self.id = id(self)
        self.closed = False
        self.ticked_nodes = set()
        self.nodes = []
        self.consts = set()
        self.ws = set()
        self.preds = set()
        self.atms = set()
        self.leaf = None
        self.tableau = tableau
        self.closed_step = None
        self.index = None
        self.model = None
        self.parent = None
        self.node_index = {
            'sentence'   : {},
            'designated' : {},
            'world'      : {},
            'world1'     : {},
            'world2'     : {},
            'w1Rw2'      : {},
        }

    def has(self, props, ticked=None):
        """
        Check whether there is a node on the branch that matches the given properties,
        optionally filtered by ticked status.
        """
        return self.find(props, ticked=ticked) != None

    def has_access(self, *worlds):
        """
        Check whether a tuple of the given worlds is on the branch.

        This is a performant way to check typical "access" nodes on the
        branch with `world1` and `world2` properties. For more advanced
        searches, use the ``has()`` method.
        """
        return str(list(worlds)) in self.node_index['w1Rw2']

    def has_any(self, props_list, ticked=None):
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``True``
        when the first match is found.
        """
        for props in props_list:
            if self.has(props, ticked=ticked):
                return True
        return False

    def has_all(self, props_list, ticked=None):
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``False``
        when the first non-match is found.
        """
        for props in props_list:
            if not self.has(props, ticked=ticked):
                return False
        return True

    def find(self, props, ticked=None):
        """
        Find the first node on the branch that matches the given properties, optionally
        filtered by ticked status. Returns ``None`` if not found.
        """
        results = self.search_nodes(props, ticked=ticked, limit=1)
        if len(results):
            return results[0]
        return None

    def find_all(self, props, ticked=None):
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status. Returns a list.
        """
        return self.search_nodes(props, ticked=ticked)

    def search_nodes(self, props, ticked=None, limit=None):
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status, up to the limit, if given. Returns a list.
        """
        results = []
        best_haystack = self._select_index(props, ticked)
        if not best_haystack:
            return results
        for node in best_haystack:
            if limit != None and len(results) >= limit:
                break
            if ticked != None and self.is_ticked(node) != ticked:
                continue
            if node.has_props(props):
                results.append(node)
        return results

    def add(self, node):
        """
        Add a node (Node object or dict of props). Returns self.
        """
        node = self.create_node(node)
        self.nodes.append(node)
        self.consts.update(node.constants())
        self.ws.update(node.worlds())
        self.preds.update(node.predicates())
        self.atms.update(node.atomics())
        node.parent = self.leaf
        self.leaf = node

        # Add to index *before* after_node_add callback
        self.__add_to_index(node)

        # Tableau callback
        if self.tableau != None:
            self.tableau.after_node_add(node, self)

        return self

    def update(self, nodes):
        """
        Add multiple nodes. Returns self.
        """
        for node in nodes:
            self.add(node)
        return self

    def tick(self, node):
        """
        Tick a node for the branch. Returns self.
        """
        if node not in self.ticked_nodes:
            self.ticked_nodes.add(node)
            node.ticked = True
            # Tableau callback
            if self.tableau != None:
                self.tableau.after_node_tick(node, self)
        return self

    def close(self):
        """
        Close the branch. Returns self.
        """
        self.closed = True
        self.add({'is_flag': True, 'flag': 'closure'})
        # Tableau callback
        if self.tableau != None:
            self.tableau.after_branch_close(self)
        return self

    def get_nodes(self, ticked=None):
        """
        Return the nodes, optionally filtered by ticked status.
        """
        if ticked == None:
            return self.nodes
        return [node for node in self.nodes if ticked == self.is_ticked(node)]

    def is_ticked(self, node):
        """
        Whether the node is ticked relative to the branch.
        """
        return node in self.ticked_nodes

    def copy(self):
        """
        Return a copy of the branch.
        """
        branch = self.__class__(self.tableau)
        branch.nodes = list(self.nodes)
        branch.ticked_nodes = set(self.ticked_nodes)
        branch.consts = set(self.consts)
        branch.ws = set(self.ws)
        branch.atms = set(self.atms)
        branch.preds = set(self.preds)
        branch.leaf = self.leaf
        branch.node_index = {
            prop : {
                key : set(self.node_index[prop][key])
                for key in self.node_index[prop]
            }
            for prop in self.node_index
        }
        return branch

    def worlds(self):
        """
        Return the set of worlds that appear on the branch.
        """
        return self.ws

    def new_world(self):
        """
        Return a new world that does not appear on the branch.
        """
        worlds = self.worlds()
        if not len(worlds):
            return 0
        return max(worlds) + 1

    def predicates(self):
        """
        Return the set of predicates that appear on the branch.
        """
        return self.preds

    def atomics(self):
        """
        Return the set of atomics that appear on the branch.
        """
        return self.atms

    def constants(self):
        """
        Return the set of constants that appear on the branch.
        """
        return self.consts

    def new_constant(self):
        """
        Return a new constant that does not appear on the branch.
        """
        constants = list(self.constants())
        if not len(constants):
            return Constant(0, 0)
        index = 0
        subscript = 0
        c = Constant(index, subscript)
        while c in constants:
            index += 1
            if index == num_const_symbols:
                index = 0
                subscript += 1
            c = Constant(index, subscript)
        return c

    def constants_or_new(self):
        """
        Return a tuple ``(constants, is_new)``, where ``constants`` is either the
        branch constants, or, if no constants are on the branch, a singleton
        containing a new constants, and ``is_new`` indicates whether it is
        a new constant.
        """
        if self.constants():
            return (self.constants(), False)
        return ({self.new_constant()}, True)

    def make_model(self):
        """
        Make a model from the open branch.
        """
        model = self.tableau.logic.Model()
        if self.closed:
            raise BranchClosedError(
                'Cannot build a model from a closed branch'
            )
        model.read_branch(self)
        if self.tableau.argument != None:
            model.is_countermodel = model.is_countermodel_to(self.tableau.argument)
        self.model = model
        return model

    def origin(self):
        """
        Traverse up through the ``parent`` property.
        """
        origin = self
        while origin.parent != None:
            origin = origin.parent
        return origin

    def branch(self):
        """
        Convenience method for ``tableau.branch()``.
        """
        return self.tableau.branch(self)

    def create_node(self, props):
        """
        Create a new node. Does not add it to the branch. If ``props`` is a
        node instance, return it. Otherwise create a new node from the props
        and return it.
        """
        if isinstance(props, Node):
            return props
        return Node(props=props)

    def __add_to_index(self, node):
        for prop in self.node_index:
            key = None
            if prop == 'w1Rw2':
                if 'world1' in node.props and 'world2' in node.props:
                    key = str([node.props['world1'], node.props['world2']])
            elif prop in node.props:
                key = str(node.props[prop])
            if key:
                if key not in self.node_index[prop]:
                    self.node_index[prop][key] = set()
                self.node_index[prop][key].add(node)

    def _select_index(self, props, ticked):
        # TODO: Mangle with __, but we are using this in a test.
        best_index = None
        for prop in self.node_index:
            key = None
            if prop == 'w1Rw2':
                if 'world1' in props and 'world2' in props:
                    key = str([props['world1'], props['world2']])
            elif prop in props:
                key = str(props[prop])
            if key != None:
                if key not in self.node_index[prop]:
                    return False
                index = self.node_index[prop][key]
                if best_index == None or len(index) < len(best_index):
                    best_index = index
                # we could do no better
                if len(best_index) == 1:
                    break
        if not best_index:
            if ticked:
                best_index = self.ticked_nodes
            else:
                best_index = self.nodes
        return best_index

    def __repr__(self):
        return {
            'id'     : self.id,
            'nodes'  : len(self.nodes),
            'leaf'   : self.leaf.id if self.leaf else None,
            'closed' : self.closed,
        }.__repr__()

class Node(object):
    """
    A tableau node.
    """

    def __init__(self, props={}):
        #: A dictionary of properties for the node.
        self.props = {
            'world'      : None,
            'designated' : None,
        }
        self.props.update(props)
        self.ticked = False
        self.parent = None
        self.step = None
        self.ticked_step = None
        self.id = id(self)

    def has(self, *names):
        """
        Whether the node has a non-``None`` property of all the given names.
        """
        for name in names:
            if name not in self.props or self.props[name] == None:
                return False
        return True

    def has_any(self, *names):
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if name in self.props and self.props[name] != None:
                return True
        return False

    def has_props(self, props):
        """
        Whether the node properties match all those give in ``props`` (dict).
        """
        for prop in props:
            if prop not in self.props or not props[prop] == self.props[prop]:
                return False
        return True

    def worlds(self):
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        worlds = set()
        if self.has('world'):
            worlds.add(self.props['world'])
        if self.has('world1'):
            worlds.add(self.props['world1'])
        if self.has('world2'):
            worlds.add(self.props['world2'])
        if self.has('worlds'):
            worlds.update(self.props['worlds'])
        return worlds

    def atomics(self):
        """
        Return the set of atomics (recusive) of the node's `sentence`
        property, if any. If the node does not have a sentence, return
        an empty set.
        """
        if self.has('sentence'):
            return self.props['sentence'].atomics()
        return set()

    def constants(self):
        """
        Return the set of constants (recusive) of the node's `sentence`
        property, if any. If the node does not have a sentence, return
        the empty set.
        """
        if self.has('sentence'):
            return self.props['sentence'].constants()
        return set()

    def predicates(self):
        """
        Return the set of constants (recusive) of the node's `sentence`
        property, if any. If the node does not have a sentence, return
        the empty set.
        """
        if self.has('sentence'):
            return self.props['sentence'].predicates()
        return set()

    def __repr__(self):
        return {
            'id'     : self.id,
            'props'  : self.props,
            'ticked' : self.ticked,
            'step'   : self.step,
            'parent' : self.parent.id if self.parent else None,
        }.__repr__()

def make_tree_structure(branches, node_depth=0, track=None):
    is_root = track == None
    if track == None:
        track = {
            'pos'            : 0,
            'depth'          : 0,
            'distinct_nodes' : 0,
        }
    track['pos'] += 1
    s = {
        # the nodes on this structure.
        'nodes'                 : [],
        # this child structures.
        'children'              : [],
        # whether this is a terminal (childless) structure.
        'leaf'                  : False,
        # whether this is a terminal structure that is closed.
        'closed'                : False,
        # whether this is a terminal structure that is open.
        'open'                  : False,
        # the pre-ordered tree left value.
        'left'                  : track['pos'],
        # the pre-ordered tree right value.
        'right'                 : None,
        # the total node count of all descendants.
        'descendant_node_count' : 0,
        # the node count plus descendant node count.
        'structure_node_count'  : 0,
        # the depth of this structure (ancestor structure count).
        'depth'                 : track['depth'],
        # whether this structure or a descendant is open.
        'has_open'              : False,
        # whether this structure or a descendant is closed.
        'has_closed'            : False,
        # if closed, the step number at which it closed.
        'closed_step'           : None,
        # the step number at which this structure first appears.
        'step'                  : None,
        # the number of descendant terminal structures, or 1.
        'width'                 : 0,
        # 0.5x the width of the first child structure, plus 0.5x the
        # width of the last child structure (if distinct from the first),
        # plus the sum of the widths of the other (distinct) children.
        'balanced_line_width'   : None,
        # 0.5x the width of the first child structure divided by the
        # width of this structure.
        'balanced_line_margin'  : None,
        # the branch id, only set for leaves
        'branch_id'             : None,
        # the model id, if exists, only set for leaves
        'model_id'              : None,
        # whether this is the one and only branch
        'is_only_branch'        : False,
    }
    while True:
        relevant = [branch for branch in branches if len(branch.nodes) > node_depth]
        for branch in relevant:
            if branch.closed:
                s['has_closed'] = True
            else:
                s['has_open'] = True
            if s['has_open'] and s['has_closed']:
                break
        distinct_nodes = []
        distinct_nodeset = set()
        for branch in relevant:
            node = branch.nodes[node_depth]
            if node not in distinct_nodeset:
                distinct_nodeset.add(node)
                distinct_nodes.append(node)
        if len(distinct_nodes) == 1:
            node = relevant[0].nodes[node_depth]
            s['nodes'].append(node)
            if s['step'] == None or s['step'] > node.step:
                s['step'] = node.step
            node_depth += 1
            continue
        break
    track['distinct_nodes'] += len(s['nodes'])
    if len(branches) == 1:
        branch = branches[0]
        s['closed'] = branch.closed
        s['open'] = not branch.closed
        if s['closed']:
            s['closed_step'] = branch.closed_step
            s['has_closed'] = True
        else:
            s['has_open'] = True
        s['width'] = 1
        s['leaf'] = True
        s['branch_id'] = branch.id
        if branch.model != None:
            s['model_id'] = branch.model.id
        if track['depth'] == 0:
            s['is_only_branch'] = True
    else:
        inbetween_widths = 0
        track['depth'] += 1
        first_width = 0
        last_width = 0
        for i, node in enumerate(distinct_nodes):

            child_branches = [
                branch for branch in branches
                if branch.nodes[node_depth] == node
            ]

            # recurse
            child = make_tree_structure(child_branches, node_depth, track)

            s['descendant_node_count'] = len(child['nodes']) + child['descendant_node_count']
            s['width'] += child['width']
            s['children'].append(child)
            if i == 0:
                s['branch_step'] = child['step']
                first_width = float(child['width']) / 2
            elif i == len(distinct_nodes) - 1:
                last_width = float(child['width']) / 2
            else:
                inbetween_widths += child['width']
            s['branch_step'] = min(s['branch_step'], child['step'])
        if s['width'] > 0:
            s['balanced_line_width'] = float(first_width + last_width + inbetween_widths) / s['width']
            s['balanced_line_margin'] = first_width / s['width']
        else:
            s['balanced_line_width'] = 0
            s['balanced_line_margin'] = 0
        track['depth'] -= 1
    s['structure_node_count'] = s['descendant_node_count'] + len(s['nodes'])
    track['pos'] += 1
    s['right'] = track['pos']
    if is_root:
        s['distinct_nodes'] = track['distinct_nodes']
    return s