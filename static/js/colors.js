/**
 * Common functions to convert values info css-classes or styles
 */

function value_color(value, max_value){
    if (value > 0) {
        // 80% - ok
        if (0 < value && value < max_value*0.8)
            return 'success';
        // 90% - not ok
        else if (max_value*0.8 <= value && value < max_value*0.9)
            return 'warning';
        else
            return 'important';
    }
    return 'none';
}

function percent_color(value){
    if (value > 0) {
        // 80% - ok
        if (0 < value && value < 80)
            return 'success';
        // 90% - not ok
        else if (80 <= value && value < 90)
            return 'warning';
        else
            return 'important';
    }
    return 'none';
}
