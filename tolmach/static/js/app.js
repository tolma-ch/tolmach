'use strict';

/* App Module */

(function () {
    angular.module('tolmachApp', [
    ])
        .controller('transCtrl', function ($scope, $http) {
            $scope.activeEntry = null;
            $http.post('.', {}).success(function (data) {
                $scope.entries = data;
            });
        })
        .run(function ($http) {
            $http.defaults.headers.post['X-CSRFToken'] = window['csrfToken'];
        })
        .config(function ($interpolateProvider) {
            // replace {{ by {=
            $interpolateProvider.startSymbol('{=');
            // replace }} by =}
            $interpolateProvider.endSymbol('=}');
        });
})();
