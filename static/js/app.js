'use strict';

function clickdir(f, div) {
  switch (div) {
    case 0:
      getlocal(f);
      break;
    case 1:
      getremote(f);
      break;
    case 2:
      getgpg(f);
      break;
  }
}

function showErr(e) {
  var msg = '\
  <div class="alert alert-danger">\
    <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>\
      <strong>Error!</strong> ' + e +
  '</div>'
  $('.container').prepend(msg)
}

function getlocal(f) {
  $.get('/list', {
    local_path: f
  }, function(data) {
    $('#local-files').html(data);
  });
}

function getremote(f) {
  $.get('/list', {
    remote_path: f
  }, function(data) {
    $('#remote-files').html(data);
  });
}

function getgpg(f) {
  $.get('/list', {
    gpg_path: f
  }, function(data) {
    $('#gpg-files').html(data);
  });
}

function getkeys() {
  $.get('/listkeys', {
  }, function(data) {
    $('#gpg-keys').html(data);
  });
}

function download(evt) {
  var download = Array.prototype.slice.call($('#remote-files .active')).map(function(ele) {
    return ele.getAttribute('fullpath')
  })
  if (download.length > 0) {
    var dlFiles = JSON.stringify(download)
    var localRoot = $('#local-files h3').text()
    $('#download-btn').addClass('disabled')
    $.post('/download', {
      downloadlist: dlFiles,
      localpath: localRoot,
    })
    .done(function(data) {
      getlocal(localRoot)
      Array.prototype.slice.call($('#remote-files .active')).forEach(function(ele) {
        $(ele).toggleClass('active');
      })
    })
    .fail(function(e) {
      //console.dir(e)
      showErr('Failed to download all files')
    })
    .always(function() {
      $('#download-btn').removeClass('disabled')
    });

  } else {
    alert('Please select files!');
  }
}

function upload(evt) {
  var uploadlist = Array.prototype.slice.call($('#local-files .active')).map(function(e) {
    return e.getAttribute('fullpath')
  })
  if (uploadlist.length > 0) {
    var remotepath = $('#remote-files h3').text();
    $('#upload-btn').addClass('disabled')
    $.post('/upload', {
      uploadlist: JSON.stringify(uploadlist),
      remotepath: remotepath
    })
    .done(function(data) {
      getremote(remotepath);
      Array.prototype.slice.call($('#local-files .active')).forEach(function(ele) {
        $(ele).toggleClass('active');
      });
    })
    .fail(function(e) {
      showErr('Failed to upload files')
    })
    .always(function() {
      $('#upload-btn').removeClass('disabled')
    })
  } else {
    alert('Please select files!');
  }
}

function gpgsubmit(evt) {
  var selectlist = Array.prototype.slice.call($('#gpg-files .active')).map(function(e) {
    return e;
  })
  if(selectlist.length==0){
    alert('No directory selected!');
  }else if(selectlist.length>=2){
    alert('Please select only one directory!');
  }else if(selectlist[0].getAttribute('isfile')==1){
    alert('Please select a directory instead of a file!');
  }else{
    var gpgpath=selectlist[0].getAttribute('fullpath');
    $('#ok-btn').addClass('disabled');
    $.post('/selectgpg', {
      gpgpath: gpgpath
    })
    .done(function(data) {
      getkeys();
      var dialog = $('#gpgdialog');
      dialog.modal('hide');
      dialog = $('#keydialog');
      dialog.modal('show');
    })
    .fail(function(e) {
      alert('Failed to select gpg folder!');
    })
    .always(function() {
      $('#ok-btn').removeClass('disabled');
    })
  }
}

function keysubmit(evt) {
  var selectlist = Array.prototype.slice.call($('#gpg-keys .active')).map(function(e) {
    return e;
  })
  if(selectlist.length==0){
    alert('No email selected!');
  }else if(selectlist.length>=2){
    alert('Please select only one email!');
  }else{
    var gpgemail=$(selectlist[0]).children("span").text();
    $('#keyok-btn').addClass('disabled');
    $.post('/selectkey', {
      gpgemail: gpgemail
    })
    .done(function(data) {
      var dialog = $('#keydialog');
      dialog.modal('hide');
      getlocal('~');
      getremote('/');
    })
    .fail(function(e) {
      alert('Failed to select gpg key!');
    })
    .always(function() {
      $('#keyok-btn').removeClass('disabled');
    })
  }
}

function sync(evt) {
  if (confirm('Are you sure to synchronize all changes?')) {
    var remotepath = $('#remote-files h3').text();
    $.post('/sync').done(function(data) {
      var dialog = $('#progressdialog');
      dialog.modal('show');
      var task = setInterval(function() {
        $.get('/status').done(function(data) {
          var status = JSON.parse(data);
          var percent = 0;
          var text = '';
          var objname = '';
          if (status['upload_file_num'] != status['uploaded_file_num']) {
            percent = status['uploaded_file_num'] / status['upload_file_num'];
            objname = status['uploading_file_name'];
            text = 'Uploading files...(' +
                    status['uploaded_file_num'] +
                    '/' +
                    status['upload_file_num'] + ') ';
          } else if (status['uploaded_index_num'] != status['upload_index_num']) {
            percent = status['uploaded_index_num'] / status['upload_index_num'];
            objname = status['uploading_index_name'];
            text = 'Uploading index...(' +
                    status['uploaded_index_num'] +
                    '/' +
                    status['upload_index_num'] + ') ';
          } else {
            clearInterval(task);
            dialog.modal('hide');
            getremote(remotepath);
          }
          percent = percent * 100;
          $('.progress-bar').css('width', percent + '%').attr('aria-valuenow', percent);
          $('#progresstext').text(text);
          $('#objname').text(objname);

        }).fail(function(e) {
        // FIXME
          console.dir(e)
          clearInterval(task)
          dialog.modal('hide');
          showErr('Failed to retrive status')
        })
      }, 500)

    // FIXME
    }).fail(function() {
      showErr('Failed to sync')
    })
  }
}

function deleteFiles(evt) {
  var deletelist = Array.prototype.slice.call($('#remote-files .active')).map(function(e) {
    return e.getAttribute('fname')
  })
  if (deletelist.length > 0) {
    if (confirm('Are you sure to delete these files?')) {
      var remotepath = $('#remote-files h3').text();
      $.post('/delete', {
        deletelist: JSON.stringify(deletelist),
        remotepath: remotepath
      })
      .done(function(data) {
        getremote(remotepath);
      })
      // FIXME
      .fail(function() {
        showErr('Failed to delete')
      })
    }
  } else {
    alert('Please select files!');
  }
}

function initgpg() {
    $.post('/initgpg',{}).done(function(data){
        if(data=='1'){
            getgpg('~');
            var dialog = $('#gpgdialog');
            dialog.modal('show');
        }else{
            getlocal('~');
            getremote('/');
        }
    });
}

$(document).ready(function() {
  $('#download-btn').click(download);

  $('#upload-btn').click(upload);

  $('#delete-btn').click(deleteFiles);

  $('#sync-btn').click(sync);

  $('#ok-btn').click(gpgsubmit);

  $('#keyok-btn').click(keysubmit);

  initgpg();
});
