(function() {
    /** Example embed code: 
     * <iframe id="player" frameborder="0" allowfullscreen="1" title="YouTube video player" width="640" height="390" src="https://www.youtube.com/embed/gukC5bCUMOw?enablejsapi=1&origin=http://localhost:8000"></iframe>
     */
    
    window.ParticipantPageView = Backbone.View.extend({
        events: {
            'click li.pause-session a': 'onPauseSession',
            'click a.disabled': 'onClickDisabledElement',
            'click .nav li.disabled a': 'onClickDisabledElement',
            'submit form#submit-page': 'onSubmitPage'
        },
        isFormComplete: function(form) {
            var complete = true;
            var children = jQuery(form).find("input,textarea,select");
            jQuery.each(children, function() {
                if (complete && jQuery(this).is(":visible") &&
                        !jQuery(this).hasClass("optional")) {
                    
                    if (this.tagName === 'INPUT' && this.type === 'text' ||
                        this.tagName === 'TEXTAREA') {
                        complete = jQuery(this).val().trim().length > 0;
                    }
            
                    if (this.tagName === 'SELECT') {
                        var value = jQuery(this).val();
                        complete = value !== undefined && value.length > 0 &&
                            jQuery(this).val().trim() !== '-----';
                    }
            
                    if (this.type === 'checkbox' || this.type === 'radio') {
                        // one in the group needs to be checked
                        var selector = 'input[name=' + jQuery(this).attr("name") + ']';
                        complete = jQuery(selector).is(":checked");
                    }
                }
            });
            
            return complete;
        },
        initialize: function(options) {
            _.bindAll(this,
                    'onPauseSession',
                    'onClickDisabledElement',
                    'onPlayerReady',
                    'onPlayerStateChange',
                    'onYouTubeIframeAPIReady',
                    'onSubmitPage',
                    'onSubmitQuiz',
                    'onSubmitVideoData',
                    'recordSecondsViewed');

            this.participant_id = options.participant_id;
            this.section_id = options.section_id;

            this.seconds_viewed = 0;
            
            // load the youtube iframe api
            window.onYouTubeIframeAPIReady = this.onYouTubeIframeAPIReady;
            window.onPlayerReady = this.onPlayerReady;
            window.onPlayerStateChange = this.onPlayerStateChange;
            
            var tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        },
        onClickDisabledElement: function(evt) {
            evt.preventDefault();
            return false;
        },
        onPlayerReady: function(event) {
            this.video_url = this.player.getVideoUrl();
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
        onSubmitPage: function(evt) {
            evt.preventDefault();
            jQuery(".alert").hide();

            var form = evt.currentTarget;
            if (this.isFormComplete(form)) {
                jQuery("#submit-page-button").button('loading');

                if (this.player.hasOwnProperty('stopVideo')) {
                    this.player.stopVideo();
                    this.recordSecondsViewed();
                }
                
                jQuery.when(this.onSubmitQuiz(form),
                            this.onSubmitVideoData())
                    .done(function(first_call, second_call) {
                        var url = jQuery("input[type='hidden'][name='next']").val();
                        window.location = url;
                    })
                    .fail(function() {
                        jQuery(".error-inline").fadeIn();
                    })
                    .always(function() {
                        jQuery("#submit-page-button").button('reset');
                    });
            } else {
                jQuery(".help-inline").fadeIn();
            }
            
            return false;
        },
        onSubmitQuiz: function(form) {
            return jQuery.ajax({
                type: form.method,
                url: form.action,
                data: jQuery(form).serialize()});
        },
        onSubmitVideoData: function(data, textStatus, jqXHR) {
            if (this.hasOwnProperty('video_url') && this.video_url.length > 0 &&
                    this.hasOwnProperty('video_duration') && this.video_duration > 0) {
                return jQuery.ajax({
                    type: "post",
                    url: '/participant/track/',
                    data: {
                        video_url: this.video_url,
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


