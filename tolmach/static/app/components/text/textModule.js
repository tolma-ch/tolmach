(function () {
    'use strict';

    angular.module('textModule', [
        'ui.bootstrap',
        'contenteditable',
        'textControllers',
        'textDirectives',
        'textFilters',
        'LocalStorageModule'
    ]);
}());