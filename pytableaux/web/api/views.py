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
pytableaux.web.api.views
^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from collections import deque
from types import MappingProxyType as MapProxy
from typing import Any, Mapping

from cherrypy import HTTPError

from ... import logics
from ...errors import ParseError, ProofTimeoutError
from ...lang import (Argument, LexWriter, Notation, Parser, Predicates,
                     TriCoords)
from ...proof import Tableau, writers
from ...tools import EMPTY_MAP
from ...tools.timing import StopWatch
from ..views import JsonView

__all__ = (
    'ApiView',
    'ParseView',
    'ProveView')

EMPTY = ()

class ApiView(JsonView):

    def get_reply(self, *args, **kw) -> dict:
        reply = {}
        try:
            try:
                result = super().get_reply(*args, **kw)
                if result is None:
                    raise HTTPError(400)
                reply['message'] = 'OK'
                reply['result'] = result
            except ProofTimeoutError as err:
                self.status = 408
                raise
            except HTTPError as err:
                self.status = err.status
                reply['message'] = err.reason
                raise
            except Exception as err:
                self.status = 500
                raise
        except Exception as err:
            reply['error'] = type(err).__name__
            self.logger.error(err, exc_info=err)
            if 'message' not in reply:
                reply['message'] = str(err)
        if self.errors:
            reply['errors'] = self.errors
        reply['status'] = self.status
        return reply

    def parse_preds(self, key: str = 'predicates') -> Predicates|None:
        specs = self.payload[key]
        if not specs:
            return Predicates.EMPTY
        preds = Predicates()
        errors = self.errors
        for i, spec in enumerate(specs):
            try:
                preds.add(TriCoords.make(spec))
            except Exception as err:
                errors[f'{key}:{i}'] = err
        if not errors:
            return preds

class ParseView(ApiView):

    payload_defaults: Mapping[str, Any] = MapProxy(dict(
        notation = Notation.polish.name,
        predicates = Predicates.EMPTY,
        input = ''))

    def POST(self):
        """
        Request example::

            {
               notation: "polish",
               input: "Fm",
               predicates : [ [0, 0, 1] ]
            }

        Response Example::

            {
              type: "Predicated",
              rendered: {
                standard: {
                  ascii: "Fa", unicode: "Fa", html: "Fa"
                },
                polish: {
                  ascii: "Fm", unicode": "Fm", html: "Fm"
                }
              }
            }
        """
        errors = self.errors
        payload = self.payload
        try:
            notn = Notation[payload['notation']]
        except KeyError as err:
            errors['notation'] = f"Invalid notation: {err}"
        preds = self.parse_preds('predicates')
        if errors:
            return
        parser = Parser(notation=notn, predicates=preds)
        try:
            sentence = parser(payload['input'])
        except Exception as err:
            errors['input'] = err
            return
        return dict(
            type = sentence.TYPE.name,
            rendered = {
                notn.name: {
                    format: LexWriter(notation=notn, format=format)(sentence)
                    for format in notn.formats}
                for notn in Notation})

class ProveView(ApiView):

    payload_defaults: Mapping[str, Any] = MapProxy(dict(
        logic=None,
        argument=MapProxy(dict(
            notation=Notation.polish.name,
            premises=EMPTY,
            predicates=EMPTY)),
        build_models=False,
        max_steps=None,
        rank_optimizations=True,
        group_optimizations=True,
        writer_registry='default',
        output=MapProxy(dict(
            notation=Notation.polish.name,
            format='html',
            dialect=None,
            attachments=False,
            options=EMPTY_MAP))))

    def setup(self, *args, **kw):
        super().setup(*args, **kw)
        self.payload['output:options:debug'] = self.is_debug
        self.logic = None
        self.argument = None
        self.tabopts = None
        self.tableau = None
        self.pw = None

    def POST(self):
        """
        Example request body::

            {
                "logic": "FDE",
                "argument": {
                    "conclusion": "Fm",
                    "premises": ["KFmFn"],
                    "notation": "polish",
                    "predicates": [ [0, 0, 1] ]
                },
                "output": {
                    "format": "html",
                    "notation": "standard",
                    "options": {}
                },
                "build_models": false,
                "max_steps": null,
                "rank_optimizations": true,
                "group_optimizations": true
            }

        Example success result::

            {
                "tableau": {
                    "logic": "FDE",
                    "argument": {
                        "premises": ["Fa &and; Fb"],
                        "conclusion": "Fb"
                    },
                    "valid": true,
                    "body": "...html...",
                    "header": "...",
                    "footer": "...",
                    "max_steps" : null
                },
                "writer": {
                    "format": "html,
                    "options": {}
                },
            }
        """
        self.argument = self.get_argument()
        self.logic = self.get_logic()
        self.pw = self.get_pw()
        self.tabopts = self.get_tabopts()
        if self.errors:
            return
        self.tableau = self.build()
        data = dict(
            tableau = dict(
                logic = self.logic.Meta.name,
                argument = dict(
                    premises   = tuple(map(self.pw.lw, self.argument.premises)),
                    conclusion = self.pw.lw(self.argument.conclusion)),
                valid  = self.tableau.valid,
                body   = self.pw(self.tableau),
                stats  = self.tableau.stats,
                result = self.tableau.stats['result']),
            writer = dict(
                engine  = self.pw.engine,
                format  = self.pw.format,
                notation = self.pw.lw.notation.name,
                options = self.pw.opts))
        if self.payload['output:attachments']:
            data['attachments'] = self.pw.attachments()
        return data

    def build(self):
        metrics = self.app.metrics if self.config['metrics_enabled'] else None
        logic = self.logic
        with StopWatch() as timer:
            if metrics:
                metrics.proofs_inprogress_count(logic.Meta.name).inc()
            tab = Tableau(logic, self.argument, **self.tabopts)
            try:
                tab.build()
                if metrics:
                    metrics.proofs_completed_count(logic.Meta.name, tab.stats['result']).inc()
            finally:
                if metrics:
                    metrics.proofs_inprogress_count(logic.Meta.name).dec()
                    metrics.proofs_execution_time(logic.Meta.name).observe(timer.elapsed_secs())
        return tab

    def get_logic(self):
        try:
            return logics.registry(self.payload['logic'])
        except Exception as err:
            self.errors['logic'] = err

    def get_tabopts(self):
        payload = self.payload
        if payload['max_steps'] is not None:
            try:
                payload['max_steps'] = int(payload['max_steps'])
            except ValueError as err:
                self.errors['max_steps'] = f"Invalid int value: {err}"
        return dict(
            is_rank_optim   = bool(payload['rank_optimizations']),
            is_group_optim  = bool(payload['group_optimizations']),
            is_build_models = bool(payload['build_models']),
            max_steps       = payload['max_steps'],
            build_timeout   = self.config['maxtimeout'])

    def get_argument(self):
        errors = self.errors
        payload = self.payload
        if isinstance(payload['argument'], str):
            try:
                return Argument.from_argstr(payload['argument'])
            except ParseError as err:
                errors['argument'] = f"Invalid argument string: {err}"
                return
        try:
            notn = Notation[payload['argument:notation']]
        except KeyError as err:
            errors['argument:notation'] = f"Invalid parser notation: {err}"
            return
        preds = self.parse_preds('argument:predicates')
        if errors:
            return
        parser = Parser(notation=notn, predicates=preds)
        premises = deque()
        for i, premise in enumerate(payload['argument:premises']):
            try:
                premises.append(parser(premise))
            except Exception as err:
                premises.append(None)
                errors[f'argument:premises:{i}'] = err
        try:
            conclusion = parser(payload['argument:conclusion'])
        except Exception as err:
            errors['argument:conclusion'] = err
        if errors:
            return
        return Argument(conclusion, premises)

    def get_pw(self):
        errors = self.errors
        payload = self.payload
        regkey = payload['writer_registry'] or self.payload_defaults['writer_registry']
        try:
            reg = writers.registries[regkey]
        except KeyError as err:
            errors['writer_registry'] = f'Invalid registry: {err}'
            return
        try:
            WriterClass = reg[payload['output:format']]
        except KeyError as err:
            errors['output:format'] = f"Invalid writer: {err}"
            return
        try:
            notn = Notation[payload['output:notation']]
        except KeyError as err:
            errors['output:notation'] = f"Invalid notation: {err}"
            return
        try:
            lw = LexWriter(
                notation=notn,
                format=payload['output:format'],
                dialect=payload['output:dialect'])
        except (KeyError, ValueError) as err:
            errors['output:format'] = f"Unsupported format: {err}"
            return
        return WriterClass(lw = lw, **payload['output:options'])
