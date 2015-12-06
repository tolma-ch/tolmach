(function () {
    'use strict';

    /* App Module */

    var module = angular.module('tolmachApp', [
        'ui.select',
        'mainControllers',
        'profileModule',
        'projectModule',
        'projectsModule',
        'textModule'
    ]);

    module.run(function ($http) {
        $http.defaults.headers.post['X-CSRFToken'] = window.csrfToken;
    });
    module.config(function ($interpolateProvider, $httpProvider) {
        // replace {{ by {=
        $interpolateProvider.startSymbol('{=');
        // replace }} by =}
        $interpolateProvider.endSymbol('=}');
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });
}());