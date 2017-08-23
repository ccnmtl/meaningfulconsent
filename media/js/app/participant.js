(function() {
    window.ParticipantPageView = Backbone.View.extend({
        events: {
            'click a.pause-session': 'onPauseSession',
            'click button.change-language': 'onChangeLanguage',
            'click .next a.btn-choose-language': 'onChooseLanguage',
            'click .next a.btn-submit-page': 'onNextPage'
        },
        initialize: function(options) {
            _.bindAll(this,
                'isFormComplete',
                'isInteractive',
                'onChangeLanguage',
                'onPauseSession',
                'onPlayerReady',
                'onPlayerStateChange',
                'onYouTubeIframeAPIReady',
                'onNextPage',
                'onSubmitPage',
                'onSubmitQuiz',
                'onSubmitVideoData',
                'recordSecondsViewed');

            this.participant_id = options.participant_id;
            this.seconds_viewed = 0;

            // load the youtube iframe api
            window.onYouTubeIframeAPIReady = this.onYouTubeIframeAPIReady;
            window.onPlayerReady = this.onPlayerReady;
            window.onPlayerStateChange = this.onPlayerStateChange;

            var tag = document.createElement('script');
            // eslint-disable-next-line  scanjs-rules/assign_to_src
            tag.src = 'https://www.youtube.com/iframe_api';
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

            // Customer popover work to support click out on the iPad
            var $popover = jQuery('.next a');
            $popover.popover({});

            jQuery('body').on('click touchstart', function(evt) {
                if (jQuery('.popover').is(':visible')) {
                    evt.preventDefault();
                    $popover.popover('hide');
                }
            });
        },
        isInteractive: function(form) {
            var children = jQuery(form).find('input,textarea,select');
            return children.length > 0;
        },
        isFormComplete: function(form) {
            var complete = true;
            var children = jQuery(form).find('input,textarea,select');
            jQuery.each(children, function() {
                if (complete) {
                    if (this.type === 'radio' || this.type === 'checkbox') {
                        // one in the group needs to be checked
                        var selector = 'input[name=' +
                            jQuery(this).attr('name') + ']';
                        complete = jQuery(selector).is(':checked');
                    }
                    if (this.tagName === 'INPUT' && this.type === 'text' ||
                            this.tagName === 'TEXTAREA') {
                        complete = jQuery(this).val().trim().length > 0;
                    }
                    if (this.tagName === 'SELECT') {
                        var value = jQuery(this).val();
                        complete = value !== undefined && value.length > 0 &&
                            jQuery(this).val().trim() !== '-----';
                    }
                }
            });
            return complete;
        },
        onChangeLanguage: function(evt) {
            jQuery('#participant-language-form').submit();
        },
        onPlayerReady: function(event) {
            this.video_id = this.player.getVideoData().video_id;
            this.video_duration = this.player.getDuration();
        },
        onPlayerStateChange: function(event) {
            switch (event.data) {
            case YT.PlayerState.ENDED:
            case YT.PlayerState.PAUSED:
                this.recordSecondsViewed();
                break;
            case YT.PlayerState.PLAYING:
                this._start = new Date().getTime();
                break;
            }
        },
        onPauseSession: function(evt) {
            jQuery(this.el).find('.pause-session-modal').modal({
                'show': true,
                'backdrop': 'static',
                'keyboard': false
            });
            return false;
        },
        onChooseLanguage: function(evt) {
            evt.preventDefault();
            evt.stopImmediatePropagation();
            var self = this;
            var $nextButton = jQuery('.next a');
            var $span = jQuery('.next a span');
            jQuery('.choose-language-quiz .glyphicon-ok').addClass('hidden');

            var $label = jQuery(evt.currentTarget)
                .nextAll('.glyphicon').first();
            $label.removeClass('hidden');

            var form = jQuery('form[name="choose-language"]')[0];
            if (!self.isFormComplete(form)) {
                $nextButton.popover('show');
                return false; // do nothing yet
            }

            $span.removeClass('glyphicon-circle-arrow-right')
                .addClass('glyphicon-repeat spin');
            jQuery.ajax({
                type: form.method,
                url: form.action,
                data: jQuery(form).serialize(),
                dataType: 'json',
                success: function(the_json, textStatus, jqXHR) {
                    $nextButton.popover('destroy');
                    $nextButton.off('click');
                    $span.removeClass('glyphicon-repeat spin');
                    $span.addClass('glyphicon-circle-arrow-right');
                    // eslint-disable-next-line scanjs-rules/assign_to_location
                    window.location = the_json.next_url;
                },
                error: function() {
                    jQuery('#error-modal').modal({
                        'show': true,
                        'backdrop': 'static',
                        'keyboard': false
                    });
                    $span.removeClass('glyphicon-repeat spin');
                    $span.addClass('glyphicon-circle-arrow-right');
                }
            });
        },
        onNextPage: function(evt) {
            evt.preventDefault();
            evt.stopImmediatePropagation();

            var form = jQuery('form[name="content-form"]')[0];
            if (!this.isInteractive(form)) {
                var $nextButton = jQuery('.next a');
                var href = $nextButton.attr('href');
                // eslint-disable-next-line scanjs-rules/assign_to_location
                window.location = href;
            } else {
                this.onSubmitPage(evt);
            }
        },
        onSubmitPage: function(evt) {
            var self = this;
            var $nextButton = jQuery('.next a');
            var $span = jQuery('.next a span');
            var href = $nextButton.attr('href');

            var form = jQuery('form[name="content-form"]')[0];
            if (!self.isFormComplete(form)) {
                $nextButton.popover('show');
                return false; // do nothing yet
            }
            $span.removeClass('glyphicon-circle-arrow-right')
                .addClass('glyphicon-repeat spin');

            if (this.player !== undefined &&
                    this.player.hasOwnProperty('stopVideo')) {
                this.player.stopVideo();
                this.recordSecondsViewed();
            }

            jQuery.when(this.onSubmitQuiz(form), this.onSubmitVideoData())
                .done(function(first_call, second_call) {
                    // eslint-disable-next-line scanjs-rules/call_setTimeout
                    setTimeout(function() {
                        $nextButton.popover('destroy');
                        $nextButton.off('click');
                        $span.removeClass('glyphicon-repeat spin');
                        $span.addClass('glyphicon-circle-arrow-right');

                        if (href === '#') {
                            var target = $nextButton.attr('data-target');
                            jQuery(target).modal({
                                'show': true,
                                'backdrop': 'static',
                                'keyboard': false
                            });
                        } else {
                            // eslint-disable-next-line scanjs-rules/assign_to_location
                            window.location = href;
                        }
                    }, 500);
                })
                .fail(function() {
                    jQuery('#error-modal').modal({
                        'show': true,
                        'backdrop': 'static',
                        'keyboard': false
                    });
                    $span.removeClass('glyphicon-repeat spin');
                    $span.addClass('glyphicon-circle-arrow-right');
                });
            return false;
        },
        onSubmitQuiz: function(form) {
            return jQuery.ajax({
                type: form.method,
                url: form.action,
                data: jQuery(form).serialize()});
        },
        onSubmitVideoData: function(data, textStatus, jqXHR) {
            if (this.hasOwnProperty('video_id') && this.video_id.length > 0 &&
                this.hasOwnProperty('video_duration') &&
                this.video_duration > 0) {
                return jQuery.ajax({
                    type: 'post',
                    url: '/participant/track/',
                    data: {
                        video_id: this.video_id,
                        video_duration: Math.round(this.video_duration),
                        seconds_viewed: Math.round(this.seconds_viewed)
                    }
                });
            } else {
                return jqXHR;
            }
        },
        onYouTubeIframeAPIReady: function() {
            this.player = new YT.Player('player', {
                events: {
                    'onReady': window.onPlayerReady,
                    'onStateChange': window.onPlayerStateChange
                }
            });
        },
        recordSecondsViewed: function() {
            if (this._start !== undefined) {
                var end = new Date().getTime();
                this.seconds_viewed += (end - this._start) / 1000;
                delete this._start;
            }
        }
    });
})();
