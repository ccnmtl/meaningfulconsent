(function() {
    window.ParticipantView = Backbone.View.extend({
        events: {
            'click li.pause-session a': 'onPauseSession'
        },
        initialize: function(options) {
            _.bindAll(this, 'onPauseSession');
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