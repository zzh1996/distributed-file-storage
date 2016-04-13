<script type="text/javascript">
(function() {
  'use strict'

  const ws = new WebSocket('ws://localhost:{{ port }}/ws')
  ws.onmessage = function(evt) {
    let data
    try {
      data = JSON.parse(evt.data)
    } catch (e) {
      data = {}
    }

    console.dir(data)
    switch (data.event) {
      case 'connect':
        //console.log(`new client from ${data.addr}:${data.port}`)
        $('#notification').text(`connection from ${data.host}:${data.port}`)
        $('#notification').fadeTo(2000, 500).slideUp(500)
        break
      case 'upload-success':
        $('#notification').text(`successfully receive ${data.name}`)
        $('#notification').fadeTo(2500, 500).slideUp(500)
        break
      default:
        console.log('new data', data)
    }
  }

})()
</script>
