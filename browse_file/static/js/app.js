;(function() {
'use strict'

  $(document).ready(function() {
    $.get('/list', {local_path: '/'}, function(data) {
      console.log(data)
    })

    $('#local-files').click(function(evt) {
      console.dir(evt)
      $.get('/list', {local_path: '/'}, function(data) {

      })

    })
    $('#remote-files').click(function(evt) {
      console.dir(evt)
      $.get('/list', {remote_path: '/'}, function(data) {

      })

    })
  })


})();
