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
                    'approved: entriesById[' + id + '].approved,' +
                    'disabled: entriesById[' + id + '].disabled}">' +
                    '<span ng-show="textTab == 0">' + elem.html() + '</span>' +
                    '<span ng-show="textTab == 1" ' +
                    'ng-bind-html="entriesById[' + id + '].translation | trusted"></span>' +
                    '</span>';
            },
            link: function (scope, element, attrs) {

            }
        };
    }]);
    module.directive('entryPage', [function () {
        return {
            template: function (elem, attr) {
                var page = attr['entryPage'];
                return '<span ng-show="page == ' + page + '">' +
                    elem.html() +
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

                return '<span ng-show="entry !== activeEntry">'
                    + elem.html() + '</span>' +
                    '<span ng-show="entry === activeEntry" ' +
                    'class="glossary-word" ' +
                    'ng-click="insertText($event, entry, \'' + word + '\')" ' +
                    'tooltip-append-to-body="true" ' +
                    'tooltip-placement="top" ' +
                    'uib-tooltip="' + word + '">'
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
                            result = domElement.innerHTML + val;
                            scope.entry.suggestion = result;
                            domElement.focus();
                        }
                    });
                }
            }
        }
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
                        scope.$emit('tagClickBefore', scope.i);
                        scope.$emit('tagClick', scope.i);
                        scope.$emit('tagClickAfter', scope.i);
                    };
                leftTag.on("click", clickTrigger);
                rightTag.on("click", clickTrigger);
                element.prepend(leftTag);

                element.append(rightTag);
            }
        };
    }]);
    module.directive('textEditor', [function () {
        var lastFixed = '',
            fixTags = function ($element) {
                var element = $element[0];
                if (lastFixed === element.innerHTML) {
                    return;
                }
                var nodes = [],
                    state = false,
                    extend = false,
                    modified = false,
                    extendNode,
                    lastBr,
                    allowBr = true,
                    i;
                angular.forEach(element.childNodes, function (node) {
                    nodes.push(node);
                });
                while (nodes.length) {
                    var node = nodes.shift(),
                        j,
                        index,
                        type;
                    if (allowBr && (node.tagName === 'BR')) {
                        lastBr = node;
                        continue;
                    }
                    if (node.tagName === 'HR') {
                        for (j = 0; j < node.attributes.length; j++) {
                            var attribute = node.attributes[j];
                            if (attribute.name === 'l') {
                                type = 'l';
                            }
                            if (attribute.name === 'r') {
                                type = 'r';
                            }
                            if (attribute.name === 's') {
                                type = 's';
                            }
                            if (attribute.name === 'i') {
                                index = attribute.value;
                            }
                        }
                        if (type && index) { // если это таки тег как надо
                            if (type === 's') {
                                // сингл-тег можем вставлять куда угодно
                            } else {
                                if (state) { // если у нас уже отрыт тег
                                    if (type === 'r') { // пришёл закрывающий
                                        if (index === state) { // если закрывается открытый тег
                                            state = false; // всё ок, выходим из состояния
                                            if (extend === index) {
                                                // у нас дважды был открыт один тег, а закрыли его только один раз. Запомним ноду
                                                extendNode = node;
                                            }
                                        } else { // пришёл закрывающий, но не тот
                                            // удалим
                                            element.removeChild(node);
                                            modified = true;
                                            extend = false;
                                        }
                                    } else {
                                        if (state === index) {
                                            // попытка открыть тег, который уже открыт - удалаем
                                            element.removeChild(node);
                                            // это может быть случай, когда у нас пользователь пытается увеличить область выделения. запоминаем, что открыли дважды
                                            extend = index;
                                        } else {
                                            // пришёл новый открывающий, закроем сначала предыдущий
                                            element.insertBefore(angular.element('<hr r i="' + state + '">')[0], node);
                                            extend = false;
                                        }
                                        modified = true;
                                        state = index;
                                    }
                                } else {
                                    if (type === 'l') {
                                        // всё тип-топ, мы открываем новый тег
                                        state = index;
                                    } else {
                                        if (extendNode && index === extend) { // у нас дважды закрывается один тег, удаляем предыдущий, оставляем последний
                                            element.removeChild(extendNode);
                                        } else {
                                            element.removeChild(node);
                                        }
                                        modified = true;
                                    }
                                    extend = false;
                                }
                            }
                            continue;
                        }
                    }
                    if (node.nodeType === 3) {
                        //var prevNode = node.previousSibling;
                        //if (prevNode && prevNode.nodeType === 3) {
                        //    var sel = window.getSelection();
                        //    if (sel.rangeCount > 0) {
                        //        var range = win.getSelection().getRangeAt(0);
                        //    }
                        //    prevNode.textContent += node.textContent;
                        //    node.remove();
                        //}
                        lastBr = false;
                        continue;
                    }
                    if (node.nodeType === 1) {
                        if (allowBr && (node.tagName === 'DIV')) {
                            if (node.childNodes
                                && (node.childNodes.length === 1)
                                && node.childNodes[0].nodeType === 1
                                && node.childNodes[0].tagName === 'BR') {
                                continue;
                            }
                            lastBr = document.createElement("br");
                            element.insertBefore(lastBr, node);
                        }
                        if (node.childNodes && (node.childNodes.length > 0)) {
                            var nextNode = node.nextSibling,
                                childNodes = [];
                            angular.forEach(node.childNodes, function (node) {
                                childNodes.push(node);
                            });
                            var newNode = childNodes.shift();
                            element.replaceChild(newNode, node);
                            nodes.unshift(newNode);
                            angular.forEach(childNodes, function (newNode) {
                                if (nextNode) {
                                    element.insertBefore(newNode, nextNode);
                                } else {
                                    element.appendChild(newNode);
                                }
                                nodes.unshift(newNode);
                            });
                            modified = true;
                        } else {
                            if (node.textContent) {
                                //var prevNode = node.previousSibling;
                                //if (prevNode && prevNode.nodeType === 3) {
                                //    prevNode.textContent += node.textContent;
                                //    node.remove();
                                //} else {
                                    element.replaceChild(document.createTextNode(node.textContent), node);
                                    lastBr = false;
                                //}
                            } else {
                                node.remove();
                            }
                            modified = true;
                        }
                    }
                }
                if (state) { // если у нас ещё отрыт тег
                    element.appendChild(angular.element('<hr r i="' + state + '">')[0], node);
                }
                if (modified) {
                    $element.trigger('input');
                    //$scope.activeEntry.suggestion = element.textContent;
                    //$timeout(function () {
                    //    //$scope.$apply(function () {

                    //    //});
                    //    console.log($scope.activeEntry ? $scope.activeEntry.suggestion : 'null');
                    //}, 1);
                }
                lastFixed = element.innerHTML;
            };
        return {
            link: function (scope, element) {
                element.on('keydown', function (e) {
                    var code = (e.charCode) ? e.charCode : ((e.which) ? e.which : e.keyCode);
                    if (e.ctrlKey) {
                        if (code === 66) { // b
                            e.preventDefault();
                        }
                        if (code === 73) { // i
                            e.preventDefault();
                        }
                        if (code === 85) { // u
                            e.preventDefault();
                        }
                    }
                    setTimeout(function () {
                        fixTags(element);
                    }, 0);
                });
                element.on('blur', function () {
                    fixTags(element);
                });
                element.on('drop', function (e) {
                    //e.preventDefault();
                    //var text = (e.originalEvent || e).dataTransfer.getData("text/plain");
                    //document.execCommand("insertHTML", false, text);
                    setTimeout(function () {
                        fixTags(element);
                    }, 0);
                });
                element.on('paste', function (e) {

                    // cancel paste
                    e.preventDefault();

                    // get text representation of clipboard
                    var text = (e.originalEvent || e).clipboardData.getData("text/plain");
                    text = text.replace(/>/g, "&gt;").replace(/</g, "&lt;");


                    // insert text manually
                    document.execCommand("insertHTML", false, text);

                    //
                    //var clipboardData = (e.originalEvent || e);
                    //clipboardData.setData(clipboardData.getData('text'));
                    setTimeout(function () {
                        fixTags(element);
                    }, 0);
                });

                scope.$on('tagClickBefore', function (event, index) {
                    fixTags(element);
                });
                scope.$on('tagClickAfter', function (event, index) {
                    fixTags(element);
                });
            }
        };
    }]);

    module.directive('focusMe', ['$timeout', function($timeout) {
      return {
        link: function(scope, element, attrs) {
          scope.$watch(attrs.focusMe, function(value) {
            if(value === true) {
              console.log('value=',value);
                $timeout(function () {
                    element[0].focus();
                    element[0].setSelectionRange(0, element[0].value.length)
                }, 100);
                scope[attrs.focusMe] = false;
            }
          });
        }
      };
    }]);
    module.directive('dynamic', function ($compile) {
      return {
        restrict: 'A',
        replace: true,
        link: function (scope, ele, attrs) {
          scope.$watch(attrs.dynamic, function(html) {
            ele.html(html);
            $compile(ele.contents())(scope);
          });
        }
      };
    });
}());