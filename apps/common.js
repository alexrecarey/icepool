
// Clips all inputs to their min/max values.
// Returns true iff any input was changed.
function validateInputs() {
    let changed = false;
    $("input").each(function() {
        let originalVal = parseInt($(this).val());
        let maxVal = parseInt($(this).attr('max'));
        let minVal = parseInt($(this).attr('min'));
        if (originalVal > maxVal) {
            $(this).val(maxVal);
            changed = true;
        } else if (originalVal < minVal) {
            $(this).val(minVal);
            changed = true;
        }
    });
    
    return changed;
}

// Sets inputs based on search query by id (assumed to be equal to name).
function setInputsFromSearchQuery() {
    let searchParams = new URLSearchParams(window.location.search);
    searchParams.forEach(function(value, key) {
        let n = parseInt(value);
        let field = $("#" + key);
        if (!(n >= field.attr('min') && n <= field.attr('max'))) {
            return;
        }
        field.val(value);
    });
}

// Updates search query based on all forms.
function updateSearchQueryFromForms() {
    let searchParams = $("form").serialize();
    history.replaceState(null, "", "?" + searchParams);
}
