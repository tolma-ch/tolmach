/*jslint node: true */
"use strict";


module.exports = function (grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        uglify: {
            dist: {
                files: {
                    'tolmach/static/jsdist/app.min.js': ['tolmach/static/jsdist/app.js']
                },
                options: {
                    mangle: false
                }
            }
        },

        clean: {
            temp: {
                src: ['tmp']
            },
            dist: {
                src: ['tolmach/static/jsdist']
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
                    "tolmach/static/cssdist/ace.css": "less/ace.less"
                }
            }
        },

        stylus: {
            dist: {
                compress: true,
                files: {
                    'tolmach/static/cssdist/all.css': ['stylus/all.styl']
                }
            }
        },

        concat: {
            options: {
                separator: ';'
            },
            dist: {
                src: ['tolmach/static/app/*.js', 'tolmach/static/app/**/*.js', 'tmp/*.js'],
                dest: 'tolmach/static/jsdist/app.js'
            }
        },

        jshint: {
            all: ['Gruntfile.js', 'tolmach/static/app/*.js', 'tolmach/static/app/**/*.js']
        },

        connect: {
            server: {
                options: {
                    hostname: 'localhost',
                    port: 8080
                }
            }
        },

        watch: {
            dev: {
                files: ['Gruntfile.js', 'app/*.js', '*.html', 'assets/**/*.less'],
                tasks: ['jshint', 'karma:unit', 'html2js:dist', 'concat:dist', 'less:dev', 'clean:temp'],
                options: {
                    atBegin: true
                }
            },
            min: {
                files: ['Gruntfile.js', 'app/*.js', '*.html', 'assets/**/*.less'],
                tasks: ['jshint', 'karma:unit', 'html2js:dist', 'concat:dist', 'less:dist', 'clean:temp', 'uglify:dist'],
                options: {
                    atBegin: true
                }
            }
        },

        karma: {
            options: {
                configFile: 'config/karma.conf.js'
            },
            unit: {
                singleRun: true
            },
            junit: {
                singleRun: true,
                reporters: ['junit', 'coverage']
            },
            continuous: {
                singleRun: false,
                autoWatch: true
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-connect');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-stylus');
    grunt.loadNpmTasks('grunt-contrib-less');

    grunt.registerTask('dev', ['clean:dist', 'connect:server', 'watch:dev']);
    grunt.registerTask('test', ['clean:dist', 'jshint', 'karma:continuous']);
    grunt.registerTask('junit', ['clean:dist', 'jshint', 'karma:junit']);
    grunt.registerTask('minified', ['clean:dist', 'connect:server', 'watch:min']);
    grunt.registerTask('package', [
        'clean:dist',
        'concat:dist',
        'uglify:dist'
    ]);
    grunt.registerTask('default', ['package']);
};
