/*jslint node: true */
"use strict";


module.exports = function (grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        uglify: {
            dist: {
                files: {
                    'tolmach/static/dist/app.min.js': ['tolmach/static/dist/app.js']
                },
                options: {
                    mangle: false
                }
            }
        },

        clean: {
            tmp: {
                src: ['tmp']
            },
            dist: {
                src: ['tolmach/static/dist']
            }
        },

        less: {
            dist: {
                options: {
                    paths: [],
                    cleancss: true,
                    compress: true
                },
                files: {
                    "tolmach/static/assets/bootstrap/dist/css/bootstrap.css": "tolmach/static/assets/bootstrap/less/bootstrap.less",
                    "tolmach/static/dist/ace.css": "tolmach/static/less/ace.less",
                    "tolmach/static/dist/landing.css": "tolmach/static/less/landing.less",
                    "tmp/tolmach.css": "tolmach/static/less/tolmach.less"
                }
            }
        },

        stylus: {
            dist: {
                compress: true,
                files: {
                    'tolmach/static/dist/all.css': ['stylus/all.styl']
                }
            }
        },

        concat: {
            options: {
                separator: ';'
            },
            js: {
                src: ['tolmach/static/app/*.js', 'tolmach/static/app/**/*.js'],
                dest: 'tolmach/static/dist/app.js'
            },
            css: {
                src: [
                    'tmp/tolmach.css',
                    'tolmach/static/assets/bootstrap/dist/css/bootstrap.css',
                    'tolmach/static/assets/handsontable/dist/handsontable.full.css'

                ],
                dest: 'tolmach/static/dist/tolmach.css'
            }
        },

        jshint: {
            all: ['Gruntfile.js', 'tolmach/static/app/*.js', 'tolmach/static/app/**/*.js']
        },

        cssmin: {
            options: {
                shorthandCompacting: false,
                roundingPrecision: -1
            },
            target: {
                files: {
                    'tolmach/static/dist/tolmach.min.css': ['tolmach/static/dist/tolmach.css']
                }
            }
        },

        includeSource: {
            options: {
                basePath: 'tolmach/static/app/',
                baseUrl: '',
                templates: {
                    html: {
                        js: '<script src="/static/app/{filePath}"></script>'
                    }
                },
                typeMappings: {
                    'php': 'html'
                }
            },
            myTarget: {
                files: {
                    'templates/main/partial/include-js.html': 'templates/main/partial/include-js-template.html'
                }
            }
        }

    });

    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-stylus');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-include-source');

    grunt.registerTask('dev', [
        'includeSource'
    ]);
    grunt.registerTask('css', [
        'less:dist',
        'concat:css',
        'cssmin',
        'stylus:dist',
        'clean:tmp'
    ]);
    grunt.registerTask('js', [
        'concat:js',
        'uglify:dist'
    ]);
    grunt.registerTask('package', [
        'clean:dist',
        'css',
        'js'
    ]);
    grunt.registerTask('default', ['package']);
};
