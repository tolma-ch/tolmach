module.exports = (grunt) ->
  version = grunt.file.readJSON("package.json").version
  fs = require "fs"

  grunt.loadNpmTasks "grunt-contrib-concat"
  grunt.loadNpmTasks "grunt-contrib-clean"
  grunt.loadNpmTasks "grunt-contrib-requirejs"
  grunt.loadNpmTasks "grunt-version"
  grunt.loadNpmTasks "grunt-contrib-coffee"
  grunt.loadNpmTasks "grunt-contrib-stylus"
  grunt.loadNpmTasks "grunt-contrib-uglify"
  grunt.loadNpmTasks "grunt-coffeelint"
  grunt.loadNpmTasks "grunt-contrib-watch"


  grunt.registerTask "components", 
  [
    "coffee:components", "concat:components", "stylus:components", "stylus:all"
  ]

  grunt.registerTask "default",
  [
    "components"
  ]

  grunt.registerTask "build", 
  [
    "version:prerelease", "default"
  ]

  grunt.registerTask "patch",
  [
    "version:patch", "default"
  ]

  grunt.registerTask "minor",
  [
    "version:minor", "default"
  ]

  grunt.registerTask "major",
  [
    "version:major", "default"
  ]

  grunt.initConfig
    pkg: grunt.file.readJSON("package.json")

    concat:
      components:
        files: 
          "../media/js/all.js": [ "../components/**/scripts/*.js" ]
          "../media/css/all.styl": [ "../components/main/mixins.styl", "../components/main/styles/main.styl", "../components/**/styles/*.styl" ]

    uglify:
      all:
        files: ["../media/js/all.js"]

    stylus:
      components:
        expand: true
        cwd: "../components/"
        src: ["**/styles/*.styl"]
        dest: "../components/"
        ext: ".css"
        options:
          yuicompress: true

      all:
        files: 
          "../media/css/all.css": "../media/css/all.styl"

    coffee:
      components:
        expand: true
        cwd: "../components/"
        src: ["**/scripts/*.coffee"]
        dest: "../components/"
        ext: ".js"

    watch:
      components:
        expand: true
        cwd: "../components/"
        files: [
          "../components/**/scripts/*.coffee",
          "../components/**/styles/*.styl",
          "../templates/components/**/*.html"
        ]
        tasks: "build"
  
        options:
          spawn: false
          interrupt: true

    version:
      options:
        prefix: '[^\\-][vV]ersion[\'"]?\\s*[:=]\\s*[\'"]?'

      prerelease: 
        options:
          release: "prerelease"
        src: ["../components/main/scripts/_.coffee", "package.json"]

      patch: 
        options:
          release: "patch"
        src: ["../components/main/scripts/_.coffee", "package.json"]

      minor:
        options:
          release: "minor"
        src: ["../components/main/scripts/_.coffee", "package.json"]

      major: 
        options:
          release: "major"
        src: ["../components/main/scripts/_.coffee", "package.json"]
      
