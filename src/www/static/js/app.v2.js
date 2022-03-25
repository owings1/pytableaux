/**
 * pytableaux, a multi-logic proof generator.
 * Copyright (C) 2014-2022 Doug Owings.
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

    const Cls = {
        app          : 'pt-app',
        arity        : 'arity',
        bad          : 'bad',
        button       : 'button',
        buttonGroup  : 'ui-controlgroup',
        colorOpen    : 'color-open',
        controls     : 'controls',
        debug        : 'debug',
        debugs       : 'debugs',
        debugContent : 'debug-content',
        debugHead    : 'debug-heading',
        good         : 'good',
        hidden       : 'hidden',
        input        : 'input',
        jsonDump     : 'json-dump',
        jsonViewDoc  : 'json-document', // used by jsonViewer plugin
        lexicon      : 'lexicon',
        lexicons     : 'lexicons',
        logicDetails : 'logic-details',
        notation     : 'notation',      // used as prefix, e.g. notation-polish
        options      : 'options',
        predAdd      : 'add-predicate',
        predDel      : 'del-predicate',
        predicate    : 'predicate',
        predicates   : 'predicates',
        predSymbol   : 'predicate-symbol',
        premise      : 'premise',
        premiseAdd   : 'add-premise',
        premiseDel   : 'del-premise',
        premiseMark  : 'premise-marker',
        premises     : 'premises',
        sentence     : 'sentence',
        shortkey     : 'shortkey',
        status       : 'status',
        tableau      : 'tableau',
        tooltip      : 'tooltip',
        uiControls   : 'ui-controls',
        withControls : 'with-controls',
        withModels   : 'with-models',
    }

    const Atr = {
        dataHash     : 'data-hash',
        dataPremNum  : 'data-premise-num',
        dataShortKey : 'data-shortcut-key',
    }

    const Sel = {
        appBody           : 'body.' + Cls.app,
        appForm           : '#argument_form',
        pageJson          : '#pt_page_data',
        appUiTabs         : '#uitabs_main',

        clearArg          : '#clear_argument',

        checkBuildModels  : '#options_build_models',
        checkColorOpen    : '#options_color_open',
        checkGroupOptim   : '#options_group_optimizations',
        checkRankOptim    : '#options_rank_optimizations',
        checkShowControls : '#options_show_controls',
        fieldApiJson       : '#api_json',
        fieldArgExample    : '#example_argument',
        fieldConclusion    : '#input_conclusion',
        fieldInputNotn     : '#input_notation',
        fieldLogic         : '#selected_logic',
        fieldMaxSteps      : '#options_max_steps',
        fieldOutputCharset : '#output_charset',
        fieldOutputFmt     : '#output_format',
        fieldOutputNotn    : '#output_notation',

        fieldsArity       : ['input', Cls.arity].join('.'),
        fieldsPredSymbol  : ['input', Cls.predSymbol].join('.'),
        fieldsPremise     : ['input', Cls.premise].join('.'),
        fieldsSentence    : ['input', Cls.sentence].join('.'),

        headerDebugs      : '#pt_debugs_heading',
        wrapDebugs        : '#pt_debugs_wrapper',

        inputPredicate    : '.' + Cls.input + '.' + Cls.predicate,
        inputPremise      : '.' + Cls.input + '.' + Cls.premise,
        inputSentence     : '.' + Cls.input + '.' + Cls.sentence,
        linksButton       : ['a', Cls.button].join('.'),

        debugs            : '.' + Cls.debug,
        predicates        : '.' + Cls.predicates,
        premises          : '.' + Cls.premises,
        tableaux          : '.' + Cls.tableau,

        templatePrem      : '#template_premise',
        templatePred      : '#template_predicate',
    }

    // Fixed optname -> checkbox mappings.
    const CheckSels = {
        show_controls       : Sel.checkShowControls,
        color_open          : Sel.checkColorOpen,
        build_models        : Sel.checkBuildModels,
        rank_optimizations  : Sel.checkRankOptim,
        group_optimizations : Sel.checkGroupOptim,
    }
    const OptClasses = {
        build_models  : Cls.withModels,
        show_controls : Cls.withControls,
        color_open    : Cls.colorOpen,
    }

    const API_PARSE_URI = '/api/parse'
    const TTIP_OPTS = {show: {delay: 1000}}

    $(document).ready(function() {

        const AppData = window.AppData
        delete window.AppData

        const PageData = JSON.parse($(Sel.pageJson).html())
        const IS_DEBUG = Boolean(PageData.is_debug)
        const IS_PROOF = Boolean(PageData.is_proof)
        const PRED_SYMCOUNT = Object.values(AppData.nups)[0].length
        const Templates = {
            premise    : $(Sel.templatePrem).html(),
            predicate  : $(Sel.templatePred).html(),
        }

        const $AppBody = $(Sel.appBody)
        const $AppForm = $(Sel.appForm)

        const ParseCache = Object.create(null)

        if (IS_DEBUG) {
            window.AppDebug = {
                AppData,
                PageData,
                ParseCache,
            }
        }

        /**
         * Main initialization routine.
         * @return {void}
         */
        function init() {

            // Load event listeners.
            initHandlers()

            // Init UI plugins and config.
            initPlugins()

            // Debugs data contents init.
            if (IS_DEBUG) {
                initDebug()
            }

            setTimeout(function() {
                refreshNotation()
                refreshLogic()
                if (IS_PROOF) {
                    refreshStatuses()
                }
            })
        }

        function initHandlers() {
            // Input form events.
            $AppForm
                .on('change selectmenuchange', function(e) {
                    const $target = $(e.target)
                    if ($target.is(Sel.fieldArgExample)) {
                        // Change to selected exampleArg.
                        if (!$target.val()) {
                            return
                        }
                        refreshArgExample()
                        refreshStatuses()
                    } else if ($target.is(Sel.fieldInputNotn)) {
                        // Change to selected parsing notation.
                        refreshNotation()
                        refreshStatuses()
                    } else if ($target.is(Sel.fieldsSentence)) {
                        // Change to a sentence input field.
                        refreshStatuses()
                    } else if ($target.hasClass(Cls.arity)) {
                        // Change to a predicate arity field.
                        refreshStatuses(true)
                    } else if ($target.is(Sel.fieldLogic)) {
                        // Change to the selected logic.
                        refreshLogic()
                    }
                })
                .on('click', function(e) {
                    const $target = $(e.target)
                    if ($target.hasClass(Cls.premiseAdd)) {
                        // Add premise.
                        addPremise()
                    } else if ($target.hasClass(Cls.predAdd)) {
                        // Add predicate.
                        const coords = getNextPredCoords()
                        const arity = 1
                        addPredicate(coords[0], coords[1], arity)
                            .find(':input')
                            .focus() 
                    } else if ($target.hasClass(Cls.premiseDel)) {
                        // Delete premise.
                        const $prem = $target.closest(Sel.inputPremise)
                        $prem.nextAll(Sel.inputPremise).each(function() {
                            // renumber later ones.
                            const $me = $(this)
                            const num = +$me.attr(Atr.dataPremNum) - 1
                            $me.attr(Atr.dataPremNum, num)
                            $('.' + Cls.premiseMark, $me).text('P' + num)
                        })
                        _removePrem($prem)
                        refreshStatuses()
                    } else if ($target.hasClass(Cls.predDel)) {
                        // Delete predicate.
                        $target.closest(Sel.inputPredicate).remove()
                        refreshStatuses()
                    } else if ($target.is(Sel.clearArg)) {
                        // Clear the argument.
                        clearArgument()
                        $(Sel.fieldArgExample).val('').selectmenu('refresh')
                        refreshStatuses()
                    }
                })
                .on('submit', function(e) {
                    submitForm()
                })
        }

        function initPlugins() {
            // UI Selectmenu
            $('select', $AppForm).selectmenu({
                classes: {
                    'ui-selectmenu-menu': Cls.app
                }
            })

            // UI Tabs
            var tabIndex = TabIndexes[PageData.selected_tab]
            if (!Number.isInteger(tabIndex)) {
                tabIndex = 0
            }
            const tabOpts = {
                active      : tabIndex,
                collapsible : IS_PROOF,
            }
            $(Sel.appUiTabs).tabs(tabOpts)

            // UI Button
            $('input:submit', $AppForm).button()
            $(Sel.linksButton, $AppBody).button()
            $('.' + Cls.buttonGroup, $AppBody).controlgroup({button: 'a'})

            // UI Tooltip - form help
            $('.' + Cls.tooltip, $AppForm).tooltip(TTIP_OPTS)

            // UI Tooltip - ui controls help
            $('.' + Cls.uiControls + ' a[title]', $AppBody).each(function() {
                const $me = $(this)
                const classNames = [Cls.tooltip, Cls.controls]
                const shortkey = $me.attr(Atr.dataShortKey)
                var html = '<span class="' + classNames.join(' ') + '">' + $me.attr('title')
                if (shortkey) {
                    html += '<hr>Shorcut key: <code class="' + Cls.shortkey + '">' + shortkey + '</code>'
                }
                html += '</span>'
                $me.tooltip({content: html, show: {delay: 2000}})
            })

            // Init Tableau Plugin
            if (IS_PROOF) {
                $(Sel.tableaux).tableau({
                    // autoWidth: true,
                    scrollContainer: $(document)
                })
            }
        }

        /**
         * Add a premise input row. All parameters are optional.
         *
         * @param {string} value The string value of the sentence.
         * @param {string} status The status class name, 'good' or 'bad'.
         * @param {string} message The status message.
         * @return {void}
         */
         function addPremise(value, status, message) {
            const premiseNum = $(Sel.fieldsPremise, $AppForm).length + 1
            const vars = {
                n       : premiseNum,
                value   : value   || '',
                status  : status  || '',
                message : message || '',
            }
            const html = render(Templates.premise, vars)
            const $prem = $(html).appendTo($(Sel.premises, $AppForm))
            $('.' + Cls.tooltip, $prem).tooltip(TTIP_OPTS)
        }

        /**
         * Cleanup tooltip and remove a premise from the DOM.
         * @param {object} $prem The singelton premise row jQuery element.
         * @return {void}
         */
        function _removePrem($prem) {
            // Destroy tooltips.
            $('.' + Cls.status, $prem).add('.' + Cls.tooltip).each(function() {
                const tooltip = $(this).tooltip('instance')
                if (tooltip) {
                    tooltip.destroy()
                }
            })
            // TODO: Prune ParseCache?
            $prem.remove()
        }

        /**
         * Add a user-defined predicate row. The first two parameters, index
         * and subscript, are required.
         *
         * @param {integer} index The integer index of the predicate.
         * @param {integer} subscript The integer subscript of the predicate.
         * @param {integer} arity The integer arity of the predicate (optional).
         * @return {object} The jquery element of the created tr.
         */
        function addPredicate(index, subscript, arity) {
            const notation = $(Sel.fieldInputNotn).val()
            var html = ''
            $.each(AppData.nups, function(notn, symbols) {
                const classes = [
                    Cls.predSymbol,
                    Cls.lexicon,
                    [Cls.notation, esc(notn)].join('-')
                ]
                if (notn !== notation)
                    classes.push(Cls.hidden)
                html += '<span class="' + classes.join(' ') + '">'
                html += $('<div/>').text(symbols[index]).html()
                if (subscript > 0)
                    html += '<sub>' + esc(subscript) + '</sub>'
                html += '</span>'
            })
            const vars = { 
                index       : index,
                subscript   : subscript,
                arity       : arity || '',
                symbol_html : html,
            }
            return $(render(Templates.predicate, vars)).appendTo(
                $(Sel.predicates, $AppForm)
            )
        }

        /**
         * Get the next available index, subscript.
         * @return {array}
         */
        function getNextPredCoords() {
            const $symbols   = $(Sel.fieldsPredSymbol, $AppForm)
            const numSymbols = $symbols.length
            var index      = 0
            var subscript  = 0
            if (numSymbols > 0) {
                var last = $symbols.last().val().split('.')
                index = +last[0] + 1
                subscript = +last[1]
                if (index === PRED_SYMCOUNT) {
                    index = 0
                    subscript += 1
                }
            }
            return [index, subscript]
        }

        /**
         * Clear all user predicates.
         * @return {void}
         */
        function clearPredicates() {
            $(Sel.inputPredicate, $AppForm).remove()
        }

        /**
         * Clear all premises and conclusion inputs.
         * @return {void}
         */
        function clearArgument() {
            $(Sel.inputPremise, $AppForm).each(function() {
                _removePrem($(this))
            })
            $(Sel.fieldConclusion).val('')
            for (var key in ParseCache) {
                delete ParseCache[key]
            }
        }

        /**
         * Logic select change handler. Show appropriate logic information.
         * @return {void}
         */
        function refreshLogic() {
            const logicName = $(Sel.fieldLogic).val()
            $('.' + Cls.logicDetails, $AppForm)
                .hide()
                .filter('.' + logicName)
                .show()
        }

        /**
         * Input notation change handler. Show appropriate lexicon, and update
         * the example argument, if any.
         * @return {void}
         */
        function refreshNotation() {

            const notation = $(Sel.fieldInputNotn).val()
            const notnClass = [Cls.notation, notation].join('-')

            // Show/hide lexicons
            $('.' + Cls.lexicon, $AppForm).each(function() {
                const $me = $(this)
                if ($me.hasClass(notnClass)) {
                    $me.removeClass(Cls.hidden).show()
                } else {
                    $me.addClass(Cls.hidden).hide()
                }
            })

            // Use built-in input strings for example arguments.
            if ($(Sel.fieldArgExample).val()) {
                refreshArgExample()
                return
            }

            // Otherwise get translations from cached succesful api-parse responses.
            $(Sel.fieldsSentence, $AppForm).each(function() {
                const value = $(this).val()
                if (value && ParseCache[value]) {
                    if (ParseCache[value][notation]) {
                        $(this).val(ParseCache[value][notation].default)
                    }
                }
            })
        }

        /**
         * Change handler for exampleArg select. If not argument selected,
         * does nothing.
         * @return {void}
         */
        function refreshArgExample() {

            const argName = $(Sel.fieldArgExample).val()
            if (!argName) {
                return
            }

            clearPredicates()
            clearArgument()

            const notation = $(Sel.fieldInputNotn).val()
            const arg = AppData.example_args[argName][notation]

            $.each(arg.premises, function(i, value) {
                addPremise(value)
            })

            $(Sel.fieldConclusion).val(arg.conclusion)

            $.each(AppData.example_preds, function(i, pred) {
                addPredicate(pred.index, pred.subscript, pred.arity)
            })
        }

        /**
         * Make AJAX requests to parse the premises & conclusion.
         *
         * @param {bool} isForce Force refresh.
         * @return {void}
         */
        function refreshStatuses(isForce) {

            const notation = $(Sel.fieldInputNotn).val()
            var preds // lazy fetch

            $(Sel.fieldsSentence, $AppForm).each(function() {

                const $me = $(this)

                const $status = $me
                    .closest(Sel.inputSentence)
                    .find('.' + Cls.status)
                
                const text = $(this).val()

                if (!text) {
                    // Clear status.
                    $status
                        .removeClass([Cls.good, Cls.bad])
                        .attr('title', '')
                        .attr(Atr.dataHash, '')
                    return
                }

                // Check for change since last request against stored value.
                const hash = [text, notation].join('.')
                const stored = $status.attr(Atr.dataHash)
                if (!isForce && stored === hash) {
                    return
                }
                $status.attr(Atr.dataHash, hash)

                if (!preds) {
                    preds = getPredsData()
                }
                // Send api-parse request.
                $.ajax({
                    url         : API_PARSE_URI,
                    method      : 'POST',
                    contentType : 'application/json',
                    dataType    : 'json',
                    data        : JSON.stringify({
                        input      : text,
                        notation   : notation,
                        predicates : preds,
                    }),
                    success: function(res) {
                        $status
                            .removeClass(Cls.bad)
                            .addClass(Cls.good)
                            .attr('title', res.result.type)
                            .tooltip()
                        ParseCache[text] = res.result.rendered
                    },
                    error: function(xhr, textStatus, errorThrown) {
                        $status.removeClass(Cls.good).addClass(Cls.bad)
                        var title
                        if (xhr.status === 400) {
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
                    }
                })
            })
        }

        /**
         * Read the form inputs into an object suitable for posting to
         * the prove api.
         *
         * @return {object}
         */
         function getApiData() {
            const data = {
                logic    : $(Sel.fieldLogic).val(),
                argument : getArgData(),
                output: {
                    format   : $(Sel.fieldOutputFmt).val(),
                    notation : $(Sel.fieldOutputNotn).val(),
                    charset  : $(Sel.fieldOutputCharset).val(),
                    options  : {
                        classes : [],
                    }
                },
                // debug/advanced options.
                rank_optimizations  : true,
                group_optimizations : true,
            }

            for (var key in CheckSels) {
                var $check = $(CheckSels[key], $AppForm)
                if ($check.length) {
                    data[key] = $check.is(':checked')
                }
            }

            // TabWriter classes option.
            const clsarr = data.output.options.classes
            for (var key in OptClasses) {
                if (data[key]) {
                    clsarr.push(OptClasses[key])
                }
            }

            // Max steps.
            const maxStepsVal = $(Sel.fieldMaxSteps, $AppForm).val()
            if (maxStepsVal.length) {
                const maxStepsIntVal = parseInt(maxStepsVal)
                if (isNaN(maxStepsIntVal)) {
                    // Let invalid max_steps value propagate.
                    data.max_steps = maxStepsVal
                } else {
                    data.max_steps = maxStepsIntVal
                }
            } else {
                data.max_steps = undefined
            }


            return data
        }

        /**
         * Returns an object with the conclusion and premises
         * inputs, Empty premises are skipped. No other validation
         * on the sentences. Includes predicates data from `getPredsData()`
         * and the selected notation.
         * 
         * @return {object}
         */
        function getArgData() {
            const premises = []
            $(Sel.fieldsPremise, $AppForm).each(function() {
                const val = $(this).val()
                if (val) {
                    premises.push(val)
                }
            })
            return {
                notation   : $(Sel.fieldInputNotn).val(),
                conclusion : $(Sel.fieldConclusion).val(),
                premises   : premises,
                predicates : getPredsData(),
            }
        }

        /**
         * Returns array of {index, subscript, arity} objects from
         * the form. Rows with no value of `arity` are skipped. Attempts
         * to cast `arity` to a number, but if it false with NaN, the
         * original input string is returned.
         * 
         * @return {array}
         */
        function getPredsData() {
            const preds = []
            $(Sel.inputPredicate, $AppForm).each(function() {
                const $row = $(this)
                const arity = $(Sel.fieldsArity, $row).val()
                if (!arity.length) {
                    // Skip blank values.
                    return
                }
                const arityNumVal = +arity
                // Let invalid arity value propagate.
                var arityVal
                if (isNaN(arityNumVal)) {
                    arityVal = arity
                } else {
                    arityVal = arityNumVal
                }
                const coords = $(Sel.fieldsPredSymbol, $row).val().split('.')
                preds.push({
                    index     : +coords[0],
                    subscript : +coords[1],
                    arity     : arityVal
                })
            })
            return preds
        }

        /**
         * Form submit handler.
         *
         * @return {void}
         */
         function submitForm() {
            $('input:submit', $AppForm).prop('disabled', true)
            const data = getApiData()
            const json = JSON.stringify(data)
            $(Sel.fieldApiJson).val(json)
        }

        /**
         * Interpolate variable strings like {varname}.
         *
         * @param {string} str The template string.
         * @param {object} vars The variables object.
         * @return {string} The rendered string.
         */
         function render(str, vars) {
            if (vars) {
                $.each(vars, function(name, val) {
                    str = str.replace(new RegExp('{' + name + '}', 'g'), val)
                })
            }
            return str
        }

        /**
         * Escape using encodeURIComponent.
         * 
         * @param {string} str The input string.
         * @return {string} Escaped output.
         */
        function esc(str) {
            return encodeURIComponent(str)
        }

        function debug(...args) {
            if (IS_DEBUG) {
                console.debug(...args)
            }
        }

        function initDebug() {
            const $debugs = $(Sel.wrapDebugs, $AppBody)
            // Debug click show/hide.
            $debugs.on('click', [Sel.debugs, Sel.headerDebugs].join(), function(e) {
                const $target = $(e.target)

                // Main Debug Header - toggle all and return.
                if ($target.is(Sel.headerDebugs)) {
                    $target.next('.' + Cls.debugs).toggle()
                    return
                }

                // Single debug content - toggle and lazy-init jsonViewer.
                var $content
                if ($target.hasClass(Cls.debugHead)) {
                    // For header click, toggle debug content.
                    $content = $target.next('.' + Cls.debugContent)
                    const isHiding = $content.is(':visible')
                    $content.toggle()
                    // If we are hiding it, no need to init jsonViewer.
                    if (isHiding) {
                        return
                    }
                } else if ($target.hasClass(Cls.debugContent)) {
                    // For content click, check whether to init jsonViewer.
                    $content = $target
                } else {
                    // No behavior defined.
                    return
                }

                // Init jsonViewer if this is a json dump and does not have
                // class from plugin.
                const shouldInit = (
                    $content.hasClass(Cls.jsonDump) &&
                    !$content.hasClass(Cls.jsonViewDoc)
                )
                if (shouldInit) {
                    const json = $content.text()
                    const data = JSON.parse(json)
                    $content.jsonViewer(data, {
                        withLinks: true,
                        withQuotes: true,
                    })
                }
            })
        }

        init()

    })

})(jQuery);