(function () {
    'use strict';

    var module = angular.module('mainDirectives', []);

    //module.directive('resize', ['$window', function ($window) {
    //    return {
    //        scope: {
    //            resize: "="
    //        },
    //        link: function (scope, element, attr) {
    //            var w = angular.element($window);
    //            scope.$watch(function () {
    //                return {
    //                    'h': w.height(),
    //                    'w': w.width()
    //                };
    //            }, function (newValue) {
    //                scope.resize();
    //            }, true);
    //
    //            w.bind('resize', function () {
    //                scope.$apply();
    //            });
    //        }
    //    };
    //}]);
    module.directive('resize', ['$window', function ($window) {
        return {
            scope: {
                resize: "="
            },
            link: function (scope, element, attr) {
                var w = angular.element($window);
                scope.$watch(function () {
                    return {
                        'h': w.height(),
                        'w': w.width()
                    };
                }, function (newValue) {
                    scope.resize(newValue);
                }, true);

                w.bind('resize', function () {
                    scope.$apply();
                });
            }
        };
    }]);
}());