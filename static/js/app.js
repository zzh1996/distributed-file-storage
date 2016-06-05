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
  getlocal('/home/');
  getremote('/');

  $('#download-btn').click(function(evt) {
    console.dir($('.active'));
  })

  $('#upload-btn').click(function(evt) {
    var uploadlist=[]
    //var localRoot = $('#local-files > h1').text();
    Array.prototype.slice.call($('.active')).forEach(function(ele) {
      //var path = localRoot + $.trim(ele.innerText);
      var path=ele.getAttribute('fullpath');
      uploadlist.push(path);
    })
    if(uploadlist){
      console.log(JSON.stringify(uploadlist));
      console.log($('#remote-files > h1').text());
      remotepath=$('#remote-files > h1').text()
      $.post('/upload',{uploadlist:JSON.stringify(uploadlist),remotepath:remotepath},function(data){
        getremote(remotepath);
        alert(data);
      });
    }
  })
});
