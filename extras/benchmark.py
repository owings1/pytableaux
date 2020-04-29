# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
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
# pytableaux - benchmarks

# NB: this file is a work in progress

import logic, examples, logics, time, json

arg_strs = {
    'benchmark 1' : [[], '(P(Fb V Fc) & XxXy(xOd & (yOd & (yOx & (aO1x V aO2x)))))']
}
arg_list = sorted(arg_strs.keys())

def fullname(o):
    return o.__module__ + '.' + o.__class__.__name__

for arg_name in arg_list:
    premises = arg_strs[arg_name][0]
    conclusion = arg_strs[arg_name][1]
    arg = logic.argument(
        premises   = premises,
        conclusion = conclusion,
        title      = arg_name,
        vocabulary = examples.vocabulary,
        notation   = 'standard'
    )
    timers = {
        'full' : {
            'start' : time.time(),
            'end'   : None
        },
        'rules' : {}
    }
    proof = logic.tableau('k3w', arg)
    for rule in proof.rules:
        timers['rules'][fullname(rule)] = 0
    while not proof.finished:
        tstart = time.time()
        application = proof.step()
        tend = time.time()
        if application:
            timers['rules'][fullname(application['rule'])] += tend - tstart
            print fullname(application['rule'])
    print json.dumps(timers, indent=2)