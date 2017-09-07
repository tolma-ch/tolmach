(function () {
    'use strict';

    var module = angular.module('dictServices', []);

    module.factory('Dict', ['$http',
        function ($http) {
            var self = {};
            self.sendMessage = function () {

            };
            return self;
        }
    ]);
}());