(function () {
    'use strict';

    var module = angular.module('chatServices', []);

    module.factory('Chat', ['$http',
        function ($http) {
            var self = {};
            self.sendMessage = function () {

            };
            return self;
        }
    ]);
}());