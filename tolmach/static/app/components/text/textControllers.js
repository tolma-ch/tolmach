(function () {
    'use strict';

    var module = angular.module('textControllers', []);

    module.controller('transCtrl', ['$rootScope', '$scope', '$http', '$timeout', 'localStorageService',
        function ($rootScope, $scope, $http, $timeout, localStorageService) {
            var clearTags = function (text) {
                    //return text;
                    var div = document.createElement("div");
                    div.innerHTML = text;
                    return div.textContent || div.innerText || "";
                },
                applyTranslation = function (entry, translation) {
                    entry.translation = (clearTranslation(entry, translation));
                },
                updateTranslation = function (entry) {
                    if (!entry.approved) {
                        entry.translation = (entry['rawBody']);
                        for (var i = entry.translations.length - 1; i >= 0; i -= 1) {
                            var translation = entry.translations[i];
                            if (translation.author.id === $scope.user) {
                                applyTranslation(entry, translation);
                                break;
                            }
                        }
                    }
                },
                clearTranslation = function (entry, translation) {
                    var translationBody;
                    if (entry['meta'] && entry['meta']['msgid_plural']) {
                        try {
                            translationBody = translation.body.split("‡")[0];
                        } catch (e) {
                            translationBody = '';
                        }
                    } else {
                        translationBody = translation['body'];
                    }
                    return translationBody;
                },
                textId = window['textId'],
                useMachine = window['useMachine'],
                getYaMachines = function (entry) {
                    $http.post('/ajax/ya-translate/', {
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
                    $http.post('/ajax/tmdb-search/', {
                        entry_id: entry['id'],
                        lang_pair: $scope.langPair
                    }).success(function (data) {
                        entry.tmdbVariants = data;
                    }).error(function (a) {
                        //console.error(a);
                    });
                };
            $scope.savingOptions = {
                btn: localStorageService.get('savingOptions-btn') || 'ctrl-enter'
            };
            $scope.changeSavingOptions = function () {
                localStorageService.set('savingOptions-btn', $scope.savingOptions.btn);
            };
            $scope.clearTags = clearTags;
            $scope.clearTranslation = clearTranslation;
            $scope.activeEntry = null;
            $scope.textTab = 0;
            $scope.page = 1;
            $scope.countPerPage = 100;
            $scope.pagesCount = 1;
            $scope.paginatorBlur = function () {
                $scope.editPage = false;
                $scope.page = parseInt($scope.page) || 1;
                $scope.page = $scope.page > $scope.pagesCount ? $scope.pagesCount : ($scope.page < 1 ? 1 : $scope.page);
            };
            $scope.paginatorKeypress = function (event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (code === 13 || code === 10) {
                    $scope.paginatorBlur();
                }
            };
            $scope.userIsManager = false;
            $http.get('/ajax/entry/', {
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
                $scope.pluralExamples = data['plural_examples'];
                $scope.user = data['user'];
                var entriesById = {},
                    i, entry;
                for (i = entries.length - 1; i >= 0; i--) {
                    entry = entries[i];
                    entry.body = entry.body.replace("\n", '<br>');
                    updateTranslation(entry);
                    entriesById[entry['idInText']] = entry;
                }
                $scope.entries = entries;
                $scope.pagesCount = Math.ceil(entries.length / $scope.countPerPage);
                $scope.entriesById = entriesById;
            }).error(function (a) {
                console.log(a);
            });
            var moveCursorToEnd = function (elem) {
                var caretPos = elem.innerHTML.length;
                var range = document.createRange();
                var sel = window.getSelection();
                range.setStart(elem.childNodes[0], caretPos);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
            };
            $scope.addMachineSuggestion = function (entry, machine) {
                if (entry.suggestion) {
                    entry.suggestion += ' ' + machine.text;
                } else {
                    entry.suggestion = machine.text;
                }
                var input = $('#entry-suggestion-' + entry.id);
                input.focus();
                var len = entry.suggestion.length * 2;
                setTimeout(function () {
                    moveCursorToEnd(input[0]);
                }, 10);
            };
            var scrollToEntry = function (entry) {
                    scrollLeftEntry(entry.idInText);
                    scrollRightEntry(entry.idInText);
                },
                scrollLeftEntry = function (id) {
                    setTimeout(function () {
                        var $container = $('#translations-container'),
                            $elem = $('#entry-' + id),
                            containerShift = $container.scrollTop() + $elem.offset()['top'] - $container.offset()['top'];
                        $container.stop().animate({
                            scrollTop: containerShift
                        }, 500);
                    }, 100);
                },
                scrollRightEntry = function (id) {
                    setTimeout(function () {
                        var $resContainer = $('#result-container'),
                            $resElem = $('#res-entry-' + id),
                            resShift = $resContainer.scrollTop() + $resElem.offset()['top'] - $resContainer.offset()['top'];
                        $resContainer.stop().animate({
                            scrollTop: resShift
                        }, 500);
                    }, 100);
                },
                expandEntry = function (entry) {
                    if (!entry.approved) {
                        $scope.activeEntry = entry;
                        if (!entry.approved
                        && (!angular.isArray(entry['translations']) || !entry['translations'].length)
                        && $scope.translationAllowed) {
                            setTimeout(function () {
                                $('#entry-suggestion-' + entry.id).focus();
                            }, 10);
                        }
                    }
                    scrollToEntry(entry);
                };
            $scope.toggleEntry = function (entry, $event) {
                if ($scope.activeEntry === entry) {
                    $scope.activeEntry = null;
                } else {
                    expandEntry(entry);
                }
                if ($event) {
                    $event.stopPropagation();
                }
            };
            $scope.focusEntry = function (id) {
                var entry = $scope.entriesById[id];
                expandEntry(entry);
            };
            $scope.approveEntry = function (translation, entry) {
                $http.post('/ajax/entry-approve/', {id: translation.id}).success(function () {
                    translation.isApproved = true;
                    entry.approved = true;
                    applyTranslation(entry, translation);
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
            $scope.disapproveEntry = function (entry) {
                var i,
                    someTranslation,
                    translation;
                for (i = 0; i < entry.translations.length; i++) {
                    someTranslation = entry.translations[i];
                    if (someTranslation.isApproved) {
                        translation = someTranslation;
                    }
                }
                if (translation) {
                    $http.post('/ajax/entry-disapprove/', {id: translation.id}).success(function () {
                        translation.isApproved = false;
                        entry.approved = false;
                        $scope.activeEntry = entry;
                        entry.translation = '';
                        updateTranslation(entry);
                    })
                }
            };
            $scope.removeTranslation = function (entry) {
                if (!entry.suggestionId) {
                    return;
                }
                $http.post('/ajax/remove-translate/', {
                    'entry': entry.id,
                    'translation': entry.suggestionId
                }).success(function () {
                    var i;
                    for (i = 0; i < entry.translations.length; i++) {
                        var translation = entry.translations[i];
                        if (translation.id === entry.suggestionId) {
                            delete entry.translations.splice(i, 1);
                            $scope.cancelEditing(entry);
                            $scope.toggleEntry(entry);
                            break;
                        }
                    }
                    updateTranslation(entry);
                });
            };
            $scope.suggestTranslation = function (entry) {
                if (entry['meta'] && entry['meta']['msgid_plural']) {
                    entry.pluralVariants[entry.plural] = entry.suggestion;
                    entry.suggestion = entry.pluralVariants.join("‡");
                }
                var suggestionId = entry['suggestionId'],
                    data = {
                        id: entry.id,
                        text: entry.suggestion.replace('<br>', "\n"),
                        target_lang: window['translationTargetLang']
                    };
                if (suggestionId) {
                    data['translation_id'] = suggestionId;
                }
                entry.suggestionId = false;
                $http.post('/ajax/entry-translate/', data).success(function (data) {
                    if (suggestionId) {
                        var i,
                            translation;
                        for (i = entry['translations'].length - 1; i >= 0; i--) {
                            translation = entry['translations'][i];
                            if (translation.id == suggestionId) {
                                translation.body = data.body;
                                translation.isApproved = data.isApproved;

                                break;
                            }
                        }
                    } else {
                        entry['translations'].push(data);
                    }
                    entry.editing = false;
                    entry.suggestion = '';
                    if (data.isApproved === true) {
                        if (entry === $scope.activeEntry) {
                            $scope.activeEntry = null;
                        }
                        entry.approved = true;
                        applyTranslation(entry, data);
                    } else {
                        updateTranslation(entry);
                    }
                })
            };
            $scope.editTranslation = function (entry, translation) {
                entry.editing = true;
                if (entry['meta'] && entry['meta']['msgid_plural']) {
                    entry.plural = 0;
                    entry.pluralVariants = (translation.body || '').split("‡");
                    entry.suggestion = entry.pluralVariants.length ? entry.pluralVariants[0] : '';
                } else {
                    entry.suggestion = translation.body;
                }
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
                $http.post('/ajax/entry/vote/', data).success(function (data) {
                    translation.busy = false;
                }).error(function (data) {
                    translation.isVoted = !vote;
                    translation.busy = false;
                })

            };
            $scope.switchPlural = function (entry, index) {
                entry.pluralVariants[entry.plural] = entry.suggestion;
                entry.plural = index;
                entry.suggestion = entry.pluralVariants[index];
            };
            $scope.startEditing = function (entry) {
                if (!entry.editing) {
                    if (entry['meta'] && entry['meta']['msgid_plural']) {
                        entry.plural = 0;
                        entry.pluralVariants = [];
                    }
                    entry.editing = true;
                    if ((useMachine) && (typeof entry['machines'] === 'undefined')) {
                        getYaMachines(entry);
                        getTmdbVariants(entry);
                    }
                }
            };
            $scope.cancelEditing = function (entry) {
                entry.editing = false;
                entry.suggestion = '';
                entry.suggestionId = false;
            };
            $scope.insertText = function (e, entry, text) {
                if (entry !== $scope.activeEntry || !entry.editing) {
                    return;
                }
                e.stopPropagation();
                $rootScope.$broadcast('insertText', {
                    'id': entry.id,
                    'text': text
                });
                //entry.suggestion += text;
            };
            var saveHotKey = function (entry) {
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
            };
            $scope.textareaKeydown = function (event, entry) {
                var code = (event.charCode) ? event.charCode : ((event.which) ? event.which : event.keyCode);
                if ($scope.savingOptions.btn === 'enter') {
                    if ((code === 13 || code === 10) && !event.metaKey && !event.ctrlKey) {
                        console.log('just enter');
                        saveHotKey(entry);
                    }
                } else {
                    if (code == 13 && event.metaKey) {
                        console.log('cmd enter');
                        saveHotKey(entry);
                    } else if (event.ctrlKey && (code === 13 || code === 10)) {
                        console.log('ctrl enter');
                        saveHotKey(entry);
                    }
                }
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
                            entry,
                            someEntry,
                            found = false;
                        if (code === 38) {
                            //up
                            for (--index; index >= 0; index--) {
                                someEntry = $scope.entries[index];
                                if (!someEntry.approved) {
                                    entry = someEntry;
                                    break;
                                }
                            }
                        }
                        if (code === 40) {
                            //down
                            for (index++; index < $scope.entries.length; index++) {
                                someEntry = $scope.entries[index];
                                if (!someEntry.approved) {
                                    entry = someEntry;
                                    break;
                                }
                            }
                        }
                        if (entry) {
                            $scope.focusEntry(entry.idInText);
                        }
                    }
                    return;
                }
                if (code === 27) {
                    if ($scope.activeEntry) {
                        if ($scope.activeEntry.editing) {
                            $scope.cancelEditing($scope.activeEntry);
                        } else {
                            $scope.toggleEntry($scope.activeEntry);
                        }
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
                    var focusedEntry,
                        rightEntry;
                    steps = [
                        function (helper) {
                            helper.currentBlock = $('#translations-container');
                            helper.position = 'right';
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
                                helper.currentBlock = $('#entry-' + focusedEntry.idInText);
                                helper.helpText = window['helpTexts']['entry'];
                                helper.hasNext = true;
                                helper.position = 'bottom';
                                helper.redrawHelp();
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            if (scope.activeEntry !== focusedEntry) {
                                expandEntry(focusedEntry);
                            }
                            helper.currentBlock = $('#entry-' + focusedEntry.idInText);
                            helper.helpText = window['helpTexts']['entry2'];
                            helper.position = 'right';
                            helper.hasNext = true;

                            $timeout(function () {
                                if (helper.currentBlock) {
                                    helper.redrawHelp();
                                } else {
                                    helper.closeHelpPresentation();
                                }
                            }, 100);

                        },
                        function (helper) {
                            helper.currentBlock = $('#entry-suggestion-' + focusedEntry.id);
                            helper.helpText = window['helpTexts']['entry-suggestion'];
                            helper.hasNext = true;
                            helper.position = 'bottom';
                            if (helper.currentBlock) {
                                helper.redrawHelp();
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            helper.currentBlock = $('#translation-text');
                            helper.helpText = window['helpTexts']['translation-text'];
                            helper.position = 'left';
                            helper.hasNext = true;
                            if (helper.currentBlock) {
                                helper.redrawHelp();
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            if (scope.entries.length) {
                                helper.helpShow = false;
                                rightEntry = scope.entries[scope.entries.length > 10 ? 10 : scope.entries.length];
                                scrollRightEntry(rightEntry.idInText);
                                helper.currentBlock = $('[data-entry="' + rightEntry.idInText + '"]');
                                helper.hasNext = true;
                                helper.position = 'bottom';
                                $timeout(function () {
                                    if (helper.currentBlock) {
                                        helper.helpText = window['helpTexts']['data-entry'];
                                        helper.redrawHelp();
                                        helper.helpShow = true;
                                    } else {
                                        helper.closeHelpPresentation();
                                    }
                                }, 1000);
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            if (rightEntry) {
                                helper.helpShow = false;
                                scope.focusEntry(rightEntry.idInText);
                                $timeout(function () {
                                    helper.currentBlock = $('#switcher__button_original-text');
                                    helper.helpText = window['helpTexts']['switcher__button_original-text'];
                                    helper.hasNext = true;
                                    helper.position = 'bottom';
                                    if (helper.currentBlock) {
                                        helper.redrawHelp();
                                        helper.helpShow = true;
                                    } else {
                                        helper.closeHelpPresentation();
                                    }
                                }, 1000);
                            } else {
                                helper.closeHelpPresentation();
                            }
                        },
                        function (helper) {
                            helper.currentBlock = $('#switcher__button_translated-text');
                            helper.position = 'bottom';
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
                        $scope.$parent.showTranslatePopup = true;
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
                if ($scope.activeEntry && $scope.activeEntry.editing) {
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
            $scope.mouseup = function () {
                translate();
            };
            //$scope.$on('GlobalMouseup', function (e, event) {
            //    translate();
            //});
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
                }
                $scope.$apply(function () {
                    $scope.activeEntry.suggestion = element.innerHTML;
                })
            });
        }
    ]);
}());