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
        $('.premises').on('keypress', 'input.premise', function(){
            setTimeout(ensureEmptyPremise, 0)
        })
    })
})(jQuery);