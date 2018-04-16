(function () {
    'use strict';

    /* App Module */

    var module = angular.module('tolmachApp', [
        'ui.select',
        'ui.toggle',
        'ngClickCopy',
        'mainModule',
        'profileModule',
        'projectModule',
        'projectsModule',
        'organizationsModule',
        'textModule',
        'chatModule',
        'dictModule'
    ]);

    module.run(function ($http) {
        $http.defaults.headers.post['X-CSRFToken'] = window.csrfToken;
    });
    module.config(function ($interpolateProvider, $httpProvider, $locationProvider) {
        // replace {{ by {=
        $interpolateProvider.startSymbol('{=');
        // replace }} by =}
        $interpolateProvider.endSymbol('=}');
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });
}());