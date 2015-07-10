(function() {
    window.ParticipantPageView = Backbone.View.extend({
        events: {
            'click a.pause-session': 'onPauseSession',
            'click button.change-language': 'onChangeLanguage',
            'click .dimmed': 'onClickDisabled',
            'click .video-complete-quiz input[type="checkbox"]': 'onSubmitPage',
            'click .topic-rating-quiz input[type="radio"]': 'onSubmitPage',
            'click .choose-language-quiz input[type="radio"]': 'onChooseLanguage',
            'click .survey input[type="radio"]': 'onSubmitPage'
        },
        initialize: function(options) {
            _.bindAll(this,
                      'isFormComplete',
                      'onPauseSession',
                      'onPlayerReady',
                      'onPlayerStateChange',
                      'onYouTubeIframeAPIReady',
                      'onClickDisabled',
                      'onSubmitPage',
                      'onSubmitQuiz',
                      'onSubmitVideoData',
                      'recordSecondsViewed');

            var self = this;
            this.participant_id = options.participant_id;
            this.seconds_viewed = 0;
            
            // load the youtube iframe api
            window.onYouTubeIframeAPIReady = this.onYouTubeIframeAPIReady;
            window.onPlayerReady = this.onPlayerReady;
            window.onPlayerStateChange = this.onPlayerStateChange;
            
            var tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

            // Customer Popover work to support click out on the iPad
            var $popover = jQuery('.next a.dimmed');
            $popover.popover({
            }).click(function(evt) {
                evt.preventDefault();
                $popover.popover('toggle');
                return false;
            });

            jQuery('body').on('click touchstart', function(evt) {
                if (jQuery('.popover').is(':visible')) {
                    evt.preventDefault();
                    $popover.popover('hide');
                }
            });
        },
        isFormComplete: function(form) {
            var complete = true;
            var children = jQuery(form).find("input");
            jQuery.each(children, function() {
                if (complete) {
                    if (this.type === 'radio') {
                        // one in the group needs to be checked
                        var selector = 'input[name=' + jQuery(this).attr("name") + ']';
                        complete = jQuery(selector).is(":checked");
                    }
                }
            });

            return complete;
        },
        onChangeLanguage: function(evt) {
            jQuery("#participant-language-form").submit();
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
        onClickDisabled: function(evt) {
            evt.preventDefault();
            return false;
        },
        onChooseLanguage: function(evt) {
            var self = this;
            var $nextButton = jQuery(".next a");
            var $span = jQuery(".next a span");
            jQuery('.choose-language-quiz .glyphicon-ok').addClass('hidden');
            
            var $label = jQuery(evt.currentTarget).nextAll('.glyphicon').first();
            $label.removeClass('hidden');

            var form = jQuery(evt.currentTarget).parents('form')[0];
            $span.removeClass('glyphicon-circle-arrow-right').addClass('glyphicon-repeat spin');
            jQuery.ajax({
                type: form.method,
                url: form.action,
                data: jQuery(form).serialize(),
                dataType: 'json',
                success: function(the_json, textStatus, jqXHR) {
                    $nextButton.popover('destroy');
                    $nextButton.off('click');
                    $nextButton.removeClass('dimmed');
                    $nextButton.attr('href', the_json.next_url);
                    $span.removeClass('glyphicon-repeat spin');
                    $span.addClass('glyphicon-circle-arrow-right');
                }
            });
        },
        onSubmitPage: function(evt) {
            var self = this;
            var $nextButton = jQuery(".next a");
            var $span = jQuery(".next a span");

            var form = jQuery(evt.currentTarget).parents('form')[0];
            if (!self.isFormComplete(form)) {
                return; // do nothing yet
            }
            $span.removeClass('glyphicon-circle-arrow-right').addClass('glyphicon-repeat spin');
            
            if (this.player !== undefined &&
                    this.player.hasOwnProperty('stopVideo')) {
                this.player.stopVideo();
                this.recordSecondsViewed();
            }

            jQuery.when(this.onSubmitQuiz(form), this.onSubmitVideoData())
                .done(function(first_call, second_call) {
                    setTimeout(function() {
                        $nextButton.popover('destroy');
                        $nextButton.off('click');
                        $nextButton.removeClass('dimmed');
                        $span.removeClass('glyphicon-repeat spin');
                        $span.addClass('glyphicon-circle-arrow-right');
                    }, 500);
                })
                .fail(function() {
                    jQuery(".error-inline").fadeIn(function() {
                        $nextButton.hide();
                    });
                });
        },
        onSubmitQuiz: function(form) {
            return jQuery.ajax({
                type: form.method,
                url: form.action,
                data: jQuery(form).serialize()});
        },
        onSubmitVideoData: function(data, textStatus, jqXHR) {
            if (this.hasOwnProperty('video_id') && this.video_id.length > 0 &&
                    this.hasOwnProperty('video_duration') && this.video_duration > 0) {
                return jQuery.ajax({
                    type: "post",
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
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
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


