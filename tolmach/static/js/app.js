'use strict';

/* App Module */

(function () {
    angular.module('tolmachApp', [
    ])
        .controller('transCtrl', function ($scope, $http) {
            $scope.activeEntry = null;
            $scope.textTab = 0;
            $http.post('.', {}).success(function (data) {
                $scope.entries = data;
                var entriesById = {};
                angular.forEach(data, function (val, key) {
                    entriesById[val.idInText] = val;
                });
                $scope.entriesById = entriesById;
            }).error(function (a) {
                console.log(a);
            });
            $scope.toogleEntry = function (entry) {
                if (entry.approved) {
                    return;
                }
                if ($scope.activeEntry === entry) {
                    $scope.activeEntry = null;
                } else {
                    $scope.activeEntry = entry;
                }
            };
            $scope.approveEntry = function (entry, parent) {
                $http.post('/api/entry-approve/', {id: entry.id}).success(function (data) {
                    entry.isApproved = true;
                    parent.approved = true;
                    parent.translation = entry.body;
                    $scope.activeEntry = null;
                })
            };
            $scope.suggestTranslation = function (translation, entry) {
                $http.post('/api/entry-translate/', {id: entry.id, text: translation}).success(function (data) {
                    entry.translations.push(data);
                    entry.mode = 0;
                })
            };
        })
        .run(function ($http) {
            $http.defaults.headers.post['X-CSRFToken'] = window['csrfToken'];
        })
        .config(function ($interpolateProvider) {
            // replace {{ by {=
            $interpolateProvider.startSymbol('{=');
            // replace }} by =}
            $interpolateProvider.endSymbol('=}');
        })
        .directive('entry', function () {
            return {
                template: function(elem, attr) {
                    var id = attr['entry'];

                    return '<span ng-click="activeEntry = entriesById[' + id + ']"' +
                                 'ng-class="{active: activeEntry.idInText === ' + id + ',' +
                                            'approved: entriesById[' + id + '].approved}">' +
                               '<span ng-show="textTab === 0">' + elem.html() + '</span>' +
                               '<span ng-show="textTab === 1" ' +
                                     'ng-bind="entriesById[' + id + '].translation"></span>' +
                           '</span>';
                },
                link: function (scope, element, attrs) {

                }
            };
        });
})();
