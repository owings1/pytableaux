;(function($){

    $(document).ready(function(){

        var app = $.parseJSON($('script.app').html())
        var premiseTemplate = $('#premiseTemplate').html()
        var predicateRowTemplate = $('#predicateRowTemplate').html()

        function render(html, vars) {
            if (vars) {
                $.each(vars, function(name, val) {
                    html = html.replace(new RegExp('{' + name + '}', 'g'), val)
                })
            }
            return html
        }

        function addPremise(value, status, message) {
            var premiseNum = $('input.premise').length + 1
            $('.premises').append(render(premiseTemplate, {
                n       : premiseNum++,
                value   : value   || '',
                status  : status  || '',
                message : message || ''
            }))
        }

        function currentNotation() {
            return $('#notation').val()
        }

        function addEmptyPremise() {
            addPremise()
        }

        function clearPremises() {
            $('.input.premise').remove()
        }

        function clearConclusion() {
            $('#conclusion').val('')
        }

        function clearArgument() {
            clearPremises()
            clearConclusion()
        }

        function addPredicate(index, subscript, name, arity) {
            var thisNotation = currentNotation()
            var html = ''
            $.each(app.notation_user_predicate_symbols, function(notation, symbols) {
                var classes = ['predicateSymbol', 'notation-' + notation]
                if (notation != thisNotation)
                    classes.push('hidden')
                html += '<span class="' + classes.join(' ') + '">'
                html += $('<div/>').text(symbols[index]).html()
                if (subscript > 0)
                    html += '<span class="subscript">' + subscript + '</span>'
                html += '</span>'
            })
            $('table.predicates tbody').append(render(predicateRowTemplate, { 
                index       : index,
                subscript   : subscript,
                name        : name || ('Predicate ' + ($('input.predicateSymbol').length + 1)),
                arity       : arity || '',
                symbol_html : html
            }))
        }

        function addEmptyPredicate() {
            var $symbols   = $('input.predicateSymbol')
            var numSymbols = $symbols.length
            var index      = 0
            var subscript  = 0
            if (numSymbols > 0) {
                var last = $symbols.last().val().split('.')
                index = +last[0] + 1
                subscript = +last[1]
                if (index == app.num_predicate_symbols) {
                    index = 0
                    subscript += 1
                }
            }
            addPredicate(index, subscript)
        }

        function clearPredicates() {
            $('tr.userPredicate').remove()
        }

        function hasEmptyPremise() {
            var hasEmpty = false
            $('input.premise').each(function(i){
                if (!$(this).val()) {
                    hasEmpty = true
                    return false
                }
            })
            return hasEmpty
        }

        function hasEmptyPredicate() {
            var hasEmpty = false
            $('input.arity').each(function(i) {
                if (!$(this).val()){
                    hasEmpty = true
                    return false
                }
            })
            return hasEmpty
        }

        function ensureEmptyPremise() {
            if (!hasEmptyPremise())
                addEmptyPremise()
        }

        function ensureEmptyPredicate() {
            if (!hasEmptyPredicate())
                addEmptyPredicate()
        }

        function refreshNotation() {
            var notation = currentNotation()
            $('.lexicons .lexicon').hide()
            $('#Lexicon_' + notation).show()
            $('.predicateSymbol').hide()
            $('.predicateSymbol.notation-' + notation).show()
            if ($('#example_argument').val())
                refreshExampleArgument()
        }

        function refreshExampleArgument() {
            clearPredicates()
            clearArgument()
            var $me = $('#example_argument')
            var argName = $me.val()
            if (!argName) {
                ensureEmptyPremise()
                ensureEmptyPredicate()
                return
            }
            var notation = currentNotation()
            var arg = app.example_arguments[argName][notation]
            $.each(arg.premises, function(i, value) {
                addPremise(value)
            })
            $('#conclusion').val(arg.conclusion)
            $.each(app.example_predicates, function(i, pred) {
                addPredicate(pred[1], pred[2], pred[0], pred[3])
            })
        }

        function refreshStatuses() {
            $('form.argument input.sentence').each(function() {
                var $status = $(this).closest('div.input').find('.status')
                var str = $(this).val()
                if (str || $(this).hasClass('conclusion')) {
                    var hash = hashString(str + '.' + currentNotation())
                    if (+$status.attr('data-hash') === hash)
                        return
                    $status.attr('data-hash', hash)
                    $.ajax({
                        url  : '/parse',
                        type : 'post',
                        data : {
                            sentence               : str,
                            notation               : currentNotation(),
                            user_predicate_names   : $('input.predicateName').map(getVal).get(),
                            user_predicate_arities : $('input.arity').map(getVal).get(),
                            user_predicate_symbols : $('input.predicateSymbol').map(getVal).get()
                        },
                        success: function(err) {
                            if (err) {
                                $status.removeClass('good').addClass('bad')
                                $status.attr('title', err)
                            } else {
                                $status.removeClass('bad').addClass('good')
                                $status.attr('title', '')
                            }
                        }
                    })
                } else {
                    $status.removeClass('bad good')
                    $status.attr('title', '')
                    $status.attr('data-hash', '')
                }
            })
        }

        function getVal() {
            return $(this).val()
        }

        // from: http://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript-jquery
        function hashString(str) {
            var hash = 0, i, chr
            if (str.length === 0)
                return hash
            for (i = 0; i < str.length; i++) {
                chr   = str.charCodeAt(i)
                hash  = ((hash << 5) - hash) + chr
                hash |= 0; // Convert to 32bit integer
            }
            return hash
        }

        $('form.argument')
          .on('keyup focus', 'input.premise, #conclusion', ensureEmptyPremise)
          .on('keyup', 'input.predicateName, input.arity', ensureEmptyPredicate)
          .on('change', '#example_argument', refreshExampleArgument)
          .on('change', '#notation', refreshNotation)
          .on('change', 'input.sentence', refreshStatuses)

        ensureEmptyPremise()
        ensureEmptyPredicate()
        refreshNotation()

    })
})(jQuery);