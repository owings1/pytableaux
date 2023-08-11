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
 * pytableaux - Tableau UI jQuery Plugin
 */
;(function() {

    if (typeof(jQuery) !== 'function') {
        console.error(new Error('jQuery not loaded. Cannot load tableau plugin.'))
        return
    }

    const PLUGIN_NAME = window.PYTABLEAUX_PLUGIN_NAME || 'tableau'
    const $ = jQuery
    const $E = $()
    const debug = console.debug

    // animation speed constants, in milliseconds.
    const Anim = {
        Fast : 150,
        Med  : 250,
        Slow : 500,
    }

    // relationship string constants
    const Rel = {
        Self       : 'self',
        Ancestor   : 'ancestor',
        Descendant : 'descendant',
        Outside    : 'outside',
    }

    /**
     * Class names. For tableau writer classes, see writers.py
     */
    const Cls = {
        // page components
        UiControls      : 'tableau-controls',
        ModelsArea      : 'tableau-models',
        // tableau classes
        Root            : 'root',
        Structure       : 'structure',
        HasOpen         : 'has_open',
        HasClosed       : 'has_closed',
        Child           : 'child-wrapper',
        Leaf            : 'leaf',
        HL              : 'horizontal-line',
        VL              : 'vertical-line',
        NodeSegment     : 'node-segment',
        NodeProps       : 'node-props',
        PropSentence    : 'sentence',
        PropAccess      : 'access',
        Node            : 'node',
        Ticked          : 'ticked',
        Closed          : 'closed',
        // controls classes
        StepStart       : 'step-start',
        StepPrev        : 'step-prev',
        StepNext        : 'step-next',
        StepEnd         : 'step-end',
        StepInput       : 'step-input',
        StepRuleDatum   : 'step-rule-datum',
        StepRuleName    : 'step-rule-name',
        StepRuleTarget  : 'step-rule-target',
        FontPlus        : 'font-plus',
        FontMinus       : 'font-minus',
        FontReset       : 'font-reset',
        WidthPlus       : 'width-plus',
        WidthPlusPlus   : 'width-plus-plus',
        WidthMinus      : 'width-minus',
        WidthMinusMinus : 'width-minus-minus',
        WidthReset      : 'width-reset',
        WidthStretch    : 'width-stretch',
        ScrollCenter    : 'scroll-center',
        BranchFilter    : 'branch-filter',
        ColorOpen       : 'color-open',
        WidthAuto       : 'auto-width',
        ScrollAuto      : 'auto-scroll',
        DragScroll      : 'drag-scroll',
        // stateful classes
        Hidden          : 'hidden',
        Zoomed          : 'zoomed',
        Inspected       : 'inspected',
        Collapsed       : 'collapsed',
        Uncollapsed     : 'uncollapsed',
        BranchFiltered  : 'branch-filtered',
        StepFiltered    : 'step-filtered',
        ZoomFiltered    : 'zoom-filtered',
        Highlight       : 'highlight',
        HighlightTicked : 'highlight-ticked',
        HighlightClosed : 'highlight-closed',
        Model           : 'model',
        MarkActive      : 'active',
        MarkDisabled    : 'disabled',
        MarkFiltered    : 'filtered',
    }

    // The id of node elements.
    const NodeIdPrefix = 'node_'

    // Class names preceded with a '.' for selecting
    const Dcls = {}
    for (const c in Cls) {
        Dcls[c] = '.' + Cls[c]
    }

    // Attributes
    const Attrib = {
        // Global attributes
        TableauId      : 'data-tableau-id',
        // Tableau attributes
        NumSteps       : 'data-num-steps',
        Step           : 'data-step',
        CurWidthPct    : 'data-current-width-pct',
        Depth          : 'data-depth',
        Width          : 'data-width',
        Left           : 'data-left',
        Right          : 'data-right',
        CloseStep      : 'data-closed-step',
        BranchId       : 'data-branch-id',
        ModelId        : 'data-model-id',
        NodeId         : 'data-node-id',
        TickStep       : 'data-tickstep',
        // Controls attributes (rules)
        NodeIds        : 'data-node-ids',
        BranchNodeId   : 'data-branch-node-id',
        // Stateful attributes
        FilteredWidth  : 'data-filtered-width',
    }

    // Selectors
    const Sel = {
        SteppedChilds: [
            '>' + Dcls.NodeSegment + '>' + Dcls.Node,
            '>' + Dcls.VL,
        ].join(','),
        Filtered: [
            Dcls.StepFiltered,
            Dcls.ZoomFiltered,
            Dcls.BranchFiltered,
        ].join(','),
        CanBranchFilter: [
            Dcls.HasOpen,
            Dcls.HasClosed,
        ].join(''),
        Unfiltered: '...',
    }
    Sel.Unfiltered = ':not(' + Sel.Filtered + ')'

    // Relevant action keys
    const ActionKeyMap = {
        StepNext: '>',
        StepPrev: '<',
        StepStart: 'B',
        StepEnd: 'E',
        FontPlus: '+',
        FontMinus: '-',
        FontReset: '=',
        WidthPlus: ']',
        WidthMinus: '[',
        WidthPlusPlus: '}',
        WidthMinusMinus: '{',
        WidthReset: '|',
        WidthStretch: '@',
        WidthAuto: 'W',
        ScrollCenter: '$',
        ScrollAuto: 'S',
        FilterOpen: 'O',
        FilterClosed: 'C',
        FilterAll: 'A',
        HighlightRule: 'r',
        HighlightRuleStay: 'R',
        HighlightTarget: 't',
        HighlightTargetStay: 'T',
        ZoomCancel: 'Z',
    }

    const AdjustWhat = {
        Font  : 'font',
        Width : 'width',
        Step  : 'step',
    }

    const AdjustWhen = {
        Before : 'before',
        After  : 'after',
    }

    const HowMuch = {
        Start       : 'start',
        End         : 'end',
        Beginning   : 'beginning',
        Reset       : 'reset',
        Stretch     : 'stretch',
        StepInc     :   1,
        FontInc     :   1,
        WidthMedium :  10,
        WidthLarge  :  25,
    }

    const FilterType = {
        Open   : 'open',
        Closed : 'closed',
        All    : 'all',
    }

    const Behave = {
        Inspect : 'inspect',
        Zoom    : 'zoom',
    }

    // default option sets
    const FuncDefaults = {
        Filter : {
            $hides     : $E,
            $shows     : $E,
            className  : null,
            adjust     : AdjustWhen.After,
        },
        Highlight : {
            stay       : true,
            off        : false,
            ruleStep   : null,
            ruleTarget : null,
        },
        ScrollTo : {
            animate: false,
        },
    }

    // cursor state
    const CurState = {
        down : false,
        xpos : 0,
        ypos : 0,
    }

    class Api {

        static getInstance(ref, setActive = false) {
            let api
            if (this.instances[ref]) {
                api = this.instances[ref]
            } else {
                if (typeof ref.attr !== 'function') {
                    ref = $(ref)
                }
                if (ref.length > 1) {
                    $.error('Cannot get instance for object with length ' + ref.length)
                }
                api = this.instances[ref.attr('id')]
            }
            if (setActive) {
                this.activeInstance = api
            }
            return api
        }

        constructor($tableau) {
            if ($tableau.length !== 1) {
                throw new Error('Cannot create Api for length ' + $tableau.length)
            }
            const id = $tableau.attr('id')
            const {instances} = this.constructor
            if (instances[id]) {
                throw new Error('Instance already created for id ' + id)
            }
            if (id == null || !id.length) {
                throw new Error('Cannot create Api for id "' + String(id) + '"')
            }
            Object.defineProperties(this, {
                id       : {value: id},
                $tableau : {value: $tableau},
            })
            instances[id] = this
            if (!this.constructor.activeInstance) {
                this.constructor.activeInstance = this
            }
        }

        init(opts) {
            this.destroy()
            this.constructor.instances[this.id] = this
            opts = this.opts = $.extend(true, Plugin.defaults, this.opts, opts)
            for (const opt of ['controls', 'models', 'scrollContainer']) {
                initSmartOpt.call(this, opt, opts[opt])
            }
            this.$tableau
                .on('click', onTableauClick)
                .on('mousedown', onMouseDown)
                .on('mouseup', onMouseUp)
                .on('mousemove', onMouseMove)
            this.$controls
                .on('click', onControlsClick)
                .on('change', onControlsChange)
            this.$models.on('click', onModelsClick)
            if (opts.autoWidth == null) {
                if ($(Dcls.WidthAuto + Dcls.MarkActive, this.$controls).length) {
                    setAutoWidth.call(this, true)
                }
            } else {
                setAutoWidth.call(this, opts.autoWidth)
            }
            if (opts.autoScroll == null) {
                if ($(Dcls.ScrollAuto + Dcls.MarkActive, this.$controls).length) {
                    setAutoScroll.call(this, true)
                }
            } else {
                setAutoScroll.call(this, opts.autoScroll)
            }
            if (opts.dragScroll) {
                this.$tableau.addClass(Cls.DragScroll)
            }
            if (!this._isAutoWidth && opts.stretch) {
                stretchWidth.call(this)
            }
            if (!this._isAutoScroll && opts.center) {
                scrollToCenter.call(this)
            }
            if (opts.actionKeys) {
                this.actionKeysHash = Object.fromEntries(
                    Object.entries(ActionKeyMap).map(
                        ([action, key]) => [key, action]
                    )
                )
                ensureKeypressHandlers()
            } else {
                this.actionKeysHash = {}
            }
            initCaches.call(this)
            return this
        }
    
        destroy() {
            const {instances} = this.constructor
            if (this.$controls) {
                this.$controls
                    .off('click', onControlsClick)
                    .off('change', onControlsChange)
                this.$controls.each(function() {
                    delete instances[$(this).attr('id')]
                })
            }
            if (this.$models) {
                this.$models.off('click', onModelsClick)
                this.$models.each(function() {
                    delete instances[$(this).attr('id')]
                })
            }
            this.$tableau
                .off('click', onTableauClick)
                .off('mousedown', onMouseDown)
                .off('mouseup', onMouseUp)
                .off('mousemove', onMouseMove)
            delete instances[this.id]
            if (this.constructor.activeInstance === this) {
                this.constructor.activeInstance = null
            }
            if (!Object.keys(instances).length) {
                unloadKeypressHandlers()
            }
            return this
        }
    
        width(value) {
            if (typeof value === 'undefined') {
                return this.$tableau.width()
            }
            adjust.call(this, AdjustWhat.Width, value)
            return this
        }
    
        center() {
            scrollToCenter.call(this)
            return this
        }
    
        autoWidth(value) {
            if (typeof value === 'undefined') {
                return Boolean(this._isAutoWidth)
            }
            setAutoWidth.call(this, value)
            return this
        }
    
        autoScroll(value) {
            if (typeof value === 'undefined') {
                return Boolean(this._isAutoScroll)
            }
            setAutoScroll.call(this, value)
            return this
        }
    }
    Api.instances = Object.create(null)
    Api.activeInstance = null

    function Plugin(opt) {
        if (opt === 'instance') {
            return Api.getInstance(this)
        }
        return this.each(function() {
            const $tableau = $(this)
            let api = Api.getInstance($tableau)
            if (api) {
                if (typeof(api[opt]) === 'function') {
                    const args = Array.prototype.slice.call(arguments, 1)
                    api[opt].apply(api, args)
                }
            } else {
                api = new Api($tableau)
                api.init(opt)
            }
        })
    }
    $.fn[PLUGIN_NAME] = Plugin

    /**
     * Plugin option defaults.
     */
    Plugin.defaults = Object.assign(Object.create(null), {
        controls: function() {
            const $controls = $(Dcls.UiControls)
            if ($controls.length > 1) {
                const $specific = $controls.filter(
                    getAttrSelector(Attrib.TableauId, this.id)
                )
                if ($specific.length) {
                    return $specific
                }
            }
            return $controls
        },
        models: function() {
            const $models = $(Dcls.ModelsArea)
            if ($models.length > 1) {
                const $specific = $models.filter(
                    getAttrSelector(Attrib.TableauId, this.id)
                )
                if ($specific.length) {
                    return $specific
                }
            }
            return $models
        },
        scrollContainer: function($tableau) {
            return $tableau.parent()
        },
        actionKeys: true,
        autoWidth: null,
        autoScroll: null,
        stretch: true,
        center: true,
        dragScroll: true,
    })

    function initSmartOpt(opt, value) {
        const prop = '$' + opt
        if (typeof value === 'function') {
            this[prop] = $(value.call(this, this.$tableau))
        } else if (value === true) {
            this[prop] = Plugin.defaults[opt].call(this, this.$tableau)
        } else {
            if (typeof value === 'string') {
                value = value.replace('{id}', this.id)
            }
            this[prop] = $(value)
        }
        const that = this
        this[prop].each(function(i) {
            let id = $(this).attr('id')
            if (!id) {
                id = [opt, that.id, String(i)].join('_')
                while ($('#' + id).length) {
                    id += [id, ++i].join('_')
                }
                $(this).attr('id', id)
            }
            Api.instances[id] = that
        })
    }
    /**
     * Set autoWidth api option, and run auto-width if enabled. Mark/unmark the
     * controls element with active class.
     * 
     * @private
     * @param {boolean} value The value to set.
     * @return {void}
     */
    function setAutoWidth(value) {
        this._isAutoWidth = Boolean(value)
        $(Dcls.WidthAuto, this.$controls).toggleClass(Cls.MarkActive, this._isAutoWidth)
        if (this._isAutoWidth) {
            stretchWidth.call(this)
        }
    }

    /**
     * Set autoScroll api option, and run auto-scrool if enabled. Mark/unmark the
     * controls element with active class.
     * 
     * @private
     * @param {boolean} value The value to set.
     * @return {void}
     */
    function setAutoScroll(value) {
        this._isAutoScroll = Boolean(value)
        $(Dcls.ScrollAuto, this.$controls).toggleClass(Cls.MarkActive, this._isAutoScroll)
        if (this._isAutoScroll) {
            scrollToCenter.call(this)
        }
    }

    function onTableauClick(e) {
        handleTableauClick.call(Api.getInstance(this, true), $(e.target))
    }

    function onControlsClick(e) {
        handleControlsClick.call(Api.getInstance(this, true), $(e.target))
    }

    function onControlsChange(e) {
        handleControlsChange.call(Api.getInstance(this, true), $(e.target))
    }

    function onModelsClick(e) {
        handleModelsClick.call(Api.getInstance(this, true), $(e.target))
    }

    function onMouseDown(m) {
        CurState.ypos = m.pageY
        CurState.xpos = m.pageX
        CurState.down = true
    }

    function onMouseUp() {
        CurState.down = false
    }

    function onMouseMove(m){
        if (CurState.down) {
            const api = Api.getInstance(this)
            if (api && api.opts.dragScroll) {
                window.scrollBy(CurState.xpos - m.pageX, CurState.ypos - m.pageY)
            }
        }
    }

    // Keypress handlers
    let IsKeyHandlersLoaded = false

    // mod key state
    const ModKey = {
        shift   : false,
        ctrl    : false,
        alt     : false,
        ctrlalt : false,
    }

    function ensureKeypressHandlers() {
        if (IsKeyHandlersLoaded) {
            return
        }
        $(document).on('keyup keydown', onKeyupKeydown)
        $(document).on('keypress', onKeypress)
        IsKeyHandlersLoaded = true
    }

    function unloadKeypressHandlers() {
        if (!IsKeyHandlersLoaded) {
            return
        }
        $(document).off('keyup keydown', onKeyupKeydown)
        $(document).off('keypress', onKeypress)
        IsKeyHandlersLoaded = false
    }

    function onKeyupKeydown(e) {
        ModKey.shift   = e.shiftKey
        ModKey.ctrl    = e.metaKey || e.ctrlKey
        ModKey.alt     = e.altKey
        ModKey.ctrlalt = ModKey.ctrl || ModKey.alt
    }

    function onKeypress(e) {
        const api = Api.activeInstance
        if (!api) {
            return
        }
        const key = String.fromCharCode(e.which)
        const action = api.actionKeysHash[key]
        if (!action) {
            return
        }
        const $target = $(e.target)
        const shouldProcess = !$target.is(':input')
        if (!shouldProcess) {
            return
        }
        NamedActions[action].call(api)
    }

    function initCaches() {
        if (this.isCacheInit) {
            return
        }
        const $tableau = this.$tableau
        const stmap = Object.create(null)
        const cache = Object.create(null)
        const sts = $(Dcls.Structure, $tableau).toArray().map(function(s) {
            const $s = $(s)
            const st = {
                id : $s.attr('id'),
                $s : $s,
                s  : $s.get(0),
                isRoot    : $s.hasClass(Cls.Root),
                left      : +$s.attr(Attrib.Left),
                right     : +$s.attr(Attrib.Right),
                step      : +$s.attr(Attrib.Step),
                tickStep  : +$s.attr(Attrib.TickStep),
                depth     : +$s.attr(Attrib.Depth),
                hasOpen   : $s.hasClass(Cls.HasOpen),
                hasClosed : $s.hasClass(Cls.HasClosed),
                hasTicked : $(Dcls.NodeProps, $s).hasClass(Cls.Ticked),
                closed    : $s.hasClass(Cls.Closed),
                leaf      : $s.hasClass(Cls.Leaf),
            }
            stmap[st.id] = st
            return st
        })
        Object.defineProperties(this, {
            isCacheInit: {value: true},
            numSteps   : {value: +$tableau.attr(Attrib.NumSteps)},
            sts        : {value: sts},
            stmap      : {value: stmap},
            cache      : {value: cache},
        })
    }

    function getStructObj(ref) {
        if (ref.$s) {
            return ref
        }
        if (typeof ref.attr !== 'function') {
            ref = $(ref)
        }
        return this.stmap[ref.attr('id')]
    }

    /**
     * Show only the lineage of the given structure.
     *
     * @private
     * @param {object} st The st cache object.
     * @param {function} next The next function.
     * @return {void}
     */
    function zoom(st, next) {
        st = getStructObj.call(this, st)
        const $s = st.$s
        // if we are currently zoomed to this structure, there is nothing to do
        if ($s.hasClass(Cls.Zoomed)) {
            return
        }
        const $tableau = this.$tableau
        // get the previously zoomed structure
        const $prev = $(Dcls.Zoomed, $tableau)
        const hides = []
        const shows = []
        $.each(this.sts, function(i, other) {
            if (getRelation(other, st) === Rel.Outside) {
                hides.push(other.s)
            } else {
                shows.push(other.s)
            }
        })
        // unmark the previous structure as zoomed
        $prev.removeClass(Cls.Zoomed)
        // mark the current structure as zoomed
        $s.addClass(Cls.Zoomed)
        const fopts = {
            $hides: $(hides),
            $shows: $(shows),
            className: Cls.ZoomFiltered,
        }
        doFilter.call(this, fopts, next)
    }

    /**
     * Set the branch being inspected.
     *
     * @private
     * @param {object} $structure The singleton jQuery .structure element.
     * @return {void}
     */
    function setInspectedBranch($structure) {
        // if we are currently inspecting this structure, there is nothing to do
        if ($structure.hasClass(Cls.Inspected)) {
            return
        }
        $(Dcls.Inspected, this.$tableau).removeClass(Cls.Inspected)
        $structure.addClass(Cls.Inspected)
        const $models = this.$models
        if ($models.length) {
            const $modelElements = $(Dcls.Model, $models)
            const modelId = $structure.attr(Attrib.ModelId)
            $modelElements.hide()
            if (modelId) {
                $models.addClass(Cls.Inspected)
                $modelElements
                    .filter(getAttrSelector(Attrib.ModelId, modelId))
                    .show(Anim.Fast)
            } else {
                $models.removeClass(Cls.Inspected)
            }
        }
    }

    /**
     * Move the proof state to the given step.
     *
     * @private
     * @param {number} n The step number.
     * @param {function} next The next function.
     * @return {void}
     */
    function step(n, next) {
        const {$tableau, $controls, numSteps} = this
        const prevStep = +$tableau.attr(Attrib.Step)
        if (n < 0) {
            n = 0
        }
        if (n > numSteps) {
            n = numSteps
        }
        if (n === prevStep) {
            return
        }
        const shows = []
        const toHide = {}
        const showChilds = []
        const hideChilds = []
        const tickNodes = []
        const untickNodes = []
        const highlightDelay = Anim.Med
        $.each(this.sts, function(i, st) {
            const $s = st.$s
            const sStep = st.step
            const s = st.s
            const sPos = st
            if (sStep > n) {
                // only hide the highest structures
                trackHighests(toHide, sPos)
                return true
            }
            shows.push(s)
            // process nodes, vertical lines
            $(Sel.SteppedChilds, $s).each(function(ni, stepped) {
                const $stepped = $(stepped)
                const nStep = +$stepped.attr(Attrib.Step)
                if (nStep > n) {
                    hideChilds.push(stepped)
                    return true
                }
                showChilds.push(stepped)
                // ticking/unticking
                if (!$stepped.hasClass(Cls.Ticked)) {
                    return true
                }
                const tStep = +$stepped.attr(Attrib.TickStep)
                const hasTicked = $(Dcls.NodeProps, $stepped).hasClass(Cls.Ticked)
                if (tStep > n) {
                    if (hasTicked) {
                        untickNodes.push(stepped)
                    }
                } else {
                    if (!hasTicked) {
                        tickNodes.push(stepped)
                    }
                }
            })
        })
        // hide nodes, vertical lines
        $(hideChilds).hide()
        // untick nodes
        $(Dcls.NodeProps, untickNodes).removeClass(Cls.Ticked)
        // filter structures
        const hides = $.map(toHide, st => st.s)
        const fopts = {
            $hides: $(hides),
            $shows: $(shows),
            className: Cls.StepFiltered,
            adjust: n > prevStep
                ? AdjustWhen.Before
                : AdjustWhen.After,
        }
        doFilter.call(this, fopts, () => {
            // show nodes, vertical lines
            $(showChilds).show()
            if (this._isAutoWidth) {
                stretchWidth.call(this)
            }
            // scroll to node
            if (this._isAutoScroll) {
                const $node = $(Dcls.Node + getAttrSelector(Attrib.Step, n), $tableau).last()
                if ($node.length) {
                    scrollTo.call(this, $node.children(Dcls.NodeProps))
                }
            }
            // highlight the result
            setTimeout(() => {
                highlightStepResult.call(this, n)
                // delay the ticking of the nodes for animated effect
                setTimeout(() => {
                    $(Dcls.NodeProps, tickNodes).addClass(Cls.Ticked)
                    // unhighlight
                    setTimeout(() => {
                        highlightStepOff.call(this)
                        if (typeof next === 'function') {
                            next()
                        }
                    }, highlightDelay)
                }, highlightDelay)
            }, highlightDelay)
        })
        // set the current step attribute on the proof
        $tableau.attr(Attrib.Step, n)
        if ($controls.length) {
            // show the rule and target in the controls panel
            const attrSelector = getAttrSelector(Attrib.Step, n)
            $(Dcls.StepRuleDatum, $controls).hide().filter(attrSelector).show()
            // update the input box
            $(Dcls.StepInput, $controls).val(n)
            // update disabled properties on forward/backward buttons
            const $backward = $([Dcls.StepStart, Dcls.StepPrev].join(', '), $controls)
            const $forward = $([Dcls.StepEnd, Dcls.StepNext].join(', '), $controls)
            if (n === numSteps) {
                $forward.addClass(Cls.MarkDisabled)
            }
            if (n < numSteps) {
                $forward.removeClass(Cls.MarkDisabled)
            }
            if (n === 0) {
                $backward.addClass(Cls.MarkDisabled)
            } else if (n > 0) {
                $backward.removeClass(Cls.MarkDisabled)
            }
        }
    }

    /**
     * Filter branches of a tableau according to their status.
     *
     * @private
     * @param {string} type The branch status to show, either 'open', 'closed', or 'all'.
     * @param {function} next The next function.
     * @return {void}
     */
    function filterBranches(type, next) {
        const $tableau = this.$tableau
        const $controls = this.$controls
        // Track current state so we don't filter if not needed.
        const markClass = [Cls.MarkFiltered, type].join('-')
        if ($tableau.hasClass(markClass)) {
            if (typeof next === 'function') {
                next()
            }
            return
        }
        let $active
        if ($controls.length) {
            const $ctrl = $(Dcls.BranchFilter, $controls)
            $active = $ctrl.filter('.' + type)
            if ($active.length) {
                $ctrl.removeClass(Cls.MarkActive)
            }
        }
        if (!this.cache.filterBranches) {
            this.cache.filterBranches = {}
        }
        const cache = this.cache.filterBranches
        if (!cache[type]) {
            let rmClasses
            switch (type) {
                case FilterType.All:
                    rmClasses = [
                        [Cls.MarkFiltered, FilterType.Open].join('-'),
                        [Cls.MarkFiltered, FilterType.Closed].join('-'),
                    ]
                    break
                case FilterType.Open:
                    rmClasses = [
                        [Cls.MarkFiltered, FilterType.All].join('-'),
                        [Cls.MarkFiltered, FilterType.Closed].join('-'),
                    ]
                    break
                case FilterType.Closed:
                    rmClasses = [
                        [Cls.MarkFiltered, FilterType.All].join('-'),
                        [Cls.MarkFiltered, FilterType.Open].join('-'),
                    ]
                    break
            }
            const toHide = []
            const toShow = []
            $.each(this.sts, (i, st) => {
                let shown
                switch (type) {
                    case FilterType.All:
                        shown = true
                        break
                    case FilterType.Open:
                        shown = st.hasOpen
                        break
                    case FilterType.Closed:
                        shown = st.hasClosed
                        break
                    default:
                        break
                }
                if (shown) {
                    toShow.push(st.s)
                } else {
                    toHide.push(st.s)
                }
            })
            cache[type] = {
                $hides: $(toHide),
                $shows: $(toShow),
                removeClasses: rmClasses,
            }
        }
        const {$hides, $shows, removeClasses} = cache[type]
        const fopts = {
            $hides: $hides,
            $shows: $shows,
            className: Cls.BranchFiltered,
        }
        setTimeout(() => doFilter.call(this, fopts, next))
        $tableau.removeClass(removeClasses).addClass(markClass)
        if ($active && $active.length) {
            $active.addClass(Cls.MarkActive)
        }
    }

    /**
     * Perform a filter operation on structures for a proof. This will apply
     * the filter class to $shows, and remove it from $hides. If there are
     * no more filter classes on an element, it is shown. The widths of the
     * child wrappers are then adjusted.
     *
     * Required options keys:
     *
     *     - $hides     : The jQuery structure elements to filter.
     *     - $shows     : The jQuery structure elements to unfilter.
     *     - className  : The filter class name to apply.
     *
     * Optional keys:
     *
     *     - adjust     : Adjust horizontal lines (boolean, 'before', or 'after').
     *                    Default is 'after'.
     *
     * @private
     * @param {object} opts The options.
     * @param {function} next The next function.
     * @return {void}
     */
    function doFilter(opts, next) {
        opts = $.extend({}, FuncDefaults.Filter, opts)
        const $hides = opts.$hides
        const $shows = opts.$shows
        const className = opts.className
        // track the lowest structures to adjust widths
        const lowests = {}
        $hides.addClass(className).each(function() {
            trackLowests(lowests, getPos($(this)))
        })
        const shows = []
        $shows.removeClass(className).each(function() {
            const pos = getPos($(this))
            trackLowests(lowests, pos)
            // if there are no more filters on the element, it will be shown
            if (pos.$structure.is(Sel.Unfiltered)) {
                shows.push(this)
            }
        })
        // sort the elements to show from higher to lower
        shows.sort((a, b) => $(a).attr(Attrib.Depth) - $(b).attr(Attrib.Depth))
        // collect the dom elements of the lowest structures
        const leaves = $.map(lowests, pos => pos.$structure.get(0))
        // hide elements that have a filter
        $hides.hide()
        this._lastShows = $shows
        let finish
        // adjust the widths (or do this 'after' below)
        if (opts.adjust === AdjustWhen.Before) {
            finish = () => {
                adjustWidths.call(this, $(leaves), () => {
                    $(shows).show()
                    if (typeof next === 'function') {
                        next()
                    }
                })
            }
        } else if (opts.adjust) {
            finish = () => {
                $(shows).show()
                adjustWidths.call(this, $(leaves), next)
            }
        } else {
            finish = () => {
                $(shows).show()
                if (typeof next === 'function') {
                    next()
                }
            }
        }
        setTimeout(finish)
    }

    /**
     * Adjust the widths of the tableau structures, after filters have been
     * applied. This takes the leaves (or lowest affected structures), and
     * traverses upward, adjusting the width of the ancestors.
     *
     * The 'leaves' will not be adjusted, since their width is fixed. True
     * leaves can only have nodes, so their width is 1.
     *
     * @private
     * @param {object} $leaves The jQuery element with the leaves, or deepest
     *   affected structures.
     * @param {function} next The next function.
     * @return {void}
     */
    function adjustWidths($leaves, next) {
        // traverse upward through the ancestors
        $leaves.parents(Dcls.Structure + Sel.Unfiltered).each((pi, parent) => {
            const $parent = $(parent)
            // The horizontal line.
            const $hl = $parent.children(Dcls.HL)
            // All the child-wrapper elements.
            const $cws = $parent.children(Dcls.Child)
            // The child-wrapper elements of the structures that are 'visible'.
            const $cwsUnfiltered = $cws.has('> ' + Sel.Unfiltered)
            // The total number of children.
            const totalChildren = $cws.length
            // The number of 'visible' children.
            const unfilteredChildren = $cwsUnfiltered.length
            // The list of child widths.
            const childWidths = $cwsUnfiltered.map(function() {
                return +(
                    $(this).attr(Attrib.FilteredWidth) ||
                    $(this).children(Dcls.Structure).attr(Attrib.Width)
                )
            }).get()
            // The total width that the parent should consume.
            const width = sum(childWidths)
            // Modify the widths of the visible children.
            $cwsUnfiltered.each((ci, cw) => {
                const $cw = $(cw)
                // calculate the new percentage
                const newWidthPct = ((childWidths[ci] * 100) / width) + '%'
                // get the current percentage from the store attribute
                const curWidthPct = $cw.attr(Attrib.CurWidthPct) || Infinity
                // round for comparisons
                const cmpNew = Math.floor(parseFloat(newWidthPct) * 10000) / 10000
                const cmpCur = Math.floor(parseFloat(curWidthPct) * 10000) / 10000
                if (cmpNew !== cmpCur) {
                    // set the current percentage attribute
                    $cw.attr(Attrib.CurWidthPct, newWidthPct)
                        .css({width: newWidthPct})
                }
            })
            // Modify the horizontal line.
            const hlcss = {}
            if (unfilteredChildren < 2) {
                // If we have 1 or 0 visible children, then make the line span 33% and center it.
                hlcss.width = (100 / 3) + '%'
                // jQuery does not animate 'auto' margins, so we set it immmediately.
                $hl.css({marginLeft: 'auto'})
            } else {
                // If there there are 2 or more visible children, calculate
                // the line width and left margin. This is a repetition of 
                // the server-side calculations for the initial state.
                const first = childWidths[0] / 2
                const last = childWidths[childWidths.length - 1] / 2
                const betweens = sum(childWidths.slice(1, childWidths.length - 1))
                hlcss.marginLeft = ((first * 100 ) / width) + '%'
                hlcss.width = (((first + betweens + last) * 100) / width) + '%'
            }
            // If all children are visible, then restore the line style, otherwise make it dotted.
            $hl.toggleClass(Cls.Collapsed, totalChildren !== unfilteredChildren)
            // Show the horizontal line if there are visible children, otherwise hide it.
            $hl.css(hlcss).toggle(unfilteredChildren > 0)
            // If this parent has a parent, mark the filtered width attribute
            // for the next traversal.
            const $pcw = $parent.closest(Dcls.Child)
            if ($pcw.length) {
                if (width === +$parent.attr(Attrib.Width)) {
                    $pcw.removeAttr(Attrib.FilteredWidth)
                } else {
                    $pcw.attr(Attrib.FilteredWidth, width || 1)
                }
            }
        })
        if (typeof next === 'function') {
            setTimeout(next)
        }
    }

    /**
     * Highlight the result nodes/ticking/markers of the given step, or current step.
     * 
     * @private
     * @param step (optional) The step number. Default is current step.
     * @return {void}
     */
    function highlightStepResult(step) {
        const {$tableau} = this
        if (step == null) {
            step = +$tableau.attr(Attrib.Step)
        }
        const nodeAttrSel = getAttrSelector(Attrib.Step, step)
        const nodeSel = Dcls.Node + nodeAttrSel
        const closeSel = Dcls.Structure + getAttrSelector(Attrib.CloseStep, step)
        const tickSel = Dcls.Node + getAttrSelector(Attrib.TickStep, step)
        $(nodeSel, $tableau).addClass(Cls.Highlight)
        $(tickSel, $tableau).addClass(Cls.HighlightTicked)
        $(closeSel, $tableau).addClass(Cls.HighlightClosed)
    }

    /**
     * Highlight the target nodes of the given step, or current step.
     * 
     * @private
     * @param {integer} step (optional) The step number. Default is current step.
     * @return {void}
     */
    function highlightStepTarget(step) {
        const {$controls, $tableau} = this
        if (step == null) {
            step = +$tableau.attr(Attrib.Step)
        }
        const nodeAttrSel = getAttrSelector(Attrib.Step, step)
        const nodeIds = []
        const $ruleTarget = $(Dcls.StepRuleTarget + nodeAttrSel, $controls)
        const nodeId = $ruleTarget.attr(Attrib.NodeId)
        if (nodeId) {
            nodeIds.push(+nodeId)
        }
        const nodeIdStr = $ruleTarget.attr(Attrib.NodeIds)
        if (nodeIdStr) {
            const nodeIdsArr = nodeIdStr.split(',').filter(Boolean)
            for (let i = 0; i < nodeIdsArr.length; ++i) {
                nodeIds.push(+nodeIdsArr[i])
            }
        }
        let $nodes
        if (nodeIds.length) {
            const nodeSel = $.map(nodeIds, id => '#' + NodeIdPrefix + id).join(', ')
            $nodes = $(nodeSel, $tableau)
        } else {
            $nodes = $E
        }
        // TODO: branch / branches
        $nodes.addClass(Cls.Highlight)
    }

    /**
     * Unhighlight any rule step result/target nodes.
     * 
     * @private
     * @return {void}
     */
    function highlightStepOff() {
        const {$controls, $tableau} = this
        $(Dcls.Highlight, $tableau).removeClass(Cls.Highlight)
        $(Dcls.HighlightTicked, $tableau).removeClass(Cls.HighlightTicked)
        $(Dcls.HighlightClosed, $tableau).removeClass(Cls.HighlightClosed)
        $(Dcls.Highlight, $controls).removeClass(Cls.Highlight)
    }

    /**
     * Make various incremental UI adjustments.
     *
     * @private
     * @param {string} what What thing to adjust (font, width, step).
     * @param {string|number} howMuch How much to adjust it, or 'reset'.
     * @return {void}
     */
    function adjust(what, howMuch) {
        const $tableau = this.$tableau
        switch (what) {
            case AdjustWhat.Font:
                if (howMuch === HowMuch.Reset) {
                    $tableau.css({fontSize: 'inherit'})
                } else {
                    $tableau.css({
                        fontSize: (
                            parseInt($tableau.css('fontSize')) +
                            (parseFloat(howMuch) || 0)
                        )
                    })
                }
                break
            case AdjustWhat.Width:
                let p
                if (howMuch === HowMuch.Reset) {
                    p = 100
                } else if (howMuch === HowMuch.Stretch) {
                    stretchWidth.call(this)
                    break
                } else {
                    p = +$tableau.attr(Attrib.CurWidthPct) + (parseFloat(howMuch) || 0)
                }
                if (p < 0) {
                    p = 0
                }
                $tableau.attr(Attrib.CurWidthPct, p)
                $tableau.css({width: p + '%'})
                break
            case AdjustWhat.Step:
                const maxSteps = this.numSteps
                let n
                if (howMuch === HowMuch.Beginning || howMuch === HowMuch.Start) {
                    n = 0
                } else if (howMuch === HowMuch.Reset || howMuch === HowMuch.End) {
                    n = maxSteps
                } else {
                    n = +$tableau.attr(Attrib.Step) + (parseInt(howMuch) || 0)
                }
                if (n < 0) {
                    n = 0
                } else if (n > maxSteps) {
                    n = maxSteps
                }
                step.call(this, n)
                break
            default:
                break
        }
    }

    /**
     * Scroll the tableau to the center
     * 
     * @private
     * @return {void}
     */
    function scrollToCenter() {
        const $cont = this.$scrollContainer
        const $tableau = this.$tableau
        const current = $cont.scrollLeft()
        const windowWidth = $(window).width()
        const sel = [Dcls.Root, Dcls.NodeSegment, Dcls.Node, Dcls.NodeProps].join(' > ')
        const centerPos = $(sel, $tableau).position().left
        const scroll = centerPos - (windowWidth / 2)
        // var scroll = centerPos - (windowWidth / 2) + current
        debug({current, centerPos, scroll, windowWidth})
        $cont.scrollLeft(scroll)
    }

    /**
     * Scroll to the given jQuery object
     * 
     * @private
     * @param {object} $what The jQuery object to scroll to.
     * @return {void}
     */
    function scrollTo($what, opts) {
        opts = $.extend({}, FuncDefaults.ScrollTo, opts)
        const pos = $what.position()
        const scrollLeft = pos.left - ($(window).width() / 2)
        const scrollTop = pos.top - ($(window).height() / 2)
        this.$scrollContainer
            .scrollLeft(scrollLeft)
            .scrollTop(scrollTop)
    }

    /**
     * Execute given callback and return to previous scroll position.
     * 
     * @private
     * @param {function} cb The callback.
     * @return {void}
     */
    function returnScroll(cb) {
        const $cont = this.$scrollContainer
        const left = $cont.scrollLeft()
        const top = $cont.scrollTop()
        try {
            cb()
        } finally {
            $cont.scrollLeft(left).scrollTop(top)
        }
    }

    /**
     * Stretch or shrink the width so nodes do not wrap.
     * 
     * @private
     * @param {object} $leaves (optional) The leaves to examine to determine the width.
     * @return {void}
     */
    function stretchWidth($leaves) {
        returnScroll.call(this, () => {
            const {$tableau} = this
            $tableau.css({width: '100%'}).attr(Attrib.CurWidthPct, '100')
            const currWidth = +$tableau.attr(Attrib.CurWidthPct)
            const guess = guessNoWrapWidth.call(this, $leaves)
            debug({guess})
            if (!guess || guess <= 1) {
                return
            }
            const p = currWidth * guess
            debug({p, currWidth})
            $tableau.attr(Attrib.CurWidthPct, p).css({width: p + '%'})
        })
    }

    /**
     * Guess the width needed so that nodes do not wrap.
     * 
     * @private
     * @return {integer} How much to multiple the current width by, e.g.
     *   a value of 1 means no change.
     */
    function guessNoWrapWidth($leaves) {
        const $tableau = this.$tableau
        if (false && !$leaves && this._lastShows) {
            var lowests = {}
            debug('lastshows', this._lastShows)
            this._lastShows.each(function(i, s) {
                trackLowests(lowests, getPos($(s)))
            })
            debug('lowests', lowests)
            var leaves = $.map(lowests, function(pos) { return pos.$structure.get(0) })
            $leaves = $(leaves)
            debug('leaves', $leaves)
        }
        if ($leaves) {
            if ($leaves.hasClass(Cls.Structure)) {
                $leaves = $(
                    '> ' + [Dcls.NodeSegment, Dcls.Node, Dcls.NodeProps].join(' > ') + ':visible',
                    $leaves
                )
            }
            // if (!$leaves.hasClass(Cls.NodeProps)) {
            //     $leaves = $(Dcls.NodeSegment + ':eq(0) ' + Dcls.NodeProps, $leaves).filter(':visible')
            // }
            debug($leaves)
        }
        if (!$leaves) {
            // A good candidate for the wrappiest node is the wrappiest of the
            // outer-most leaf segments.
            // TODO: compare with right leaf
            $leaves = $(Dcls.Leaf + ':visible:eq(0) ' + Dcls.NodeProps, $tableau)
        }

        let maxDiffPct = 0
        $leaves.each(function() {
            const $me = $(this)
            const h = $me.height()
            const h2 = $me.css('position', 'absolute').height()
            $me.css('position', 'inherit')
            if (h > h2) {
                const diff = h / h2
                if (diff > maxDiffPct) {
                    debug($me.text(), {h, h2, nid: $me.parent().attr('id')})
                    maxDiffPct = diff
                }
            }
            // debug({h, h2})
        })
        let guess = maxDiffPct
        if (guess > 1) {
            if (guess <= 1.5) {
                guess = guess - ((guess - 1) / 2)
            } else if (guess <= 2) {
                guess = guess * 0.8
            } else if (guess <= 4) {
                guess = guess * 0.7
            } else if (guess <= 8) {
                guess = guess * 0.6
            }
        } else {
            guess = 1
        }
        debug({maxDiffPct, guess})
        return guess
    }


    /**
     * Handle a click event on a tableau.
     *
     * @private
     * @param {object} $target The target jQuery element.
     * @return {void}
     */
    function handleTableauClick($target) {
        const $structure = $target.closest(Dcls.Structure)
        if ($structure.length) {
            const behavior = ModKey.ctrlalt
                ? Behave.Zoom
                : Behave.Inspect
            switch (behavior) {
                case Behave.Zoom:
                    zoom.call(this, $structure)
                    setInspectedBranch.call(this, $structure)
                    break
                case Behave.Inspect:
                    setInspectedBranch.call(this, $structure)
                    break
                default:
                    break
            }
        }
    }
    /**
     * Handle a click event on a controls panel element.
     *
     * @private
     * @param {object} $target The event target jQuery element.
     * @return {void}
     */
    function handleControlsClick($target) {
        if ($target.is(Dcls.MarkDisabled + ', :disabled, :checkbox, select')) {
            return
        }
        const classMap = Object.create(null)
        const classStr = $target.attr('class')
        if (!classStr) {
            return
        }
        const classes = classStr.split(' ')
        for (let i = 0; i < classes.length; ++i) {
            classMap[classes[i]] = true
        }
        for (const action in NamedActions) {
            if (classMap[Cls[action]]) {
                NamedActions[action].call(this)
                return
            }
        }
        if (classMap[Cls.StepRuleTarget]) {
            const markClass = Cls.MarkActive
            const off = Boolean(classMap[markClass])
            if (off) {
                highlightStepOff.call(this)
                $target.removeClass(markClass)
            } else {
                highlightStepTarget.call(this)
                $target.addClass(markClass)
            }
        } else if (classMap[Cls.StepRuleName]) {
            const markClass = Cls.MarkActive
            const off = Boolean(classMap[markClass])
            if (off) {
                highlightStepOff.call(this)
                $target.removeClass(markClass)
            } else {
                highlightStepResult.call(this)
                $target.addClass(markClass)
            }
        } else if (classMap[Cls.BranchFilter]) {
            for (const filterType of Object.values(FilterType)) {
                if (classMap[filterType]) {
                    filterBranches.call(this, filterType)
                    break
                }
            }
        }
    }

    /**
     * Handle a change event on a controls panel.
     *
     * @private
     * @param {object} $target The event target jQuery element.
     * @return {void}
     */
    function handleControlsChange($target) {
        const $tableau = this.$tableau
        if ($target.hasClass(Cls.StepInput)) {
            const n = +$target.val()
            if (isNaN(n) || n < 0 || n > +$tableau.attr(Attrib.NumSteps)) {
                $target.val($tableau.attr(Attrib.Step))
                return
            }
            step.call(this, n)
        } else if ($target.hasClass(Cls.BranchFilter)) {
            filterBranches.call(this, $target.val())
        } else if ($target.hasClass(Cls.ColorOpen)) {
            $tableau.toggleClass(Cls.ColorOpen, $target.is(':checked'))
        }
    }

    /**
     * Handle a click event on a models panel.
     *
     * @private
     * @param {object} $target The event target jQuery element.
     * @return {void}
     */
    function handleModelsClick($target) {

    }

    /**
     * Highlight shortcut key function builder.
     */
    function makeHighlightAction(stay, isResult) {
        return function actionHighlightCommon() {
            const step = this.$tableau.attr(Attrib.Step)
            const dcls = isResult
                ? Dcls.StepRuleName
                : Dcls.StepRuleTarget
            const $target = $(dcls + getAttrSelector(Attrib.Step, step), this.$controls)
            const markClass = Cls.MarkActive
            if ($target.hasClass(markClass)) {
                highlightStepOff.call(this)
                $target.removeClass(markClass)
            } else {
                $target.addClass(markClass)
                if (isResult) {
                    highlightStepResult.call(this)
                } else {
                    highlightStepTarget.call(this)
                }
                if (!stay) {
                    setTimeout(() => {
                        highlightStepOff.call(this)
                        $target.removeClass(markClass)
                    }, Anim.Slow)
                }
            }
        }
    }

    /**
     * Adjust shortcut key function builder.
     */
    function makeAdjustAction(what, howMuch) {
        return function() {
            adjust.call(this, what, howMuch)
        }
    }
    /**
     * Filter shortcut key function builder.
     */
    function makeFilterAction(filterType) {
        return function() {
            if (this.$tableau.children(Sel.CanBranchFilter).length) {
                filterBranches.call(this, filterType)
            }
        }
    }

    /**
     * Shortcut action functions.
     */
    const NamedActions = Object.assign(Object.create(null), {
        StepNext: makeAdjustAction(AdjustWhat.Step, HowMuch.StepInc),
        StepPrev: makeAdjustAction(AdjustWhat.Step, -HowMuch.StepInc),
        StepStart: makeAdjustAction(AdjustWhat.Step, HowMuch.Start),
        StepEnd: makeAdjustAction(AdjustWhat.Step, HowMuch.End),
        FontPlus: makeAdjustAction(AdjustWhat.Font, HowMuch.FontInc),
        FontMinus: makeAdjustAction(AdjustWhat.Font, -HowMuch.FontInc),
        FontReset: makeAdjustAction(AdjustWhat.Font, HowMuch.Reset),
        WidthPlus: makeAdjustAction(AdjustWhat.Width, HowMuch.WidthMedium),
        WidthMinus: makeAdjustAction(AdjustWhat.Width, -HowMuch.WidthMedium),
        WidthPlusPlus: makeAdjustAction(AdjustWhat.Width, HowMuch.WidthLarge),
        WidthMinusMinus: makeAdjustAction(AdjustWhat.Width, -HowMuch.WidthLarge),
        WidthReset: makeAdjustAction(AdjustWhat.Width, HowMuch.Reset),
        WidthStretch: stretchWidth,
        WidthAuto: function() { setAutoWidth.call(this, !this._isAutoWidth) },
        ScrollCenter: scrollToCenter,
        ScrollAuto: function() { setAutoScroll.call(this, !this._isAutoScroll) },
        FilterOpen: makeFilterAction(FilterType.Open),
        FilterClosed: makeFilterAction(FilterType.Closed),
        FilterAll: makeFilterAction(FilterType.All),
        HighlightRule: makeHighlightAction(false, true),
        HighlightRuleStay: makeHighlightAction(true, true),
        HighlightTarget: makeHighlightAction(false, false),
        HighlightTargetStay: makeHighlightAction(true, false),
        ZoomCancel: function() { zoom.call(this, this.$tableau.children(Dcls.Structure)) },
    })

    /**
     * Get the left/right values of the given structure, as well a reference
     * to the structure's jQuery element.
     *
     * @param {object} $structure The singleton jQuery .structure element.
     * @return {object} A plain object with left/right/$structure keys.
     */
     function getPos($structure) {
        return {
            left: +$structure.attr(Attrib.Left),
            right: +$structure.attr(Attrib.Right),
            $structure: $structure,
        }
    }

    /**
     * Get the relation of one position object to the other (see getPos() above).
     *
     * @param {object} from The related position object.
     * @param {object} to The position object to compare to.
     * @return {string} Either 'self', 'ancestor', 'descendant', or 'other'.
     */
     function getRelation(from, to) {
        if (from.left === to.left) {
            return Rel.Self
        }
        if (from.left < to.left && from.right > to.right) {
            return Rel.Ancestor
        }
        if (from.left > to.left && from.right < to.right) {
            return Rel.Descendant
        }
        return Rel.Outside
    }

    /**
     * Track only the highest disjoint positions. This checks pos against the
     * values already in trackObj. If pos is a descendant of a position already
     * in trackObj, then it is not added. If it is an ancestor, then it is added
     * to trackObj, and the descendant positions in trackObj are removed.
     *
     * @param trackObj The object store to check and modify.
     * @param pos The position object to potentially add.
     * @return {void}
     */
    function trackHighests(trackObj, pos) {
        consolidateRelated(Rel.Descendant, Rel.Ancestor, trackObj, pos)
    }

    /**
     * Track only the lowest disjoint positions. This checks pos against the
     * values already in trackObj. If pos is an ancestor of a position already
     * in trackObj, then it is not added. If it is a descendant, then it is added
     * to trackObj, and the ancestor positions in trackObj are removed.
     *
     * @param trackObj The object store to check and modify.
     * @param pos The position object to potentially add.
     * @return {void}
     */
    function trackLowests(trackObj, pos) {
        consolidateRelated(Rel.Ancestor, Rel.Descendant, trackObj, pos)
    }

    /**
     * Track only the highest or lowest positions of a lineage. This is the
     * generic function for trackHighests() and tackLowests().
     *
     * @param {Rel} dropIf The relation to drop, either descendant or ancestor.
     * @param {Rel} replaceIf The relation to replace, either ancestor or descendant.
     * @param {object} trackObj The object store to check and modify.
     * @param {object} pos The position object to potentially add.
     * @return {void}
     */
    function consolidateRelated(dropIf, replaceIf, trackObj, pos) {
        const replaces = []
        for (const hleft in trackObj) {
            const hpos = trackObj[hleft]
            const relation = getRelation(pos, hpos)
            if (relation === dropIf) {
                return
            }
            if (relation === replaceIf) {
                replaces.push(hleft)
            }
        }
        for (let i = 0; i < replaces.length; i++) {
            delete(trackObj[replaces[i]])
        }
        trackObj[pos.left] = pos
    }

    /**
     * Sum all elements in an array. Return 0 if empty.
     *
     * @param {array} arr The array.
     * @return {number} The sum, or 0 if empty.
     */
    function sum(arr) {
        return arr.reduce((a, b) => a + b, 0)
    }

    /**
     * Form a selector string for an attribute.
     *
     * @param {string} attr The attribute name.
     * @param {string} val The attribute value.
     * @param {string} oper The operator, default is '='.
     * @return The attribute selector string.
     */
    function getAttrSelector(attr, val, oper) {
        return ['[', attr, oper || '=', '"', val, '"]'].join('')
    }

    /**
     * Compute the right offset from the left position.
     *
     * @param {object} $el The jQuery element.
     * @return {number} The right offset value.
     */
    function getRightOffset($el) {
        return (
            $(document).width() -
            $el.offset().left -
            $el.width() -
            parseFloat($el.css('marginRight') || 0)
        )
    }

    /**
     * Compute the absolute right offset value to simulate a right float inside
     * the parent element,
     *
     * @param {object} $el The jQuery element.
     * @return {number} The right offset value.
     */
    function computeRightZeroOffset($el) {
        let n = parseFloat($el.css('marginRight') || 0)
        $el = $el.parent()
        while ($el.length && $el.get(0) != document) {
            n += parseFloat($el.css('marginRight') || 0)
            n += parseFloat($el.css('paddingRight') || 0)
            $el = $el.parent()
        }
        return n
    }
})();