"use strict";

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
  });
}

function getremote(f) {
  $.get('/list', {remote_path: f}, function(data) {
    $('#remote-files').html(data);
  });
}

$(document).ready(function() {
  getlocal('/home/');
  getremote('/');

  $('#download-btn').click(function(evt) {
    console.dir($('.active'));
  });

  $('#upload-btn').click(function(evt) {
    var uploadlist=[]
    //var localRoot = $('#local-files > h1').text();
    Array.prototype.slice.call($('#local-files .active')).forEach(function(ele) {
      //var path = localRoot + $.trim(ele.innerText);
      var path=ele.getAttribute('fullpath');
      uploadlist.push(path);
    });
    if(uploadlist.length>0){
      console.log(JSON.stringify(uploadlist));
      console.log($('#remote-files h3').text());
      var remotepath=$('#remote-files h3').text();
      $.post('/upload',{uploadlist:JSON.stringify(uploadlist),remotepath:remotepath},function(data){
        getremote(remotepath);
        Array.prototype.slice.call($('#local-files .active')).forEach(function(ele) {
          $(ele).toggleClass("active");
        });
      });
    }else{
      alert('Please select files!');
    }
  });

  $('#delete-btn').click(function(evt) {
    var deletelist=[];
    Array.prototype.slice.call($('#remote-files .active')).forEach(function(ele) {
      var file=$.trim(ele.innerText);
      deletelist.push(file);
    });
    if(deletelist.length>0){
      if(confirm('Are you sure to delete these files?')){
        var remotepath=$('#remote-files h3').text();
        $.post('/delete',{deletelist:JSON.stringify(deletelist),remotepath:remotepath},function(data){
          getremote(remotepath);
          //alert(data);
        });
      }
    }else{
      alert('Please select files!');
    }
  });

  $('#sync-btn').click(function(evt) {
    if(confirm('Are you sure to synchronize all changes?')){
      var remotepath=$('#remote-files h3').text();
      $.post('/sync',{},function(data){
        var dialog = $('#progressdialog');
        dialog.modal('show');
        var task=setInterval(function(){
          $.get('/status',{},function(data){
            var nums=JSON.parse(data);
            var percent=0;
            var text='';
            if(nums['upload_file_num']!=nums['uploaded_file_num']){
              percent=nums['uploaded_file_num']/nums['upload_file_num'];
              text='Uploading files...('+nums['uploaded_file_num']+'/'+nums['upload_file_num']+')';
            }else if(nums['uploaded_index_num']!=nums['upload_index_num']){
              percent=nums['uploaded_index_num']/nums['upload_index_num'];
              text='Uploading index...('+nums['uploaded_index_num']+'/'+nums['upload_index_num']+')';;
            }else{
              clearInterval(task);
              dialog.modal('hide');
              getremote(remotepath);
            }
            percent=percent*100;
            $('.progress-bar').css('width', percent+'%').attr('aria-valuenow', percent);
            $('#progresstext').html(text);
          });
        },500);
      });
    }
  });
});
