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
 * pytableaux - interactive tableau ui
 */
;(function() {

    if (typeof(jQuery) != 'function') {
        console.error(new Error('jQuery not loaded. Not initializing interactive handlers.'))
        return
    }

    const $ = jQuery
    const IntervalPeriod = 40

    const $E = $()
    // default option sets
    const Defaults = {
        Filter : {
            $proof       : $E      ,
            $hides       : $E      ,
            $shows       : $E      ,
            className    : null    ,
            adjust       : 'after'
        },
        Highlight : {
            $proof     : $E    ,
            exclusive  : true  ,
            stay       : true  ,
            off        : false ,
            ruleStep   : null  ,
            ruleTarget : null
        }
    }

    // animation speed constants, in milliseconds.
    const Anim = {
        Fast : 150,
        Med  : 250,
        Slow : 500
    }

    // relationship string contants
    const Rel = {
        Self       : 'self'       ,
        Ancestor   : 'ancestor'   ,
        Descendant : 'descendant' ,
        Outside    : 'outside'
    }

    // class names
    const Cls = {
        Main            : 'html-writer'          ,
        Structure       : 'structure'            ,
        Child           : 'child-wrapper'        ,
        Leaf            : 'leaf'                 ,
        Proof           : 'html-writer-proof'    ,
        NodeSegment     : 'node-segment'         ,
        NodeProps       : 'node-props'           ,
        Node            : 'node'                 ,
        Hidden          : 'hidden'               ,
        Controls        : 'html-writer-controls' ,
        Models          : 'html-writer-models'   ,
        Zoomed          : 'zoomed'               ,
        Inspected       : 'inspected'            ,
        HL              : 'horizontal-line'      ,
        VL              : 'vertical-line'        ,
        Collapsed       : 'collapsed'            ,
        Uncollapsed     : 'uncollapsed'          ,
        Close           : 'closeMark'            ,
        StepStart       : 'step-start'           ,
        StepPrev        : 'step-prev'            ,
        StepNext        : 'step-next'            ,
        StepEnd         : 'step-end'             ,
        StepInput       : 'step-input'           ,
        StepRuleName    : 'step-rule-name'       ,
        StepRuleTarget  : 'step-rule-target'     ,
        StepFiltered    : 'step-filtered'        ,
        ZoomFiltered    : 'zoom-filtered'        ,
        BranchFiltered  : 'branch-filtered'      ,
        Ticked          : 'ticked'               ,
        FontPlus        : 'font-plus'            ,
        FontMinus       : 'font-minus'           ,
        FontReset       : 'font-reset'           ,
        WidthPlus       : 'width-plus'           ,
        WidthPlusPlus   : 'width-plus-plus'      ,
        WidthMinus      : 'width-minus'          ,
        WidthMinusMinus : 'width-minus-minus'    ,
        WidthReset      : 'width-reset'          ,
        HasOpen         : 'has-open'             ,
        HasClosed       : 'has-closed'           ,
        BranchFilter    : 'branch-filter'        ,
        Highlight       : 'highlight'            ,
        HighlightTicked : 'highlight-ticked'     ,
        Stay            : 'stay'                 ,
        ControlsHeading : 'controls-heading'     ,
        ControlsContent : 'controls-contents'    ,
        ControlsPos     : 'controls-position'    ,
        ModelsPos       : 'models-position'      ,
        ControlsWrap    : 'controls-wrapper'     ,
        CollapseWrap    : 'collapser-wrapper'    ,
        CollapseHead    : 'collapser-heading'    ,
        CollapseContent : 'collapser-contents'   ,
        PositionSelect  : 'position-select'      ,
        PositionedLeft  : 'positioned-left'      ,
        PositionedRight : 'positioned-right'     ,
        DragPanel       : 'drag-panel'           ,
        DragHandle      : 'drag-handle'          ,
        HasDragged      : 'has-dragged'          ,
        IsDrag          : 'is-drag'              ,
        PartHeader      : 'part-header'          ,
        Model           : 'model'
    }

    // class names preceded with a '.' for selecting
    const Dcls = {}
    for (var c in Cls) {
        Dcls[c] = '.' + Cls[c]
    }

    // attributes
    const Attrib = {
        Left           : 'data-left'              ,
        Right          : 'data-right'             ,
        Step           : 'data-step'              ,
        Ticked         : 'data-ticked'            ,
        TickStep       : 'data-ticked-step'       ,
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
        TopOffset      : 'data-top-offset'
    }

    // selectors
    const Sel = {
        SteppedChilds  : [
            '>' + Dcls.NodeSegment + '>' + Dcls.Node,
            '>' + Dcls.NodeSegment + '>' + Dcls.Close,
            '>' + Dcls.VL
        ].join(','),
        Filtered       : [
            Dcls.StepFiltered,
            Dcls.ZoomFiltered,
            Dcls.BranchFiltered
        ].join(','),
        CanBranchFilter : [
            Dcls.HasOpen,
            Dcls.HasClosed
        ].join('')
    }
    Sel.Unfiltered = ':not(' + Sel.Filtered + ')'

    /**
     * Show only the lineage of the given structure.
     *
     * @param $structure The singleton jQuery .structure element.
     * @param $proof The singleton jQuery .html-writer-proof element. If not
     *   passed, it will be retrieved.
     * @return void
     */
    function zoom($structure, $proof) {

        if (!$structure.hasClass(Cls.Structure)) {
            throw new Error('Invalid structure argument: ' + $structure)
        }

        // if we are currently zoomed to this structure, there is nothing to do
        if ($structure.hasClass(Cls.Zoomed)) {
            return
        }

        if (!$proof) {
            $proof = $structure.closest(Dcls.Proof)
        }

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

        doFilter({
            $hides    : $(hides),
            $shows    : $(shows),
            $proof    : $proof,
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
     * @param $proof The singleton jQuery .html-writer-proof element. If not
     *   passed, it will be retrieved.
     * @param $models The models jQuery element. If not passed, it will be
     *   retrieved.
     * @return void
     */
    function setInspectedBranch($structure, $proof, $models) {

        if (!$structure.hasClass(Cls.Structure)) {
            throw new Error('Invalid structure argument: ' + $structure)
        }

        // if we are currently inspecting this structure, there is nothing to do
        if ($structure.hasClass(Cls.Inspected)) {
            return
        }

        if (!$proof) {
            $proof = $structure.closest(Dcls.Proof)
        }

        const $main = $proof.closest(Dcls.Main)

        if (!$models) {
            $models = $(Dcls.Models, $main)
        }

        $(Dcls.Inspected, $proof).removeClass(Cls.Inspected)
        $structure.addClass(Cls.Inspected)

        const $modelElements = $(Dcls.Model, $models)
        const modelId = $structure.attr(Attrib.ModelId)
        $modelElements.hide()
        if (modelId) {
            $models.addClass(Cls.Inspected)
            $modelElements.filter(getAttrSelector(Attrib.ModelId, modelId)).show(Anim.Fast)
        } else {
            $models.removeClass(Cls.Inspected)
        }

        adjustMainHeight($main, Anim.Fast)
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

        const $main = $proof.closest(Dcls.Main)

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
            // process nodes, markers, vertical lines
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

        // hide nodes, markers, vertical lines
        $(hideChilds).hide(Anim.Fast)

        // untick nodes
        $(Dcls.NodeProps, untickNodes).removeClass(Cls.Ticked)

        // filter structures
        const hides = $.map(toHide, function(pos) { return pos.$el.get(0) })
        doFilter({
            $proof    : $proof,
            $hides    : $(hides),
            $shows    : $(shows),
            className : Cls.StepFiltered,
            adjust    : (n > prevStep) ? 'before' : 'after'
        })

        // show nodes, markers, vertical lines
        $(showChilds).show(Anim.Med)

        // delay the ticking of the nodes for animated effect
        setTimeout(function() { $(Dcls.NodeProps, tickNodes).addClass(Cls.Ticked) }, Anim.Med)

        // do a highlight of the result with a longer delay
        setTimeout(function() { doHighlight({$proof: $proof, stay: false, ruleStep: n})}, Anim.Slow)

        // set the current step attribute on the proof
        $proof.attr(Attrib.Step, n)

        // show the rule and target in the controls panel
        const $controls = $(Dcls.Controls, $main)
        const attrSelector = '[' + Attrib.Step + '=' + n + ']'
        $(Dcls.StepRuleName, $controls).hide().filter(attrSelector).show()
        $(Dcls.StepRuleTarget, $controls).hide().filter(attrSelector).show()
        // update the input box
        $(Dcls.StepInput, $controls).val(n)
    }

    /**
     * Filter branches of a proof according to their status.
     *
     * @param type The branch status to show, either 'open', 'closed', or 'all'.
     * @param $proof The singleton jQuery proof element.
     * @return void
     */
    function filterBranches(type, $proof) {
        if (type != 'all' && type != 'closed' && type != 'open') {
            throw new Error("Invalid filter type: " + type)
        }
        const $main = $proof.closest(Dcls.Main)
        const toHide = []
        const toShow = []
        $(Dcls.Structure, $proof).each(function(i, s) {
            const $s = $(s)
            var shown
            switch (type) {
                case 'all':
                    shown = true
                    break
                case 'open' :
                    shown = $s.hasClass(Cls.HasOpen)
                    break
                case 'closed' :
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
        doFilter({
            $proof    : $proof,
            $hides    : $(toHide),
            $shows    : $(toShow),
            className : Cls.BranchFiltered
        })
        const $controls = $(Dcls.Controls, $main)
        $(Dcls.BranchFilter, $controls).val(type)
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
     *     - $proof     : The singleton jQuery proof element.
     *     - className  : The filter class name to apply.
     *
     * Optional keys:
     *
     *     - adjust     : Adjust horizontal lines (boolean, 'before', or 'after').
     *                    Default is 'after'.
     *
     * @param opts The options.
     * @return void
     */
    function doFilter(opts) {

        opts = $.extend({}, Defaults.Filter, opts)

        const $hides = opts.$hides
        const $shows = opts.$shows
        const $proof = opts.$proof
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
            if (pos.$el.is(Sel.Unfiltered)) {
                shows.push(this)
            }
        })

        // sort the elements to show from higher to lower
        shows.sort(function(a, b) { return $(a).attr(Attrib.Depth) - $(b).attr(Attrib.Depth) })

        // collect the dom elements of the lowest structures
        const leaves = $.map(lowests, function(pos) { return pos.$el.get(0) })

        // hide elements that have a filter
        $hides.hide(Anim.Fast)

        // adjust the widths (or do this 'after' below)
        if (opts.adjust == 'before') {
            adjustWidths($proof, $(leaves), false)
        }

        // show elements that do not have a filter
        $(shows).show(Anim.Med)

        if (opts.adjust && opts.adjust != 'before') {
            adjustWidths($proof, $(leaves), true)
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
     * @param animate Whether to animate the width transitions. Default
     *   is to animate all horizontal lines changes, and to animate width
     *   changes if the adjusted width is known to be an increase.
     * @return void
     */
    function adjustWidths($proof, $leaves, animate) {

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
                    if (animate && cmpNew > cmpCur) {
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
                if (animate) {
                    $hl.show(Anim.Fast).animate(hlcss, Anim.Fast)
                } else {
                    $hl.show().css(hlcss)
                }
            } else {
                $hl.css(hlcss)
                if (animate) {
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
     *   - $proof     : The singled jQuery proof element.
     *   - exclusive  : Whether to unhighlight everything else on the proof.
     *                  Default true.
     *   - stay       : Whether to keep the highlighting effect, default true.
     *                  If false, it will flash.
     *   - off        : Whether to unhighlight everything on the proof.
     *   - ruleStep   : true || step number. Highlight the resulting nodes of
     *                  the current (or given) proof step.
     *   - ruleTarget : true || step number. Highlight the target nodes of
     *                  the current (or given) proof step.
     *
     * @param opts The options.
     * @return void
     */
    function doHighlight(opts) {
        opts = $.extend({}, Defaults.Highlight, opts)
        const $proof = opts.$proof
        const $main = $proof.closest(Dcls.Main)
        if (opts.off || opts.exclusive) {
            $(Dcls.Highlight, $proof).removeClass(Cls.Highlight)
            $(Dcls.HighlightTicked, $proof).removeClass(Cls.HighlightTicked)
        }
        if (opts.off) {
            var $controls = $(Dcls.Controls, $main)
            $(Dcls.Highlight, $controls).removeClass(Cls.Highlight)
            return
        }
        if (opts.ruleStep == null && opts.ruleTarget == null) {
            return
        }
        if (opts.ruleStep != null) {
            var n = opts.ruleStep === true ? +$proof.attr(Attrib.Step) : opts.ruleStep
            var nodeAttrSel = getAttrSelector(Attrib.Step, n)
            var nodeSel = [Dcls.Node + nodeAttrSel, Dcls.Close + nodeAttrSel].join(',')
            var tickSel = Dcls.Node + getAttrSelector(Attrib.TickStep, n)
            $(nodeSel, $proof).addClass(Cls.Highlight)
            $(tickSel, $proof).addClass(Cls.HighlightTicked)
        } else {
            var n = opts.ruleTarget === true ? +$proof.attr(Attrib.Step) : opts.ruleTarget
            var nodeAttrSel = getAttrSelector(Attrib.Step, n)
            var nodeIds = []
            var $controls = $(Dcls.Controls, $main)
            var $ruleTarget = $(Dcls.StepRuleTarget + nodeAttrSel, $controls)
            var nodeId = $ruleTarget.attr(Attrib.NodeId)
            if (nodeId) {
                nodeIds.push(+nodeId)
            }
            var nodeIdStr = $ruleTarget.attr(Attrib.NodeIds)
            if (nodeIdStr) {
                var nodeIdsArr = nodeIdStr.split(',')
                nodeIdsArr.shift()
                $.each(nodeIdsArr, function(i, id) { nodeIds.push(+id) })
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
            setTimeout(function() { doHighlight({$proof: $proof, off: true})}, Anim.Slow)
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
            case 'font'  :
                if (howMuch == 'reset') {
                    $proof.css({fontSize: 'inherit'})
                } else {
                    $proof.css({fontSize: parseInt($proof.css('font-size')) + (parseFloat(howMuch) || 0)})
                }
                break
            case 'width' :
                var p
                if (howMuch == 'reset') {
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
            case 'step':
                var maxSteps = +$proof.attr(Attrib.NumSteps)
                var n
                if (howMuch == 'beginning' || howMuch == 'start') {
                    n = 0
                } else if (howMuch == 'reset' || howMuch == 'end') {
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

    /**
     * Show/hide handler for collapser.
     *
     * @param $heading The heading jQuery element
     * @return void
     */
    function handleCollapserHeadingClick($heading) {
        const $wrapper = $heading.closest(Dcls.CollapseWrap)
        const $contents = $wrapper.find(Dcls.CollapseContent)
        const $main = $heading.closest(Dcls.Main)
        const isShow = $heading.hasClass(Cls.Collapsed)
        const speed = isShow ? Anim.Med : Anim.Fast
        if (isShow) {
            $heading.add($wrapper).removeClass(Cls.Collapsed).addClass(Cls.Uncollapsed)
            $contents.removeClass(Cls.Collapsed).addClass(Cls.Uncollapsed).show(speed)
        } else {
            $heading.add($wrapper).removeClass(Cls.Uncollapsed).addClass(Cls.Collapsed)
            $contents.removeClass(Cls.Uncollapsed).addClass(Cls.Collapsed).hide(speed)
        }
        adjustMainHeight($main, speed)
    }

    /**
     * Resetting the minHeight of the parent element of the  panel.
     *
     * @param $main The main jQuery element.
     * @param delay The delay, default is Anim.Fast or 100 if Anim.Fast is NaN.
     * @return void
     */
    function adjustMainHeight($main, delay) {
        delay = +delay
        if (isNaN(delay)) {
            delay = (!isNaN(+Anim.Fast) && Anim.Fast) || 100
        }
        delay += 50
        setTimeout(function() {
            var maxMinHeight = 0
            $main.find(Dcls.CollapseWrap).each(function() {
                const $wrapper = $(this)
                const $panel = $wrapper.closest(Dcls.DragPanel)
                const offset = $panel.position().top - $main.position().top
                const wrapperHeight = parseFloat($wrapper.css('height'))
                const marginTop = parseFloat($panel.css('marginTop')) || 0
                const minHeight = wrapperHeight + offset + marginTop
                if (minHeight > maxMinHeight) {
                    maxMinHeight = minHeight
                }
            })
            if (maxMinHeight > 0) {
                $main.css({minHeight: maxMinHeight})
            } else {
                $main.css({minHeight: ''})
            }
        }, delay)
    }

    /**
     * Position the panel element.
     *
     * @param $panel The panel jQuery element.
     * @return void
     */
    function positionDraggable($panel) {
        const value = $(Dcls.PositionSelect, $panel).val() || 'left'
        const $wrapper = $(Dcls.CollapseWrap, $panel)
        const $parent = $panel.parent()
        if (value == 'right') {
            if ($panel.hasClass(Cls.IsDrag)) {
                // convert left to right
                var rightVal = getRightOffset($panel)
            } else {
                // compute contained "0"ish right offset
                var rightVal = computeRightZeroOffset($panel)
            }
            $panel.css({left: '', right: rightVal})
            $wrapper.removeClass(Cls.PositionedLeft).addClass(Cls.PositionedRight)
        } else {
            if (!$panel.hasClass(Cls.IsDrag)) {
                $panel.css({left: '', right: ''})
            }
            $wrapper.removeClass(Cls.PositionedRight).addClass(Cls.PositionedLeft)
        }
    }

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

    /**
     * Draggable start handler.
     *
     * @return void
     */
    function onDraggableStart() {
        const $me = $(this)
        $me.css({left: '', right: ''})
        $me.addClass(Cls.HasDragged).addClass(Cls.IsDrag)
    }

    /**
     * Draggable stop handler.
     *
     * @return void
     */
    function onDraggableStop() {
        const $me = $(this)
        const $parent = $me.parent()

        // check if we are more to the left or right
        const leftVal = $me.position().left
        const middle = $parent.width() / 2
        $(Dcls.PositionSelect, $me).val(leftVal > middle ? 'right' : 'left')
        positionDraggable($me)
        // store the top offset relative to parent
        const topOffset = $me.offset().top - $parent.offset().top
        $me.attr(Attrib.TopOffset, topOffset)

        const $main = $me.closest(Dcls.Main)
        adjustMainHeight($main)
    }

    /**
     * Main interval function.
     *
     * @return void
     */
    function mainInterval() {
        $(Dcls.Main).each(function() {
            const $main = $(this)
            const thisTop = $main.offset().top
            const lastTop = $main.attr(Attrib.LastTop)
            if (thisTop != lastTop) {
                $(Dcls.DragPanel, $main).each(function() {
                    const $me = $(this)
                    const $parent = $me.parent()
                    const topOffset = +$me.attr(Attrib.TopOffset) || 0
                    const parentTop = $parent.offset().top
                    const newTop = parentTop + topOffset
                    $me.css({top: newTop})
                })
                $main.attr(Attrib.LastTop, thisTop)
            }
        })
    }

    $(document).ready(function() {

        const modkey = {
            shift : false,
            ctrl  : false,
            alt   : false
        }

        var $lastProof
        var IntervalHandle
        var lastDocHeight

        // monitor modifier keys
        $(document).on('keyup keydown', function(e) {
            modkey.shift   = e.shiftKey
            modkey.ctrl    = e.metaKey || e.ctrlKey
            modkey.alt     = e.altKey
            modkey.ctrlalt = modkey.ctrl || modkey.alt
        })

        $(Dcls.ControlsContent).accordion({
            header      : 'h4',
            heightStyle : 'content',
            animate     : Anim.Fast
        })

        const $dragPanels = $(Dcls.DragPanel)

        $dragPanels.draggable({
            containment : 'parent',
            handle      : Dcls.DragHandle,
            start       : onDraggableStart,
            stop        : onDraggableStop,
            // TODO: apply rewrite to deprecated option when available.
            // see https://jqueryui.com/upgrade-guide/1.12/#deprecated-distance-and-delay-options
            distance    : 10
        }).css({position: 'absolute'})

        if ($(Dcls.Controls).length) {
            $(Dcls.Models).each(function() {
                const $me = $(this)
                const currentTop = $me.offset().top
                $me.css({top: currentTop + 50})
                $me.attr(Attrib.TopOffset, '50')
            })
        }

        if ($dragPanels.length) {
            $dragPanels.each(function() {
                const $me = $(this)
                $me.attr(Attrib.LastTop, $me.offset().top)
            })
            IntervalHandle = setInterval(mainInterval, IntervalPeriod)
        }
        

        // load a click event handler for each proof in the document.
        $(Dcls.Proof).on('click', function(e) {
            const $proof     = $(this)
            const $target    = $(e.target)
            const $main      = $proof.closest(Dcls.Main)
            const $controls  = $(Dcls.Controls, $main)
            const $models    = $(Dcls.Models, $main)
            const $structure = $target.closest(Dcls.Structure)
            if ($structure.length) {
                const behavior = modkey.ctrlalt ? 'zoom' : 'inspect'
                switch (behavior) {
                    case 'zoom':
                        zoom($structure, $proof)
                        setInspectedBranch($structure, $proof, $models)
                        break
                    case 'inspect':
                        setInspectedBranch($structure, $proof, $models)
                        break
                    default :
                        break
                }
            }
            $lastProof = $proof
        })

        // load a change event for the controls panel
        $(Dcls.Controls).on('change', function(e) {
            const $controls = $(this)
            const $target   = $(e.target)
            const $main     = $controls.closest(Dcls.Main)
            const $proof    = $(Dcls.Proof, $main)
            const $models   = $(Dcls.Models, $main)
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
            } else if ($target.hasClass(Cls.ControlsPos)) {
                $controls.removeClass(Cls.IsDrag)
                positionDraggable($controls)
            } else if ($target.hasClass(Cls.ModelsPos)) {
                $(Dcls.PositionSelect, $models).val($target.val())
                $models.removeClass(Cls.IsDrag)
                positionDraggable($models)
            }
            $lastProof = $proof
        })

        // load a click event for the controls panel
        $(Dcls.Controls).on('click', function(e) {
            const $controls = $(this)
            const $target   = $(e.target)
            const $main     = $controls.closest(Dcls.Main)
            const $proof    = $(Dcls.Proof, $main)
            const $collapserHeading = $target.closest(Dcls.CollapseHead)
            if ($collapserHeading.length) {
                handleCollapserHeadingClick($collapserHeading)
            } else if ($target.is(Dcls.PartHeader)) {
                adjustMainHeight($main, Anim.Fast)
            } else if ($target.hasClass(Cls.StepStart)) {
                adjust($proof, 'step', 'start')
            } else if ($target.hasClass(Cls.StepNext)) {
                adjust($proof, 'step', 1)
            } else if ($target.hasClass(Cls.StepPrev)) {
                adjust($proof, 'step', -1)
            } else if ($target.hasClass(Cls.StepEnd)) {
                adjust($proof, 'step', 'end')
            } else if ($target.hasClass(Cls.FontPlus)) {
                adjust($proof, 'font', 1)
            } else if ($target.hasClass(Cls.FontMinus)) {
                adjust($proof, 'font', -1)
            } else if ($target.hasClass(Cls.FontReset)) {
                adjust($proof, 'font', 'reset')
            } else if ($target.hasClass(Cls.WidthPlus)) {
                adjust($proof, 'width', 10)
            } else if ($target.hasClass(Cls.WidthPlusPlus)) {
                adjust($proof, 'width', 25)
            } else if ($target.hasClass(Cls.WidthMinus)) {
                adjust($proof, 'width', -10)
            } else if ($target.hasClass(Cls.WidthMinusMinus)) {
                adjust($proof, 'width', -25)
            } else if ($target.hasClass(Cls.WidthReset)) {
                adjust($proof, 'width', 'reset')
            } else if ($target.hasClass(Cls.StepRuleTarget)) {
                var off = $target.hasClass(Cls.Highlight) || $target.hasClass(Cls.Stay)
                doHighlight({$proof: $proof, stay: true, off: off, ruleTarget: true})
                $target.toggleClass(Cls.Stay)
            } else if ($target.hasClass(Cls.StepRuleName)) {
                var off = $target.hasClass(Cls.Highlight) || $target.hasClass(Cls.Stay)
                doHighlight({$proof: $proof, stay: true, off: off, ruleStep: true})
                $target.toggleClass(Cls.Stay)
            }
            $lastProof = $proof
        })

        $(Dcls.Models).on('click', function(e) {
            const $models   = $(this)
            const $target   = $(e.target)
            const $main     = $models.closest(Dcls.Main)
            const $proof    = $(Dcls.Proof, $main)
            const $controls = $(Dcls.Controls, $main)
            const $collapserHeading = $target.closest(Dcls.CollapseHead)
            if ($collapserHeading.length) {
                handleCollapserHeadingClick($collapserHeading)
            }
            $lastProof = $proof
        })

        // shortcut keys
        $(document).on('keypress', function(e) {
            const $target = $(e.target)
            const isInput = $target.is(':input')
            if (!isInput && $lastProof) {
                const $proof = $lastProof
                const $main  = $proof.closest(Dcls.Main)
                var s = String.fromCharCode(e.which)
                switch (s) {
                    case '>':
                        adjust($proof, 'step', 1)
                        break
                    case '<':
                        adjust($proof, 'step', -1)
                        break
                    case 'B':
                        adjust($proof, 'step', 'start')
                        break
                    case 'E':
                        adjust($proof, 'step', 'end')
                        break
                    case '+':
                        adjust($proof, 'font', 1)
                        break
                    case '-':
                        adjust($proof, 'font', -1)
                        break
                    case '=':
                        adjust($proof, 'font', 'reset')
                        break
                    case ']':
                        adjust($proof, 'width', 10)
                        break
                    case '}':
                        adjust($proof, 'width', 25)
                        break
                    case '[':
                        adjust($proof, 'width', -10)
                        break
                    case '{':
                        adjust($proof, 'width', -25)
                        break
                    case '|':
                        adjust($proof, 'width', 'reset')
                        break
                    case 'O':
                        if ($proof.children(Sel.CanBranchFilter).length) {
                            filterBranches('open', $proof)
                        }
                        break
                    case 'C':
                        if ($proof.children(Sel.CanBranchFilter).length) {
                            filterBranches('closed', $proof)
                        }
                        break
                    case 'A':
                        if ($proof.children(Sel.CanBranchFilter).length) {
                            filterBranches('all', $proof)
                        }
                        break
                    case 'r':
                    case 'R':
                        var stay = s == 'R'
                        var $controls = $(Dcls.Controls, $main)
                        doHighlight({$proof: $proof, stay: stay, ruleStep: true})
                        if (stay) {
                            $(Dcls.StepRuleName, $controls).toggleClass(Cls.Stay)
                        }
                        break
                    case 't':
                    case 'T':
                        var stay = s == 'T'
                        var $controls = $(Dcls.Controls, $main)
                        doHighlight({$proof: $proof, stay: stay, ruleTarget: true})
                        if (stay) {
                            $(Dcls.StepRuleName, $controls).toggleClass(Cls.Stay)
                        }
                        break
                    case 'Z':
                        zoom($proof.children(Dcls.Structure), $proof)
                        break
                    case 'q':
                    case 'Q':
                        var $controls = $(Dcls.Controls, $main)
                        var $heading = $(Dcls.CollapseHead, $controls)
                        handleCollapserHeadingClick($heading)
                        break
                    case 'm':
                    case 'M':
                        var $models = $(Dcls.Models, $main)
                        var $heading = $(Dcls.CollapseHead, $models)
                        handleCollapserHeadingClick($heading)
                        break
                    default:
                        break
                }
            }         
        })
    })

})();