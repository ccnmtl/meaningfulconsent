(function() {
    Participant = Backbone.Model.extend({
        url: '/api/participants/'
    });
    
    ParticipantCollection = Backbone.Collection.extend({
        url: '/api/participants/',
        model: Participant,
        parse: function(response) {
            this.next = response.next;
            this.previous = response.previous;
            return response.results || response;
        },
        get_by_username: function(value) {
            for (var i=0; i < this.length; i++) {
                var item = this.at(i);
                var user = item.get('user');
                if (value === user.username) {
                    return item;
                }
            }
        },
    });
    
    window.formatDate = function(dateString) {
        var dt = new Date(dateString);
        return dt.toLocaleDateString() + " " + dt.toLocaleTimeString();
    };
    
    window.FacilitatorView = Backbone.View.extend({
        events: {
            'click .btn-archive': 'onArchiveParticipant',
            'click .btn-confirm-archive': 'onConfirmArchiveParticipant',
            'click .create-participant': 'onCreateParticipant',
            'click .btn-edit-notes': 'onEditParticipantNotes',
            'click .btn-print': 'onPrint',
            'click .btn-save-notes': 'onSaveParticipantNotes',
            'click .btn-verify-record': 'onVerifyRecording',
            'shown.bs.modal #notes-modal': 'onShowParticipantNotes',
            'hidden.bs.modal #notes-modal': 'onHideParticipantNotes'      
        },
        initialize: function(options) {
            _.bindAll(this,
                      'render',
                      'onArchiveParticipant',
                      'onConfirmArchiveParticipant',
                      'onCreateParticipant',
                      'onEditParticipantNotes',
                      'onPrint',
                      'onSaveParticipantNotes',
                      'onVerifyRecording');
            
            var html = jQuery("#participant-sessions-template").html();
            this.template = _.template(html);
            this.el_sessions = options.el_sessions;
            
            jQuery('#launch-demo-popover').popover();            
            
            this.max_sessions = options.max_sessions;
            
            this.participants = new ParticipantCollection();           
            this.participants.on("reset", this.render);

            this.participants.fetch({
                data: {page_size: this.max_sessions},
                processData: true,
                reset: true
            });
        },
        render: function() {
            var context = {'participants': this.participants.toJSON()};
            context.next = this.participants.next;
            context.previous = this.participants.previous;
            jQuery(this.el_sessions).html(this.template(context));
            
            if (this.participants.length > 0) {
                jQuery(".administration").show();
            } else {
                jQuery(".administration").hide();
            }
            
            jQuery(this.el_sessions).find('table').tablesorter({
                sortList: [[2,1]],
                dateFormat:'mm/dd/yyyy hh:mm:ss tt'
            });
        },
        onArchiveParticipant: function(evt) {
            var username = jQuery(evt.currentTarget).data('username');
            var msg = "Are you sure you want to archive " + username + "?";
            
            jQuery("#confirm-modal").find('.modal-body').html(msg);
            jQuery("#confirm-modal").find('.btn-confirm-archive').data('username', username);
            
            jQuery("#confirm-modal").modal({
                'show': true,
                'backdrop': 'static',
                'keyboard': false
            });
        },
        onConfirmArchiveParticipant: function(evt) {
            var self = this;
            var username = jQuery(evt.currentTarget).data('username');

            jQuery("#confirm-modal").modal('hide');
            jQuery("#confirm-modal").find('.modal-body').html('');
            jQuery("#confirm-modal").find('.btn-confirm-archive').data('username', '');
            
            jQuery.ajax({
                type: "post",
                url: '/participant/archive/',
                data: {username: username},
                success: function() {
                    self.participants.reset();
                    self.participants.fetch({
                        data: {page_size: self.max_sessions},
                        processData: true,
                        reset: true
                    });
                },
                error: function() {
                    alert("An error occurred. Please try again");
                }
            });            
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
        onEditParticipantNotes: function(evt) {
            var username = jQuery(evt.currentTarget).data('username');
            jQuery("#notes-modal").find('.btn-save-notes').data('username', username);
            
            var p = this.participants.get_by_username(username);
            jQuery("#notes-modal").find('textarea.notes').val(p.get('notes'));
            
            jQuery("#notes-modal").modal({
                'show': true,
                'backdrop': 'static',
                'keyboard': false
            });
        },
        onPrint: function(evt) {
            alert('onPrint');
        },
        onSaveParticipantNotes: function(evt) {
            var self = this;
            var username = jQuery(evt.currentTarget).data('username');
            var notes = jQuery("textarea.notes").val();
            
            jQuery("#notes-modal").modal('hide');

            jQuery.ajax({
                type: "post",
                url: '/participant/note/',
                data: {username: username, notes: notes},
                success: function() {
                    var p = self.participants.get_by_username(username);
                    p.set('notes', notes);
                },
                error: function() {
                    alert("An error occurred. Please try again");
                }
            });            
        },
        onShowParticipantNotes: function() {
            jQuery("#notes-modal").find('textarea.notes').focus();
        },
        onHideParticipantNotes: function() {
            jQuery("#notes-modal").find('.btn-save-notes').data('username', '');
            jQuery("#notes-modal").find('textarea.notes').val('');
        },
        onVerifyRecording: function(evt) {
            var parent = jQuery(evt.target).parents('div.modal-footer')[0]; 
            jQuery(parent).fadeOut(function() {
                jQuery(parent).next().show(); 
            });
        }
    });
})();