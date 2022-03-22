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
        notation     : 'notation',      // used as prefix
        options      : 'options',
        predAdd      : 'add-predicate',
        predicates   : 'predicates',
        predSymbol   : 'predicate-symbol',
        predUser     : 'user-predicate',
        premise      : 'premise',
        sentence     : 'sentence',
        shortkey     : 'shortkey',
        status       : 'status',
        tableau      : 'tableau',
        tooltip      : 'tooltip',
        uiControls   : 'ui-conrols',
        withControls : 'with-controls',
        withModels   : 'with-models',
    }

    const Atr = {
        dataHash     : 'data-hash',
        dataShortKey : 'data-shortcut-key',
    }

    const Sel = {
        appBody           : 'body.' + Cls.app,
        appForm           : '#tableau_input_form',
        appJson           : '#pt_app_data',
        appTabs           : '#proove-tabs',
        checkBuildModels  : '#options_build_models',
        checkColorOpen    : '#options_color_open',
        checkGroupOptim   : '#options_group_optimizations',
        checkRankOptim    : '#options_rank_optimizations',
        checkShowControls : '#options_show_controls',
        checksOption      : ['input:checkbox', Cls.options].join('.'),
        clearArgExample   : '#clear_argument',
        headDebugs        : '#pt_debugs_heading',
        inputConclusion   : '#conclusion',
        inputMaxSteps     : '#options_max_steps',
        inputsPredArity   : ['input', Cls.arity].join('.'),
        inputsPredSymbol  : ['input', Cls.predSymbol].join('.'),
        inputsPremise     : ['input', Cls.premise].join('.'),
        inputsSentence    : ['input', Cls.sentence].join('.'),
        linksButton       : ['a', Cls.button].join('.'),
        rowsDebug         : '.' + Cls.debug,
        rowsPredUser      : ['tr', Cls.predUser].join('.'),
        rowsPremise       : ['.input', Cls.premise].join('.'),
        selectArgExample  : '#example_argument',
        selectLogic       : '#selected_logic',
        selectOutputFmt   : '#output_format',
        selectOutputNotn  : '#output_notation',
        selectParseNotn   : '#input_notation',
        selectOutputChrs  : '#output_charset',
        submitJson        : '#tableau_form_api_json',
        tableaux          : '.' + Cls.tableau,
        templatePrem      : '#premiseTemplate',
        templatePred      : '#predicateRowTemplate',
        wrapDebugs        : '#pt_debugs_wrapper',
        wrapPredicates    : '#predicates_input_table',
        wrapPremises      : '#premises_inputs',
    }

    const API_PARSE_URI = '/api/parse'


    $(document).ready(function() {

        const AppData = JSON.parse($(Sel.appJson).html())
        const IS_DEBUG = Boolean(AppData.is_debug)
        const IS_PROOF = Boolean(AppData.is_proof)
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
                ParseCache,
            }
        }

        /**
         * Main initialization routine.
         *
         * @return {void}
         */
        function init() {
            // Input form events.
            $AppForm
                .on('keyup focus', [Sel.inputsPremise, Sel.inputConclusion].join(), ensureEmptyPremise)
                .on('change selectmenuchange', function(e) {
                    const $target = $(e.target)
                    if ($target.is(Sel.selectArgExample)) {
                        refreshArgExample()
                        refreshStatuses()
                    } else if ($target.is(Sel.selectParseNotn)) {
                        refreshNotation()
                        refreshStatuses()
                    } else if ($target.is(Sel.inputsSentence)) {
                        refreshStatuses()
                    } else if ($target.hasClass(Cls.arity)) {
                        refreshStatuses(true)
                    } else if ($target.is(Sel.selectLogic)) {
                        refreshLogic()
                    }
                })
                .on('submit', function(e) {
                    submitForm()
                })
                .on('click', function(e) {
                    const $target = $(e.target)
                    if ($target.is(Sel.clearArgExample)) {
                        clearArgument()
                        clearArgExample()
                        ensureEmptyPremise()
                        refreshStatuses()
                    } else if ($target.hasClass(Cls.predAdd)) {
                        addEmptyPredicate().find(':input').focus()
                    }
                })
                

            // UI Selectmenu
            $('select', $AppForm).selectmenu({
                classes: {
                    'ui-selectmenu-menu': Cls.app
                }
            })

            // UI Tabs
            var tabIndex = TabIndexes[AppData.selected_tab]
            if (!Number.isInteger(tabIndex)) {
                tabIndex = 0
            }
            const tabOpts = {
                active      : tabIndex,
                collapsible : IS_PROOF,
            }
            $(Sel.appTabs).tabs(tabOpts)

            // UI Button
            $('input:submit', $AppForm).button()
            $(Sel.linksButton, $AppBody).button()
            $('.' + Cls.buttonGroup, $AppBody).controlgroup({button: 'a'})

            // UI Tooltip - form help
            $('.' + Cls.tooltip, $AppForm).tooltip({show: {delay: 1000}})
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
            
            setTimeout(function() {
                ensureEmptyPremise()
                refreshNotation()
                refreshLogic()
                if (IS_PROOF) {
                    refreshStatuses()
                }
            })

            // Init Tableau Plugin
            if (IS_PROOF) {
                $(Sel.tableaux).tableau({
                    // autoWidth: true,
                    scrollContainer: $(document)
                })
            }


            // Debugs data contents init.

            if (IS_DEBUG) {
                const $debugs = $(Sel.wrapDebugs, $AppBody)
                // Debug click show/hide.
                $debugs.on('click', [Sel.rowsDebug, Sel.headDebugs].join(), function(e) {
                    const $target = $(e.target)

                    // Main Debug Header - toggle all and return.
                    if ($target.is(Sel.headDebugs)) {
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
            $(Sel.submitJson).val(json)
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
         * Add a premise input row. All parameters are optional.
         *
         * @param {string} value The string value of the sentence.
         * @param {string} status The status class name, 'good' or 'bad'.
         * @param {string} message The status message.
         * @return {void}
         */
        function addPremise(value, status, message) {
            const premiseNum = $(Sel.inputsPremise, $AppForm).length + 1
            const vars = {
                n       : premiseNum,
                value   : value   || '',
                status  : status  || '',
                message : message || '',
            }
            $(Sel.wrapPremises).append(render(Templates.premise, vars))
        }

        /**
         * Clear all premises and conclusion inputs.
         *
         * @return {void}
         */
        function clearArgument() {
            $(Sel.rowsPremise, $AppForm).remove()
            $(Sel.inputConclusion).val('')
            for (var key in ParseCache) {
                delete ParseCache[key]
            }
            // ParseCache = Object.create(null)
        }

        /**
         * Clear the example argument select menu.
         *
         * @return {void}
         */
        function clearArgExample() {
            $(Sel.selectArgExample).val('').selectmenu('refresh')
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
            const thisNotation = $(Sel.selectParseNotn).val()
            var html = ''
            $.each(AppData.nups, function(notation, symbols) {
                const classes = [
                    Cls.predSymbol,
                    [Cls.notation, esc(notation)].join('-')
                ]
                if (notation !== thisNotation)
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
            const $el = $(render(Templates.predicate, vars))
            $(Sel.wrapPredicates).append($el)
            return $el
        }

        /**
         * Add an empty input for a user-defined predicate. Calculates the next
         * index and subscript.
         *
         * @return {object} The jQuery element of the created tr.
         */
        function addEmptyPredicate() {
            const $symbols   = $(Sel.inputsPredSymbol, $AppForm)
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
            return addPredicate(index, subscript)
        }

        /**
         * Clear all the user-defined predicate input rows.
         *
         * @return {void}
         */
        function clearPredicates() {
            $(Sel.rowsPredUser, $AppForm).remove()
        }

        /**
         * Check whether there is already an empty premise input row available
         * for input.
         *
         * @return {boolean}
         */
        function hasEmptyPremise() {
            var hasEmpty = false
            $(Sel.inputsPremise, $AppForm).each(function(i){
                if (!$(this).val()) {
                    hasEmpty = true
                    // Stop iteration (break).
                    return false
                }
            })
            return hasEmpty
        }

        /**
         * Ensure that there is an empty premise input row available for input.
         *
         * @return {void}
         */
        function ensureEmptyPremise() {
            if (!hasEmptyPremise()) {
                addPremise()
            }
        }

        /**
         * Logic select change handler. Show appropriate logic information.
         *
         * @return {void}
         */
        function refreshLogic() {
            const logicName = $(Sel.selectLogic).val()
            $('.' + Cls.logicDetails, $AppForm)
                .hide()
                .filter('.' + logicName)
                .show()
        }

        /**
         * Input notation change handler. Show appropriate lexicon, and update
         * the example argument, if any.
         *
         * @return {void}
         */
        function refreshNotation() {

            const notation = $(Sel.selectParseNotn).val()
            const notnClassSel = '.' + [Cls.notation, notation].join('-')

            // Show/hide lexicons (TODO: make selectors)
            $('.' + Cls.lexicons + ' .' + Cls.lexicon + ':not(.' + Cls.predicates + ')', $AppForm).hide()
            $('.' + Cls.lexicon + notnClassSel, $AppForm).show()
            $('.' + Cls.predSymbol, $AppForm)
                .addClass(Cls.hidden)
                .filter(notnClassSel)
                .removeClass(Cls.hidden)

            // Use built-in input strings for example arguments.
            if ($(Sel.selectArgExample).val()) {
                refreshArgExample()
                return
            }

            // Otherwise get translations from cached succesful api-parse responses.
            $(Sel.inputsSentence, $AppForm).each(function() {
                const value = $(this).val()
                if (value && ParseCache[value]) {
                    if (ParseCache[value][notation]) {
                        $(this).val(ParseCache[value][notation].default)
                    }
                }
            })
        }

        /**
         * Example argument change handler.
         *
         * @return {void}
         */
        function refreshArgExample() {
            clearPredicates()
            clearArgument()
            const argName = $(Sel.selectArgExample).val()

            if (!argName) {
                ensureEmptyPremise()
                return
            }
            const notation = $(Sel.selectParseNotn).val()
            const arg = AppData.example_args[argName][notation]
            $.each(arg.premises, function(i, value) {
                addPremise(value)
            })
            $(Sel.inputConclusion).val(arg.conclusion)
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
            $(Sel.inputsSentence, $AppForm).each(function() {

                const $status = $(this).closest('div.' + Cls.input).find('.' + Cls.status)
                const notation = $(Sel.selectParseNotn).val()
                const input = $(this).val()

                if (!input) {
                    // Clear status.
                    $status
                        .removeClass([Cls.good, Cls.bad])
                        .attr('title', '')
                        .attr(Atr.dataHash, '')
                    return
                }

                // Check for change against stored value.
                const hash = [input, notation].join('.')
                const stored = $status.attr(Atr.dataHash)
                if (!isForce && stored === hash) {
                    return
                }
                $status.attr(Atr.dataHash, hash)

                // Send api-parse request.
                const apiData = getApiData()
                $.ajax({
                    url         : API_PARSE_URI,
                    method      : 'POST',
                    contentType : 'application/json',
                    dataType    : 'json',
                    data        : JSON.stringify({
                        input      : input,
                        notation   : notation,
                        predicates : apiData.argument.predicates
                    }),
                    success: function(res) {
                        $status
                            .removeClass(Cls.bad)
                            .addClass(Cls.good)
                            .attr('title', res.result.type)
                            .tooltip()
                        ParseCache[input] = res.result.rendered
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
                logic: $(Sel.selectLogic).val(),
                argument : {
                    notation   : $(Sel.selectParseNotn).val(),
                    conclusion : $(Sel.inputConclusion).val(),
                    premises   : [],
                    predicates : [],
                },
                output: {
                    format   : $(Sel.selectOutputFmt).val(),
                    notation : $(Sel.selectOutputNotn).val(),
                    charset  : $(Sel.selectOutputChrs).val(),
                    options  : {
                        classes : [],
                    }
                },
                show_controls       : undefined,
                build_models        : undefined,
                max_steps           : undefined,
                // debug/advanced options.
                rank_optimizations  : true,
                group_optimizations : true,
            }
            $(Sel.inputsPremise, $AppForm).each(function() {
                const val = $(this).val()
                if (val) {
                    data.argument.premises.push(val)
                }
            })
            $(Sel.rowsPredUser, $AppForm).each(function() {
                const $row = $(this)
                const arity = $(Sel.inputsPredArity, $row).val()
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
                const coords = $(Sel.inputsPredSymbol, $row).val().split('.')
                data.argument.predicates.push({
                    index     : +coords[0],
                    subscript : +coords[1],
                    arity     : arityVal
                })
            })

            // Fixed optname -> checkbox mappings. 
            const checkSels = {
                show_controls       : Sel.checkShowControls,
                build_models        : Sel.checkBuildModels,
                rank_optimizations  : Sel.checkRankOptim,
                group_optimizations : Sel.checkGroupOptim,
            }
            const optClasses = {
                build_models  : Cls.withModels,
                show_controls : Cls.withControls,
            }

            for (var key in checkSels) {
                var $check = $(checkSels[key], $AppForm)
                if ($check.length) {
                    data[key] = $check.is(':checked')
                }
            }

            // TabWriter classes option.
            const clsarr = data.output.options.classes
            for (var key in optClasses) {
                if (data[key]) {
                    clsarr.push(optClasses[key])
                }
            }
            const $colorOpen = $(Sel.checkColorOpen, $AppForm)
            if (!$colorOpen.length || $colorOpen.is(':checked')) {
                clsarr.push(Cls.colorOpen)
            }

            // Max steps.
            const maxStepsVal = $(Sel.inputMaxSteps, $AppForm).val()
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
                console.log(...args)
            }
        }

        init()

    })

})(jQuery);