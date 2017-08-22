(function() {
    var PAGE_SIZE = 20;

    window.Participant = Backbone.Model.extend({
        url: '/api/participants/'
    });

    window.ParticipantCollection = Backbone.Collection.extend({
        urlRoot: '/api/participants/',
        model: window.Participant,
        page: 1,
        context: function() {
            var context = {'participants': this.toJSON()};

            context.next = this.next;
            context.previous = this.previous;
            context.pages = Math.ceil(this.total / PAGE_SIZE);
            context.page = this.page;

            if (this.hasOwnProperty('filterBy')) {
                context.filterBy = this.filterBy;
            } else {
                context.filterBy = '';
            }

            return context;
        },
        getByUsername: function(value) {
            for (var i = 0; i < this.length; i++) {
                var item = this.at(i);
                var user = item.get('user');
                if (value === user.username) {
                    return item;
                }
            }
        },
        refresh: function() {
            this.fetch({
                data: {page_size: this.max_sessions},
                processData: true,
                reset: true
            });
        },
        parse: function(response) {
            this.total = response.count;
            this.next = response.next;
            this.previous = response.previous;
            return response.results || response;
        },
        url: function() {
            var url = this.urlRoot + '?page=' + this.page;
            if (this.hasOwnProperty('filterBy')) {
                url += '&username=' + this.filterBy;
            }
            return url;
        }
    });

    window.formatDate = function(dateString) {
        var dt = new Date(dateString);
        return dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString();
    };

    window.FacilitatorView = Backbone.View.extend({
        events: {
            'click .btn-archive': 'onArchiveParticipant',
            'click #participant-clear-button': 'onClearParticipantSearch',
            'click .btn-confirm-archive': 'onConfirmArchiveParticipant',
            'click .create-participant': 'onCreateParticipant',
            'click .btn-edit-notes': 'onEditParticipantNotes',
            'hidden.bs.modal #notes-modal': 'onHideParticipantNotes',
            'click .btn-save-notes': 'onSaveParticipantNotes',
            'click #participant-search-button': 'onSearchParticipants',
            'shown.bs.modal #notes-modal': 'onShowParticipantNotes',
            'click a.page-link': 'onTurnPage',
            'click .btn-verify-record': 'onVerifyRecording'
        },
        initialize: function(options) {
            _.bindAll(this, 'render', 'onArchiveParticipant',
                'onClearParticipantSearch', 'onConfirmArchiveParticipant',
                'onCreateParticipant', 'onEditParticipantNotes',
                'onSaveParticipantNotes', 'onSearchParticipants',
                'onTurnPage', 'onVerifyRecording');

            var html = jQuery('#participant-sessions-template').html();
            this.template = _.template(html);
            this.el_sessions = options.el_sessions;

            jQuery('#launch-demo-popover').popover();

            this.participants = new window.ParticipantCollection();
            this.participants.max_sessions = options.max_sessions;
            this.participants.on('reset', this.render);

            this.participants.refresh();
        },
        render: function() {
            var ctx = this.participants.context();

            jQuery(this.el_sessions).html(this.template(ctx));

            if (this.participants.length > 0) {
                jQuery('.participant-sessions.recent').show();
            } else {
                jQuery('.participant-sessions.recent').hide();
            }

            if (this.participants.hasOwnProperty('filterBy')) {
                jQuery('#participant-clear-button').show();
            } else {
                jQuery('#participant-clear-button').hide();
            }

            jQuery('#participant-search-button').button('reset');
            jQuery('#participant-clear-button').button('reset');
        },
        onArchiveParticipant: function(evt) {
            var username = jQuery(evt.currentTarget).data('username');
            var msg = 'Are you sure you want to archive ' + username + '?';

            jQuery('#confirm-modal').find('.modal-body').html(msg);
            jQuery('#confirm-modal').find('.btn-confirm-archive')
                .data('username', username);

            jQuery('#confirm-modal').modal({
                'show': true,
                'backdrop': 'static',
                'keyboard': false
            });
        },
        onClearParticipantSearch: function(evt) {
            evt.preventDefault();
            jQuery('#participant-clear-button').button('loading');
            jQuery('.help-block').hide();
            jQuery('input[name="participant-search"]').val('');
            this.participants.page = 1;
            delete this.participants.filterBy;
            this.participants.refresh();
            return false;
        },
        onConfirmArchiveParticipant: function(evt) {
            var self = this;
            var username = jQuery(evt.currentTarget).data('username');

            jQuery('#confirm-modal').modal('hide');
            jQuery('#confirm-modal').find('.modal-body').html('');
            jQuery('#confirm-modal').find('.btn-confirm-archive')
                .data('username', '');

            jQuery.ajax({
                type: 'post',
                url: '/participant/archive/',
                data: {username: username},
                success: function() {
                    self.participants.refresh();
                },
                error: function() {
                    alert('An error occurred. Please try again');
                }
            });
        },
        onCreateParticipant: function(evt) {
            var self = this;
            jQuery.post('/participant/create/',
                {},
                function(data) {
                    jQuery('span.participant-id').html(data.user.username);
                    jQuery('input.participant-id').val(data.user.username);

                    jQuery(self.el).find('.create-participant-modal').modal({
                        'show': true,
                        'backdrop': 'static',
                        'keyboard': false
                    });
                });
        },
        onEditParticipantNotes: function(evt) {
            var username = jQuery(evt.currentTarget).data('username');
            jQuery('#notes-modal').find('.btn-save-notes')
                .data('username', username);

            var p = this.participants.getByUsername(username);
            jQuery('#notes-modal').find('textarea.notes').val(p.get('notes'));

            jQuery('#notes-modal').modal({
                'show': true,
                'backdrop': 'static',
                'keyboard': false
            });
        },
        onHideParticipantNotes: function() {
            jQuery('#notes-modal').find('.btn-save-notes').data('username', '');
            jQuery('#notes-modal').find('textarea.notes').val('');
        },
        onSaveParticipantNotes: function(evt) {
            var self = this;
            var username = jQuery(evt.currentTarget).data('username');
            var notes = jQuery('textarea.notes').val();

            jQuery('#notes-modal').modal('hide');

            jQuery.ajax({
                type: 'post',
                url: '/participant/note/',
                data: {username: username, notes: notes},
                success: function() {
                    var p = self.participants.getByUsername(username);
                    p.set('notes', notes);
                },
                error: function() {
                    alert('An error occurred. Please try again');
                }
            });
        },
        onSearchParticipants: function(evt) {
            evt.preventDefault();

            var filterBy = jQuery('input[name="participant-search"]').val();
            if (filterBy.length < 1) {
                jQuery('.help-block').show();
            } else {
                jQuery('#participant-search-button').button('loading');
                jQuery('.help-block').hide();
                this.participants.page = 1;
                this.participants.filterBy = filterBy;
                this.participants.refresh();
            }

            return false;
        },
        onShowParticipantNotes: function() {
            jQuery('#notes-modal').find('textarea.notes').focus();
        },
        getParameterByName: function(name, url) {
            name = name.replace(/[[]/, '\\[').replace(/[\]]/, '\\]');
            // eslint-disable-next-line security/detect-non-literal-regexp
            var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
            var results = regex.exec(url);
            return results === null ? '' : decodeURIComponent(
                results[1].replace(/\+/g, ' '));
        },
        onTurnPage: function(evt) {
            evt.preventDefault();

            if (jQuery(evt.currentTarget).hasClass('disabled')) {
                return false;
            }

            // parse the page number out of the url
            var href = jQuery(evt.currentTarget).attr('href');
            var page = this.getParameterByName('page', href);
            if (page !== null) {
                this.participants.page = parseInt(page, 10);
                this.participants.refresh();
            }
            return false;
        },
        onVerifyRecording: function(evt) {
            var parent = jQuery(evt.target).parents('div.modal-footer')[0];
            jQuery(parent).fadeOut(function() {
                jQuery(parent).next().show();
            });
        }
    });
})();
