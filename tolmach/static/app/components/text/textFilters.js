(function () {
    'use strict';

    var module = angular.module('textFilters', []);

    module.filter('trusted', ['$sce', function ($sce) {
        return function (text) {
            return $sce.trustAsHtml(text);
        };
    }]);
}());