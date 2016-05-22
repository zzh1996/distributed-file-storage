function clickdir(f,div){
  if(div==0){
    getlocal(f);
  }else{
    getremote(f);
  }
}

function getlocal(f){
  $.get('/list', {local_path: f}, function(data) {
    $('#local-files').html(data);
  })
}

function getremote(f){
  $.get('/list', {remote_path: f}, function(data) {
    $('#remote-files').html(data);
  })
}

$(document).ready(function() {
  getlocal('/');
  getremote('/');
});
