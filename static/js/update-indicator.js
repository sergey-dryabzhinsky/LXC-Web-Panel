/**
 * Use one implementation of update indicator for all pages
 */

if (!window.LWP) LWP = {};
if (!window.LWP.UI) LWP.UI = {};
if (!window.LWP.UI.UpdateIndicator) {

    LWP.UI.UpdateIndicator = (function(){

        var proto = function()
        {
            this.updating = 0;
        };

        /**
         * Show loading indicator and increment active updates counter
         * Shows only if no updates running
         */
        proto.prototype.updateStart = function()
        {
            if (!this.updating) {
                $('#home-load').fadeIn();
            }
            this.updating++;
        };

        /**
         * Decrement updates counter
         * Hide loading indicator if no other updates running
         */
        proto.prototype.updateDone = function()
        {
            if (this.updating) {
                this.updating--;
            }
            if (!this.updating) {
                $('#home-load').fadeOut();
            }
        };

        return new proto;
    })();

}
