'use strict';

var fs = require('fs');
var path = require('path');

var ROOT = process.cwd();

function read(p) {
  return fs.readFileSync(path.join(ROOT, p), 'utf8');
}
function write(p, content) {
  fs.mkdirSync(path.dirname(path.join(ROOT, p)), { recursive: true });
  fs.writeFileSync(path.join(ROOT, p), content);
}
function rmrf(p) {
  var abs = path.join(ROOT, p);
  fs.rmSync ? fs.rmSync(abs, { recursive: true, force: true }) : (function () {
    try {
      var cmd = require('child_process').execFileSync;
      cmd('rm', ['-rf', abs]);
    } catch (e) { /* ignore */ }
  })();
}
function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(path.join(ROOT, dest)), { recursive: true });
  fs.writeFileSync(path.join(ROOT, dest), fs.readFileSync(path.join(ROOT, src)));
}
function copyDir(src, dest) {
  var from = path.join(ROOT, src);
  var to = path.join(ROOT, dest);
  mkdirp(to);
  walk(from, function (f) {
    var rel = path.relative(from, f);
    var target = path.join(to, rel);
    if (fs.statSync(f).isDirectory()) {
      mkdirp(target);
    } else {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, fs.readFileSync(f));
    }
  });
}
function mkdirp(p) {
  fs.mkdirSync(p, { recursive: true });
}
function walk(dir, fn) {
  if (!fs.existsSync(dir)) return;
  var entries = fs.readdirSync(dir);
  for (var i = 0; i < entries.length; i++) {
    var p = path.join(dir, entries[i]);
    var st = fs.statSync(p);
    if (st.isDirectory()) walk(p, fn);
    fn(p);
  }
}

function copyNpmWebAssets() {
  var copies = [
    ['node_modules/angular/angular.js', 'tolmach/static/assets/angular/angular.js'],
    ['node_modules/angular/angular.min.js', 'tolmach/static/assets/angular/angular.min.js'],
    ['node_modules/angular-dragdrop/src/angular-dragdrop.js', 'tolmach/static/assets/angular-dragdrop/src/angular-dragdrop.js'],
    ['node_modules/angular-local-storage/dist/angular-local-storage.min.js', 'tolmach/static/assets/angular-local-storage/dist/angular-local-storage.min.js'],
    ['node_modules/jquery/dist/jquery.min.js', 'tolmach/static/assets/jquery/dist/jquery.min.js'],
    ['node_modules/ng-file-upload/dist/ng-file-upload.js', 'tolmach/static/assets/ng-file-upload/ng-file-upload.js'],
    ['node_modules/ng-file-upload/dist/ng-file-upload.min.js', 'tolmach/static/assets/ng-file-upload/ng-file-upload.min.js'],
    ['node_modules/ng-file-upload/dist/ng-file-upload-all.js', 'tolmach/static/assets/ng-file-upload/ng-file-upload-all.js'],
    ['node_modules/ng-file-upload/dist/ng-file-upload-all.min.js', 'tolmach/static/assets/ng-file-upload/ng-file-upload-all.min.js'],
    ['node_modules/ng-file-upload/dist/ng-file-upload-shim.js', 'tolmach/static/assets/ng-file-upload/ng-file-upload-shim.js'],
    ['node_modules/ng-file-upload/dist/ng-file-upload-shim.min.js', 'tolmach/static/assets/ng-file-upload/ng-file-upload-shim.min.js'],
    ['node_modules/ng-file-upload/dist/FileAPI.js', 'tolmach/static/assets/ng-file-upload/FileAPI.js'],
    ['node_modules/ng-file-upload/dist/FileAPI.min.js', 'tolmach/static/assets/ng-file-upload/FileAPI.min.js'],
    ['node_modules/less/dist/less.js', 'tolmach/static/assets/less/dist/less.js'],
    ['node_modules/bootstrap/dist/js/bootstrap.min.js', 'tolmach/static/assets/bootstrap/dist/js/bootstrap.min.js'],
    ['node_modules/handsontable/dist/handsontable.full.min.js', 'tolmach/static/assets/handsontable/dist/handsontable.full.min.js'],
    ['node_modules/handsontable/dist/handsontable.full.css', 'tolmach/static/assets/handsontable/dist/handsontable.full.css'],
    ['node_modules/plotly.js/dist/plotly.min.js', 'tolmach/static/assets/plotly/plotly-v1.41.0.min.js'],
    ['node_modules/font-awesome/css/font-awesome.min.css', 'tolmach/static/assets/font-awesome/css/font-awesome.min.css']
  ];
  copies.forEach(function (c) { copyFile(c[0], c[1]); });
  copyDir('node_modules/bootstrap/fonts', 'tolmach/static/assets/bootstrap/fonts');
  // less sources are imported by tolmach/static/less/*.less via `../assets/bootstrap/less/...`
  copyDir('node_modules/bootstrap/less', 'tolmach/static/assets/bootstrap/less');
  copyDir('node_modules/font-awesome/fonts', 'tolmach/static/assets/font-awesome/fonts');
  copyDir('node_modules/handsontable/dist/moment', 'tolmach/static/assets/handsontable/dist/moment');
  copyDir('node_modules/handsontable/dist/numbro', 'tolmach/static/assets/handsontable/dist/numbro');
  console.log('npm web assets copied');
}

function compileLess(src, dest) {
  var less = require('less');
  var source = read(src);
  return new Promise(function (resolve, reject) {
    less.render(source, { filename: path.join(ROOT, src), compress: true, cleancss: true }, function (err, output) {
      if (err && err.message && /clean.?css/i.test(err.message)) {
        // retry without cleancss if the plugin is unavailable
        return less.render(source, { filename: path.join(ROOT, src), compress: true }, function (err2, out2) {
          if (err2) return reject(err2);
          write(dest, out2.css);
          resolve();
        });
      }
      if (err) return reject(err);
      write(dest, output.css);
      resolve();
    });
  });
}

function run() {
  console.log('== build.js (grunt replacement) ==');
  copyNpmWebAssets();

  console.log('clean dist + tmp');
  rmrf('tolmach/static/dist');
  rmrf('tmp');
  fs.mkdirSync(path.join(ROOT, 'tolmach/static/dist'), { recursive: true });
  fs.mkdirSync(path.join(ROOT, 'tmp'), { recursive: true });

  var steps = [];
  steps.push(compileLess('node_modules/bootstrap/less/bootstrap.less', 'tolmach/static/assets/bootstrap/dist/css/bootstrap.css'));
  steps.push(compileLess('tolmach/static/less/ace.less', 'tolmach/static/dist/ace.css'));
  steps.push(compileLess('tolmach/static/less/landing.less', 'tolmach/static/dist/landing.css'));
  steps.push(compileLess('tolmach/static/less/new_landing.less', 'tolmach/static/dist/new_landing.css'));
  steps.push(compileLess('tolmach/static/less/tolmach.less', 'tmp/tolmach.css'));
  steps.push(compileLess('tolmach/static/less/tolmach-dark-bootstrap.less', 'tmp/tolmach-dark-bootstrap.css'));
  steps.push(compileLess('tolmach/static/less/all.less', 'tolmach/static/dist/all.css'));

  Promise.all(steps).then(function () {
    console.log('less compiled');
    // concat css
    var concatCss =
      read('tmp/tolmach.css') +
      read('tolmach/static/assets/bootstrap/dist/css/bootstrap.css') +
      read('tolmach/static/assets/handsontable/dist/handsontable.full.css') +
      read('tmp/tolmach-dark-bootstrap.css');
    write('tolmach/static/dist/tolmach.css', concatCss);
    console.log('concat css done');

    // cssmin
    var CleanCSS = require('clean-css');
    var min = new CleanCSS().minify(concatCss);
    if (min.errors && min.errors.length) {
      console.error('clean-css errors:', min.errors);
      process.exit(1);
    }
    write('tolmach/static/dist/tolmach.min.css', min.styles);
    console.log('cssmin done');

    // clean tmp
    rmrf('tmp');

    // concat js
    var glob = [];
    function addJs(dir) {
      if (!fs.existsSync(path.join(ROOT, dir))) return;
      fs.readdirSync(path.join(ROOT, dir)).forEach(function (name) {
        var p = dir + '/' + name;
        if (fs.statSync(path.join(ROOT, p)).isDirectory()) addJs(p);
        else if (/\.js$/.test(name)) glob.push(p);
      });
    }
    addJs('tolmach/static/app');
    // grunt used ['*.js', '**/*.js'] -> this recursive walk covers both
    var js = glob.map(function (p) { return read(p); }).join(';');
    write('tolmach/static/dist/app.js', js);
    console.log('concat js done (' + glob.length + ' files)');

    // uglify
    var uglify = require('uglify-js');
    var result = uglify.minify(js, { fromString: true, mangle: false });
    if (result.error) { console.error(result.error); process.exit(1); }
    write('tolmach/static/dist/app.min.js', result.code);
    console.log('uglify done');

    // string-replace: cache-bust front_version
    var baseHtml = path.join(ROOT, 'templates/main/base.html');
    var html = fs.readFileSync(baseHtml, 'utf8');
    var rand = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    html = html.replace(/with front_version=".+?"/g, 'with front_version="' + rand + '"');
    fs.writeFileSync(baseHtml, html);
    console.log('string-replace done');

    console.log('== build complete ==');
  }).catch(function (e) {
    console.error('build failed:', e);
    process.exit(1);
  });
}

run();