$(document).ready(function() {
    // Test connection button for XML Director controlpanel
    var button = $('.template-pp-client-plone-settings #form-buttons-save');
    if (button.length > 0) {
        var button2 = button.clone();
        var cancel_button = $('#form-buttons-cancel');
        button2.attr('value', 'Test connection');
        button2.attr('name', 'form-button-test-connection');
        button2.attr('id', 'form-button-test-connection');
        button2.attr('type', 'button');
        button2.attr('style', 'margin-left: 1em');
        button2.insertAfter(cancel_button);
        button2.on('click', function() {
            window.location.href = '@@pp-client-plone-connection-test'; 
        });
    }            
});
