(function () {
    'use strict';

    var module = angular.module('textControllers', []);

    module.controller('transCtrl', ['$rootScope', '$scope', '$http', '$timeout',
        function ($rootScope, $scope, $http, $timeout) {
            var clearTags = function (text) {
                    var div = document.createElement("div");
                    div.innerHTML = text;
                    return div.textContent || div.innerText || "";
                },
                updateTranslation = function (entry) {
                    if (!entry.isApproved) {
                        entry.translation = clearTags(entry['rawBody']);
                        for (var i = entry.translations.length - 1; i >= 0; i -= 1) {
                            var translation = entry.translations[i];
                            if (translation.author.id === $scope.user) {
                                entry.translation = clearTags(translation['body']);
                                break;
                            }
                        }
                    }
                },
                textId = window['textId'],
                getYaMachines = function (entry) {
                    $http.post('/api/ya-translate/', {
                        lang_pair: $scope.langPair,
                        entry_body: clearTags(entry['rawBody'])
                    }).success(function (data) {
                        entry.yaMachines = [{
                            text: data
                        }];
                    }).error(function (a) {
                        //console.error(a);
                    });
                },
                getTmdbVariants = function (entry) {
                    $http.post('/api/tmdb-search/', {
                        entry_id: entry['id'],
                        lang_pair: $scope.langPair
                    }).success(function (data) {
                        entry.tmdbVariants = data;
                    }).error(function (a) {
                        //console.error(a);
                    });
                };
            $scope.clearTags = clearTags;
            $scope.activeEntry = null;
            $scope.textTab = 0;
            $scope.userIsManager = false;
            $http.get('/api/entry/', {
                params: {
                    text: textId,
                    target_lang: window['translationTargetLang']
                }
            }).success(function (data) {
                var entries = data['entries'];
                $scope.userIsManager = !!data['user_is_manager'];
                $scope.translationAllowed = !!data['translation_allowed'];
                $scope.langPair = data['lang_pair'];
                $scope.langPair3 = data['639_3'];
                $scope.user = data['user'];
                var entriesById = {},
                    i, entry;
                for (i = entries.length - 1; i >= 0; i--) {
                    entry = entries[i];
                    updateTranslation(entry);
                    entry.mode = (angular.isArray(entry['translations']) && !!entry['translations'].length)
                    || !$scope.translationAllowed ? 0 : 1;
                    entriesById[entry['idInText']] = entry;
                }
                $scope.entries = entries;
                $scope.entriesById = entriesById;
            }).error(function (a) {
                console.log(a);
            });
            $scope.addMachineSuggestion = function (entry, machine) {
                if (entry.suggestion) {
                    entry.suggestion += ' ' + machine.text;
                } else {
                    entry.suggestion = machine.text;
                }
            };
            var scrollToEntry = function (entry) {
                    setTimeout(function () {
                        var $body = $('html, body'),
                            $container = $('#translations-container'),
                            $elem = $('#entry-' + entry.idInText),
                            $resElem = $('#res-entry-' + entry.idInText),
                            bodyTop = $body.scrollTop(),
                            containerShift = $container.scrollTop() + $elem.offset()['top'] - Math.max($container.offset()['top'], bodyTop),
                            resTop = $resElem.offset()['top'] - bodyTop,
                            minTop = 10,
                            maxTop = Math.max(0, $(window).height() - $resElem.height()) - 20,
                            bodyShift = 0;
                        if (resTop < minTop) {
                            bodyShift = resTop - minTop;
                        }
                        if (resTop > maxTop) {
                            bodyShift = resTop - maxTop;
                        }
                        if (bodyShift) {
                            $body.stop().animate({
                                scrollTop: bodyTop + bodyShift
                            }, 500);
                        }
                        $container.stop().animate({
                            scrollTop: containerShift - bodyShift
                        }, 500);
                    }, 100);
                },
                expandEntry = function (entry) {
                    if (!entry.approved) {
                        if (typeof entry['machines'] === 'undefined') {
                            getYaMachines(entry);
                            getTmdbVariants(entry);
                        }
                        $scope.activeEntry = entry;
                        if (entry.mode === 1) {
                            setTimeout(function () {
                                $('#entry-suggestion-' + entry.id).focus();
                            }, 10);
                        }
                    }
                    scrollToEntry(entry);
                };
            $scope.toggleEntry = function (entry) {
                if ($scope.activeEntry === entry) {
                    $scope.activeEntry = null;
                } else {
                    expandEntry(entry);
                }
            };
            $scope.focusEntry = function (id) {
                var entry = $scope.entriesById[id];
                expandEntry(entry);
            };
            $scope.approveEntry = function (translation, entry) {
                $http.post('/api/entry-approve/', {id: translation.id}).success(function () {
                    translation.isApproved = true;
                    entry.approved = true;
                    entry.translation = translation.body;
                    $scope.activeEntry = null;
                    var t;
                    for (var i = entry['translations'].length - 1; i >= 0; i--) {
                        t = entry['translations'][i];
                        if (t.id !== translation.id) {
                            t.isApproved = false;
                        }
                    }
                })
            };
            $scope.disapproveEntry = function (entry, parent) {
                $http.post('/api/entry-disapprove/', {id: entry.id}).success(function () {
                    entry.isApproved = false;
                    parent.approved = false;
                    $scope.activeEntry = parent;
                    parent.translation = '';
                    updateTranslation(parent);
                })
            };
            $scope.suggestTranslation = function (entry) {
                var suggestionId = entry['suggestionId'],
                    data = {
                        id: entry.id,
                        text: entry.suggestion,
                        target_lang: window['translationTargetLang']
                    };
                if (suggestionId) {
                    data['translation_id'] = suggestionId;
                }
                entry.suggestionId = false;
                $http.post('/api/entry-translate/', data).success(function (data) {
                    if (suggestionId) {
                        var i,
                            translation;
                        for (i = entry['translations'].length - 1; i >= 0; i--) {
                            translation = entry['translations'][i];
                            if (translation.id == suggestionId) {
                                translation.body = data.body;
                                if (translation.isApproved === true) {
                                    entry.approved = true;
                                    entry.translation = translation.body;
                                } else {
                                    updateTranslation(entry);
                                }
                                break;
                            }
                        }
                    } else {
                        entry['translations'].push(data);
                        updateTranslation(entry);
                    }
                    entry.mode = 0;
                    entry.suggestion = '';
                    if (data.isApproved === true) {
                        entry.approved = true;
                    }
                })
            };
            $scope.editTranslation = function (entry, translation) {
                entry.mode = 1;
                entry.suggestion = translation.body;
                entry.suggestionId = translation.id;
            };
            $scope.voteTranslation = function (entry, translation) {
                translation.busy = true;
                var vote = !translation.isVoted,
                    data = {
                        text: textId,
                        entry: translation.id,
                        vote: vote ? 1 : 0
                    };
                translation.isVoted = vote;
                $http.post('/api/entry/vote/', data).success(function (data) {
                    translation.busy = false;
                }).error(function (data) {
                    translation.isVoted = !vote;
                    translation.busy = false;
                })

            };
            $scope.cancelEditing = function (entry) {
                entry.mode = 0;
                entry.suggestion = '';
                entry.suggestionId = false;
            };
            $scope.insertText = function (e, entry, text) {
                if (entry !== $scope.activeEntry && entry.mode !== 1) {
                    return;
                }
                e.stopPropagation();
                $rootScope.$broadcast('insertText', {
                    'id': entry.id,
                    'text': text
                });
                //entry.suggestion += text;
            };
            $scope.textareaKeypress = function (event, entry) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (event.ctrlKey && (code === 13 || code === 10)) {
                    $scope.suggestTranslation(entry);
                    var i,
                        found = false;
                    for (i in $scope.entries) {
                        var someEntry = $scope.entries[i];
                        if (found === true && !someEntry.approved) {
                            $scope.toggleEntry(someEntry);
                            break;
                        }
                        if (someEntry === entry) {
                            found = true;
                        }
                    }
                }
            };
            $scope.textareaKeydown = function (event, entry) {
                $timeout(function () {
                    fixTags($('#entry-suggestion-' + entry.id)[0]);
                }, 0);
            };
            $scope.textareaBlur = function (event, entry) {
                fixTags($('#entry-suggestion-' + entry.id)[0]);
            };
            $scope.$on('GlobalKeydown', function (e, event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (event.ctrlKey && event.altKey) {
                    if (code === 84) { // Ctrl- Alt - t
                        translate();
                    }
                    return;
                }
                if (event.ctrlKey) {
                    if ((code === 38 || code === 40) && $scope.entries.length) {
                        var index = $scope.entries.indexOf($scope.activeEntry),
                            entry;
                        if (code === 38) {
                            //up
                            if (index === -1) {
                                entry = $scope.entries[$scope.entries.length - 1];
                            } else {
                                if (index === 0) {
                                    entry = $scope.entries[$scope.entries.length - 1];
                                } else {
                                    entry = $scope.entries[index - 1];
                                }
                            }
                        }
                        if (code === 40) {
                            //down
                            if (index === -1) {
                                entry = $scope.entries[0];
                            } else {
                                if (index < $scope.entries.length - 1) {
                                    entry = $scope.entries[index + 1];
                                } else {
                                    entry = $scope.entries[0];
                                }
                            }
                        }
                        $scope.focusEntry(entry.idInText);
                    }

                }
            });
            $scope.taggedSelected = function () {

            };
            (function (scope) {
                var steps,
                    nextStep = function (event) {
                        event.customized = true;
                        if (event.targetScope.clickBlock) {
                            event.targetScope.clickBlock();
                        } else {
                            steps.length && steps.shift()(event.targetScope);
                        }
                    };
                scope.$on('helpPresentationStart', function (event) {
                    var focusedEntry;
                    steps = [
                        function (helper) {
                            helper.currentBlock = $('#translations-container');
                            helper.clickBlock = false;
                            helper.leftAlign = false;
                            var i = 0,
                                len = scope.entries.length;
                            for (i; i < len; i++) {
                                var entry = scope.entries[i];
                                if (!entry.approved && (scope.activeEntry !== entry)) {
                                    focusedEntry = entry;
                                    break;
                                }
                            }
                            helper.hasNext = !!focusedEntry;
                            if (focusedEntry) {
                                scrollToEntry(focusedEntry);
                            }
                            if (helper.currentBlock) {
                                helper.helpText = window['helpTexts']['translations-container'];
                                helper.redrawHelp();
                                helper.helpShow = true;
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            if (focusedEntry) {
                                helper.currentBlock = $('#entry-' + focusedEntry.idInText).find('.translation__sentence-translation-toggle');
                                helper.helpText = window['helpTexts']['translation__sentence-translation-toggle'];
                                helper.hasNext = true;
                                helper.leftAlign = false;
                                helper.clickBlock = function () {
                                    if (scope.activeEntry !== focusedEntry) {
                                        expandEntry(focusedEntry);
                                        helper.helpText = '';
                                        if (focusedEntry.mode === 0) {
                                            helper.hasNext = true;
                                            helper.currentBlock = $('#entry-' + focusedEntry.idInText).find('.switcher__button_make-translate');
                                            helper.leftAlign = false;
                                            helper.clickBlock = function () {
                                                focusedEntry.mode = 1;
                                                helper.currentBlock = $('#entry-' + focusedEntry.idInText).find('.translation__sentence-commitance');
                                                helper.helpText = '';
                                                helper.hasNext = true;
                                                helper.leftAlign = false;
                                                helper.clickBlock = false;
                                                $timeout(function () {
                                                    if (helper.currentBlock) {
                                                        helper.redrawHelp();
                                                        helper.helpText = window['helpTexts']['translation__sentence-commitance'];
                                                    } else {
                                                        helper.closeHelpPresentation();
                                                    }
                                                }, 100);
                                            };
                                        } else {
                                            helper.hasNext = true;
                                            helper.currentBlock = $('#entry-' + focusedEntry.idInText).find('.translation__sentence-commitance');
                                            helper.leftAlign = false;
                                            helper.clickBlock = false;
                                        }
                                        $timeout(function () {
                                            if (helper.currentBlock) {
                                                helper.redrawHelp();
                                                if (focusedEntry.mode === 0) {
                                                    helper.helpText = window['helpTexts']['switcher__button_make-translate'];
                                                } else {
                                                    helper.helpText = window['helpTexts']['translation__sentence-commitance'];
                                                }
                                            } else {
                                                helper.closeHelpPresentation();
                                            }
                                        }, 1000);
                                    }
                                };
                                helper.redrawHelp();
                            }
                        },
                        function (helper) {
                            helper.currentBlock = $('#translation-text');
                            helper.clickBlock = false;
                            helper.leftAlign = true;
                            helper.hasNext = true;
                            if (helper.currentBlock) {
                                helper.helpText = window['helpTexts']['translation-text'];
                                helper.redrawHelp();
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            if (scope.entries.length) {
                                var entry = scope.entries[scope.entries.length > 3 ? 3 : scope.entries.length];
                                helper.currentBlock = $('[data-entry="' + entry.idInText + '"]');
                                helper.leftAlign = false;
                                helper.clickBlock = function () {
                                    helper.helpShow = false;
                                    scope.focusEntry(entry.idInText);
                                    $timeout(function () {
                                        helper.currentBlock = $('#switcher__button_original-text');
                                        helper.leftAlign = false;
                                        helper.clickBlock = false;
                                        helper.hasNext = true;
                                        if (helper.currentBlock) {
                                            helper.helpText = window['helpTexts']['switcher__button_original-text'];
                                            helper.redrawHelp();
                                            helper.helpShow = true;
                                        } else {
                                            helper.closeHelpPresentation();
                                        }
                                    }, 1000);
                                };
                                helper.hasNext = true;
                                if (helper.currentBlock) {
                                    helper.helpText = window['helpTexts']['data-entry'];
                                    helper.redrawHelp();
                                } else {
                                    helper.closeHelpPresentation();
                                }
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            helper.currentBlock = $('#switcher__button_translated-text');
                            helper.clickBlock = false;
                            helper.leftAlign = false;
                            helper.hasNext = false;
                            if (helper.currentBlock) {
                                helper.helpText = window['helpTexts']['switcher__button_translated-text'];
                                helper.redrawHelp();
                            } else {
                                helper.closeHelpPresentation();
                            }
                        }
                    ];
                    nextStep(event);
                });
                scope.$on('helpPresentationNext', nextStep);
            }($scope));
            $scope.$parent.showTranslatePopup = false;
            $scope.$parent.translatedPhrase = '';
            $scope.$parent.translationResults = [];
            var getSelectionText = function () {
                    var text = "",
                        x = 0,
                        y = 0,
                        width = 0;
                    if (window.getSelection) {
                        var sel = window.getSelection(),
                            range = sel.rangeCount ? sel.getRangeAt(0) : false,
                            rect = range ? range.getClientRects()[0] : false;
                        if (rect) {
                            y = rect.bottom;
                            x = rect.left;
                            width = rect.right - rect.left;
                        }
                        text = sel.toString();
                    } else if (document.selection && document.selection.type != "Control") {
                        var range = sel.createRange();
                        range.collapse(true);
                        x = range.boundingLeft;
                        y = range.boundingTop + range.boundingHeight;
                        width = rande.boundingWidth;
                        text = document.selection.createRange().text;
                    }
                    return [text, x, y, width];
                },
                translate = function () {
                    var selection = getSelectionText(),
                        phrase = selection[0].trim().toLowerCase(),
                        coords = {'x': selection[1], 'y': selection[2]},
                        width = selection[3];
                    if (!phrase) {
                        return;
                    }
                    var prevPhrase = $scope.translatedPhrase;
                    $scope.translatedPhrase = phrase;
                    if (phrase === prevPhrase) {
                        $scope.$parent.showTranslatePopup = false;
                        $scope.translatedPhrase = false;
                        return;
                    }
                    $http.jsonp('https://glosbe.com/gapi/translate', {
                        params: {
                            from: $scope.langPair3[0],
                            dest: $scope.langPair3[1],
                            phrase: phrase,
                            callback: 'JSON_CALLBACK',
                            format: 'json'
                        }
                    }).success(function (res) {
                        var results = [];
                        if (angular.isArray(res['tuc'])) {
                            angular.forEach(res['tuc'], function (elem) {
                                if (elem['phrase'] && elem['phrase']['text']) {
                                    results.push(elem['phrase']['text']);
                                }
                            });
                        }
                        $scope.$parent.translationResults = results;
                        $scope.$parent.translatePopupStyle = {
                            display: 'block',
                            left: coords['x'] + 'px',
                            top: coords['y'] + 'px'
                        };
                        $scope.$parent.showTranslatePopup = results.length > 0;
                        if ($scope.$parent.showTranslatePopup) {
                            $timeout(function () {
                                var elem = $('#translation-popup'),
                                    elemWidth = elem.width(),
                                    left = coords['x'] + (width - elemWidth) / 2;
                                $scope.$parent.translatePopupStyle.left = left + 'px';
                            },1);
                        }
                    })
                };
            $scope.$parent.copyToClipboard = function (text) {
                if ($scope.activeEntry && $scope.activeEntry.mode == 1) {
                    $scope.activeEntry.suggestion = ($scope.activeEntry.suggestion || '') + ' ' + text;
                } else {
                    window.prompt("Copy to clipboard: Ctrl+C, Enter", text);
                }
                $scope.$parent.showTranslatePopup = false;
            };
            $scope.$on('GlobalClick', function (e, event) {
                $scope.$parent.showTranslatePopup = false;
                $scope.translatedPhrase = false;
            });
            $scope.$watch('activeEntry.suggestion', function () {
                if ($scope.activeEntry) {
                    //fixTags($('#entry-suggestion-' + $scope.activeEntry.id)[0]);
                }
            });
            var fixTags = function (element) {
                console.log('fix');
                var nodes = [],
                    state = false,
                    extend = false,
                    extendNode,
                    i;
                angular.forEach(element.childNodes, function (node) {
                    nodes.push(node);
                });
                while (nodes.length) {
                    var node = nodes.shift(),
                        j,
                        index,
                        type;
                    console.log(node.nodeType);
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
                                    }
                                    extend = false;
                                }
                            }
                        }
                        continue;
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
                        continue;
                    }
                    if (node.nodeType === 1) {
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
                        } else {
                            if (node.textContent) {
                                //var prevNode = node.previousSibling;
                                //if (prevNode && prevNode.nodeType === 3) {
                                //    prevNode.textContent += node.textContent;
                                //    node.remove();
                                //} else {
                                    element.replaceChild(document.createTextNode(node.textContent), node);
                                //}
                            } else {
                                node.remove();
                            }
                        }
                    }
                }
                if (state) { // если у нас ещё отрыт тег
                    element.appendChild(angular.element('<hr r i="' + state + '">')[0], node);
                }
            };
            $scope.$on('tagClick', function (event, index) {
                if (!$scope.activeEntry) {
                    return;
                }
                var element = $('#entry-suggestion-' + $scope.activeEntry.id)[0],
                    doc = element.ownerDocument || element.document,
                    win = doc.defaultView || doc.parentWindow,
                    sel,
                    nodes = [],
                    checkSelectedNodes = 0;

                if (typeof win.getSelection != "undefined") {
                    sel = win.getSelection();
                    if (sel.rangeCount > 0) {
                        var range = win.getSelection().getRangeAt(0);
                        angular.forEach(element.childNodes, function (node) {
                            nodes.push(node);
                            if (range.startContainer === node) {
                                checkSelectedNodes++;
                            }
                            if (range.endContainer === node) {
                                checkSelectedNodes++;
                            }
                        });
                        if (checkSelectedNodes < 2) {
                            fixTags(element);
                            nodes = [];
                            angular.forEach(element.childNodes, function (node) {
                                nodes.push(node);
                            });
                        }
                        while (nodes.length) {
                            var node = nodes.shift();
                            var text = node.textContent,
                                newNodes = [];
                            if (range.startContainer === node) {
                                if (range.startOffset > 0) {
                                    newNodes.push(document.createTextNode(text.substr(0, range.startOffset)));
                                }
                                newNodes.push(angular.element('<hr l i="' + index + '">')[0]);
                                if (range.endContainer === node) {
                                    if (range.endOffset > range.startOffset) {
                                        newNodes.push(document.createTextNode(text.substr(range.startOffset, range.endOffset - range.startOffset)));
                                    }
                                    newNodes.push(angular.element('<hr r i="' + index + '">')[0]);
                                    if (range.endOffset < text.length) {
                                        newNodes.push(document.createTextNode(text.substr(range.endOffset)));
                                    }
                                } else {
                                    if (range.startOffset < text.length) {
                                        newNodes.push(document.createTextNode(text.substr(range.startOffset)));
                                    }
                                }
                            } else if (range.endContainer === node) {
                                if (range.endOffset > 0) {
                                    newNodes.push(document.createTextNode(text.substr(0, range.endOffset)));
                                }
                                newNodes.push(angular.element('<hr r i="' + index + '">')[0]);
                                if (range.endOffset < text.length) {
                                    newNodes.push(document.createTextNode(text.substr(range.endOffset)));
                                }
                            }
                            if (newNodes.length) {
                                var nextNode = node.nextSibling;
                                element.replaceChild(newNodes.shift(), node);
                                angular.forEach(newNodes, function (node) {
                                    if (nextNode) {
                                        element.insertBefore(node, nextNode);
                                    } else {
                                        element.appendChild(node);
                                    }
                                });
                            }
                        }
                    }
                    sel.removeAllRanges();
                } else if ((sel = doc.selection) && sel.type != "Control") {
                    document.selection.empty();
                    //var textRange = sel.createRange();
                    //var preCaretTextRange = doc.body.createTextRange();
                    //preCaretTextRange.moveToElementText(element);
                    //preCaretTextRange.setEndPoint("EndToEnd", textRange);
                    //endOffset = preCaretTextRange.text.length;
                }
                fixTags(element);
                $scope.$apply(function () {
                    $scope.activeEntry.suggestion = element.innerHTML;
                })
            });
        }
    ]);
}());