(function() {
    window.ParticipantView = Backbone.View.extend({
        events: {
            'click li.pause-session a': 'onPauseSession',
            'click a.disabled': 'onClickDisabledElement',
            'click .nav li.disabled a': 'onClickDisabledElement'
        },
        initialize: function(options) {
            _.bindAll(this,
                    'onPauseSession',
                    'onClickDisabledElement',
                    'onEnableNextButton');

            setTimeout(this.onEnableNextButton, 20000);
        },
        onClickDisabledElement: function(evt) {
            evt.preventDefault();
            return false;
        },
        onEnableNextButton: function() {
            jQuery("a.btn-next").removeAttr("disabled");
        },
        onPauseSession: function(evt) {
            jQuery(this.el).find('.pause-session-modal').modal({
                'show': true,
                'backdrop': 'static',
                'keyboard': false
            });            
            return false;
        }
    });
})();