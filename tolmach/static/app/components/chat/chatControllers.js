(function () {
    'use strict';

    var module = angular.module('chatControllers', []);

    module.controller('ChatCtrl', ['$scope', '$window', 'Chat',
        function ($scope, $window, Chat) {
            $scope.style = {};
            $scope.$on('GlobalResize', function (e, w) {
                var height = w.h,
                    width = w.w;
                //$scope.style.right = width + 'px';
                //$scope.style.right = width + 'px';
            });
            $scope.textareaKeypress = function (event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (event.ctrlKey && (code === 13 || code === 10)) {
                    Chat.sendMessage(this.value);
                }
            };
        }
    ]);
}());