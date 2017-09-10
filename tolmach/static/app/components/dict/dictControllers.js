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
                console.log(wordId);
                $('.meanings').css('display', 'none');
                if (wordId != lastMeaningNum){
                    $('#meanings-' + wordId).css('display', 'block');
                }
                lastMeaningNum = wordId;
            };
            $scope.searchWord = function () {
                //$scope.word = '';
                //alert(angular.toJson($scope.word));
                var notFoundBlock = document.getElementById('dict-nothing-found');
                notFoundBlock.style.display = "none";
                $scope.foundWords = [];
                $scope.wordToFind = "";
                var opts = {
                  lines: 13 // The number of lines to draw
                , length: 40 // The length of each line
                , width: 2 // The line thickness
                , radius: 16 // The radius of the inner circle
                , scale: 0.50 // Scales overall size of the spinner
                , corners: 0.4 // Corner roundness (0..1)
                , color: '#777676' // #rgb or #rrggbb or array of colors
                , opacity: 0 // Opacity of the lines
                , rotate: 0 // The rotation offset
                , direction: 1 // 1: clockwise, -1: counterclockwise
                , speed: 1 // Rounds per second
                , trail: 83 // Afterglow percentage
                , fps: 20 // Frames per second when using setTimeout() as a fallback for CSS
                , zIndex: 2e9 // The z-index (defaults to 2000000000)
                , className: 'spinner' // The CSS class to assign to the spinner
                , top: '50%' // Top position relative to parent
                , left: '50%' // Left position relative to parent
                , shadow: false // Whether to render a shadow
                , hwaccel: false // Whether to use hardware acceleration
                , position: 'absolute' // Element positioning
                };
                var target = document.getElementById('dict-body');
                var spinner = new Spinner(opts).spin(target);
                $http.post('/ajax/dict-search/', {
                        params: {
                            from: window['translationSourceLang'],
                            dest: window['translationTargetLang'],
                            //from: 'eng',
                            //dest: 'rus',
                            phrase: $scope.word
                        }
                    }).success(function (res) {
                        var results = [];
                        angular.forEach(res, function (elem, key){
                            results.push({id: key,
                                        word: elem['translation'],
                                        meanings: elem['meanings']
                            });
                        });
                        spinner.stop();
                        if (results && results.length == 0) {
                            var notFoundBlock = document.getElementById('dict-nothing-found');
                            notFoundBlock.style.display = "block";
                        } else {
                            $scope.wordToFind = $scope.word;
                            $scope.foundWords = results;
                        }
                        //$scope.$apply();
                        console.log(res);
                        console.log($scope.foundWords);
                    })
            }
        }
    ]);
}());