/**
 * pytableaux, a multi-logic proof generator.
 * Copyright (C) 2014-2020 Doug Owings.
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * pytableaux - web ui core
*/
;(function($) {

    $(document).ready(function() {

        const AppData = $.parseJSON($('script.app').html())
        const Templates = {
            premise    : $('#premiseTemplate').html(),
            predicate  : $('#predicateRowTemplate').html()
        }

        /**
         * Main initialization routine.
         *
         * @return void
         */
        function init() {
            $('form.argument')
              .on('keyup focus', 'input.premise, #conclusion', ensureEmptyPremise)
              .on('keyup', 'input.predicateName, input.arity', ensureEmptyPredicate)
              .on('change', '#example_argument', function() {
                   refreshExampleArgument()
                   refreshStatuses()
               })
              .on('change', '#input_notation', function() {
                   refreshNotation()
                   refreshStatuses()
               })
              .on('change', 'input.sentence', refreshStatuses)
            
            ensureEmptyPremise()
            ensureEmptyPredicate()
            refreshNotation()
        }

        /**
         * Interpolate variable strings like {varname}.
         *
         * @param html The template html.
         * @param vars The variables object.
         * @return string The rendered content.
         */
        function render(html, vars) {
            if (vars) {
                $.each(vars, function(name, val) {
                    html = html.replace(new RegExp('{' + name + '}', 'g'), val)
                })
            }
            return html
        }

        /**
         * Add a premise input row. All parameters are optional.
         *
         * @param value The string value of the sentence.
         * @param status The status class name, 'good' or 'bad'.
         * @param message The status message.
         * @return void
         */
        function addPremise(value, status, message) {
            var premiseNum = $('input.premise').length + 1
            $('.premises').append(render(Templates.premise, {
                n       : premiseNum++,
                value   : value   || '',
                status  : status  || '',
                message : message || ''
            }))
        }

        /**
         * Get the input notation value.
         *
         * @return String name of the notation, e.g. 'standard'
         */
        function currentNotation() {
            return $('#input_notation').val()
        }

        /**
         * Add an empty premise input row.
         *
         * @return void
         */
        function addEmptyPremise() {
            addPremise()
        }

        /**
         * Remove all premise input rows.
         *
         * @return void
         */
        function clearPremises() {
            $('.input.premise').remove()
        }

        /**
         * Clear the value of the conclusion input.
         *
         * @return void
         */
        function clearConclusion() {
            $('#conclusion').val('')
        }

        /**
         * Clear all premises and conclusion inputs.
         *
         * @return void
         */
        function clearArgument() {
            clearPremises()
            clearConclusion()
        }

        /**
         * Add a user-defined predicate row. The first two parameters, index
         * and subscript, are required.
         *
         * @param index The integer index of the predicate.
         * @param subscript The integer subscript of the predicate.
         * @param name The name of the predicate (optional).
         * @param arity The integer arity of the predicate (optional).
         * @return void
         */
        function addPredicate(index, subscript, name, arity) {
            const thisNotation = currentNotation()
            var html = ''
            $.each(AppData.notation_user_predicate_symbols, function(notation, symbols) {
                var classes = ['predicateSymbol', 'notation-' + notation]
                if (notation != thisNotation)
                    classes.push('hidden')
                html += '<span class="' + classes.join(' ') + '">'
                html += $('<div/>').text(symbols[index]).html()
                if (subscript > 0)
                    html += '<span class="subscript">' + subscript + '</span>'
                html += '</span>'
            })
            $('table.predicates tbody').append(render(Templates.predicate, { 
                index       : index,
                subscript   : subscript,
                name        : name || ('Predicate ' + ($('input.predicateSymbol').length + 1)),
                arity       : arity || '',
                symbol_html : html
            }))
        }

        /**
         * Add an empty input for a user-defined predicate. Calculates the next
         * index and subscript.
         *
         * @return void
         */
        function addEmptyPredicate() {
            const $symbols   = $('input.predicateSymbol')
            const numSymbols = $symbols.length
            var index      = 0
            var subscript  = 0
            if (numSymbols > 0) {
                var last = $symbols.last().val().split('.')
                index = +last[0] + 1
                subscript = +last[1]
                if (index == AppData.num_predicate_symbols) {
                    index = 0
                    subscript += 1
                }
            }
            addPredicate(index, subscript)
        }

        /**
         * Clear all the user-defined predicate input rows.
         *
         * @return void
         */
        function clearPredicates() {
            $('tr.userPredicate').remove()
        }

        /**
         * Check whether there is already an empty premise input row available
         * for input.
         *
         * @return boolean
         */
        function hasEmptyPremise() {
            var hasEmpty = false
            $('input.premise').each(function(i){
                if (!$(this).val()) {
                    hasEmpty = true
                    // stop iteration
                    return false
                }
            })
            return hasEmpty
        }

        /**
         * Check whether there is already an empty predicate input row available
         * for input.
         *
         * @return boolean
         */
        function hasEmptyPredicate() {
            var hasEmpty = false
            $('input.arity').each(function(i) {
                if (!$(this).val()){
                    hasEmpty = true
                    // stop iteration
                    return false
                }
            })
            return hasEmpty
        }

        /**
         * Ensure that there is an empty premise input row available for input.
         *
         * @return void
         */
        function ensureEmptyPremise() {
            if (!hasEmptyPremise()) {
                addEmptyPremise()
            }
        }

        /**
         * Ensure that there is an empty predicate input row available for input.
         *
         * @return void
         */
        function ensureEmptyPredicate() {
            if (!hasEmptyPredicate()) {
                addEmptyPredicate()
            }   
        }

        /**
         * Input notation change handler. Show appropriate lexicon, and update
         * the example argument, if any.
         *
         * @return void
         */
        function refreshNotation() {
            const notation = currentNotation()
            $('.lexicons .lexicon').hide()
            $('#Lexicon_' + notation).show()
            $('.predicateSymbol').hide()
            $('.predicateSymbol.notation-' + notation).show()
            if ($('#example_argument').val()) {
                refreshExampleArgument()
            }
        }

        /**
         * Example argument change handler.
         *
         * @return void
         */
        function refreshExampleArgument() {
            clearPredicates()
            clearArgument()
            const $me = $('#example_argument')
            const argName = $me.val()
            if (!argName) {
                ensureEmptyPremise()
                ensureEmptyPredicate()
                return
            }
            const notation = currentNotation()
            const arg = AppData.example_arguments[argName][notation]
            $.each(arg.premises, function(i, value) {
                addPremise(value)
            })
            $('#conclusion').val(arg.conclusion)
            $.each(AppData.example_predicates, function(i, pred) {
                addPredicate(pred[1], pred[2], pred[0], pred[3])
            })
        }

        /**
         * Make AJAX requests to parse the premises & conclusion.
         */
        function refreshStatuses() {
            $('form.argument input.sentence').each(function(sentenceIndex) {
                const $status = $(this).closest('div.input').find('.status')
                const notation = currentNotation()
                const input = $(this).val()
                if (input || $(this).hasClass('conclusion')) {
                    const hash = hashString([input, notation].join('.'))
                    if (+$status.attr('data-hash') === hash) {
                        return
                    }
                    $status.attr('data-hash', hash)
                    apiData = getApiData()
                    $.ajax({
                        url         : '/api/parse',
                        method      : 'POST',
                        contentType : 'application/json',
                        dataType    : 'json',
                        data        : JSON.stringify({
                            input      : input,
                            notation   : notation,
                            predicates : apiData.argument.predicates
                        }),
                        success: function(res) {
                            $status.removeClass('bad').addClass('good')
                            $status.attr('title', res.result.type)
                        },
                        error: function(xhr, textStatus, errorThrown) {
                            $status.removeClass('good').addClass('bad')
                            var title
                            if (xhr.status == 400) {
                                const res = xhr.responseJSON
                                title = [res.error, res.message].join(': ')
                            } else {
                                title = [textStatus, errorThrown].join(': ')
                            }
                            $status.attr('title', title)
                        }
                    })
                } else {
                    $status.removeClass('bad good')
                    $status.attr('title', '')
                    $status.attr('data-hash', '')
                }
            })
        }

        /**
         * Generate an integer hash for a string.
         *
         * From: http://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript-jquery
         *
         * @param str The input string.
         * @return int The hash.
         */
        function hashString(str) {
            var hash = 0
            if (str.length === 0) {
                return hash
            }
            var chr
            for (var i = 0; i < str.length; i++) {
                chr   = str.charCodeAt(i)
                hash  = ((hash << 5) - hash) + chr
                hash |= 0; // Convert to 32bit integer
            }
            return hash
        }

        /**
         * Read the form inputs into an object suitable for posting to
         * the prove api.
         *
         * @return object
         */
        function getApiData() {
            const data = {
                argument : {
                    premises  : [],
                    predicates: []
                },
                output: {}
            }
            data.logic = $('select[name="logic"]').val()
            data.argument.notation = currentNotation()
            data.argument.conclusion = $('#conclusion').val()
            $('input.premise').each(function() {
                const val = $(this).val()
                if (val) {
                    data.argument.premises.push(val)
                }
            })
            $('.userPredicate').each(function() {
                const $tr = $(this)
                const arity = $('input.arity', $tr).val()
                if (arity.length > 0) {
                    const coords = $('input.predicateSymbol', $tr).val().split('.')
                    data.argument.predicates.push({
                        name      : $('input.predicateName', $tr).val(),
                        index     : +coords[0],
                        subscript : +coords[1],
                        arity     : +arity
                    })
                }
            })
            data.output.notation = $('#output_notation').val()
            data.output.format = $('#format').val()
            data.output.symbol_set = $('#symbol_set').val()
            return data
        }

        init()

    })
})(jQuery);