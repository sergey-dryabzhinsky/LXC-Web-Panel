/**
 * UI script for index template
 * Used for home page and some modal pages
 *
 * @use jquery / bootstrap / $
 * @use colors.js
 * @use update-indicator.js
 *
 */

if (!LWP) window.LWP = {};
if (!LWP.UI) window.LWP.UI = {};
if (!LWP.UI.IndexPage) {
    window.LWP.UI.IndexPage = (function(){

        var proto = function()
        {
            this.su = 'No';
            this.token = '';
            this.scriptRoot = '';
            this.containersCount = 0;
        };

        /**
         * Set options:
         * {
         *      su: (string)            // 'Yes' / 'No'
         *      token: (string)
         *      scriptRoot: (string)
         *      containersCount: (int)
         * }
         *
         * @param options
         */
        proto.prototype.init = function(options)
        {
            this.su = options.su + '';                                  // convert to string
            this.token = options.token + '';                            // convert to string
            this.scriptRoot = options.scriptRoot + '';                  // convert to string
            this.containersCount = parseInt(options.containersCount);   // convert to int

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
            var self = this;
			$(function() {
				self.refreshFast();
				self.refreshMedium();
				self.refreshLong();
				self.checkVersion();

				setInterval(function(){
                    self.refreshFast();
                }, 10*1000);
				setInterval(function(){
                    self.refreshMedium();
                }, 60*1000);
				setInterval(function(){
                    self.refreshLong();
                }, 300*1000);
			});
        };

        proto.prototype._initEventListeners = function()
        {
            var self = this;
            if (self.su == 'Yes' && self.token) {
                $(function(){
                    $(".destroy").on('click',function(e){
                        $(".destroy-link").attr('href',"/action?action=destroy&token="+ self.token +"&name="+ $(this).data('container-name'));
                        $('#destroy').modal('show');
                    });

                    // Create CT
                    $('#advancedcreate').click(function(e){
                        e.preventDefault();
                        $('#advancedcreatediv').slideToggle();
                    });

                    // Clone CT
                    $('#advancedclone').click(function(e){
                        e.preventDefault();
                        $('#advancedclonediv').slideToggle();
                    });

                    // Create CT
                    $(".backingstore").on('change',function(){
                        var _val = $(this).val();
                        var _lvm = $(this).closest('.advanced-wrapper').find('.lvm');
                        var _directory = $(this).closest('.advanced-wrapper').find('.directory');

                        if( _val == 'lvm'){
                            _lvm.slideDown();
                            _directory.slideUp();
                        }
                        else if ( _val == 'directory' ){
                            _directory.slideDown();
                            _lvm.slideUp();
                        }
                        else{
                            _directory.slideUp();
                            _lvm.slideUp();
                        }
                    });

                    $('.modalbutton').on('click', function () {
                        $('.buttons-modal-footer').slideUp();
                        $('.loader-modal-footer').slideDown();
                    });

                    $("#selectTemplate").on('change',function(){
                        self.appendTemplateOptions();
                    });

                });
            }
        };

        proto.prototype.refreshMemoryHost = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_memory_host', function(data) {
                $('#memory-usage').text(data.used +' / '+ data.total +' MB').fadeIn();
                $('#memory-usage-bar').css({'width':data.percent+'%'});
                $('#memory-cache-usage-bar').css({'width':data.percent_cached+'%'});
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.refreshCPUHost = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.get(this.scriptRoot + '/_refresh_cpu_host', function(data) {
                $('#cpu-usage').text(data +'%').fadeIn();
                $('#cpu-usage-bar').css({'width':data +'%'});
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.refreshDiskHost = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_disk_host', function(data) {
                LWP.UI.UpdateIndicator.updateDone();
                if (!data) return;
                $('#disk-usage').text(data.used +' ('+ data.free +' free)').fadeIn();
                $('#disk-usage-bar').css({'width':data.percent});
            });
        };

        proto.prototype.refreshLvmHost = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_lvm_host', function(data) {
                LWP.UI.UpdateIndicator.updateDone();
                if (!data || !data.vgs) return;
                $.each(data.vgs, function(idx, vg){
                    $('#lvm-usage-'+vg.name).text(vg.used +' ('+ vg.free +' free) ' + vg.unit).fadeIn();
                    $('#lvm-usage-bar-'+vg.name).css({'width':vg.percent});
                });
            });
        };

        proto.prototype.refreshUptimeHost = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_uptime_host', function(data) {
                $('#uptime').text(data.day +' day(s) '+ data.time).fadeIn();
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.refreshMemoryContainers = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_memory_containers', function(data) {
                $.each(data.data, function(idx, item){
                    var el = $('#'+item.name+' span');
                    el.text(item.memusg+' of '+item.max_memusg+' MB');
                    el[0].className = el[0].className.replace(
                            /label\-(success|warning|important|none)/g,
                            'label-'+value_color(item.memusg, item.max_memusg));
                });
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.refreshDiskContainers = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_disk_containers', function(data) {
                $.each(data.data, function(idx, item){
                    var el = $('#disk_'+item.name+' span');
                    el.text(item.diskusg.used+' of '+item.diskusg.total);
                    el[0].className = el[0].className.replace(
                            /label\-(success|warning|important|none)/g,
                            'label-'+percent_color(item.diskusg.percent));
                });
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

		proto.prototype.refreshCpuContainers = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_refresh_cpu_containers', function(data) {
                $.each(data.data, function(idx, item){
                    var el = $('#cpu_'+item.name+' span');
                    el.text(item.cpu+' %');
                    el[0].className = el[0].className.replace(
                            /label\-(success|warning|important|none)/g,
                            'label-'+percent_color(item.cpu));
                });
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        proto.prototype.checkVersion = function()
        {
            LWP.UI.UpdateIndicator.updateStart();
            $.getJSON(this.scriptRoot + '/_check_version', function(data) {
                var $version = $('#vernumber');
                if (data.latest > data.current) {
                    $version.text(data.latest);
                    // Better blink
                    $version.parent('small.hide')
                        .fadeTo(100, 1)
                        .fadeTo(500, 0.5)
                        .fadeTo(500, 1)
                        .fadeTo(500, 0.5)
                        .fadeTo(500, 1)
                        .fadeTo(500, 0.5)
                        .fadeTo(500, 1)
                        .fadeTo(5000, 0.5)
                    ;
                    $version.parent('small.hide').hover(
                        function() {
                            $(this).fadeTo(400, 1);
                        },
                        function() {
                            $(this).fadeTo(400, 0.5);
                        });
                } else {
                    $version.text(data.current);
                }
                LWP.UI.UpdateIndicator.updateDone();
            });
        };

        // Call every 10-15 seconds
        proto.prototype.refreshFast = function()
        {
            var self = this;
            this.refreshMemoryHost();
            this.refreshMemoryContainers();
            // Slide by time to not cross with other requests.
            setTimeout(function(){
                self.refreshCPUHost();
            }, 200);
            setTimeout(function(){
                self.refreshCpuContainers();
            }, 400);
        };

        // Call every minute
        proto.prototype.refreshMedium = function()
        {
            this.refreshUptimeHost();
        };

        // Call every 5 or more minutes
        proto.prototype.refreshLong = function()
        {
            this.refreshDiskHost();
            this.refreshLvmHost();
            this.refreshDiskContainers();
        };

        proto.prototype.appendTemplateOptions = function()
        {
            var selT = $('select#selectTemplate');
            if (!selT) return;

            var _val = selT.val();
            $.getJSON(this.scriptRoot + '/_get_template_options_' + _val, function(data) {
                var _archSelect = $('#selectTemplateArch');
                var _releaseSelect = $('#selectTemplateRelease');

                _archSelect.empty().append(function(){
                    var output = '';
                        output += '<option value="">-- System default --</option>';
                    $.each(data.arch, function(index, value){
                        if (value == data.system.arch) {
                            output += '<option value="'+value+'" selected="selected">'+value+'</option>';
                        } else {
                            output += '<option value="'+value+'">'+value+'</option>';
                        }
                    });
                    return output;
                });
                _releaseSelect.empty().append(function(){
                    var output = '';
                        output += '<option value="">-- System default --</option>';
                    $.each(data.releases, function(index, value){
                        if (value == data.system.release) {
                            output += '<option value="'+value+'" selected="selected">'+value+'</option>';
                        } else {
                            output += '<option value="'+value+'">'+value+'</option>';
                        }
                    });
                    return output;
                });
            });
        };

        return new proto;
    })();
}