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

    if (typeof($) != 'function') {
        console.error(new Error('jQuery not loaded. Not initializing interactive handlers.'))
        return
    }

    const $E = $()
    // default option sets
    const DEFAULTS = {
        FILTER : {
            $proof       : $E      ,
            $hides       : $E      ,
            $shows       : $E      ,
            className    : null    ,
            adjust       : 'after'
        },
        HIGHLIGHT : {
            $proof     : $E,
            exclusive  : true,
            stay       : true,
            off        : false,
            ruleStep   : null,
            ruleTarget : null
        }
    }

    // animation speed constants, in milliseconds.
    const ANIM = {
        FAST : 150,
        MED  : 250,
        SLOW : 500
    }

    // relationship string contants
    const REL = {
        SELF       : 'self'       ,
        ANCESTOR   : 'ancestor'   ,
        DESCENDANT : 'descendant' ,
        OUTSIDE    : 'outside'
    }

    // class names
    const CLS = {
        STRUCTURE       : 'structure'                ,
        CHILD           : 'child-wrapper'            ,
        LEAF            : 'leaf'                     ,
        PROOF           : 'html-writer-proof'        ,
        NODESEGMENT     : 'node-segment'             ,
        NODEPROPS       : 'node-props'               ,
        NODE            : 'node'                     ,
        HIDDEN          : 'hidden'                   ,
        STATUS          : 'html-writer-status-panel' ,
        ZOOMED          : 'zoomed'                   ,
        HL              : 'horizontal-line'          ,
        VL              : 'vertical-line'            ,
        COLLAPSED       : 'collapsed'                ,
        CLOSE           : 'closeMark'                ,
        STEPSTART       : 'step-start'               ,
        STEPPREV        : 'step-prev'                ,
        STEPNEXT        : 'step-next'                ,
        STEPEND         : 'step-end'                 ,
        STEPINPUT       : 'step-input'               ,
        STEPRULENAME    : 'step-rule-name'           ,
        STEPRULETARGET  : 'step-rule-target'         ,
        STEPFILTERED    : 'step-filtered'            ,
        ZOOMFILTERED    : 'zoom-filtered'            ,
        BRANCHFILTERED  : 'branch-filtered'          ,
        TICKED          : 'ticked'                   ,
        FONTPLUS        : 'font-plus'                ,
        FONTMINUS       : 'font-minus'               ,
        FONTRESET       : 'font-reset'               ,
        WIDTHPLUS       : 'width-plus'               ,
        WIDTHPLUSPLUS   : 'width-plus-plus'          ,
        WIDTHMINUS      : 'width-minus'              ,
        WIDTHMINUSMINUS : 'width-minus-minus'        ,
        WIDTHRESET      : 'width-reset'              ,
        HASOPEN         : 'has-open'                 ,
        HASCLOSED       : 'has-closed'               ,
        BRANCHFILTER    : 'branch-filter'            ,
        HIGHLIGHT       : 'highlight'                ,
        HIGHLIGHTTICKED : 'highlight-ticked'         ,
        STAY            : 'stay'
    }

    // class names preceded with a '.' for selecting
    var DCLS = {}
    for (var c in CLS) {
        DCLS[c] = '.' + CLS[c]
    }

    // attributes
    const ATTR = {
        LEFT           : 'data-left'              ,
        RIGHT          : 'data-right'             ,
        STEP           : 'data-step'              ,
        TICKED         : 'data-ticked'            ,
        TICKSTEP       : 'data-ticked-step'       ,
        NUMSTEPS       : 'data-num-steps'         ,
        DEPTH          : 'data-depth'             ,
        FILTEREDWIDTH  : 'data-filtered-width'    ,
        WIDTH          : 'data-width'             ,
        CURWIDTHPCT    : 'data-current-width-pct' ,
        NODEID         : 'data-node-id'           ,
        NODEIDS        : 'data-node-ids'          ,
        BRANCHNODEID   : 'data-branch-node-id'
    }

    // selectors
    var SEL = {
        STEPPEDCHILDS  : [
            '>' + DCLS.NODESEGMENT + '>' + DCLS.NODE,
            '>' + DCLS.NODESEGMENT + '>' + DCLS.CLOSE,
            '>' + DCLS.VL
        ].join(','),
        FILTERED       : [
            DCLS.STEPFILTERED,
            DCLS.ZOOMFILTERED,
            DCLS.BRANCHFILTERED
        ].join(','),
        CANBRANCHFILTER : [
            DCLS.HASOPEN,
            DCLS.HASCLOSED
        ].join('')
    }
    SEL.UNFILTERED = ':not(' + SEL.FILTERED + ')'

    /**
     * Show only the lineage of the given structure.
     *
     * @param $structure The singleton jQuery .structure element.
     * @param $proof The singleton jQuery .html-writer-proof element. If not
     *   passed, it will be retrieved.
     * @return void
     */
    function zoom($structure, $proof) {

        if (!$structure.hasClass(CLS.STRUCTURE)) {
            throw new Error('Invalid structure argument: ' + $structure)
        }

        // if we are currently zoomed to this structure, there is nothing to do
        if ($structure.hasClass(CLS.ZOOMED)) {
            return
        }

        if (!$proof) {
            $proof = $structure.closest(DCLS.PROOF)
        }

        // get the previously zoomed structure
        var $prev = $(DCLS.ZOOMED, $proof)

        var thisPos = getPos($structure)

        var hides = []
        var shows = []

        $(DCLS.STRUCTURE, $proof).each(function(i, s) {
            if (getRelation(getPos($(s)), thisPos) == REL.OUTSIDE) {
                hides.push(s)
            } else {
                shows.push(s)
            }
        })

        doFilter({
            $hides    : $(hides),
            $shows    : $(shows),
            $proof    : $proof,
            className : CLS.ZOOMFILTERED
        })

        // unmark the previous structure as zoomed
        $prev.removeClass(CLS.ZOOMED)

        // mark the current structure as zoomed
        $structure.addClass(CLS.ZOOMED)
    }

    /**
     * Move the proof state to the given step.
     *
     * @param $proof The singleton jQuery proof element.
     * @param n The step number.
     * @return void
     */
    function step($proof, n) {

        var numSteps = +$proof.attr(ATTR.NUMSTEPS)
        var prevStep = +$proof.attr(ATTR.STEP)

        if (n < 0) {
            n = 0
        }
        if (n > numSteps) {
            n = numSteps
        }
        if (n == prevStep) {
            return
        }

        var shows  = []
        var toHide = {}
        var showChilds  = []
        var hideChilds  = []
        var tickNodes   = []
        var untickNodes = []
        $(DCLS.STRUCTURE, $proof).each(function(i, s) {
            var $s = $(s)
            var sPos = getPos($s)
            var sStep = +$s.attr(ATTR.STEP)
            if (sStep > n) {
                // only hide the highest structures
                trackHighests(toHide, sPos)
                return true
            }
            shows.push(s)
            // process nodes, markers, vertical lines
            $(SEL.STEPPEDCHILDS, $s).each(function(ni, stepped) {
                var $stepped = $(stepped)
                var nStep = +$stepped.attr(ATTR.STEP)
                if (nStep > n) {
                    hideChilds.push(stepped)
                    return true
                }
                showChilds.push(stepped)
                // ticking/unticking
                if (!+$stepped.attr(ATTR.TICKED)) {
                    return true
                }
                var tStep = +$stepped.attr(ATTR.TICKSTEP)
                var hasTicked = $(DCLS.NODEPROPS, $stepped).hasClass(CLS.TICKED)
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
        $(hideChilds).hide(ANIM.FAST)

        // untick nodes
        $(DCLS.NODEPROPS, untickNodes).removeClass(CLS.TICKED)

        // filter structures
        var hides = $.map(toHide, function(pos) { return pos.$el.get(0) })
        doFilter({
            $proof       : $proof,
            $hides       : $(hides),
            $shows       : $(shows),
            className    : CLS.STEPFILTERED,
            adjust       : (n > prevStep) ? 'before' : 'after'
        })

        // show nodes, markers, vertical lines
        $(showChilds).show(ANIM.MED)

        // delay the ticking of the nodes for animated effect
        setTimeout(function() { $(DCLS.NODEPROPS, tickNodes).addClass(CLS.TICKED) }, ANIM.MED)

        // do a highlight of the result with a longer delay
        setTimeout(function() { doHighlight({$proof: $proof, stay: false, ruleStep: n})}, ANIM.SLOW)

        // set the current step attribute on the proof
        $proof.attr(ATTR.STEP, n)

        // show the rule and target in the status panel
        var $status = getStatusFromProof($proof)
        var attrSelector = '[' + ATTR.STEP +'=' + n + ']'
        $(DCLS.STEPRULENAME, $status).hide().filter(attrSelector).show()
        $(DCLS.STEPRULETARGET, $status).hide().filter(attrSelector).show()
        // update the input box
        $(DCLS.STEPINPUT, $status).val(n)
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
        var toHide = []
        var toShow = []
        $(DCLS.STRUCTURE, $proof).each(function(i, s) {
            var $s = $(s)
            var shown
            switch (type) {
                case 'all':
                    shown = true
                    break
                case 'open' :
                    shown = $s.hasClass(CLS.HASOPEN)
                    break
                case 'closed' :
                    shown = $s.hasClass(CLS.HASCLOSED)
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
            $proof       : $proof,
            $hides       : $(toHide),
            $shows       : $(toShow),
            className    : CLS.BRANCHFILTERED
        })
        $status = getStatusFromProof($proof)
        $(DCLS.BRANCHFILTER, $status).val(type)
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

        opts = $.extend({}, DEFAULTS.FILTER, opts)

        var $hides = opts.$hides
        var $shows = opts.$shows
        var $proof = opts.$proof
        var className = opts.className

        // track the lowest structures to adjust widths
        var lowests = {}
        
        $hides.addClass(className).each(function() {
            trackLowests(lowests, getPos($(this)))
        })

        var shows = []

        $shows.removeClass(className).each(function() {
            var pos = getPos($(this))
            trackLowests(lowests, pos)
            // if there are no more filters on the element, it will be shown
            if (pos.$el.is(SEL.UNFILTERED)) {
                shows.push(this)
            }
        })

        // sort the elements to show from higher to lower
        shows.sort(function(a, b) { return $(a).attr(ATTR.DEPTH) - $(b).attr(ATTR.DEPTH) })

        // collect the dom elements of the lowest structures
        var leaves = $.map(lowests, function(pos) { return pos.$el.get(0) })

        // hide elements that have a filter
        $hides.hide(ANIM.FAST)

        // adjust the widths (or do this 'after' below)
        if (opts.adjust == 'before') {
            adjustWidths($proof, $(leaves), false)
        }

        // show elements that do not have a filter
        $(shows).show(ANIM.MED)

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
            $leaves = $(DCLS.LEAF, $proof)
        }

        // traverse upward through the ancestors
        $leaves.parents(DCLS.STRUCTURE + SEL.UNFILTERED).each(function(pi, parent) {

            var $parent            = $(parent)

            // The horizontal line.
            var $hl                = $parent.children(DCLS.HL)

            // All the child-wrapper elements.
            var $cws               = $parent.children(DCLS.CHILD)

            // The child-wrapper elements of the structures that are 'visible'.
            var $cwsUnfiltered     = $cws.has('> ' + SEL.UNFILTERED)

            // The total number of children.
            var totalChildren      = $cws.length

            // The number of 'visible' children.
            var unfilteredChildren = $cwsUnfiltered.length

            // The list of child widths.
            var childWidths        = $cwsUnfiltered.map(function() {
                return +(
                    $(this).attr(ATTR.FILTEREDWIDTH) ||
                    $(this).children(DCLS.STRUCTURE).attr(ATTR.WIDTH)
                )
            }).get()

            // The total width that the parent should consume.
            var width = sum(childWidths)

            // Modify the widths of the visible children.

            $cwsUnfiltered.each(function(ci, cw) {
                var $cw = $(cw)
                // calculate the new percentage
                var newWidthPct = ((childWidths[ci] * 100) / width) + '%'
                // get the current percentage from the store attribute
                var curWidthPct = $cw.attr(ATTR.CURWIDTHPCT) || Infinity
                // round for comparisons
                var cmpNew = Math.floor(parseFloat(newWidthPct) * 10000) / 10000
                var cmpCur = Math.floor(parseFloat(curWidthPct) * 10000) / 10000
                if (cmpNew != cmpCur) {
                    // set the current percentage attribute
                    $cw.attr(ATTR.CURWIDTHPCT, newWidthPct)
                    var css = {width: newWidthPct}
                    // only animate if the width is increasing
                    if (animate && cmpNew > cmpCur) {
                        $cw.animate(css, ANIM.FAST)
                    } else {
                        $cw.css(css)
                    }
                }
            })

            // Modify the horizontal line.

            var hlcss = {}

            if (unfilteredChildren < 2) {
                // If we have 1 or 0 visible children, then make the line span 33% and center it.
                hlcss.width = (100 / 3) + '%'
                // jQuery does not animate 'auto' margins, so we set it immmediately.
                $hl.css({marginLeft: 'auto'})
            } else {
                // If there there are 2 or more visible children, calculate
                // the line width and left margin. This is a repetition of 
                // the server-side calculations for the initial state.
                var first    = childWidths[0] / 2
                var last     = childWidths[childWidths.length - 1] / 2
                var betweens = sum(childWidths.slice(1, childWidths.length - 1))
                hlcss.marginLeft = ((first * 100 ) / width) + '%'
                hlcss.width = (((first + betweens + last) * 100) / width) + '%'
            }

            // If all children are visible, then restore the line style, otherwise make it dotted.
            if (totalChildren == unfilteredChildren) {
                $hl.removeClass(CLS.COLLAPSED)
            } else {
                $hl.addClass(CLS.COLLAPSED)
            }

            // Show the horizontal line if there are visible children, otherwise hide it.
            if (unfilteredChildren > 0) {
                if (animate) {
                    $hl.show(ANIM.FAST).animate(hlcss, ANIM.FAST)
                } else {
                    $hl.show().css(hlcss)
                }
            } else {
                $hl.css(hlcss)
                if (animate) {
                    $hl.hide(ANIM.FAST)
                } else {
                    $hl.hide()
                }
            }

            // If this parent has a parent, mark the filtered width attribute
            // for the next traversal.
            var $pcw = $parent.closest(DCLS.CHILD)
            if ($pcw.length) {
                if (width == +$parent.attr(ATTR.WIDTH)) {
                    $pcw.removeAttr(ATTR.FILTEREDWIDTH)
                } else {
                    $pcw.attr(ATTR.FILTEREDWIDTH, width || 1)
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
        opts = $.extend({}, DEFAULTS.HIGHLIGHT, opts)
        var $proof = opts.$proof
        if (opts.off || opts.exclusive) {
            $(DCLS.HIGHLIGHT, $proof).removeClass(CLS.HIGHLIGHT)
            $(DCLS.HIGHLIGHTTICKED, $proof).removeClass(CLS.HIGHLIGHTTICKED)
        }
        if (opts.off) {
            var $status = getStatusFromProof($proof)
            $(DCLS.HIGHLIGHT, $status).removeClass(CLS.HIGHLIGHT)
            return
        }
        if (opts.ruleStep == null && opts.ruleTarget == null) {
            return
        }
        if (opts.ruleStep != null) {
            var n = opts.ruleStep === true ? +$proof.attr(ATTR.STEP) : opts.ruleStep
            var nodeAttrSel = getAttrSelector(ATTR.STEP, n)
            var nodeSel = [DCLS.NODE + nodeAttrSel, DCLS.CLOSE + nodeAttrSel].join(',')
            var tickSel = DCLS.NODE + getAttrSelector(ATTR.TICKSTEP, n)
            $(nodeSel, $proof).addClass(CLS.HIGHLIGHT)
            $(tickSel, $proof).addClass(CLS.HIGHLIGHTTICKED)
        } else {
            var n = opts.ruleTarget === true ? +$proof.attr(ATTR.STEP) : opts.ruleTarget
            var nodeAttrSel = getAttrSelector(ATTR.STEP, n)
            var nodeIds = []
            var $status = getStatusFromProof($proof)
            var $ruleTarget = $(DCLS.STEPRULETARGET + nodeAttrSel, $status)
            var nodeId = $ruleTarget.attr(ATTR.NODEID)
            if (nodeId) {
                nodeIds.push(+nodeId)
            }
            var nodeIdStr = $ruleTarget.attr(ATTR.NODEIDS)
            if (nodeIdStr) {
                var nodeIdsArr = nodeIdStr.split(',')
                nodeIdsArr.shift()
                $.each(nodeIdsArr, function(i, id) { nodeIds.push(+id) })
            }
            if (nodeIds.length) {
                var nodeSel = $.map(nodeIds, function(id) { return DCLS.NODE + getAttrSelector(ATTR.NODEID, id) }).join(',')
                var $nodes = $(nodeSel, $proof)
            } else {
                var $nodes = $E
            }
            // TODO: branch / branches
            $nodes.addClass(CLS.HIGHLIGHT)
        }
        if (!opts.stay) {
            setTimeout(function() { doHighlight({$proof: $proof, off: true})}, ANIM.SLOW)
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
            left  : +$el.attr(ATTR.LEFT),
            right : +$el.attr(ATTR.RIGHT),
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
            return REL.SELF
        }
        if (from.left < to.left && from.right > to.right) {
            return REL.ANCESTOR
        }
        if (from.left > to.left && from.right < to.right) {
            return REL.DESCENDANT
        }
        return REL.OUTSIDE
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
        consolidateRelated(REL.DESCENDANT, REL.ANCESTOR, trackObj, pos)
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
        consolidateRelated(REL.ANCESTOR, REL.DESCENDANT, trackObj, pos)
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
        var replaces = []
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
     * Get the status panel element(s) from the proof element(s).
     *
     * @param $proof The jQuery proof element(s).
     * @return The jQuery status panel element(s).
     */
    function getStatusFromProof($proof) {
        return $proof.prevAll(DCLS.STATUS)
    }

    /**
     * Get the proof element(s) from the status panel element(s).
     *
     * @param $status The jQuery status panel element(s).
     * @return The jQuery proof element(s).
     */
    function getProofFromStatus($status) {
        return $status.nextAll(DCLS.PROOF)
    }

    function getAttrSelector(attr, val, oper) {
        oper = oper || '='
        return '[' + attr + oper +'"' + val + '"]'
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
                    p = +$proof.attr(ATTR.CURWIDTHPCT) + (parseFloat(howMuch) || 0)
                }
                if (p < 0) {
                    p == 0
                }
                $proof.attr(ATTR.CURWIDTHPCT, p)
                $proof.css({width: p + '%'})
                break
            case 'step':
                var maxSteps = +$proof.attr(ATTR.NUMSTEPS)
                var n
                if (howMuch == 'beginning' || howMuch == 'start') {
                    n = 0
                } else if (howMuch == 'reset' || howMuch == 'end') {
                    n = maxSteps
                } else {
                    n = +$proof.attr(ATTR.STEP) + (parseInt(howMuch) || 0)
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

    $(document).ready(function() {

        var modkey = {
            shift : false,
            ctrl  : false,
            alt   : false
        }

        var $lastProof

        // monitor modifier keys
        $(document).on('keyup keydown', function(e) {
            modkey.shift = e.shiftKey
            modkey.ctrl  = e.metaKey || e.ctrlKey
            modkey.alt   = e.altKey
            modkey.ctrlalt = modkey.ctrl || modkey.alt
        })

        // load a click event handler for each proof in the document.
        $(DCLS.PROOF).on('click', function(e) {
            var $proof = $(this)
            var $target = $(e.target)
            var $status = getStatusFromProof($proof)
            var behavior = modkey.ctrlalt ? 'zoom' : 'inspect'
            switch (behavior) {
                case 'zoom':
                    var $structure = $target.closest(DCLS.STRUCTURE)
                    if ($structure.length) {
                        zoom($structure, $proof)
                    }
                    break
                case 'inspect':
                    break
                default :
                    break
            }
            $lastProof = $proof
        })

        // load a change event for the status panel
        $(DCLS.STATUS).on('change', function(e) {
            var $status = $(this)
            var $proof = getProofFromStatus($status)
            var $target = $(e.target)
            if ($target.hasClass(CLS.STEPINPUT)) {
                var n = +$target.val()
                var maxSteps = +$proof.attr(ATTR.NUMSTEPS)
                if (isNaN(n) || n < 0 || n > maxSteps) {
                    $target.val($proof.attr(ATTR.STEP))
                    return
                }
                step($proof, n)
            } else if ($target.hasClass(CLS.BRANCHFILTER)) {
                filterBranches($target.val(), $proof)
            }
            $lastProof = $proof
        })

        // load a click event for the status panel
        $(DCLS.STATUS).on('click', function(e) {
            var $status = $(this)
            var $proof = getProofFromStatus($status)
            var $target = $(e.target)
            if ($target.hasClass(CLS.STEPSTART)) {
                adjust($proof, 'step', 'start')
            } else if ($target.hasClass(CLS.STEPNEXT)) {
                adjust($proof, 'step', 1)
            } else if ($target.hasClass(CLS.STEPPREV)) {
                adjust($proof, 'step', -1)
            } else if ($target.hasClass(CLS.STEPEND)) {
                adjust($proof, 'step', 'end')
            } else if ($target.hasClass(CLS.FONTPLUS)) {
                adjust($proof, 'font', 1)
            } else if ($target.hasClass(CLS.FONTMINUS)) {
                adjust($proof, 'font', -1)
            } else if ($target.hasClass(CLS.FONTRESET)) {
                adjust($proof, 'font', 'reset')
            } else if ($target.hasClass(CLS.WIDTHPLUS)) {
                adjust($proof, 'width', 10)
            } else if ($target.hasClass(CLS.WIDTHPLUSPLUS)) {
                adjust($proof, 'width', 25)
            } else if ($target.hasClass(CLS.WIDTHMINUS)) {
                adjust($proof, 'width', -10)
            } else if ($target.hasClass(CLS.WIDTHMINUSMINUS)) {
                adjust($proof, 'width', -25)
            } else if ($target.hasClass(CLS.WIDTHRESET)) {
                adjust($proof, 'width', 'reset')
            } else if ($target.hasClass(CLS.STEPRULETARGET)) {
                var off = $target.hasClass(CLS.HIGHLIGHT) || $target.hasClass(CLS.STAY)
                doHighlight({$proof: $proof, stay: true, off: off, ruleTarget: true})
                $target.toggleClass(CLS.STAY)
            } else if ($target.hasClass(CLS.STEPRULENAME)) {
                var off = $target.hasClass(CLS.HIGHLIGHT) || $target.hasClass(CLS.STAY)
                doHighlight({$proof: $proof, stay: true, off: off, ruleStep: true})
                $target.toggleClass(CLS.STAY)
            }
            $lastProof = $proof
        })

        // shortcut keys
        $(document).on('keypress', function(e) {
            var $target = $(e.target)
            var isInput = $target.is(':input')
            if (!isInput && $lastProof) {
                var $proof = $lastProof
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
                        if ($proof.children(SEL.CANBRANCHFILTER).length) {
                            filterBranches('open', $proof)
                        }
                        break
                    case 'C':
                        if ($proof.children(SEL.CANBRANCHFILTER).length) {
                            filterBranches('closed', $proof)
                        }
                        break
                    case 'A':
                        if ($proof.children(SEL.CANBRANCHFILTER).length) {
                            filterBranches('all', $proof)
                        }
                        break
                    case 'r':
                    case 'R':
                        var stay = s == 'R'
                        doHighlight({$proof: $proof, stay: stay, ruleStep: true})
                        if (stay) {
                            $(DCLS.STEPRULENAME, getStatusFromProof($proof)).toggleClass(CLS.STAY)
                        }
                        break
                    case 't':
                    case 'T':
                        var stay = s == 'T'
                        doHighlight({$proof: $proof, stay: stay, ruleTarget: true})
                        if (stay) {
                            $(DCLS.STEPRULENAME, getStatusFromProof($proof)).toggleClass(CLS.STAY)
                        }
                        break
                    case 'Z':
                        zoom($proof.children(DCLS.STRUCTURE), $proof)
                        break
                    default:
                        break
                }
            }         
        })
    })

})();