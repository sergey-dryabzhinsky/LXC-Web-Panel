/**
 * UI script for edit template
 * Used for edit page and some modal pages
 *
 * @use jquery / bootstrap / $
 * @use colors.js
 * @use update-indicator.js
 *
 */

if (!window.LWP) LWP = {};
if (!window.LWP.UI) LWP.UI = {};
if (!window.LWP.UI.EditPage) {
    LWP.UI.EditPage = (function(){

        var proto = function()
        {
            this.status = 'STOPPED';
            this.container = '';
            this.scriptRoot = '';
        };

        /**
         * Set options:
         * {
         *      status: (string)            // 'RUNNING' / 'STOPPED' ...
         *      container: (string)         // Container name
         *      scriptRoot: (string)        // URI prefix for LWP
         * }
         *
         * @param options
         */
        proto.prototype.init = function(options)
        {
            this.status = options.status + '';          // convert to string
            this.container = options.container + '';    // convert to string
            this.scriptRoot = options.scriptRoot + '';    // convert to string

            this._initTimers();
            this._initEventListeners();
            this._initUI();
        };

        proto.prototype._initUI = function()
        {
            var self = this;
            $(function(){
                if (self.su == 'Yes' && self.token) {
                    self.appendTemplateOptions();
                    if (self.containersCount == 0) {
                        $('#createCT').modal('show');
                    }
                }
            });
        };

        proto.prototype._initTimers = function()
        {
            if (this.status == 'STOPPED') {
                return;
            }

            var self = this;
			$(function() {
				self.refreshFast();
				self.refreshLong();

				setInterval(function(){
                    self.refreshFast();
                }, 10*1000);
				setInterval(function(){
                    self.refreshLong();
                }, 300*1000);
			});
        };

        proto.prototype._initEventListeners = function()
        {
            var self = this;

            $(function(){

                $('#sliderMemlimit').change(function(){
                    self.updateMemInput('inputMemlimit', $(this).val(), $(this).data('total'));
                });
                $('#inputMemlimit').change(function(){
                    self.updateMemInput('sliderMemlimit', $(this).val());
                });

                $('#sliderSwlimit').change(function(){
                    self.updateMemInput('inputSwlimit', $(this).val(), $(this).data('total'));
                });
                $('#inputSwlimit').change(function(){
                    self.updateMemInput('sliderSwlimit', $(this).val());
                });

                // Network flags
                var network = $("#network");
                $(".switch-network-flags").on('switch-change', function(e, data){
                    if(data.value){
                        $(data.el).val('up');
                        network.delay(350).slideDown();
                    }
                    else{
                        $(data.el).val('down');
                        network.delay(350).slideUp();
                    }
                });

            });
        };

        proto.prototype.refreshMemory = function()
        {
            var self = this;
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_memory_' + this.container, function(data) {
                var el = $('#'+self.container+' span');
                el.text(data.memusg+' MB');
                el[0].className = el[0].className.replace(
                        /label\-(success|warning|important|none)/g,
                        'label-'+value_color(data.memusg, data.max_memusg));
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.refreshDisk = function()
        {
            var self = this;
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_disk_'+this.container, function(data) {
                var el = $('#disk_'+self.container+' span');
                el.text(data.diskusg.used);
                el[0].className = el[0].className.replace(
                        /label\-(success|warning|important|none)/g,
                        'label-'+percent_color(data.diskusg.percent));
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.refreshCPU = function()
        {
            var self = this;
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_cpu_'+this.container, function(data) {
                var el = $('#cpu_'+self.container+' span');
                el.text(data.cpu + ' %');
                el[0].className = el[0].className.replace(
                        /label\-(success|warning|important|none)/g,
                        'label-'+percent_color(data.cpu));
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        // Call every 10-15 seconds
        proto.prototype.refreshFast = function()
        {
            var self = this;
            this.refreshMemory();
            // Slide by time to not cross with other requests.
            setTimeout(function(){
                self.refreshCPU();
            }, 200);
        };

        // Call every 5 or more minutes
        proto.prototype.refreshLong = function()
        {
            this.refreshDisk();
        };


        proto.prototype.updateMemInput = function(elem, value, mem_total)
        {
            if (value < mem_total) {
                $('#' + elem).val(value).show().next('.help-inline').text('MB');
            } else {
                $('#' + elem).val(mem_total).hide().next('.help-inline').text('Unlimited');
            }
        };

        proto.prototype.updateMemSlider = function(elem, value)
        {
            $('#' + elem).val(value);
        };

        return new proto;
    })();
}
