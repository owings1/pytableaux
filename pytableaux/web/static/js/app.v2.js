/**
 * pytableaux, a multi-logic proof generator.
 * Copyright (C) 2014-2023 Doug Owings.
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
;($ => {

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
        uitabInsert  : 'uitab-insert',
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
        fieldWriterRegistry: '#writer_registry',

        fieldsArity       : ['input', Cls.arity].join('.'),
        fieldsPredSymbol  : ['input', Cls.predSymbol].join('.'),
        fieldsPremise     : ['input', Cls.premise].join('.'),
        fieldsSentence    : ['input', Cls.sentence].join('.'),

        headerDebugs      : '#pt_debugs_heading',
        wrapDebugs        : '#pt_debugs_wrapper',
        uitabStatsLink    : '#uitab_stats_link',

        inputPredicate    : '.' + Cls.input + '.' + Cls.predicate,
        inputPremise      : '.' + Cls.input + '.' + Cls.premise,
        inputSentence     : '.' + Cls.input + '.' + Cls.sentence,
        linksButton       : ['a', Cls.button].join('.'),

        debugs            : '.' + Cls.debug,
        predicates        : '.' + Cls.predicates,
        premises          : '.' + Cls.premises,
        tableaux          : '.' + Cls.tableau,

        resultAdmon       : '.proof-result-admon',
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
    const CheckSelsHtmlOnly = {
        show_controls: true,
        color_open: true,
        build_models: true,
    }
    const OptClasses = {
        build_models  : Cls.withModels,
        show_controls : Cls.withControls,
        color_open    : Cls.colorOpen,
    }

    const API_PARSE_URI = '/api/parse'
    const TTIP_OPTS = {show: {delay: 1000}}

    $(document).ready(function() {
        const {AppData} = window
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

        delete window.AppData
        if (IS_DEBUG) {
            window.AppDebug = {
                AppData,
                PageData,
                ParseCache,
            }
        }

        let CurrentInputNotation = $(Sel.fieldInputNotn, $AppForm).val()
        let LastActiveTab = null

        /**
         * Main initialization routine.
         * @return {void}
         */
        function init() {
            // Load event listeners.
            initHandlers()
            // Init UI plugins and config.
            initPlugins()
            setTimeout(() => {
                refreshNotation()
                refreshLogic()
                if (IS_PROOF) {
                    const $tabins = $('<div/>').addClass(Cls.uitabInsert).html(
                        $(Sel.resultAdmon, $AppBody).get(0).outerHTML
                    )
                    $tabins.insertBefore($(Sel.uitabStatsLink, $AppBody).parent())
                    refreshStatuses()
                }
            })
        }

        function initHandlers() {
            // Input form events.
            $AppForm
                .on('submit', handleFormSubmit)
                .on('change selectmenuchange', handleFormChange)
                .on('click', handleFormClick)
                .on('keyup', Sel.fieldsSentence, handleFormSentenceKeyup)
            // Tabs header click
            $(Sel.appUiTabs, $AppBody)
                .on('click', 'ul.ui-tabs-nav', handleTabsHeaderClick)
            if (IS_DEBUG) {
                // Debug click show/hide.
                $(Sel.wrapDebugs, $AppBody)
                    .on('click', [Sel.debugs, Sel.headerDebugs].join(), handleDebugsClick)
            }
        }

        function initPlugins() {
            // UI Selectmenu
            $('select', $AppForm).selectmenu({
                classes: {
                    'ui-selectmenu-menu': Cls.app
                }
            })
            // UI Tabs
            $(Sel.appUiTabs, $AppBody).tabs({
                collapsible: IS_PROOF,
                active: PageData.selected_tab === false
                    ? false
                    : TabIndexes[PageData.selected_tab] || 0
            })
            // UI Button
            $('input:submit', $AppForm).button()
            $(Sel.linksButton, $AppBody).button()
            $('.' + Cls.buttonGroup, $AppBody).controlgroup({button: 'a'})
            // UI Tooltip - form help
            $('.' + Cls.tooltip, $AppBody).tooltip(TTIP_OPTS)
            // UI Tooltip - ui controls help
            $('.' + Cls.uiControls + ' a[title]', $AppBody).each(function() {
                const $me = $(this)
                const shortkey = $me.attr(Atr.dataShortKey)
                const $wrap = $('<span/>')
                    .addClass([Cls.tooltip, Cls.controls])
                    .append($('<span/>').text($me.attr('title')))
                if (shortkey) {
                    $wrap
                        .append($('<hr/>'))
                        .append($('<span/>').text('Shortcut key: '))
                        .append($('<code/>').addClass(Cls.shortkey).text(shortkey))
                }
                const content = $wrap.get(0).outerHTML
                $me.tooltip({content, show: {delay: 2000}})
            })
            // Init Tableau Plugin
            if (IS_PROOF) {
                $(Sel.tableaux, $AppBody).tableau({
                    // autoWidth: true,
                    // dragScroll: true,
                    scrollContainer: $(document)
                })
            }
        }

        /**
         * Form submit handler.
         *
         * @return {void}
         */
        function handleFormSubmit(e) {
            $('input:submit', $AppForm).prop({disabled: true})
            const data = getApiData()
            const json = JSON.stringify(data)
            $(Sel.fieldApiJson, $AppForm).val(json)
        }

        function handleFormChange(e) {
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
        }

        function handleFormClick(e) {
            const $target = $(e.target)
            if ($target.hasClass(Cls.premiseAdd)) {
                // Add premise.
                addPremise()
            } else if ($target.hasClass(Cls.predAdd)) {
                // Add predicate.
                addPredicate(...getNextPredCoords(), 1).find(':input').focus() 
            } else if ($target.hasClass(Cls.premiseDel)) {
                // Delete premise.
                removePremise($target.closest(Sel.inputPremise))
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
        }

        function handleFormSentenceKeyup(e) {
            const {target} = e
            const {selectionStart, selectionEnd, value} = target
            if (selectionStart !== selectionEnd) {
                return
            }
            const newValue = sentenceDisplayValue(value)
            if (value === newValue) {
                return
            }
            target.value = newValue
            target.setSelectionRange(selectionStart, selectionEnd)
        }

        function handleTabsHeaderClick(e) {
            // Collapse tabs when you click the header bar.
            if (!IS_PROOF) {
                return
            }
            const $target = $(e.target)
            if ($target.is('a') || $target.hasClass(Cls.uitabInsert)) {
                return
            }
            const $tabs = $(Sel.appUiTabs, $AppBody)
            const active = $tabs.tabs('option', 'active')
            if (Number.isInteger(active)) {
                LastActiveTab = active
                $tabs.tabs('option', 'active', false)
            } else if (Number.isInteger(LastActiveTab)) {
                $tabs.tabs('option', 'active', LastActiveTab)
            }
        }

        function handleDebugsClick(e) {
            const $target = $(e.target)
            // Main Debug Header - toggle all and return.
            if ($target.is(Sel.headerDebugs)) {
                $target.next('.' + Cls.debugs).toggle()
                return
            }
            // Single debug content - toggle and lazy-init jsonViewer.
            let $content
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
        function removePremise($prem) {
            $prem = $($prem)
            $prem.nextAll(Sel.inputPremise).each(function() {
                // renumber later ones.
                const $me = $(this)
                const num = +$me.attr(Atr.dataPremNum) - 1
                $me.attr(Atr.dataPremNum, num)
                $('.' + Cls.premiseMark, $me).text('P' + num)
            })
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
            const notation = CurrentInputNotation
            arity = arity || ''
            let symbol_html = ''
            $.each(AppData.nups, (notn, symbols) => {
                const classes = [
                    Cls.predSymbol,
                    Cls.lexicon,
                    [Cls.notation, esc(notn)].join('-')
                ]
                if (notn !== notation) {
                    classes.push(Cls.hidden)
                }
                symbol_html += '<span class="' + classes.join(' ') + '">'
                symbol_html += $('<div/>').text(symbols[index]).html()
                if (subscript > 0) {
                    symbol_html += '<sub>' + esc(subscript) + '</sub>'
                }
                symbol_html += '</span>'
            })
            const vars = {index, subscript, arity, symbol_html}
            return $(render(Templates.predicate, vars)).appendTo(
                $(Sel.predicates, $AppForm)
            )
        }

        /**
         * Get the next available index, subscript.
         * @return {array}
         */
        function getNextPredCoords() {
            const $symbols = $(Sel.fieldsPredSymbol, $AppForm)
            let index = 0
            let subscript = 0
            if ($symbols.length > 0) {
                const last = $symbols.last().val().split('.')
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
            $(Sel.inputPremise, $AppForm).each(function() { removePremise(this) })
            $(Sel.fieldConclusion, $AppForm).val('')
            for (const key in ParseCache) {
                delete ParseCache[key]
            }
        }

        /**
         * Logic select change handler. Show appropriate logic information.
         * @return {void}
         */
        function refreshLogic() {
            const logicName = $(Sel.fieldLogic, $AppForm).val()
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

            CurrentInputNotation = $(Sel.fieldInputNotn, $AppForm).val()
    
            const notation = CurrentInputNotation
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
            if ($(Sel.fieldArgExample, $AppForm).val()) {
                refreshArgExample()
                return
            }

            // Otherwise get translations from cached succesful api-parse responses.
            $(Sel.fieldsSentence, $AppForm).each(function() {
                const value = sentenceInputValue($(this).val())
                const cache = ParseCache[value]
                if (!cache || !cache[notation]) {
                    return
                }
                $(this).val(sentenceDisplayValue(cache[notation].default))
            })
        }

        /**
         * Change handler for exampleArg select. If not argument selected,
         * does nothing.
         * @return {void}
         */
        function refreshArgExample() {
            const argName = $(Sel.fieldArgExample, $AppForm).val()
            if (!argName) {
                return
            }
            clearPredicates()
            clearArgument()
            const notation = CurrentInputNotation
            const argBase = AppData.example_args[argName]
            if (!argBase) {
                console.log('not found', {argBase})
                return
            }
            const arg = argBase[notation]
            // Set translated display values.
            $.each(arg.premises, (i, value) => addPremise(  (value)))
            $(Sel.fieldConclusion, $AppForm).val(sentenceDisplayValue(arg.conclusion))
            $.each(argBase['@Predicates'], (i, pred) => {
                if (!Array.isArray(pred)) {
                    pred = [pred.index, pred.subscript, pred.arity]
                }
                addPredicate(...pred)
            })
        }

        /**
         * Make AJAX requests to parse the premises & conclusion.
         *
         * @param {bool} isForce Force refresh.
         * @return {void}
         */
        function refreshStatuses(isForce) {
            let predicates // lazy fetch
            const notation = CurrentInputNotation
            $(Sel.fieldsSentence, $AppForm).each(function() {
                const $me = $(this)
                const $status = $me
                    .closest(Sel.inputSentence)
                    .find('.' + Cls.status)
                const input = sentenceInputValue($me.val())
                if (!input) {
                    // Clear status.
                    $status
                        .removeClass([Cls.good, Cls.bad])
                        .attr({title: '', [Atr.dataHash]: ''})
                    return
                }
                // Set translated display value.
                $me.val(sentenceDisplayValue(input))
                // Check for change since last request against stored value.
                const hash = [input, notation].join('.')
                const stored = $status.attr(Atr.dataHash)
                if (!isForce && stored === hash) {
                    return
                }
                $status.attr(Atr.dataHash, hash)
                if (!predicates) {
                    predicates = getPredicatesData()
                }
                const payload = {input, notation, predicates}
                // Send api-parse request.
                $.ajax({
                    url         : API_PARSE_URI,
                    method      : 'POST',
                    contentType : 'application/json',
                    dataType    : 'json',
                    data        : JSON.stringify(payload),
                    success: res => {
                        $status
                            .removeClass(Cls.bad)
                            .addClass(Cls.good)
                            .attr({title: res.result.type})
                            .tooltip()
                        ParseCache[input] = res.result.rendered
                    },
                    error: (...args) => {
                        $status
                            .removeClass(Cls.good)
                            .addClass(Cls.bad)
                            .attr({title: _makeAjaxParseErrorMessage(...args)})
                            .tooltip()
                    }
                })
            })
        }

        function sentenceDisplayValue(str) {
            return translate(str, AppData.display_trans[CurrentInputNotation])
        }

        function sentenceInputValue(str) {
            return translate(str, AppData.parse_trans[CurrentInputNotation])
        }

        /**
         * Read the form inputs into an object suitable for posting to
         * the prove api.
         *
         * @return {object}
         */
        function getApiData() {
            const outputFormat = $(Sel.fieldOutputFmt, $AppForm).val()
            const isHtml = outputFormat === 'html'
            const data = {
                logic    : $(Sel.fieldLogic, $AppForm).val(),
                argument : getArgumentData(),
                output: {
                    format   : outputFormat,
                    notation : $(Sel.fieldOutputNotn, $AppForm).val(),
                    charset  : $(Sel.fieldOutputCharset, $AppForm).val(),
                    options  : {
                        classes : [],
                    }
                },
                // debug/advanced options.
                rank_optimizations  : true,
                group_optimizations : true,
                writer_registry     : $(Sel.fieldWriterRegistry, $AppForm).val(),
            }
            for (const key in CheckSels) {
                if (!isHtml && CheckSelsHtmlOnly[key]) {
                    continue
                }
                const $check = $(CheckSels[key], $AppForm)
                if ($check.length) {
                    data[key] = $check.is(':checked')
                }
            }
            // TabWriter classes option.
            if (isHtml) {
                const clsarr = data.output.options.classes
                for (const key in OptClasses) {
                    if (data[key]) {
                        clsarr.push(OptClasses[key])
                    }
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
                delete data.max_steps
            }
            if (!data.writer_registry) {
                delete data.writer_registry
            }
            if (!data.output.charset) {
                delete data.output.charset
            }
            if (!data.output.options.classes.length) {
                delete data.output.options.classes
            }
            if (!Object.keys(data.output.options).length) {
                delete data.output.options
            }
            if (!data.argument.predicates.length) {
                delete data.argument.predicates
            }
            if (!data.argument.premises.length) {
                delete data.argument.premises
            }
            return data
        }

        /**
         * Returns an object with the conclusion and premises
         * inputs, Empty premises are skipped. No other validation
         * on the sentences. Includes predicates data from `getPredicatesData()`
         * and the selected notation.
         * 
         * @return {object}
         */
        function getArgumentData() {
            const premises = []
            $(Sel.fieldsPremise, $AppForm).each(function() {
                const val = $(this).val()
                if (val) {
                    premises.push(sentenceInputValue(val))
                }
            })
            return {
                notation   : CurrentInputNotation,
                conclusion : sentenceInputValue($(Sel.fieldConclusion, $AppForm).val()),
                premises   : premises,
                predicates : getPredicatesData(),
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
        function getPredicatesData() {
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
                let arityVal
                if (isNaN(arityNumVal)) {
                    arityVal = arity
                } else {
                    arityVal = arityNumVal
                }
                const spec = $(Sel.fieldsPredSymbol, $row).val().split('.')
                preds.push({
                    index     : +spec[0],
                    subscript : +spec[1],
                    arity     : arityVal,
                })
            })
            return preds
        }
        init()
    })

    /**
     * Interpolate variable strings like {varname}.
     *
     * @param {string} str The template string.
     * @param {object} vars The variables object.
     * @return {string} The rendered string.
     */
    function render(str, vars) {
        if (!str || !vars) {
            return str
        }
        $.each(vars, (name, val) => str = str.replaceAll(`{${name}}`, val))
        return str
    }

    /**
     * Make simple string replacements.
     *
     * @param {string} str The input string.
     * @param {object} vars The translations object.
     * @return {string} The translated string.
     */
    function translate(str, translations) {
        if (!str || !translations) {
            return str
        }
        $.each(translations, (srch, repl) => str = str.replaceAll(srch, repl))
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

    function _makeAjaxParseErrorMessage(xhr, textStatus, errorThrown) {
        if (xhr.status !== 400) {
            return [textStatus, errorThrown].join(': ')
        }
        const res = xhr.responseJSON
        if (!res.errors) {
            return [res.error, res.message].join(': ')
        }
        if (res.errors.Sentence) {
            return res.errors.Sentence
        }
        const errKey = Object.keys(res.errors)[0]
        return [errKey, res.errors[errKey]].join(': ')
    }

})(window.jQuery);