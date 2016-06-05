
function clickdir(f, div) {
  switch (div) {
    case 0:
      getlocal(f);
      break;
    case 1:
      getremote(f);
      break;
  }
}

function getlocal(f) {
  $.get('/list', {local_path: f}, function(data) {
    $('#local-files').html(data);
  })
}

function getremote(f) {
  $.get('/list', {remote_path: f}, function(data) {
    $('#remote-files').html(data);
  })
}

$(document).ready(function() {
  getlocal('/');
  getremote('/');

  $('#download-btn').click(function(evt) {
    console.dir($('.active'));
  })

  $('#upload-btn').click(function(evt) {
    var localRoot = $('#local-files > h1').text();
    Array.prototype.slice.call($('.active')).forEach(function(ele) {
      var path = localRoot + $.trim(ele.innerText);
      alert(path);
    })
  })
});
