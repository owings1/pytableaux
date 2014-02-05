;(function($){
    
    function render(html, vars) {
        if (vars) {
            $.each(vars, function(name, val) {
                html = html.replace(new RegExp('{' + name + '}', 'g'), val)
            })
        }
        return html
    }
    $(document).ready(function(){
        
        var app = $.parseJSON($('script.app').html())
        var premiseNum = $('input.premise').length + 1
        var premiseTemplate = $('#premiseTemplate').html()
        var predicateRowTemplate = $('#predicateRowTemplate').html()
        function addPremise() {
            $('.premises').append(render(premiseTemplate, {n: premiseNum++ }))
        }
        function addPredicate() {
            var $symbols = $('input.predicateSymbol')
            var numSymbols = $symbols.length
            var next
            if (numSymbols == 0)
                next = [0, 0]
            else {
                var last = $symbols.last().val().split('.')
                next = [ +last[0] + 1, +last[1]]
                if (next[0] == app.num_user_predicate_symbols)
                    next = [0, +last[1] + 1]
            }
            var html = ''
            var currentNotation = $('#notation').val()
            $.each(app.notation_user_predicate_symbols, function(notation, symbols) {
                html += '<span class="predicateSymbol notation-' + notation + (notation == currentNotation ? '' : ' hidden') + '">'
                console.log(symbols[next[0]])
                html += $('<div/>').text(symbols[next[0]]).html()
                if (next[1])
                    html += '<span class="subscript">' + next[1] + '</span>'
                html += '</span>'
            })
            $('table.predicates tbody').append(render(predicateRowTemplate, { 
                index: next[0],
                subscript: next[1],
                name: 'Predicate ' + (numSymbols + 1),
                arity: '',
                symbol_html: html 
            }))
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
                addPremise()
        }
        function ensureEmptyPredicate() {
            if (!hasEmptyPredicate())
                addPredicate()
        }
        ensureEmptyPremise()
        ensureEmptyPredicate()
        $('form.argument')
          .on('keyup', 'input.premise', ensureEmptyPremise)
          .on('keyup', 'input.predicateName, input.arity', ensureEmptyPredicate)
          .on('change', 'input.sentence', function(){
            var $status = $(this).closest('div.input').find('.status')
            var str = $(this).val()
            if (str || $(this).hasClass('conclusion')) {
                $.ajax({
                    url: '/parse',
                    data: {
                        sentence: str,
                        notation: $('#notation').val()
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
            }
        })
        $('#notation').on('change', function() {
            var notation = $(this).val()
            $('.lexicons .lexicon').hide()
            $('#Lexicon_' + notation).show()
            $('.predicateSymbol').hide()
            $('.predicateSymbol.notation-' + notation).show()
        }).trigger('change')
    })
})(jQuery);