var Login = Login || {}

Login.Controller = Backbone.View.extend(
    {
        events : {
            "click .chooseClassify" : "enableClassification",
            "click .chooseSegment" : "enableSegmentation",
            "click .doClassify" : "doClassification",
            "click .doSegment" : "doSegmentation",
            "click .next" : "next",
            "click .reset" : "doReset"
        },

        initialize : function(options)
        {
            this.lines = [];

            this.mode = 'CHOOSE';
        },

        next : function()
        {
            window.location = '/';
        },

        doReset : function()
        {
            window.location = '/?figureId=' + this.data.id;
        },

        handleImageLoadFinish : function()
        {
            this.height = this.img.height;
            this.width = this.img.width;
            
            this.canvas.width = this.img.width;
            this.canvas.height = this.img.height;

            var offset = $( this.canvas ).offset()

            var visWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth || this.width;

            var visHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || this.height;

            visHeight -= offset.top;

            var hs = visHeight / this.height;
            var ws = visWidth / this.width;

            if(hs < ws)
            {
                $( this.canvas ).css('height', visHeight * 0.75);
                $( this.canvas ).css('width', '');
            }
            else
            {
                $( this.canvas ).css('height', '');
                $( this.canvas ).css('width', visWidth * 0.75);
            }
            
            this.context.drawImage(this.img, 0, 0);
        },

        handleImageLoadFail : function()
        {
            this.$el.find( '.caption' ).text( "Image failed to load! Go next!" );
        },

        doSegmentation : function()
        {
            this.$el.find( '.msg' ).html("<span>Submitting results and acquiring new image...</span>");

            $.ajax( { url : '/doSegmentation',
                      data : { data : JSON.stringify({ lines : this.lines,
                                                       id : this.data.id }) },
                      dataType : 'json',
                      method : 'POST',
                      success : _.bind(this.next, this),
                      error : _.bind(this.next, this)
                    } );
        },

        enableSegmentation : function()
        {
            this.mode = 'SEGMENT';

            this.$el.find( '.choose' ).hide();
            this.$el.find( '.segment' ).show();

            $( this.canvas ).mousemove( _.bind(this.handleMouseMove, this) );
            $( this.canvas ).keypress( _.bind(this.handleMouseMove, this) );
            $( this.canvas ).mousedown( _.bind(this.addLine, this) );
        },

        doClassification : function()
        {
            this.$el.find( '.msg' ).html("<span>Submitting results and acquiring new image...</span>");

            var selectors = this.$el.find( '.keywordSelector' );

            var categories = [];

            for(var i = 0; i < selectors.length; i++)
            {
                var el = selectors.eq(i);

                if(el.hasClass('selected'))
                {
                    categories.push(el.text().trim());
                }
            }

            var customKeywords = this.$el.find( '.customKeywords' ).val().trim().split(' ');

            for(var i = 0; i < customKeywords.length; i++)
            {
                categories.push(customKeywords[i]);
            }

            $.ajax( { url : '/doClassification',
                      data : { data : JSON.stringify({ categories : categories,
                                                       id : this.data.id }) },
                      dataType : 'json',
                      method : 'POST',
                      success : _.bind(this.next, this),
                      error : _.bind(this.next, this)
                    } );
        },

        enableClassification : function()
        {
            this.mode = 'CLASSIFY';

            this.$el.find( '.choose' ).hide();
            this.$el.find( '.classify' ).show();

            var keywords = [["superalloy microstructure", 0.5], ["plot", 0.5], ["phase diagram", 0.5], ["xray", 0.5], ["picture", 0.5], ["schematic", 0.5]];//.concat(this.data.keywords);

            for(var i = 0; i < keywords.length; i++)
            {
                var el = $( '<div>' + keywords[i][0] + '</div>' ).appendTo( this.$el.find( '.keywords' ) );

                el.addClass('keywordSelector')

                el.click( _.partial( function(el) {
                    el.toggleClass('selected');
                }, el ));
            }
        },

        handleKeyPress : function(e)
        {
            var code = (e.keyCode ? e.keyCode : e.which);
            if(code == 13) { //Enter keycode
                if(this.mode == 'CLASSIFY')
                {
                    this.doClassification();
                }
                else if(this.mode == 'SEGMENT')
                {
                    this.doSegmentation();
                }
            }
        },

        drawLines : function()
        {
            for(var i = 0; i < this.lines.length; i++)
            {
                this.drawLine(this.lines[i].bounds, '#00AAFF', i);
            }
        },

        drawLine : function(bounds, color, index)
        {
            this.context.beginPath();

            if(typeof(color) != 'undefined')
                this.context.strokeStyle = color;
            
            this.context.moveTo(bounds.x1, bounds.y1);
            this.context.lineTo(bounds.x2, bounds.y2);

            this.context.lineWidth = 3;
            this.context.stroke();
        },

        getLineBounds : function(orientation, x, y, index)
        {
            if(typeof(index) == 'undefined')
                var index = this.lines.length;

            if(orientation == 'h')
            {
                var xlt = 0,
                xgt = this.img.width;

                for(var i = 0; i < index; i++)
                {
                    if(this.lines[i].t == 'v')
                    {
                        if((this.lines[i].bounds.y1 < y && this.lines[i].bounds.y2 > y))
                        {
                            if(this.lines[i].bounds.x1 > xlt && this.lines[i].bounds.x1 <= x)
                                xlt = this.lines[i].bounds.x1;
                        
                            if(this.lines[i].bounds.x1 < xgt && this.lines[i].bounds.x1 >= x)
                                xgt = this.lines[i].bounds.x1;
                        }
                    }
                }

                return { x1 : xlt,
                         x2 : xgt,
                         y1 : y,
                         y2 : y }
            }
            else
            {
                var ylt = 0,
                ygt = this.img.height;

                for(var i = 0; i < index; i++)
                {
                    if(this.lines[i].t == 'h')
                    {
                        if((this.lines[i].bounds.x1 < x && this.lines[i].bounds.x2 > x))
                        {
                            if(this.lines[i].bounds.y1 > ylt && this.lines[i].bounds.y1 <= y)
                                ylt = this.lines[i].bounds.y1;
                            
                            if(this.lines[i].bounds.y1 < ygt && this.lines[i].bounds.y1 >= y)
                                ygt = this.lines[i].bounds.y1;
                        }
                    }
                }

                return { x1 : x,
                         y1 : ylt,
                         x2 : x,
                         y2 : ygt};
            }
        },

        addLine : function(event)
        {
            var rect = this.canvas.getBoundingClientRect();
            
            var x = event.clientX - rect.left;
            var y = event.clientY - rect.top;

            x = Math.round(this.width * x / this.canvas.scrollWidth);
            y = Math.round(this.height * y / this.canvas.scrollHeight);

            if(event.shiftKey)
            {
                if(event.ctrlKey)
                {
                    bounds = { x1 : x,
                               x2 : x,
                               y1 : 0,
                               y2 : this.img.height };
                }
                else
                {
                    bounds = this.getLineBounds('v', x, y);
                }

                this.lines.push({ t : 'v',
                                  x : x,
                                  y : y,
                                  override : event.ctrlKey,
                                  bounds : bounds });
            }
            else
            {
                if(event.ctrlKey)
                {
                    bounds = { x1 : 0,
                               x2 : this.img.width,
                               y1 : y,
                               y2 : y };
                }
                else
                {
                    bounds = this.getLineBounds('h', x, y);
                }

                this.lines.push({ t : 'h',
                                  x : x,
                                  y : y,
                                  override : event.ctrlKey,
                                  bounds : bounds });
            }
        },

        handleMouseMove : function(event)
        {
            var rect = this.canvas.getBoundingClientRect();
            
            var x = event.clientX - rect.left;
            var y = event.clientY - rect.top;

            this.context.drawImage(this.img, 0, 0);

            this.drawLines();

            x = Math.round(this.width * x / this.canvas.scrollWidth);
            y = Math.round(this.height * y / this.canvas.scrollHeight);

            if(event.shiftKey)
            {
                if(event.ctrlKey)
                {
                    bounds = { x1 : x,
                               x2 : x,
                               y1 : 0,
                               y2 : this.img.height };
                }
                else
                {
                    bounds = this.getLineBounds('v', x, y);
                }

                this.drawLine(bounds, '#FF0011');
            }
            else
            {
                if(event.ctrlKey)
                {
                    bounds = { x1 : 0,
                               x2 : this.img.width,
                               y1 : y,
                               y2 : y };
                }
                else
                {
                    bounds = this.getLineBounds('h', x, y);
                }

                this.drawLine(bounds, '#FF0011');
            }
        },

        render : function()
        {
            this.$el = $("body");
            this.el = this.$el[0];

            var img = new Image();

            this.$el.find( '.choose' ).show();
            this.$el.find( '.segment' ).hide();
            this.$el.find( '.classify' ).hide();

            this.img = img;
            this.canvas = this.$el.find( '.canvas' )[0];
            this.context = this.canvas.getContext('2d');

            img.onload = _.bind(this.handleImageLoadFinish, this);
            img.onerror = _.bind(this.handleImageLoadFail, this);
            img.onabort = _.bind(this.handleImageLoadFail, this);

            this.$el.keypress(_.bind(this.handleKeyPress, this));

            this.data = $.parseJSON(this.$el.find( '.data' ).text());

            img.src = this.data.url;

            this.delegateEvents();
        },
    }
);

$( document ).ready( function() {
    var cont = new Login.Controller();
    
    cont.render();
});

