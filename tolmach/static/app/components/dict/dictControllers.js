(function () {
    'use strict';

    var module = angular.module('dictControllers', []);

    module.controller('DictCtrl', ['$scope', '$http', '$window', 'Dict',
        function ($scope, $http, $window, Dict) {
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
            };
            $scope.searchWord = function () {
                //$scope.word = '';
                //alert(angular.toJson($scope.word));
                $scope.foundWords = [];
                $http.post('/ajax/dict-search/', {
                        params: {
                            //from: $scope.langPair3[0],
                            //dest: $scope.langPair3[1],
                            from: 'eng',
                            dest: 'rus',
                            phrase: $scope.word
                        }
                    }).success(function (res) {
                        var results = [];
                        angular.forEach(res, function (elem){
                            $scope.foundWords.push(elem['translation']);
                        });
                        //$scope.$apply();
                        console.log(res);
                        console.log($scope.foundWords);
                        //$scope.$parent.translationResults = results;
                        //$scope.$parent.translatePopupStyle = {
                        //    display: 'block',
                        //    left: coords['x'] + 'px',
                        //    top: coords['y'] + 'px'
                        //};
                        //$scope.$parent.showTranslatePopup = true;
                        //if ($scope.$parent.showTranslatePopup) {
                        //    $timeout(function () {
                        //        var elem = $('#translation-popup'),
                        //            elemWidth = elem.width(),
                        //            left = coords['x'] + (width - elemWidth) / 2;
                        //        $scope.$parent.translatePopupStyle.left = left + 'px';
                        //    },1);
                        //}
                    })
            }
        }
    ]);
}());