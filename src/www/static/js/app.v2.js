/**
 * pytableaux, a multi-logic proof generator.
 * Copyright (C) 2014-2021 Doug Owings.
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

    const TabIndexes = {
        argument : 0,
        options  : 1,
        stats    : 2,
        view     : 3,
        step     : 4,
        models   : 5,
    }

    $(document).ready(function() {

        const AppData = $.parseJSON($('script.app').html())
        const {is_debug} = AppData
        const is_proof  = Boolean(AppData.is_proof)
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
                // .on('keyup', 'input.predicateName, input.arity', ensureEmptyPredicate)
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
                    } else if ($target.hasClass('arity')) {
                        refreshStatuses(true)
                    }/* else if ($target.hasClass('predicateName')) {
                        refreshStatuses(true)
                    } */else if ($target.is('#selected_logic')) {
                        refreshLogic()
                    }
                    // if ($target.closest('.fieldset.output').length) {
                    //     refreshArgumentHeader()
                    // }
                })
                .on('submit', function(e) {
                    //e.preventDefault()
                    submitForm()
                })

                $Ctx.on('click', function(e) {
                    const $target = $(e.target)
                    if ($target.is('#clear_argument')) {
                        clearArgument()
                        clearExampleArgument()
                        ensureEmptyPremise()
                        refreshStatuses()
                        // refreshArgumentHeader()
                    } else if ($target.hasClass('add-predicate')) {
                        addEmptyPredicate().find(':input').focus()
                    }
                })
                

            $('select', $Frm).selectmenu({
                classes: {
                    'ui-selectmenu-menu': 'pt-app'
                }
            })
            $('input[type="submit"]', $Frm).button()

            
            var selectedTab = TabIndexes[AppData.selected_tab]
            if (!Number.isInteger(selectedTab)) {
                selectedTab = 0
            }
            const tabOpts = {
                active      : selectedTab,
                collapsible : is_proof,
            }
            $('#proove-tabs').tabs(tabOpts)
            $('a.button').button()
            $('.ui-controlgroup').controlgroup({
                button: 'a',
            })
            $('.tableau-controls a[title]').each(function() {
                const $me = $(this)
                var html = '<span class="tooltip controls">' + $me.attr('title')
                var shortkey = $me.attr('data-shortcut-key')
                if (shortkey) {
                    html += '<hr>Shorcut key: <code class="shortkey">' + shortkey + '</code>'
                }
                html += '</span>'
                $me.tooltip({content: html, show: {delay: 2000}})
            })
            $('.tooltip', $Frm).tooltip({show: {delay: 1000}})

            $('.tableau').tableau({
                // autoWidth: true,
                scrollContainer: $(document)
            })

            setTimeout(function() {
                if (is_proof) {
                    var tableau = $('.tableau').tableau('instance')
                }
                ensureEmptyPremise()
                // ensureEmptyPredicate()
                refreshNotation()
                refreshLogic()
                if (is_proof) {
                    refreshStatuses()
                }
            })
        }

        /**
         * Form submit handler.
         *
         * @return void
         */
        function submitForm() {
            $('input:submit', $Frm).prop('disabled', true)
            const data = getApiData()
            const json = JSON.stringify(data)
            debug('submitForm', data)
            $('input[name="api-json"]', $Frm).val(json)
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
                message : message || '',
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

        // /**
        //  * Get the output format value.
        //  *
        //  * @return String name of the foramat, e.g. 'html'
        //  */
        // function currentOutputFormat() {
        //     return $('#format', $Ctx).val()
        // }

        // /**
        //  * Get the output notation value.
        //  *
        //  * @return String name of the notation, e.g. 'standard'
        //  */
        // function currentOutputNotation() {
        //     return $('#output_notation', $Ctx).val()
        // }

        // /**
        //  * Get the output symbol set value.
        //  *
        //  * @return String name of the symbol set, e.g. 'default'
        //  */
        // function currentOutputSymbolEnc() {
        //     return $('#symbol_enc', $Ctx).val()
        // }

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
         * Clear the example argument select menu.
         *
         * @return void
         */
        function clearExampleArgument() {
            $('#example_argument', $Ctx).val('')
            $('#example_argument', $Ctx).selectmenu('refresh')
        }

        /**
         * Add a user-defined predicate row. The first two parameters, index
         * and subscript, are required.
         *
         * @param index The integer index of the predicate.
         * @param subscript The integer subscript of the predicate.
         * @param name The name of the predicate (optional).
         * @param arity The integer arity of the predicate (optional).
         * @return The jquery element of the created tr.
         */
        function addPredicate(index, subscript, name, arity) {
            const thisNotation = currentNotation()
            var html = ''
            $.each(AppData.nups, function(notation, symbols) {
                var classes = ['predicate-symbol', 'notation-' + notation]
                if (notation != thisNotation)
                    classes.push('hidden')
                html += '<span class="' + classes.join(' ') + '">'
                html += $('<div/>').text(symbols[index]).html()
                if (subscript > 0)
                    html += '<sub>' + subscript + '</sub>'
                html += '</span>'
            })
            // debug(html)
            const $el = $(render(Templates.predicate, { 
                index       : index,
                subscript   : subscript,
                name        : name || ('Predicate ' + ($('input.predicate-symbol', $Ctx).length + 1)),
                arity       : arity || '',
                symbol_html : html
            }))
            $('table.predicates', $Ctx).append($el)
            return $el
        }

        /**
         * Add an empty input for a user-defined predicate. Calculates the next
         * index and subscript.
         *
         * @return The jquery element of the created tr.
         */
        function addEmptyPredicate() {
            const $symbols   = $('input.predicate-symbol', $Ctx)
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
            return addPredicate(index, subscript)
        }

        /**
         * Clear all the user-defined predicate input rows.
         *
         * @return void
         */
        function clearPredicates() {
            $('tr.user-predicate', $Ctx).remove()
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
        }

        /**
         * Input notation change handler. Show appropriate lexicon, and update
         * the example argument, if any.
         *
         * @return void
         */
        function refreshNotation() {
            const notation = currentNotation()
            $('.lexicons .lexicon:not(.predicates)', $Ctx).hide()
            $('.lexicon.notation-' + notation, $Ctx).show()
            $('.predicate-symbol', $Ctx).addClass('hidden')
            $('.predicate-symbol.notation-' + notation, $Ctx).removeClass('hidden')
            if ($('#example_argument', $Ctx).val()) {
                refreshExampleArgument()
            } else {
                // translate good sentences
                $('input.sentence', $Ctx).each(function() {
                    const value = $(this).val()
                    if (value && SentenceRenders[value]) {
                        if (SentenceRenders[value][notation]) {
                            $(this).val(SentenceRenders[value][notation].default)
                        }
                    }
                })
            }
        }

        /**
         * Example argument change handler.
         *
         * @return void
         */
        function refreshExampleArgument() {
            debug('refreshExampleArgument', 1)
            clearPredicates()
            clearArgument()
            const $me = $('#example_argument')
            const argName = $me.val()

            debug('refreshExampleArgument', 5)
            if (!argName) {
                ensureEmptyPremise()
                // ensureEmptyPredicate()
                return
            }
            debug('refreshExampleArgument', 8)
            const notation = currentNotation()
            const arg = AppData.example_arguments[argName][notation]
            $.each(arg.premises, function(i, value) {
                addPremise(value)
            })
            debug('refreshExampleArgument', 15)
            $('#conclusion').val(arg.conclusion)
            $.each(AppData.example_predicates, function(i, pred) {
                addPredicate(pred[1], pred[2], pred[0], pred[3])
            })
            debug('refreshExampleArgument', 35)
        }

        /**
         * Make AJAX requests to parse the premises & conclusion.
         *
         * @return void
         */
        function refreshStatuses(isForce) {
            $('input.sentence', $Ctx).each(function(sentenceIndex) {
                const $status = $(this).closest('div.input').find('.status')
                const notation = currentNotation()
                const input = $(this).val()
                if (input) {
                    const hash = hashString([input, notation].join('.'))
                    if (!isForce && +$status.attr('data-hash') === hash) {
                        return
                    }
                    $status.attr('data-hash', hash)
                    var apiData = getApiData()
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
                            $status.attr('title', res.result.type).tooltip()
                            SentenceRenders[input] = res.result.rendered
                            // debug({SentenceRenders})
                            // refreshArgumentHeader()
                        },
                        error: function(xhr, textStatus, errorThrown) {
                            $status.removeClass('good').addClass('bad')
                            var title
                            if (xhr.status == 400) {
                                const res = xhr.responseJSON
                                if (res.errors) {
                                    if (res.errors.Sentence) {
                                        title = res.errors.Sentence
                                    } else {
                                        var errKey = Object.keys(res.errors)[0]
                                        title = [errKey, res.errors[errKey]].join(': ')
                                    }
                                } else {
                                    title = [res.error, res.message].join(': ')
                                }
                            } else {
                                title = [textStatus, errorThrown].join(': ')
                            }
                            $status.attr('title', title).tooltip()
                            // delete SentenceRenders[input]
                        }
                    })
                } else {
                    $status.removeClass('bad good')
                    $status.attr('title', '')
                    $status.attr('data-hash', '')
                }
            })
        }

        // /**
        //  * Update the argument display in the header bar of the argument fieldset.
        //  *
        //  * @return void
        //  */
        // function refreshArgumentHeader() {
        //     const notation = currentOutputNotation()
        //     const enc = currentOutputSymbolEnc()
        //     const premises = []
        //     var conclusion
        //     $('input.sentence', $Ctx).each(function(sentenceIndex) {
        //         const $status = $(this).closest('div.input').find('.status')
        //         const input = $(this).val()
        //         const isConclusion = $(this).hasClass('conclusion')
        //         const isGood = $status.hasClass('good')
        //         if (input || isConclusion) {
        //             var sentence
        //             if (isGood && SentenceRenders[input]) {
        //                 // debug({notation, enc})
        //                 sentence = SentenceRenders[input][notation][enc]
        //                 if (enc != 'html') {
        //                     sentence = h(sentence)
        //                 }
        //             } else {
        //                 sentence = '?'
        //             }
        //             if (isConclusion) {
        //                 conclusion = sentence
        //             } else {
        //                 premises.push(sentence)
        //             }
        //         }
        //     })
        //     $('#argument-heading-rendered').html(premises.join(', ') + ' &there4; ' + conclusion)
        // }

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
                logic: $('select[name="logic"]', $Frm).val(),
                argument : {
                    conclusion: $('#conclusion', $Frm).val(),
                    premises  : [],
                    predicates: [],
                    notation: currentNotation(),
                },
                output: {
                    format   : $('#format', $Frm).val(),
                    notation : $('#output_notation', $Frm).val(),
                    symbol_enc : $('#symbol_enc', $Frm).val(),
                    options : {
                        classes: [],
                        models: undefined,
                    }
                },
                build_models: undefined,
                max_steps: undefined,
                rank_optimizations: undefined,
                group_optimizations: undefined,
                show_controls: undefined,
            }
            $('input.premise', $Frm).each(function() {
                const val = $(this).val()
                if (val) {
                    data.argument.premises.push(val)
                }
            })
            $('.user-predicate', $Frm).each(function() {
                const $tr = $(this)
                const arity = $('input.arity', $tr).val()
                if (arity.length > 0) {
                    const coords = $('input.predicate-symbol', $tr).val().split('.')
                    const arityNumVal = +arity
                    // let invalid arity propagate
                    var arityVal
                    if (isNaN(arityNumVal)) {
                        arityVal = arity
                    } else {
                        arityVal = arityNumVal
                    }
                    data.argument.predicates.push({
                        // name      : $('input.predicateName', $tr).val(),
                        index     : +coords[0],
                        subscript : +coords[1],
                        arity     : arityVal
                    })
                }
            })
            $('input:checkbox.options', $Frm).each(function() {
                const $me = $(this)
                const name = $me.attr('name')
                const opt = name.split('.')[1]
                const value = $me.is(':checked')
                data.output.options[opt] = value
            })
            if (data.output.options.models) {
                data.output.options.classes.push('with-models')
                data.build_models = true
            }
            const maxStepsVal = $('#options_max_steps', $Frm).val()
            if (maxStepsVal.length) {
                const maxStepsIntVal = parseInt(maxStepsVal)
                if (isNaN(maxStepsIntVal)) {
                    // let invalid values propagate
                    data.max_steps = maxStepsVal
                } else {
                    data.max_steps = maxStepsIntVal
                }
            } else {
                data.max_steps = undefined
            }
            const $rankOptim = $('#options_rank_optimizations', $Frm)
            if ($rankOptim.length) {
                data.rank_optimizations = $rankOptim.is(':checked')
            }
            const $groupOptim = $('#options_group_optimizations', $Frm)
            if ($groupOptim.length) {
                data.group_optimizations = $groupOptim.is(':checked')
            }
            const $showControls = $('#options_show_controls', $Frm)
            if ($showControls.length) {
                if ($showControls.attr('type') == 'checkbox') {
                    data.show_controls = $showControls.is(':checked')
                } else {
                    data.show_controls = Boolean($showControls.val())
                }
            } else {
                data.show_controls = true
            }
            if (data.show_controls) {
                data.output.options.classes.push('with-controls')
            }
            const $colorOpen = $('#options_color_open', $Frm)
            if (!$colorOpen.length || $colorOpen.is(':checked')) {
                data.output.options.classes.push('color-open')
            }
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

        function debug(...args) {
            if (is_debug) {
                console.log(...args)
            }
        }

        init()

        // debug({AppData})
    })
})(jQuery);