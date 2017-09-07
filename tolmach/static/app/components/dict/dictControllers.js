(function () {
    'use strict';

    var module = angular.module('dictControllers', []);

    module.controller('DictCtrl', ['$scope', '$window', 'Dict',
        function ($scope, $window, Chat) {
            var lastMeaningNum = 0;
            var showDictModal = 0;
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
                    Dict.sendMessage(this.value);
                }
            };
            $scope.showMeanings = function (wordId) {
                $('.meanings').css('display', 'none');
                if (wordId != lastMeaningNum){
                    $('#meanings-' + wordId).css('display', 'block');
                }
                lastMeaningNum = wordId;
            }
        }
    ]);
}());