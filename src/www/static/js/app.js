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
        
        // window.pytableaux = {}
        // $('script.app').each(function() {
        //     window.pytableaux[$(this).attr('id')] = $.parseJSON($(this).html())
        // })
        var premiseNum = $('input.premise').length + 1
        var premiseTemplate = $('#premiseTemplate').html()
        function addPremise() {
            $('.premises').append(render(premiseTemplate, {n: premiseNum++ }))
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
        function ensureEmptyPremise() {
            if (!hasEmptyPremise())
                addPremise()
        }
        ensureEmptyPremise()
        $('.premises').on('keyup', 'input.premise', ensureEmptyPremise)
        $('form.argument').on('change', 'input.sentence', function(){
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
        }).trigger('change')
    })
})(jQuery);