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

        var SentenceRenders = {}

        const $Ctx = $('form.argument')
        const $Frm = $Ctx
        /**
         * Main initialization routine.
         *
         * @return void
         */
        function init() {
            $Frm.on('keyup focus', 'input.premise, #conclusion', ensureEmptyPremise)
                .on('keyup', 'input.predicateName, input.arity', ensureEmptyPredicate)
                .on('change selectmenuchange', function(e) {
                    const $target = $(e.target)
                    if ($target.is('#example_argument')) {
                        refreshExampleArgument()
                        refreshStatuses()
                    } else if ($target.is('#input_notation')) {
                        refreshNotation()
                        refreshStatuses()
                    } else if ($target.is('input.sentence')) {
                        refreshStatuses()
                    } else if ($target.is('#selected_logic')) {
                        refreshLogic()
                    }
                    if ($target.closest('.fieldset.output').length) {
                        refreshOutputHeader()
                        refreshArgumentHeader()
                    }
                })
                .on('submit', function(e) {
                    //e.preventDefault()
                    submitForm()
                })

                $Ctx.on('click', function(e) {
                    const $target = $(e.target)
                    const $heading = $target.closest('.heading')
                    const $collapserHeading = $target.closest('.collapser-heading')
                    if ($heading.length) {
                        handleFieldsetHeadingClick($heading)
                    } else if ($collapserHeading.length) {
                        handlerCollapserHeadingClick($collapserHeading)
                    } else if ($target.is('.toggler')) {
                        $($target.attr('data-target')).toggle()
                    }
                })
                

            $('select', $Frm).selectmenu({
                classes: {
                    'ui-selectmenu-menu': 'pt-app'
                }
            })
            $('input[type="submit"]', $Frm).button()

            setTimeout(function() {
                ensureEmptyPremise()
                ensureEmptyPredicate()
                refreshNotation()
                refreshLogic()
                refreshOutputHeader()
                if ($('.evaluation').length) {
                    refreshStatuses()
                }
            })
        }

        function submitForm() {
            const data = getApiData()
            const json = JSON.stringify(data)
            $('input[name="api-json"]', $Frm).val(json)
        }

        /**
         * Show/hide handler for fieldset heading.
         *
         * @return void
         */
        function handleFieldsetHeadingClick($heading) {
            const $contents = $heading.closest('.fieldset').find('.fieldset-contents')
            const isVisible = $contents.is(':visible')
            $('.fieldset-contents', $Ctx).removeClass('uncollapsed').addClass('collapsed').hide('fast')
            $('.heading', $Ctx).removeClass('uncollapsed').addClass('collapsed')
            if (!isVisible) {
                $contents.removeClass('collapsed').addClass('uncollapsed').show('medium')
                $heading.removeClass('collapsed').addClass('uncollapsed')
            }
        }

        /**
         * Show/hide handler for collapser.
         *
         * @param $heading The heading jQuery element
         * @return void
         */
        function handlerCollapserHeadingClick($heading) {
            const $wrapper = $heading.closest('.collapser-wrapper')
            const $contents = $wrapper.find('.collapser-contents')
            if ($heading.hasClass('collapsed')) {
                $heading.add($wrapper).removeClass('collapsed').addClass('uncollapsed')
                $contents.removeClass('collapsed').addClass('uncollapsed').show('medium')
            } else {
                $heading.add($wrapper).removeClass('uncollapsed').addClass('collapsed')
                $contents.removeClass('uncollapsed').addClass('collapsed').hide('fast')
            }
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
            var premiseNum = $('input.premise', $Ctx).length + 1
            $('.premises', $Ctx).append(render(Templates.premise, {
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
            return $('#input_notation', $Ctx).val()
        }

        /**
         * Get the output format value.
         *
         * @return String name of the foramat, e.g. 'html'
         */
        function currentOutputFormat() {
            return $('#format', $Ctx).val()
        }

        /**
         * Get the output notation value.
         *
         * @return String name of the notation, e.g. 'standard'
         */
        function currentOutputNotation() {
            return $('#output_notation', $Ctx).val()
        }

        /**
         * Get the output symbol set value.
         *
         * @return String name of the symbol set, e.g. 'default'
         */
        function currentOutputSymbolSet() {
            return $('#symbol_set', $Ctx).val()
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
            $('.input.premise', $Ctx).remove()
        }

        /**
         * Clear the value of the conclusion input.
         *
         * @return void
         */
        function clearConclusion() {
            $('#conclusion', $Ctx).val('')
        }

        /**
         * Clear all premises and conclusion inputs.
         *
         * @return void
         */
        function clearArgument() {
            clearPremises()
            clearConclusion()
            SentenceRenders = {}
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
            $('table.predicates tbody', $Ctx).append(render(Templates.predicate, { 
                index       : index,
                subscript   : subscript,
                name        : name || ('Predicate ' + ($('input.predicateSymbol', $Ctx).length + 1)),
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
            const $symbols   = $('input.predicateSymbol', $Ctx)
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
            $('input.premise', $Ctx).each(function(i){
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
            $('input.arity', $Ctx).each(function(i) {
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
         * Logic select change handler. Show appropriate logic information.
         *
         * @return void
         */
        function refreshLogic() {
            const logicName = $('#selected_logic').val()
            $('.logic-details', $Ctx).hide()
            $('.logic-details.' + logicName, $Ctx).show()
            $('#logic-heading-description').html(
                [
                    $('.logic-details .logic-name.' + logicName, $Ctx).html(),
                    $('.logic-details .logic-title.' + logicName, $Ctx).html()
                ].join(' - ')
            )
        }

        /**
         * Input notation change handler. Show appropriate lexicon, and update
         * the example argument, if any.
         *
         * @return void
         */
        function refreshNotation() {
            const notation = currentNotation()
            $('.lexicons .lexicon', $Ctx).hide()
            $('.lexicon.notation-' + notation, $Ctx).show()
            $('.predicateSymbol', $Ctx).hide()
            $('.predicateSymbol.notation-' + notation, $Ctx).show()
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
         *
         * @return void
         */
        function refreshStatuses() {
            $('input.sentence', $Ctx).each(function(sentenceIndex) {
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
                            SentenceRenders[input] = res.result.rendered
                            refreshArgumentHeader()
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
                            delete SentenceRenders[input]
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
         * Update the argument display in the header bar of the argument fieldset.
         *
         * @return void
         */
        function refreshArgumentHeader() {
            const notation = currentOutputNotation()
            const symset = currentOutputSymbolSet()
            const premises = []
            var conclusion
            $('input.sentence', $Ctx).each(function(sentenceIndex) {
                const $status = $(this).closest('div.input').find('.status')
                const input = $(this).val()
                const isConclusion = $(this).hasClass('conclusion')
                const isGood = $status.hasClass('good')
                if (input || isConclusion) {
                    var sentence
                    if (isGood && SentenceRenders[input]) {
                        sentence = SentenceRenders[input][notation][symset]
                        if (symset != 'html') {
                            sentence = h(sentence)
                        }
                    } else {
                        sentence = '?'
                    }
                    if (isConclusion) {
                        conclusion = sentence
                    } else {
                        premises.push(sentence)
                    }
                }
            })
            $('#argument-heading-rendered').html(premises.join(', ') + ' &there4; ' + conclusion)
        }

        /**
         * Update the display in the header bar of the output fieldset.
         *
         * @return void
         */
        function refreshOutputHeader() {
            $('#output-heading-description').html(
                [
                    currentOutputFormat().toUpperCase(),
                    currentOutputNotation()
                ].join(' | ')
            )
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
            data.logic = $('select[name="logic"]', $Frm).val()
            data.argument.notation = currentNotation()
            data.argument.conclusion = $('#conclusion').val()
            $('input.premise', $Frm).each(function() {
                const val = $(this).val()
                if (val) {
                    data.argument.premises.push(val)
                }
            })
            $('.userPredicate', $Frm).each(function() {
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
            data.output.notation = $('#output_notation', $Frm).val()
            data.output.format = $('#format', $Frm).val()
            data.output.symbol_set = $('#symbol_set', $Frm).val()
            data.output.options = {}
            $('input:checkbox.options', $Frm).each(function() {
                const $me = $(this)
                const opt = $me.attr('name').split('.')[1]
                data.output.options[opt] = $me.is(':checked')
            })
            return data
        }

        /**
         * Escape HTML
         *
         * @param str The input string.
         * @return string output.
         */
        function h(str) {
            return str.replace(/</g, '&lt;')
        }

        init()

    })
})(jQuery);