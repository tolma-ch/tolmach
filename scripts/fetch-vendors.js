'use strict';

var fs = require('fs');
var path = require('path');
var crypto = require('crypto');
var http = require('http');
var https = require('https');

var MANIFEST = [
  {
    dest: 'tolmach/static/assets/angular-ui-select/dist/select.min.js',
    sha256: '63b09d3a2f7108f34d96c188f18b06a4be0c48b59fcadc7789d3ef9fdc7ddecd',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/angular-ui-select/0.17.1/select.min.js',
      'https://cdn.jsdelivr.net/npm/angular-ui-select@0.17.1/dist/select.min.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-ui-select/dist/select.css',
    sha256: '4f0c6ec3dd8b83fdb7b3b2a8f27863d399449beb0e5fbc65c28d8783b859680c',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/angular-ui-select/0.17.1/select.css',
      'https://cdn.jsdelivr.net/gh/angular-ui/ui-select@0.17.1/dist/select.css'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-image-crop/image-crop.js',
    sha256: '46f6b39046cbcd18a4196ff83b5ae0fa7b6643582ff7ac4361d3a8ceadd41c74',
    urls: [
      'https://cdn.jsdelivr.net/gh/andyshora/angular-image-crop@v2.0.0/image-crop.js',
      'https://raw.githubusercontent.com/andyshora/angular-image-crop/v2.0.0/image-crop.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-contenteditable/angular-contenteditable.js',
    sha256: 'c15a31d1a97cd1fe38380968d3580eabce757450694ffc6391a3ca1df0e48721',
    urls: [
      'https://cdn.jsdelivr.net/gh/akatov/angular-contenteditable@0.3.8/angular-contenteditable.js',
      'https://raw.githubusercontent.com/akatov/angular-contenteditable/0.3.8/angular-contenteditable.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-img-cropper/dist/angular-img-cropper.min.js',
    sha256: '87723f0f686e0329f301ec82d07c414a0f332b62e7bf10c5dca233799d9341d1',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/angular-img-cropper/1.1.0/angular-img-cropper.min.js',
      'https://cdn.jsdelivr.net/npm/angular-img-cropper@1.1.0/dist/angular-img-cropper.min.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-elastic/elastic.js',
    sha256: '8f32e3978f7754b9860073b361d924f5397f94c84ce279ed0f569e4ec9908771',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/angular-elastic/2.4.2/elastic.js',
      'https://cdn.jsdelivr.net/npm/angular-elastic@2.4.2/elastic.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-bootstrap-toggle/dist/angular-bootstrap-toggle.min.js',
    sha256: '12e89054e5dc7fa2617f817bb70596cec91847d94f3ffe7eead7498776c8c854',
    urls: [
      'https://cdn.jsdelivr.net/gh/ziscloud/angular-bootstrap-toggle@v0.1.1/dist/angular-bootstrap-toggle.min.js',
      'https://raw.githubusercontent.com/ziscloud/angular-bootstrap-toggle/v0.1.1/dist/angular-bootstrap-toggle.min.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-bootstrap-toggle/dist/angular-bootstrap-toggle.min.css',
    sha256: 'edf9a4ab4c124b010e6ed3324592a8683c008519439be08fe2eb4f23c1c7f9e5',
    urls: [
      'https://cdn.jsdelivr.net/gh/ziscloud/angular-bootstrap-toggle@v0.1.1/dist/angular-bootstrap-toggle.min.css',
      'https://raw.githubusercontent.com/ziscloud/angular-bootstrap-toggle/v0.1.1/dist/angular-bootstrap-toggle.min.css'
    ]
  },
  {
    dest: 'tolmach/static/assets/ngDraggable/ngDraggable.js',
    sha256: '097b5a944ab83b3a5230e9f8d7263f3a8f7fa326e8c5295b67d08fef1cd8091b',
    urls: [
      'https://cdn.jsdelivr.net/gh/fatlinesofcode/ngDraggable@0.1.8/ngDraggable.js',
      'https://raw.githubusercontent.com/fatlinesofcode/ngDraggable/0.1.8/ngDraggable.js'
    ]
  },
  {
    dest: 'tolmach/static/assets/angular-bootstrap/ui-bootstrap-tpls-2.5.0.min.js',
    sha256: 'b727d65b62ed250348fa5dc5d21eb10d5fe28fa31f9fc97048a1d63ac9848173',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/angular-ui-bootstrap/2.5.0/ui-bootstrap-tpls.min.js',
      'https://cdn.jsdelivr.net/npm/angular-ui-bootstrap@2.5.0/dist/ui-bootstrap-tpls.min.js'
    ]
  },
  {
    dest: 'tolmach/static/js/screenfull.js',
    sha256: '16861757a5b0d72f3333bc0955f7d3447b6bcb15254308d47893659802b8457e',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/screenfull.js/3.3.2/screenfull.min.js',
      'https://cdn.jsdelivr.net/npm/screenfull@3.3.2/dist/screenfull.min.js'
    ]
  },
  {
    dest: 'tolmach/static/js/reconnecting-websocket.min.js',
    sha256: '03827095c0efa8ee095e9bc4b6f598d511fc24010cbb95b6d703fc1945cb50db',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/reconnecting-websocket/1.0.0/reconnecting-websocket.min.js',
      'https://raw.githubusercontent.com/joewalnes/reconnecting-websocket/master/reconnecting-websocket.min.js'
    ]
  },
  {
    dest: 'tolmach/static/js/jquery-2.0.3.min.js',
    sha256: 'a57b5242b9a9adc4c1ef846c365147b89c472b9cd770face331efcb965346b25',
    urls: [
      'https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js',
      'https://cdn.jsdelivr.net/npm/jquery@2.0.3/dist/jquery.min.js'
    ]
  },
  {
    dest: 'tolmach/static/js/bootstrap.min.js',
    sha256: '54d21b0676784d0c983bbd4093898770adefa932d89b72c8afd88183a19172a7',
    urls: [
      'https://raw.githubusercontent.com/twbs/bootstrap/v3.0.0/dist/js/bootstrap.min.js',
      'https://cdn.jsdelivr.net/npm/bootstrap@3.0.0/dist/js/bootstrap.min.js'
    ]
  }
];

function sha256File(filePath) {
  var hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function fetchToFile(url, tmpPath) {
  return new Promise(function (resolve, reject) {
    var parsed = new URL(url);
    var client = parsed.protocol === 'https:' ? https : http;
    var req = client.get(url, function (res) {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        var next = new URL(res.headers.location, url).toString();
        fetchToFile(next, tmpPath).then(resolve, reject);
        return;
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error('HTTP ' + res.statusCode));
      }
      var file = fs.createWriteStream(tmpPath);
      res.pipe(file);
      file.on('finish', function () { file.close(); resolve(); });
      file.on('error', reject);
    });
    req.setTimeout(60000, function () { req.abort(); reject(new Error('timeout')); });
    req.on('error', reject);
  });
}

function asyncFetch(url, tmpPath, dest, sha256) {
  return fetchToFile(url, tmpPath).then(function () {
    var actual = sha256File(tmpPath);
    if (actual !== sha256) {
      throw new Error('sha256 mismatch (expected ' + sha256 + ', got ' + actual + ')');
    }
    fs.renameSync(tmpPath, dest);
    return true;
  }).catch(function (err) {
    if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
    console.error('Failed to fetch ' + url + ': ' + err.message);
    return false;
  });
}

function download(url, tmpPath, dest, sha256) {
  return asyncFetch(url, tmpPath, dest, sha256);
}

var downloaded = 0;

function runEntry(index) {
  if (index >= MANIFEST.length) {
    console.log('downloaded ' + downloaded + ' files');
    return;
  }
  var entry = MANIFEST[index];
  var dest = path.resolve(process.cwd(), entry.dest);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  var tmpPath = dest + '.part';

  function tryUrls(idx) {
    if (idx >= entry.urls.length) {
      console.error(
        'FATAL: all mirrors failed for ' + entry.dest + ' (' + entry.sha256 + ')'
      );
      process.exit(1);
    }
    asyncFetch(entry.urls[idx], tmpPath, dest, entry.sha256).then(function (ok) {
      if (ok) {
        downloaded++;
        console.log('downloaded ' + entry.dest);
        runEntry(index + 1);
        return;
      }
      if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
      tryUrls(idx + 1);
    });
  }

  tryUrls(0);
}

runEntry(0);