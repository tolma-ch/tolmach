(function () {
    'use strict';

    var module = angular.module('textDirectives', []);

    module.directive("fileread", [function () {
        return {
            scope: {
                fileread: "="
            },
            link: function (scope, element) {
                element.bind("change", function (changeEvent) {
                    var reader = new FileReader();
                    reader.onload = function (loadEvent) {
                        scope.$apply(function () {
                            scope.fileread['file'] = loadEvent.target.result;
                        });
                    };
                    scope.fileread = changeEvent.target.files[0];
                    reader.readAsDataURL(changeEvent.target.files[0]);
                });
            }
        }
    }]);

    module.directive('entry', [function () {
        return {
            template: function (elem, attr) {
                var id = attr['entry'];

                return '<span ng-click="focusEntry(' + id + ')" ' +
                    'id="res-entry-' + id + '" ' +
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
    }]);
    module.directive('glossaryWord', [function () {
        return {
            template: function (elem, attr) {
                var word = attr['glossaryWord'];

                return '<span ng-show="entry !== activeEntry || entry.mode !== 1">'
                    + elem.html() + '</span>' +
                    '<span ng-show="entry === activeEntry && entry.mode === 1" ' +
                    'class="glossary-word" ' +
                    'ng-click="insertText($event, entry, \'' + word + '\')" ' +
                    'tooltip-append-to-body="true" ' +
                    'tooltip-placement="top" ' +
                    'tooltip="' + word + '">'
                    + elem.html() + '</span>';
            },
            link: function (scope, element, attrs) {
            }
        };
    }]);
    module.directive('htmlContent', ['$compile', '$parse', function ($compile, $parse) {
        return {
            link: function (scope, element, attr) {
                var content = attr['htmlContent'];
                element.html($parse(content)(scope));
                $compile(element.contents())(scope);
            }
        }
    }]);
    module.directive('insertText', ['$rootScope', function ($rootScope) {
        return {
            link: function (scope, element) {
                if (typeof scope.entry !== 'undefined') {
                    scope.entry = scope.entry || undefined;
                    var id = scope.entry.id;
                    $rootScope.$on('insertText', function (e, data) {
                        if (data['id'] !== id) {
                            return;
                        }
                        var domElement = element[0],
                            val = data['text'],
                            result = '';
                        if (document.selection) {
                            domElement.focus();
                            //var sel = document.selection.createRange();
                            result = val;
                            scope.entry.suggestion = result;
                            domElement.focus();
                        } else if (domElement.selectionStart || domElement.selectionStart === 0) {
                            var startPos = domElement.selectionStart;
                            var endPos = domElement.selectionEnd;
                            var scrollTop = domElement.scrollTop;
                            result = domElement.value.substring(0, startPos) + val + domElement.value.substring(endPos, domElement.value.length);
                            scope.entry.suggestion = result;
                            domElement.focus();
                            domElement.selectionStart = startPos + val.length;
                            domElement.selectionEnd = startPos + val.length;
                            domElement.scrollTop = scrollTop;
                        } else {
                            result = domElement.value + val;
                            scope.entry.suggestion = result;
                            domElement.focus();
                        }
                    });
                }
            }
        }
    }]);
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
                    scope.resize();
                }, true);

                w.bind('resize', function () {
                    scope.$apply();
                });
            }
        };
    }]);
    module.directive('tag', [function () {
        return {
            scope: {
                i: "="
            },
            link: function (scope, element, attr) {
                var leftTag = angular.element('<a href="#" class="tag-left" i="' + scope.i + '">'),
                    rightTag = angular.element('<a href="#" class="tag-right" i="' + scope.i + '">'),
                    clickTrigger = function () {
                        scope.$emit('tagClick', scope.i);
                    };
                leftTag.on("click", clickTrigger);
                rightTag.on("click", clickTrigger);
                element.prepend(leftTag);

                element.append(rightTag);
            }
        };
    }]);
}());