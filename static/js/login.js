var Login = Login || {}

Login.Controller = Backbone.View.extend(
    {
        events : {
            "click button" : "doLogin"
        },

        initialize : function(options)
        {
        },

        doLogin : function()
        {
            var name = this.$el.find( '#name' ).val().trim();

            window.location = '/login?username=' + name;
        },

        render : function()
        {
            this.$el = $("body");
            this.el = this.$el[0];

            this.delegateEvents();
        },
    }
);

$( document ).ready( function() {
    var cont = new Login.Controller();
    
    cont.render();
    
    //$( "#addManualWords" ).click();
    //$( "#search" ).click();
});

