(function() {
    window.ParticipantPageView = Backbone.View.extend({
        events: {
            'click li.pause-session a': 'onPauseSession',
            'click button.change-language': 'onChangeLanguage',
            'click a.disabled': 'onClickDisabledElement',
            'click .nav li.disabled a': 'onClickDisabledElement',
            'submit #submit-page': 'onSubmitPage',
            'click #next-page-button': 'onNextPage'
        },
        isFormComplete: function(form) {
            var complete = true;
            var children = jQuery(form).find("input,textarea,select");
            jQuery.each(children, function() {
                if (complete) {
                    
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
                    'onPlayerReady',
                    'onPlayerStateChange',
                    'onYouTubeIframeAPIReady',
                    'onNextPage',
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
        onChangeLanguage: function(evt) {
            jQuery("#participant-language-form").submit();
        },
        onClickDisabledElement: function(evt) {
            evt.preventDefault();
            return false;
        },
        onNextPage: function(evt) {
            var elts = jQuery("input[type='hidden'][name='next-section']");
            if (elts.length < 1) {
                jQuery(this.el).find('.end-session-modal').modal({
                    'show': true,
                    'backdrop': 'static',
                    'keyboard': false
                });            
                return false;
            } else {
                jQuery(".btn-next").hide();
                jQuery("#working").show();
                    
                var url = jQuery(elts[0]).val();
                window.location = url;
            }
            return false;
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
        onSubmitPage: function(evt) {
            var self = this;

            evt.preventDefault();
            jQuery(".alert").hide();

            var form = evt.currentTarget;
            if (this.isFormComplete(form)) {
                jQuery(".btn-next").hide();
                jQuery("#working").fadeIn();
                
                if (this.player.hasOwnProperty('stopVideo')) {
                    this.player.stopVideo();
                    this.recordSecondsViewed();
                }
                
                jQuery.when(this.onSubmitQuiz(form),
                            this.onSubmitVideoData())
                    .done(function(first_call, second_call) {
                        self.onNextPage();
                    })
                    .fail(function() {
                        jQuery(".error-inline").fadeIn(function() {
                            jQuery(".btn-next").hide();
                            jQuery("#working").show();
                        });
                        
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


