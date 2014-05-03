(function() {
    window.FacilitatorView = Backbone.View.extend({
        events: {
            'click .create-participant': 'onCreateParticipant',
            'click .btn-verify-record': 'onVerifyRecording'
        },
        initialize: function(options) {
            _.bindAll(this, 'onCreateParticipant', 'onVerifyRecording');
        },
        onCreateParticipant: function(evt) {
            var self = this;
            jQuery.post("/participant/create/",
                {},
                function(data) {
                    jQuery("span.participant-id").html(data.user.username);
                    jQuery("input.participant-id").val(data.user.username);

                     jQuery(self.el).find('.create-participant-modal').modal({
                         'show': true,
                         'backdrop': 'static',
                         'keyboard': false
                     });
                 });
        },
        onVerifyRecording: function(evt) {
            var parent = jQuery(evt.target).parents('div.modal-footer')[0]; 
            jQuery(parent).fadeOut(function() {
                jQuery(parent).next().show(); 
            });
        }
    });
})();