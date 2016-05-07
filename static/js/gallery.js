var Login = Login || {}

Login.Controller = Backbone.View.extend(
    {
        events : {
            "change .category" : "loadImages",
            "click .predict" : "loadImages",
            "click .next" : "next",
            "click .previous" : "previous"
        },

        initialize : function(options)
        {
            this.start = 0;
        },

        next : function()
        {
            this.start += 39;

            this.loadImages();
        },

        previous : function()
        {
            this.start -= 39;

            this.loadImages();
        },

        loadImages : function()
        {
            this.$el.find( '.count' ).text( this.start );
            this.category = $( '.category' ).val().trim();
            this.predict = this.$el.find( '.predict' ).prop('checked');

            $.ajax( { url : '/gallery_page',
                      data : { category : this.category,
                               start : this.start,
                               predict : this.predict },
                      dataType : 'json',
                      method : 'GET',
                      success : _.bind(this.handleLoadImages, this)
                    } );
        },

        handleLoadImages : function(data)
        {
            this.figures = data.figures;

            this.$el.find( '.total' ).text(data.total);

            this.$el.find( '.gallery' ).empty()

            //Technique for this stolen from http://www.dwuser.com/education/content/creating-responsive-tiled-layout-with-pure-css/
            var template = _.template($( '.galleryItemTemplate' ).text());

            for(var i = 0; i < this.figures.length; i++)
            {
                var el = $( template(this.figures[i]) ).appendTo( this.$el.find( '.gallery' ) );

                el = el.find('img');

                el.data('id', this.figures[i].id);
                
                if(this.figures[i].classified)
                {
                    if(this.figures[i].correct)
                    {
                        el.addClass('correctly classified');
                    }
                    else
                    {
                        el.addClass('incorrectly classified');
                    }
                }

                el.click( _.bind(this.handleImageClick, this) );
            }
        },

        handleImageClick : function(event)
        {
            var el = $( event.target );

            if(event.ctrlKey)
            {
                if(el.hasClass('classified'))
                {
                    el.removeClass('classified');
                    el.addClass('classifying');

                    //Remove last classification
                    $.ajax( {
                        url : '/removeClassifications',
                        data : { data : JSON.stringify({ id : el.data('id') }) },
                        dataType : 'json',
                        method : 'POST',
                        success : _.bind(_.partial(this.handleRemoveClassify, el), this),
                        error : _.bind(_.partial(this.handleRemoveClassifyError, el), this)
                    } );
                }
                else
                {
                    el.addClass('classifying');

                    $.ajax( {
                        url : '/doClassification',
                        data : { data : JSON.stringify({ categories : [this.category],
                                                         id : el.data('id') }) },
                        dataType : 'json',
                        method : 'POST',
                        success : _.bind(_.partial(this.handleClassify, el), this),
                        error : _.bind(_.partial(this.handleClassifyError, el), this)
                    } );
                }
            }
            else
            {
                this.$el.find( '.msg' ).text('Downloading info...');

                this.token = Math.random();

                $.ajax( {
                    url : '/get_info',
                    data : { figureId : el.data('id'),
                             token : this.token },
                    dataType : 'json',
                    method : 'POST',
                    success : _.bind(this.handleGetInfo, this)
                } );
            }
        },

        handleRemoveClassify : function(el)
        {
            el.removeClass('correctly incorrectly classifying');
        },

        handleRemoveClassifyError : function()
        {
            el.removeClass('classifying');
            el.addClass('classified');
        },

        handleClassify : function(el)
        {
            el.removeClass('classifying');

            el.addClass('newly classified');
        },

        handleClassifyError : function()
        {
            el.removeClass('classifying');
        },

        handleGetInfo : function(data)
        {
            if(this.token == data.token)
            {
                this.$el.find( '.info' ).empty();

                var template = _.template($( '.infoTemplate' ).text());
                var el = $( template(data) ).appendTo($( '.info' ));

                el.find( 'button' ).click( _.bind(_.partial(this.saveNotes, data.figureId), this) );

                this.$el.find( '.msg' ).text('Ready');
            }
        },

        saveNotes : function(figureId)
        {
            this.$el.find( '.msg' ).text('Saving notes...');
            
            $.ajax( {
                url : '/save_notes',
                data : { figureId : figureId,
                         string : this.$el.find( '.info textarea' ).val(),
                         category : this.$el.find( 'input.category').val().trim() },
                dataType : 'json',
                method : 'POST',
                success : _.bind(this.handleSaveNotesSuccess, this)
            } );
        },

        handleSaveNotesSuccess : function()
        {
            this.$el.find( '.msg' ).text('Notes saved!');
        },

        render : function()
        {
            this.$el = $("body");
            this.el = this.$el[0];

            //this.data = $.parseJSON(this.$el.find( '.data' ).text());

            this.loadImages();

            this.delegateEvents();
        },
    }
);

$( document ).ready( function() {
    var cont = new Login.Controller();
    
    cont.render();
});

