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
 * pytableaux - interactive tableau ui
 */
 ;(function() {

    if (typeof(jQuery) != 'function') {
        console.error(new Error('jQuery not loaded. Not initializing interactive handlers.'))
        return
    }

    const $ = jQuery
    const $E = $()

    // default option sets
    const Defaults = {
        Filter : {
            $proof       : $E      ,
            $hides       : $E      ,
            $shows       : $E      ,
            className    : null    ,
            adjust       : 'after' ,
        },
        Highlight : {
            $proof     : $E    ,
            exclusive  : true  ,
            stay       : true  ,
            off        : false ,
            ruleStep   : null  ,
            ruleTarget : null  ,
        }
    }

    // animation speed constants, in milliseconds.
    const Anim = {
        Fast : 150,
        Med  : 250,
        Slow : 500,
    }

    // relationship string contants
    const Rel = {
        Self       : 'self'       ,
        Ancestor   : 'ancestor'   ,
        Descendant : 'descendant' ,
        Outside    : 'outside'    ,
    }

    /*
        html-writer classes:

       misc : clear
    
       wrapper : tableau-wrapper
          tableau : tableau
            structure : structure [, has-open, has-closed, leaf, only-branch, closed, open]
              node-segment : node-sement
                 vertical-line : vertical-line
                horizontal-line : horizontal-line
                    node : node [, ticked]
                       node-props : node-props [, ticked]
                            inline : [sentence, world, designation, designated, undesignated, world1,
                                       world2, access, ellipsis, flag, <flag>]
    */
    // class names
    const Cls = {
        Controls        : 'proof-controls'       ,
        Models          : 'models-output'        ,
        ControlsHeading : 'controls-heading'     ,
        ControlsContent : 'controls-contents'    ,
        ControlsPos     : 'controls-position'    ,
        Proof           : 'tableau'              ,
        Root            : 'root'                 ,
        Structure       : 'structure'            ,
        Child           : 'child-wrapper'        ,
        Leaf            : 'leaf'                 ,
        NodeSegment     : 'node-segment'         ,
        NodeProps       : 'node-props'           ,
        PropSentence    : 'sentence'             ,
        PropAccess      : 'access'               ,
        Node            : 'node'                 ,
        Hidden          : 'hidden'               ,
        Zoomed          : 'zoomed'               ,
        Inspected       : 'inspected'            ,
        HL              : 'horizontal-line'      ,
        VL              : 'vertical-line'        ,
        Collapsed       : 'collapsed'            ,
        Uncollapsed     : 'uncollapsed'          ,
        StepStart       : 'step-start'           ,
        StepPrev        : 'step-prev'            ,
        StepNext        : 'step-next'            ,
        StepEnd         : 'step-end'             ,
        StepInput       : 'step-input'           ,
        StepRuleDatum   : 'step-rule-datum'      ,
        StepRuleName    : 'step-rule-name'       ,
        StepRuleTarget  : 'step-rule-target'     ,
        StepFiltered    : 'step-filtered'        ,
        ZoomFiltered    : 'zoom-filtered'        ,
        BranchFiltered  : 'branch-filtered'      ,
        Ticked          : 'ticked'               ,
        Closed          : 'closed'               ,
        FontPlus        : 'font-plus'            ,
        FontMinus       : 'font-minus'           ,
        FontReset       : 'font-reset'           ,
        WidthPlus       : 'width-plus'           ,
        WidthPlusPlus   : 'width-plus-plus'      ,
        WidthMinus      : 'width-minus'          ,
        WidthMinusMinus : 'width-minus-minus'    ,
        WidthReset      : 'width-reset'          ,
        WidthAutoStretch: 'width-auto-stretch'   ,
        ScrollCenter    : 'scroll-center'        ,
        HasOpen         : 'has-open'             ,
        HasClosed       : 'has-closed'           ,
        BranchFilter    : 'branch-filter'        ,
        Highlight       : 'highlight'            ,
        HighlightTicked : 'highlight-ticked'     ,
        HighlightClosed : 'highlight-closed'     ,
        Stay            : 'stay'                 ,
        ColorOpen       : 'color-open'           ,
        ModelsPos       : 'models-position'      ,
        Model           : 'model'                ,
        MarkActive      : 'active'               ,
        MarkFiltered    : 'filtered'             ,
    }

    // class names preceded with a '.' for selecting
    const Dcls = {}
    for (var c in Cls) {
        Dcls[c] = '.' + Cls[c]
    }

    // attributes
    const Attrib = {
        ProofId        : 'data-proof-element-id'  ,
        ProofClue      : 'data-step'              ,
        Left           : 'data-left'              ,
        Right          : 'data-right'             ,
        Step           : 'data-step'              ,
        Ticked         : 'data-ticked'            ,
        TickStep       : 'data-ticked-step'       ,
        CloseStep      : 'data-closed-step'       ,
        NumSteps       : 'data-num-steps'         ,
        Depth          : 'data-depth'             ,
        FilteredWidth  : 'data-filtered-width'    ,
        Width          : 'data-width'             ,
        CurWidthPct    : 'data-current-width-pct' ,
        NodeId         : 'data-node-id'           ,
        NodeIds        : 'data-node-ids'          ,
        BranchNodeId   : 'data-branch-node-id'    ,
        BranchId       : 'data-branch-id'         ,
        ModelId        : 'data-model-id'          ,
        LastTop        : 'data-last-top'          ,
        TopOffset      : 'data-top-offset'        ,
    }

    // selectors
    const Sel = {
        SteppedChilds  : [
            '>' + Dcls.NodeSegment + '>' + Dcls.Node,
            '>' + Dcls.VL,
        ].join(','),
        Filtered       : [
            Dcls.StepFiltered,
            Dcls.ZoomFiltered,
            Dcls.BranchFiltered,
        ].join(','),
        CanBranchFilter : [
            Dcls.HasOpen,
            Dcls.HasClosed,
        ].join('')
    }
    Sel.Unfiltered = ':not(' + Sel.Filtered + ')'

    // mod key state
    const ModKey = {
        shift : false,
        ctrl  : false,
        alt   : false,
    }

    // relevant action keys
    const ActionKeys = {
        '>' : true,
        '<' : true,
        'B' : true,
        'E' : true,
        '+' : true,
        '-' : true,
        '=' : true,
        ']' : true,
        '}' : true,
        '[' : true,
        '{' : true,
        '|' : true,
        'O' : true,
        'C' : true,
        'A' : true,
        'r' : true,
        'R' : true,
        't' : true,
        'T' : true,
        'Z' : true,
        'q' : true,
        'Q' : true,
        'm' : true,
        'M' : true,
        '@' : true,
        '$' : true,
    }

    // enums
    const E_AdjustWhat = {
        Font  : 'font'  ,
        Width : 'width' ,
        Step  : 'step'  ,
    }

    const E_AdjustWhen = {
        Before : 'before',
        After  : 'after' ,
    }

    const E_HowMuch = {
        Start           : 'start'     ,
        End             : 'end'       ,
        Beginning       : 'beginning' ,
        Reset           : 'reset'     ,
        StepInc         :   1         ,
        StepDec         :  -1         ,
        FontInc         :   1         ,
        FontDec         :  -1         ,
        WidthInc        :   1         ,
        WidthDec        :  -1         ,
        WidthUpMed      :  10         ,
        WidthDownMed    : -10         ,
        WidthUpLarge    :  25         ,
        WidthDownLarge  : -25         ,
    }

    const E_FilterType = {
        Open   : 'open'   ,
        Closed : 'closed' ,
        All    : 'all'    ,
    }

    const E_Behave = {
        Inspect : 'inspect',
        Zoom    : 'zoom'   ,
    }

    /**
     * Document ready init function.
     * 
     * @return void
     */
    function onReady() {

        var $currentProof = $(Dcls.Proof + '[' + Attrib.ProofClue + ']').first()

        // load a click event handler for each proof in the document.
        $(Dcls.Proof).on('click', function(e) {
            const $proof  = $(this)
            handleProofClick($(e.target), $proof)
            $currentProof = $proof
        })

        // load a change event for the controls panel
        $(Dcls.Controls).on('change', function(e) {
            const $controls = $(this)
            handleControlsChange($(e.target), $controls)
            $currentProof = getProofFromControls($controls)
        })

        // load a click event for the controls panel
        $(Dcls.Controls).on('click', function(e) {
            const $controls = $(this)
            handleControlsClick($(e.target), $controls)
            $currentProof = getProofFromControls($controls)
        })

        // load a click event for the models panel
        $(Dcls.Models).on('click', function(e) {
            const $models = $(this)
            handleModelsClick($(e.target), $models)
            $currentProof = getProofFromModels($models)
        })

        // monitor modifier keys
        $(document).on('keyup keydown', function(e) {
            ModKey.shift   = e.shiftKey
            ModKey.ctrl    = e.metaKey || e.ctrlKey
            ModKey.alt     = e.altKey
            ModKey.ctrlalt = ModKey.ctrl || ModKey.alt
        })

        // action keys
        $(document).on('keypress', function(e) {
            const key = String.fromCharCode(e.which)
            if (!ActionKeys[key]) {
                return
            }
            const $target = $(e.target)
            const isInput = $target.is(':input')
            const shouldProcess = !isInput && $currentProof && $currentProof.length
            if (!shouldProcess) {
                return
            }
            handleActionKey(key, $currentProof)
        })
    }

    const debug = console.debug

    const Index = {proof: {}, controls: {}, models: {}}
    /**
     * Get the target proof jQuery element from the controls jQuery
     * element
     * 
     * @param $controls The controls jQuery element.
     * @return $proof|null The jQuery proof element, or null if not found.
     */
    function getProofFromControls($controls) {
        const controlsId = $controls.attr('id')
        if (!Index.controls[controlsId]) {
            Index.controls[controlsId] = {}
        }
        if (!Index.controls[controlsId] || Index.controls[controlsId].$proof === undefined) {
            var proofId = $controls.attr(Attrib.ProofId)
            Index.controls[controlsId].$proof = null
            if (proofId) {
                var $proof = $('#' + proofId)
                if ($proof.length) {
                    Index.controls[controlsId].$proof = $proof
                }
                if (!Index.proof[proofId]) {
                    Index.proof[proofId] = {}
                }
                Index.proof[proofId].$controls = $controls
            }
        }
        var $proof = Index.controls[controlsId].$proof
        if (!$proof) {
            console.debug('Cannot find proof element')
        }
        return $proof
    }

    /**
     * Get the target proof jQuery element from the models jQuery
     * element
     * 
     * @param $controls The controls jQuery element.
     * @return $proof|null The jQuery proof element, or null if not found.
     */
     function getProofFromModels($models) {
        const modelsId = $models.attr('id')
        if (!Index.models[modelsId]) {
            Index.models[modelsId] = {}
        }
        if (!Index.models[modelsId] || Index.models[modelsId].$proof === undefined) {
            var proofId = $models.attr(Attrib.ProofId)
            Index.models[modelsId].$proof = null
            if (proofId) {
                var $proof = $('#' + proofId)
                if ($proof.length) {
                    Index.models[modelsId].$proof = $proof
                }
                if (!Index.proof[proofId]) {
                    Index.proof[proofId] = {}
                }
                Index.proof[proofId].$models = $models
            }
        }
        var $proof = Index.models[modelsId].$proof
        if (!$proof) {
            console.debug('Cannot find proof element')
        }
        return $proof
    }

    /**
     * Get the controls container from the proof.
     * 
     * @param $proof The proof jQuery element
     * @return The jQuery controls element, or null if not found.
     */
    function getControlsFromProof($proof) {
        const id = $proof.attr('id')
        if (id) {
            if (Index.proof[id] && Index.proof[id].$controls) {
                return Index.proof[id].$controls
            }
            var $controls = $(Dcls.Controls).filter(getAttrSelector(Attrib.ProofId, id))
            if ($controls.length) {
                return $controls
            }
        }
        console.debug('Cannot find controls element')
        return null
    }
    /**
     * Get the models container from the proof.
     * 
     * @param $proof The proof jQuery element
     * @return The jQuery models element, or null if not found.
     */
    function getModelsFromProof($proof) {
        const id = $proof.attr('id')
        if (id) {
            if (Index.proof[id] && Index.proof[id].$models) {
                return Index.proof[id].$models
            }
            var $models = $(Dcls.Models).filter(getAttrSelector(Attrib.ProofId, id))
            if ($models.length) {
                return $models
            }
        }
        console.debug('Cannot find models element')
        return null
    }
    /**
     * Show only the lineage of the given structure.
     *
     * @param $structure The jQuery .structure element(s).
     * @return void
     */
    function zoom($structure) {

        // if we are currently zoomed to this structure, there is nothing to do
        if ($structure.hasClass(Cls.Zoomed)) {
            return
        }

        const $proof = $structure.first().closest(Dcls.Proof)

        // get the previously zoomed structure
        const $prev = $(Dcls.Zoomed, $proof)

        const thisPos = getPos($structure)

        const hides = []
        const shows = []

        $(Dcls.Structure, $proof).each(function(i, s) {
            if (getRelation(getPos($(s)), thisPos) == Rel.Outside) {
                hides.push(s)
            } else {
                shows.push(s)
            }
        })

        doFilter($proof, {
            $hides    : $(hides),
            $shows    : $(shows),
            className : Cls.ZoomFiltered
        })

        // unmark the previous structure as zoomed
        $prev.removeClass(Cls.Zoomed)

        // mark the current structure as zoomed
        $structure.addClass(Cls.Zoomed)
    }

    /**
     * Set the branch being inspected.
     *
     * @param $structure The singleton jQuery .structure element.
     * @return void
     */
    function setInspectedBranch($structure) {

        // if we are currently inspecting this structure, there is nothing to do
        if ($structure.hasClass(Cls.Inspected)) {
            return
        }

        const $proof = $structure.closest(Dcls.Proof)

        $(Dcls.Inspected, $proof).removeClass(Cls.Inspected)
        $structure.addClass(Cls.Inspected)

        const $models = getModelsFromProof($proof)
        if (!$models) {
            return
        }
        const $modelElements = $(Dcls.Model, $models)
        const modelId = $structure.attr(Attrib.ModelId)

        $modelElements.hide()
        if (modelId) {
            $models.addClass(Cls.Inspected)
            $modelElements.filter(getAttrSelector(Attrib.ModelId, modelId)).show(Anim.Fast)
        } else {
            $models.removeClass(Cls.Inspected)
        }
    }

    /**
     * Move the proof state to the given step.
     *
     * @param $proof The singleton jQuery proof element.
     * @param n The step number.
     * @return void
     */
    function step($proof, n) {

        const numSteps = +$proof.attr(Attrib.NumSteps)
        const prevStep = +$proof.attr(Attrib.Step)

        if (n < 0) {
            n = 0
        }
        if (n > numSteps) {
            n = numSteps
        }
        if (n == prevStep) {
            return
        }

        const shows  = []
        const toHide = {}
        const showChilds  = []
        const hideChilds  = []
        const tickNodes   = []
        const untickNodes = []

        var highlightDelay = Anim.Slow

        $(Dcls.Structure, $proof).each(function(i, s) {
            const $s = $(s)
            const sPos = getPos($s)
            const sStep = +$s.attr(Attrib.Step)
            
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
                if (!+$stepped.attr(Attrib.Ticked)) {
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
        $(hideChilds).hide(Anim.Fast)

        // untick nodes
        $(Dcls.NodeProps, untickNodes).removeClass(Cls.Ticked)

        // filter structures
        const hides = $.map(toHide, function(pos) { return pos.$el.get(0) })
        doFilter($proof, {
            $hides    : $(hides),
            $shows    : $(shows),
            className : Cls.StepFiltered,
            adjust    : (n > prevStep) ? E_AdjustWhen.Before : E_AdjustWhen.After
        })

        // show nodes, vertical lines
        $(showChilds).show(Anim.Med)

        // delay the ticking of the nodes for animated effect
        setTimeout(function() { $(Dcls.NodeProps, tickNodes).addClass(Cls.Ticked) }, Anim.Med)

        // highlight the result
        setTimeout(function() { doHighlight($proof, {stay: false, ruleStep: n})}, highlightDelay)

        // set the current step attribute on the proof
        $proof.attr(Attrib.Step, n)

        var $controls = getControlsFromProof($proof)
        if ($controls) {
            // show the rule and target in the controls panel
            const attrSelector = getAttrSelector(Attrib.Step, n)
            $(Dcls.StepRuleDatum, $controls).hide().filter(attrSelector).show()
            //$(Dcls.StepRuleTarget, $controls).hide().filter(attrSelector).show()
            // update the input box
            $(Dcls.StepInput, $controls).val(n)
            // update disabled properties on forward/backward buttons
            var $backward = $([Dcls.StepStart, Dcls.StepPrev].join(', '), $controls)
            var $forward = $([Dcls.StepEnd, Dcls.StepNext].join(', '), $controls)
            if (n === numSteps) {
                $forward.addClass('disabled')//.prop('disabled', true)
            } else if (n < numSteps) {
                $forward.removeClass('disabled')//.prop('disabled', undefined)
            }
            if (n === 0) {
                $backward.addClass('disabled')//.prop('disabled', true)
            } else if (numSteps > n) {
                $backward.removeClass('disabled')//.prop('disabled', undefined)
            }
        }
    }

    /**
     * Filter branches of a proof according to their status.
     *
     * @param type The branch status to show, either 'open', 'closed', or 'all'.
     * @param $proof The singleton jQuery proof element.
     * @return void
     */
    function filterBranches(type, $proof) {

        // Track current state so we don't filter if not needed.
        const markClass = [Cls.MarkFiltered, type].join('-')
        if ($proof.hasClass(markClass)) {
            return
        }
    
        var removeClasses
        switch (type) {
            case E_FilterType.All:
                removeClasses = [
                    [Cls.MarkFiltered, E_FilterType.Open].join('-'),
                    [Cls.MarkFiltered, E_FilterType.Closed].join('-'),
                ]
                break
            case E_FilterType.Open:
                removeClasses = [
                    [Cls.MarkFiltered, E_FilterType.All].join('-'),
                    [Cls.MarkFiltered, E_FilterType.Closed].join('-'),
                ]
                break
            case E_FilterType.Closed:
                removeClasses = [
                    [Cls.MarkFiltered, E_FilterType.All].join('-'),
                    [Cls.MarkFiltered, E_FilterType.Open].join('-'),
                ]
                break
        }

        const $controls = getControlsFromProof($proof)
        var $active
        if ($controls) {
            var $ctrl = $(Dcls.BranchFilter, $controls)
            $active = $ctrl.filter('.' + type)
            if ($active.length) {
                $ctrl.removeClass(Cls.MarkActive)
            }
        }

        const toHide = []
        const toShow = []

        $(Dcls.Structure, $proof).each(function(i, s) {
            const $s = $(s)
            var shown
            switch (type) {
                case E_FilterType.All:
                    shown = true
                    break
                case E_FilterType.Open:
                    shown = $s.hasClass(Cls.HasOpen)
                    break
                case E_FilterType.Closed:
                    shown = $s.hasClass(Cls.HasClosed)
                    break
                default:
                    break
            }
            if (shown) {
                toShow.push(s)
            } else {
                toHide.push(s)
            }
        })

        doFilter($proof, {
            $hides    : $(toHide),
            $shows    : $(toShow),
            className : Cls.BranchFiltered
        })

        $proof.removeClass(removeClasses).addClass(markClass)
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
     * @param $proof The singleton jQuery proof element.
     * @param opts The options.
     * @return void
     */
    function doFilter($proof, opts) {

        opts = $.extend({}, Defaults.Filter, opts)

        const $hides = opts.$hides
        const $shows = opts.$shows
        const className = opts.className
        var showSpeed = Anim.Fast
        var hideSpeed = Anim.Fast
        var animateWidths = true

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
            if (pos.$el.is(Sel.Unfiltered)) {
                shows.push(this)
            }
        })

        // TODO: :)
        if (shows.length + $hides.length > 30) {
            showSpeed = 0
            hideSpeed = 0
            animateWidths = false
        }

        // sort the elements to show from higher to lower
        shows.sort(function(a, b) { return $(a).attr(Attrib.Depth) - $(b).attr(Attrib.Depth) })

        // collect the dom elements of the lowest structures
        const leaves = $.map(lowests, function(pos) { return pos.$el.get(0) })

        // hide elements that have a filter
        $hides.hide(hideSpeed)

        // adjust the widths (or do this 'after' below)
        if (opts.adjust == E_AdjustWhen.Before) {
            adjustWidths($proof, $(leaves), false)
        }

        // debug({shows: shows.length, hides: $hides.length})
        // show elements that do not have a filter
        $(shows).show(showSpeed)

        if (opts.adjust && opts.adjust != E_AdjustWhen.Before) {
            adjustWidths($proof, $(leaves), animateWidths)
        }
    }

    /**
     * Adjust the widths of the proof structures, after filters have been
     * applied. This takes the leaves (or lowest affected structures), and
     * traverses upward, adjusting the width of the ancestors.
     *
     * The 'leaves' will not be adjusted, since their width is fixed. True
     * leaves can only have nodes, so their width is 1.
     *
     * @param $proof The singleton proof jQuery element.
     * @param $leaves The jQuery element with the leaves, or deepest
     *   affected structures.
     * @param isAnimate Whether to animate the width transitions. Default
     *   is to animate all horizontal lines changes, and to animate width
     *   changes if the adjusted width is known to be an increase.
     * @return void
     */
    function adjustWidths($proof, $leaves, isAnimate) {

        if (!$leaves) {
            $leaves = $(Dcls.Leaf, $proof)
        }

        // traverse upward through the ancestors
        $leaves.parents(Dcls.Structure + Sel.Unfiltered).each(function(pi, parent) {

            const $parent            = $(parent)

            // The horizontal line.
            const $hl                = $parent.children(Dcls.HL)

            // All the child-wrapper elements.
            const $cws               = $parent.children(Dcls.Child)

            // The child-wrapper elements of the structures that are 'visible'.
            const $cwsUnfiltered     = $cws.has('> ' + Sel.Unfiltered)

            // The total number of children.
            const totalChildren      = $cws.length

            // The number of 'visible' children.
            const unfilteredChildren = $cwsUnfiltered.length

            // The list of child widths.
            const childWidths        = $cwsUnfiltered.map(function() {
                return +(
                    $(this).attr(Attrib.FilteredWidth) ||
                    $(this).children(Dcls.Structure).attr(Attrib.Width)
                )
            }).get()

            // The total width that the parent should consume.
            const width = sum(childWidths)

            // Modify the widths of the visible children.

            $cwsUnfiltered.each(function(ci, cw) {
                const $cw = $(cw)
                // calculate the new percentage
                const newWidthPct = ((childWidths[ci] * 100) / width) + '%'
                // get the current percentage from the store attribute
                const curWidthPct = $cw.attr(Attrib.CurWidthPct) || Infinity
                // round for comparisons
                const cmpNew = Math.floor(parseFloat(newWidthPct) * 10000) / 10000
                const cmpCur = Math.floor(parseFloat(curWidthPct) * 10000) / 10000
                if (cmpNew != cmpCur) {
                    // set the current percentage attribute
                    $cw.attr(Attrib.CurWidthPct, newWidthPct)
                    const css = {width: newWidthPct}
                    // only animate if the width is increasing
                    if (isAnimate && cmpNew > cmpCur) {
                        $cw.animate(css, Anim.Fast)
                    } else {
                        $cw.css(css)
                    }
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
                const first    = childWidths[0] / 2
                const last     = childWidths[childWidths.length - 1] / 2
                const betweens = sum(childWidths.slice(1, childWidths.length - 1))
                hlcss.marginLeft = ((first * 100 ) / width) + '%'
                hlcss.width = (((first + betweens + last) * 100) / width) + '%'
            }

            // If all children are visible, then restore the line style, otherwise make it dotted.
            if (totalChildren == unfilteredChildren) {
                $hl.removeClass(Cls.Collapsed)
            } else {
                $hl.addClass(Cls.Collapsed)
            }

            // Show the horizontal line if there are visible children, otherwise hide it.
            if (unfilteredChildren > 0) {
                if (isAnimate) {
                    $hl.show(Anim.Fast).animate(hlcss, Anim.Fast)
                } else {
                    $hl.show().css(hlcss)
                }
            } else {
                $hl.css(hlcss)
                if (isAnimate) {
                    $hl.hide(Anim.Fast)
                } else {
                    $hl.hide()
                }
            }

            // If this parent has a parent, mark the filtered width attribute
            // for the next traversal.
            const $pcw = $parent.closest(Dcls.Child)
            if ($pcw.length) {
                if (width == +$parent.attr(Attrib.Width)) {
                    $pcw.removeAttr(Attrib.FilteredWidth)
                } else {
                    $pcw.attr(Attrib.FilteredWidth, width || 1)
                }
            }
        })
    }

    /**
     * Perform a node highlighting operation on a proof.
     *
     * Option keys:
     *
     *   - exclusive  : Whether to unhighlight everything else on the proof.
     *                  Default true.
     *   - stay       : Whether to keep the highlighting effect, default true.
     *                  If false, it will flash.
     *   - off        : Whether to unhighlight everything on the proof.
     *   - ruleStep   : true || step number. Highlight the resulting nodes of
     *                  the current (or given) proof step.
     *   - ruleTarget : true || step number. Highlight the target nodes of
     *                  the current (or given) proof step.
     * @param $proof The singleton jQuery proof element.
     * @param opts The options.
     * @return void
     */
    function doHighlight($proof, opts) {
        opts = $.extend({}, Defaults.Highlight, opts)
        if (opts.off || opts.exclusive) {
            $(Dcls.Highlight, $proof).removeClass(Cls.Highlight)
            $(Dcls.HighlightTicked, $proof).removeClass(Cls.HighlightTicked)
            $(Dcls.HighlightClosed, $proof).removeClass(Cls.HighlightClosed)
        }
        if (opts.off) {
            var $controls = getControlsFromProof($proof)
            if ($controls) {
                $(Dcls.Highlight, $controls).removeClass(Cls.Highlight)
            }
            return
        }
        if (opts.ruleStep == null && opts.ruleTarget == null) {
            return
        }
        if (opts.ruleStep != null) {
            var n = opts.ruleStep === true ? +$proof.attr(Attrib.Step) : opts.ruleStep
            var nodeAttrSel = getAttrSelector(Attrib.Step, n)
            var nodeSel = Dcls.Node + nodeAttrSel
            var closeSel = Dcls.Structure + getAttrSelector(Attrib.CloseStep, n)
            var tickSel = Dcls.Node + getAttrSelector(Attrib.TickStep, n)
            $(nodeSel, $proof).addClass(Cls.Highlight)
            $(tickSel, $proof).addClass(Cls.HighlightTicked)
            $(closeSel, $proof).addClass(Cls.HighlightClosed)
        } else {
            var n = opts.ruleTarget === true ? +$proof.attr(Attrib.Step) : opts.ruleTarget
            var nodeAttrSel = getAttrSelector(Attrib.Step, n)
            var nodeIds = []
            var $controls = getControlsFromProof($proof)
            var $ruleTarget = $(Dcls.StepRuleTarget + nodeAttrSel, $controls)
            var nodeId = $ruleTarget.attr(Attrib.NodeId)
            if (nodeId) {
                nodeIds.push(+nodeId)
            }
            var nodeIdStr = $ruleTarget.attr(Attrib.NodeIds)
            if (nodeIdStr) {
                var nodeIdsArr = nodeIdStr.split(',').filter(Boolean)
                for (var i = 0; i < nodeIdsArr.length; ++i) {
                    nodeIds.push(+nodeIdsArr[i])
                }
                // nodeIdsArr.shift()
                // $.each(nodeIdsArr, function(i, id) { nodeIds.push(+id) })
            }
            if (nodeIds.length) {
                var nodeSel = $.map(nodeIds, function(id) { return Dcls.Node + getAttrSelector(Attrib.NodeId, id) }).join(',')
                var $nodes = $(nodeSel, $proof)
            } else {
                var $nodes = $E
            }
            // TODO: branch / branches
            $nodes.addClass(Cls.Highlight)
        }
        if (!opts.stay) {
            setTimeout(function() { doHighlight($proof, {off: true})}, Anim.Slow)
        }
    }

    /**
     * Get the left/right values of the given structure, as well a reference
     * to the structure's jQuery element.
     *
     * @param $el The singleton jQuery .structure element.
     * @return A plain object with left/right/$el keys.
     */
    function getPos($el) {
        return {
            left  : +$el.attr(Attrib.Left),
            right : +$el.attr(Attrib.Right),
            $el   : $el
        }
    }

    /**
     * Get the relation of one position object to the other (see getPos() above).
     *
     * @param from The related position object.
     * @param to The position object to compare to.
     * @return A string, either 'self', 'ancestor', 'descendant', or 'other'.
     */
    function getRelation(from, to) {
        if (from.left == to.left) {
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
     * @return void
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
     * @return void
     */
    function trackLowests(trackObj, pos) {
        consolidateRelated(Rel.Ancestor, Rel.Descendant, trackObj, pos)
    }

    /**
     * Track only the highest or lowest positions of a lineage. This is the
     * generic function for trackHighests() and tackLowests().
     *
     * @param dropIf The relation to drop, either descendant or ancestor.
     * @param replaceIf The relation to replace, either ancestor or descendant.
     * @param trackObj The object store to check and modify.
     * @param The position object to potentially add.
     * @return void
     */
    function consolidateRelated(dropIf, replaceIf, trackObj, pos) {
        const replaces = []
        for (var hleft in trackObj) {
            var hpos = trackObj[hleft]
            var relation = getRelation(pos, hpos)
            if (relation == dropIf) {
                return
            }
            if (relation == replaceIf) {
                replaces.push(hleft)
            }
        }
        for (var i = 0; i < replaces.length; i++) {
            delete(trackObj[replaces[i]])
        }
        trackObj[pos.left] = pos
    }

    /**
     * Sum all elements in an array. Return 0 if empty.
     *
     * @param arr The array.
     * @return The sum, or 0 if empty.
     */
    function sum(arr) {
        return arr.reduce(function(a, b) { return a + b }, 0)
    }

    /**
     * Form a selector string for an attribute.
     *
     * @param attr The attribute name.
     * @param val The attribute value.
     * @param oper The operator, default is '='.
     * @return The attribute selector string.
     */
    function getAttrSelector(attr, val, oper) {
        oper = oper || '='
        return ['[', attr, oper, '"', val, '"]'].join('')
    }

    // function flipObject(obj) {
    //     const ret = Object.create(null)
    //     for (var k in obj) {
    //         ret[obj[k]] = k
    //     }
    //     return ret
    // }

    /**
     * Make various incremental UI adjustments.
     *
     * @param $proof The singleton jQuery proof element.
     * @param what What thing to adjust (font, width, step).
     * @param howMuch How much to adjust it, or 'reset'.
     * @return void
     */
    function adjust($proof, what, howMuch) {

        switch (what) {
            case E_AdjustWhat.Font  :
                if (howMuch == E_HowMuch.Reset) {
                    $proof.css({fontSize: 'inherit'})
                } else {
                    $proof.css({fontSize: parseInt($proof.css('fontSize')) + (parseFloat(howMuch) || 0)})
                }
                break
            case E_AdjustWhat.Width :
                var p
                if (howMuch == E_HowMuch.Reset) {
                    p = 100
                } else {
                    p = +$proof.attr(Attrib.CurWidthPct) + (parseFloat(howMuch) || 0)
                }
                if (p < 0) {
                    p == 0
                }
                $proof.attr(Attrib.CurWidthPct, p)
                $proof.css({width: p + '%'})
                break
            case E_AdjustWhat.Step:
                var maxSteps = +$proof.attr(Attrib.NumSteps)
                var n
                if (howMuch == E_HowMuch.Beginning || howMuch == E_HowMuch.Start) {
                    n = 0
                } else if (howMuch == E_HowMuch.Reset || howMuch == E_HowMuch.End) {
                    n = maxSteps
                } else {
                    n = +$proof.attr(Attrib.Step) + (parseInt(howMuch) || 0)
                }
                if (n < 0) {
                    n = 0
                } else if (n > maxSteps) {
                    n = maxSteps
                }
                step($proof, n)
                break
            default:
                break
        }
    }

    function autoStretchWidth($proof) {
        var guess = guessNoWrapWidth($proof)
        debug({guess})
        if (!guess || guess <= 1) {
            return
        }
        adjust($proof, E_AdjustWhat.Width, (guess - 1) * 100)
    }

    function scrollToCenter($proof) {
        const $parent = $proof.parent()
        var current = $parent.scrollLeft()
        var windowWidth = $(window).width()
        var sel = [Dcls.Root, Dcls.NodeSegment, Dcls.Node, Dcls.NodeProps].join(' > ')
        var centerPos = $(sel, $proof).position().left
        var scroll = centerPos - (windowWidth / 2) + current
        debug({current, centerPos, scroll, windowWidth})
        $parent.scrollLeft(scroll)
    }
    /**
     * Guess the width needed so that nodes do not wrap
     */
    function guessNoWrapWidth($proof) {
        var currentWidth = $proof.width()
        // Likely the first node does not wrap
        var noWrapHeight = $(Dcls.NodeProps + ':eq(0)', $proof).height()
        if (!noWrapHeight) {
            return
        }
        // A good candidate for the wrappiest node is the wrappiest of the
        // outer-most leaf segments.
        var maxWrapHeight = noWrapHeight
        // another strategy
        var maxDiffPct = 0
        $(Dcls.Leaf + ':visible:eq(0) ' + Dcls.NodeProps, $proof).each(function() {
            const $me = $(this)
            const h = $me.height()

            // one stragegy
            if (h > maxWrapHeight) {
                // only count sentence or access nodes (not flags)
                if ($me.children([Dcls.PropSentence, Dcls.PropAccess].join(', ')).length) {

                    maxWrapHeight = h
                }
            }
            // another
            var h2 = $me.css('position', 'absolute').height()
            $me.css('position', 'inherit')
            if (h > h2) {
                var diff = h / h2
                if (diff > maxDiffPct) {
                    maxDiffPct = diff
                }
            }
            // debug({h, h2})
        })
        var strategy1 = 1, strategy2 = 1
        if (maxWrapHeight >= noWrapHeight * 1.5) {
            strategy1 = maxWrapHeight / noWrapHeight
        }
        if (maxDiffPct > 1.5) {
            strategy2 = maxDiffPct
        }
        debug({strategy1, strategy2, maxDiffPct, maxWrapHeight})
        return strategy1
        
        // TODO: compare with right leaf
    }

    /**
     * Handle a click event on a proof.
     *
     * @param $target The target jQuery element.
     * @param $proof The proof jQuery element.
     * @return void
     */
    function handleProofClick($target, $proof) {

        const $structure = $target.closest(Dcls.Structure)

        if ($structure.length) {
            const behavior = ModKey.ctrlalt ? E_Behave.Zoom : E_Behave.Inspect
            switch (behavior) {
                case E_Behave.Zoom:
                    zoom($structure)
                    setInspectedBranch($structure)
                    break
                case E_Behave.Inspect:
                    setInspectedBranch($structure)
                    break
                default :
                    break
            }
        }
    }

    /**
     * Handle a click event on a controls panel
     *
     * @param $target The target jQuery element.
     * @param $controls The controls jQuery element.
     * @return void
     */
    function handleControlsClick($target, $controls) {

        if ($target.is(':disabled, .disabled, :checkbox, select')) {
            return
        }
        const $proof = getProofFromControls($controls)
        if (!$proof) {
            return
        }
        // const classMap = Object.fromEntries(
        //     $target.attr('class').split(' ').map(function(c) { return [c, true] })
        // )
        if ($target.hasClass(Cls.StepStart)) {
            adjust($proof, E_AdjustWhat.Step, E_HowMuch.Start)
        } else if ($target.hasClass(Cls.StepNext)) {
            adjust($proof, E_AdjustWhat.Step, E_HowMuch.StepInc)
        } else if ($target.hasClass(Cls.StepPrev)) {
            adjust($proof, E_AdjustWhat.Step, E_HowMuch.StepDec)
        } else if ($target.hasClass(Cls.StepEnd)) {
            adjust($proof, E_AdjustWhat.Step, E_HowMuch.End)
        } else if ($target.hasClass(Cls.FontPlus)) {
            adjust($proof, E_AdjustWhat.Font, E_HowMuch.FontInc)
        } else if ($target.hasClass(Cls.FontMinus)) {
            adjust($proof, E_AdjustWhat.Font, E_HowMuch.FontDec)
        } else if ($target.hasClass(Cls.FontReset)) {
            adjust($proof, E_AdjustWhat.Font, E_HowMuch.Reset)
        } else if ($target.hasClass(Cls.WidthPlus)) {
            adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthUpMed)
        } else if ($target.hasClass(Cls.WidthPlusPlus)) {
            adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthUpLarge)
        } else if ($target.hasClass(Cls.WidthMinus)) {
            adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthDownMed)
        } else if ($target.hasClass(Cls.WidthMinusMinus)) {
            adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthDownLarge)
        } else if ($target.hasClass(Cls.WidthReset)) {
            adjust($proof, E_AdjustWhat.Width, E_HowMuch.Reset)
        } else if ($target.hasClass(Cls.WidthAutoStretch)) {
            autoStretchWidth($proof)
        } else if ($target.hasClass(Cls.ScrollCenter)) {
            scrollToCenter($proof)
        } else if ($target.hasClass(Cls.StepRuleTarget)) {
            var off = $target.hasClass(Cls.Highlight) || $target.hasClass(Cls.Stay)
            doHighlight($proof, {stay: true, off: off, ruleTarget: true})
            $target.toggleClass(Cls.Stay)
        } else if ($target.hasClass(Cls.StepRuleName)) {
            debug('StepRuleName')
            var off = $target.hasClass(Cls.Highlight) || $target.hasClass(Cls.Stay)
            doHighlight($proof, {stay: true, off: off, ruleStep: true})
            $target.toggleClass(Cls.Stay)
        } else if ($target.hasClass(Cls.BranchFilter)) {
            for (var filterType of Object.values(E_FilterType)) {
                if ($target.hasClass(filterType)) {
                    filterBranches(filterType, $proof)
                    break
                }
            }
        }
    }

    /**
     * Handle a change event on a controls panel.
     *
     * @param $target The target jQuery element.
     * @param $controls The controls jQuery element.
     * @return void
     */
    function handleControlsChange($target, $controls) {

        var $proof = getProofFromControls($controls)
        if (!$proof) {
            return
        }

        if ($target.hasClass(Cls.StepInput)) {
            var n = +$target.val()
            var maxSteps = +$proof.attr(Attrib.NumSteps)
            if (isNaN(n) || n < 0 || n > maxSteps) {
                $target.val($proof.attr(Attrib.Step))
                return
            }
            step($proof, n)
        } else if ($target.hasClass(Cls.BranchFilter)) {
            filterBranches($target.val(), $proof)
        } else if ($target.hasClass(Cls.ColorOpen)) {
            if ($target.is(':checked')) {
                $proof.addClass(Cls.ColorOpen)
            } else {
                $proof.removeClass(Cls.ColorOpen)
            }
        }
    }

    /**
     * Handle a click event on a models panel.
     *
     * @param $target The target jQuery element.
     * @param $models The models panel jQuery element.
     * @return void
     */
    function handleModelsClick($target, $models) {

    }

    /**
     * Handle an action key on the proof.
     *
     * @param key The action key character.
     * @param $proof The proof jQuery element.
     * @return void
     */
    function handleActionKey(key, $proof) {

        switch (key) {
            case '>':
                adjust($proof, E_AdjustWhat.Step, E_HowMuch.StepInc)
                break
            case '<':
                adjust($proof, E_AdjustWhat.Step, E_HowMuch.StepDec)
                break
            case 'B':
                adjust($proof, E_AdjustWhat.Step, E_HowMuch.Start)
                break
            case 'E':
                adjust($proof, E_AdjustWhat.Step, E_HowMuch.End)
                break
            case '+':
                adjust($proof, E_AdjustWhat.Font, E_HowMuch.FontInc)
                break
            case '-':
                adjust($proof, E_AdjustWhat.Font, E_HowMuch.FontDec)
                break
            case '=':
                adjust($proof, E_AdjustWhat.Font, E_HowMuch.Reset)
                break
            case ']':
                adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthUpMed)
                break
            case '}':
                adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthUpLarge)
                break
            case '[':
                adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthDownMed)
                break
            case '{':
                adjust($proof, E_AdjustWhat.Width, E_HowMuch.WidthDownLarge)
                break
            case '|':
                adjust($proof, E_AdjustWhat.Width, E_HowMuch.Reset)
                break
            case '@':
                autoStretchWidth($proof)
                break
            case '$':
                scrollToCenter($proof)
                break
            case 'O':
                //defer(function() {
                    if ($proof.children(Sel.CanBranchFilter).length) {
                        filterBranches(E_FilterType.Open, $proof)
                    }
                //})
                break
            case 'C':
                if ($proof.children(Sel.CanBranchFilter).length) {
                    filterBranches(E_FilterType.Closed, $proof)
                }
                break
            case 'A':
                if ($proof.children(Sel.CanBranchFilter).length) {
                    filterBranches(E_FilterType.All, $proof)
                }
                break
            case 'r':
            case 'R':
                var stay = key == 'R'
                doHighlight($proof, {stay: stay, ruleStep: true})
                if (stay) {
                    var $controls = getControlsFromProof($proof)
                    if ($controls) {
                        $(Dcls.StepRuleName, $controls).toggleClass(Cls.Stay)
                    }
                }
                break
            case 't':
            case 'T':
                var stay = key == 'T'
                doHighlight($proof, {stay: stay, ruleTarget: true})
                if (stay) {
                    var $controls = getControlsFromProof($proof)
                    if ($controls) {
                        $(Dcls.StepRuleName, $controls).toggleClass(Cls.Stay)
                    }
                }
                break
            case 'Z':
                zoom($proof.children(Dcls.Structure))
                break
            default:
                break
        }
    }

    $(document).ready(function() {
        onReady()
    })

    // var BUSY = false
    // function defer(cb) {
    //     if (BUSY) {
    //         console.log('BUSY')
    //         return false
    //     }
    //     BUSY = true
    //     setTimeout(function() {
    //         try {
    //             cb()
    //         } finally {
    //             BUSY = false
    //         }
    //     })
    //     return true
    // }

    /**
     * Compute the right offset from the left position.
     *
     * @param $el The jQuery element.
     * @return float The right offset value.
     */
    function getRightOffset($el) {
        return $(document).width() - $el.offset().left - $el.width() - parseFloat($el.css('marginRight') || 0)
    }

    /**
     * Compute the absolute right offset value to simulate a right float inside
     * the parent element,
     *
     * @param $el The jQuery element.
     * @return float The right offset value.
     */
    function computeRightZeroOffset($el) {
        var n = parseFloat($el.css('marginRight') || 0)
        $el = $el.parent()
        while ($el.length && $el.get(0) != document) {
            n += parseFloat($el.css('marginRight') || 0)
            n += parseFloat($el.css('paddingRight') || 0)
            $el = $el.parent()
        }
        return n
    }
})();
