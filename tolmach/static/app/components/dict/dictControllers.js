(function () {
    'use strict';

    var module = angular.module('dictControllers', []);

    module.controller('DictCtrl', ['$scope', '$http', '$window', '$sce', 'Dict', '$rootScope',
        function ($scope, $http, $window, $sce, Dict, $rootScope) {
            var lastMeaningNum = 0;
            var showDictModal = 0;
            $rootScope.setDictWord = function (word) {
                $scope.word = word;
                $scope.searchWord();
            };
            $scope.dictSourceLang = window['translationSourceLang'].split("-")[0];
            $scope.dictTargetLang = window['translationTargetLang'].split("-")[0];
            $scope.style = {};
            $scope.$on('GlobalResize', function (e, w) {
                var height = w.h,
                    width = w.w;
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
            $scope.dictSwitchLangs = function () {
                var cur_source_lang = $scope.dictSourceLang;
                var cur_target_lang = $scope.dictTargetLang;
                $scope.dictSourceLang = cur_target_lang;
                $scope.dictTargetLang = cur_source_lang;
            };
            $scope.searchWord = function () {
                var notFoundBlock = document.getElementById('dict-nothing-found');
                notFoundBlock.style.display = "none";
                $scope.foundWords = [];
                $scope.wordToFind = "";

                var progressIcon = document.getElementById("dict-progress-anim");
                progressIcon.style.display = "inline-block";

                $http.post('/ajax/dict-search/', {
                        params: {
                            from: $scope.dictSourceLang,
                            dest: $scope.dictTargetLang,
                            phrase: $scope.word,
                            text: window['textId'],
                        }
                    }).success(function (res) {
                        var results = [];
                        angular.forEach(res, function (elem, key){
                            results.push({id: key,
                                        dict: elem['dict'],
                                        word: elem['word'],
                                        definition: elem['definition'].replace(/(\n)+/g, '<br />'),
                                        meanings: elem['meanings']
                            });
                        });
                        progressIcon.style.display = "none";
                        if (results && results.length == 0) {
                            var notFoundBlock = document.getElementById('dict-nothing-found');
                            notFoundBlock.style.display = "block";
                        } else {
                            $scope.wordToFind = $scope.word;
                            $scope.foundWords = results;
                        }
                    })
            }
        }
    ]);
}());