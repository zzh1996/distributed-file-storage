;(function() {
  'use strict'

  const ws = new WebSocket('ws://localhost:8000/ws')
  ws.onmessage = function(evt) {
    //console.dir(evt)
    let data
    try {
      data = JSON.parse(evt.data)
    } catch (e) {
      data = {}
    }

    switch (data.event) {
      case 'connect':
        //console.log(`new client from ${data.addr}:${data.port}`)
        $('#notification').text(`connection from ${data.host}:${data.port}`)
        $('#notification').fadeTo(1000, 500).slideUp(500)
        break
      case 'upload-success':
        $('#notification').text(`successfully receive ${data.name}`)
        $('#notification').fadeTo(1000, 500).slideUp(500)
        break
      default:
        console.log('new data', data)
    }
  }

})()
