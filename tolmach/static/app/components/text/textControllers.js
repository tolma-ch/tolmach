(function () {
    'use strict';

    var module = angular.module('textControllers', []);

    module.controller('transCtrl', ['$rootScope', '$scope', '$sce', '$http', '$timeout', 'localStorageService',
        function ($rootScope, $scope, $sce, $http, $timeout, localStorageService) {
            $scope.translationProgress = window['translation_progress'];
            $scope.translationCounts = window['translation_counts'];
            $scope.userMembershipStatus = window['userMembershipStatus'];

            $scope.keyLength = function (obj) {
                return Object.keys(obj).length;
            };

            $scope.ws_active = false;
            $scope.socket = new ReconnectingWebSocket(window['wsTextConnectHost']
                + '/ws/text/'
                + window['textId']
                + '/'
                + window['translationTargetLang']
                + '/');

            $scope.socket.onopen = function open() {
                console.log('WebSockets connection created.');
                $scope.ws_active = true;
                $scope.$apply()
            };
            $scope.socket.onclose = function () {
                console.log("Disconnected from translation socket");
                $scope.ws_active = false;
                $scope.$apply()
            };

            if ($scope.socket.readyState == WebSocket.OPEN) {
              $scope.socket.onopen();
            }

            $scope.socket.onmessage = function(message) {
                //console.log(message.data);
                // TODO:
                // 1) [done] Обновлять у всех пользователей прогресс документа
                // 2) [done] Присылать пользователям новые варианты перевода фрагментов и удалять удалённые
                // 3) [done] Обновлять у пользователей статус фрагментов "подтверждён/не подтверждён"
                // 4) [done] Показывать пользователям, какие фрагменты в данный момент переводят
                var ws_data = JSON.parse(message.data);
                if ('progress' in ws_data) {
                    //console.log('updating progressbars');
                    $scope.translationProgress = ws_data['progress']['translation_progress'];
                    $scope.translationCounts = ws_data['progress']['translation_counts'];
                }
                if ('entry_to_approve' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        var entry_to_approve = ws_data['entry_to_approve'];
                        $scope.entries.forEach(function (item, i, arr) {
                            if (item.id == entry_to_approve.id) {
                                var local_entry_to_approve = item;
                                //console.log("entry: " + item);
                                local_entry_to_approve['translations'].forEach(function (item_translation, x, a) {
                                    if (item_translation.id == entry_to_approve.translation.id) {
                                        var local_translation_to_approve = item_translation;
                                        //console.log("entry translation: " + item_translation);
                                        item_translation.isApproved = true;
                                        item.approved = true;
                                        applyTranslation(item, item_translation);
                                    }
                                })
                            }
                        });
                    }
                }
                if ('entry_to_disapprove' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        var entry_to_disapprove = ws_data['entry_to_disapprove'];
                        $scope.entries.forEach(function (item, x, arr) {
                            if (item.id == entry_to_disapprove.id) {
                                var local_entry_to_disapprove = item;
                                var i,
                                    someTranslation,
                                    translation;
                                for (i = 0; i < local_entry_to_disapprove.translations.length; i++) {
                                    someTranslation = local_entry_to_disapprove.translations[i];
                                    if (someTranslation.isApproved) {
                                        translation = someTranslation;
                                    }
                                }
                                translation.isApproved = false;
                                local_entry_to_disapprove.approved = false;
                                local_entry_to_disapprove.translation = '';
                                updateTranslation(local_entry_to_disapprove);
                            }
                        });
                    }
                }
                if ('entry_new_translation' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        var entry_new_translation = ws_data['entry_new_translation'];
                        $scope.entries.forEach(function (item, x, arr) {
                            if (item.id == entry_new_translation.id) {
                                var local_entry_to_translate = item,
                                    translation_to_update = false;

                                local_entry_to_translate.translations.forEach(function (item_translation, x, a) {
                                    if (item_translation.id == entry_new_translation.translation.id) {
                                        translation_to_update = item_translation;
                                    }
                                });
                                if (translation_to_update) {
                                    // если перевод не новый, а апдейтится уже имеющийся
                                    translation_to_update.body = entry_new_translation.translation.body;
                                    translation_to_update.isApproved = entry_new_translation.translation.isApproved;
                                } else {
                                    // а если перевод новый, то проверяем, не закинут ли он ещё в общий пул аяксом
                                    // и добавляем его
                                    if (!(entry_new_translation.translation in local_entry_to_translate['translations'])) {
                                        local_entry_to_translate['translations'].push(entry_new_translation.translation);
                                    }
                                }

                                if (entry_new_translation.translation.isApproved === true) {
                                    if (local_entry_to_translate === $scope.activeEntry) {
                                        $scope.activeEntry = null;
                                    }
                                    local_entry_to_translate.approved = true;
                                    applyTranslation(local_entry_to_translate, entry_new_translation.translation);
                                } else {
                                    updateTranslation(local_entry_to_translate);
                                }
                            }
                        })
                    }
                }
                if ('remove_translation' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        $scope.entries.forEach(function (item, x, arr) {
                            if (item.id == ws_data['remove_translation'].id) {
                                var i;
                                for (i = 0; i < item.translations.length; i++) {
                                    var translation = item.translations[i];
                                    if (translation.id === ws_data['remove_translation'].translation.id) {
                                        delete item.translations.splice(i, 1);
                                        break;
                                    }
                                }
                                updateTranslation(item);
                            }
                        })
                    }
                }
                if ('current_edit_start' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        $scope.entries.forEach(function (item, i, arr) {
                            if (item.id == ws_data['current_edit_start']) {
                                item.isBeingEdited[ws_data['user']] = ".";
                            } else {
                                delete item.isBeingEdited[ws_data['user']];
                            }
                        });
                    }
                }
                if ('current_edit_stop' in ws_data) {
                    //console.log('current: ' + $scope.user + "; from message: " + ws_data['user']);
                    if (!($scope.user == ws_data['user'])) {
                        $scope.entries.forEach(function (item, i, arr) {
                            if (item.id == ws_data['current_edit_stop']) {
                                delete item.isBeingEdited[ws_data['user']];
                            }
                        });
                    }
                }
                $scope.$apply();
            };

            var clearTags = function (text) {
                    //return text;
                    var div = document.createElement("div");
                    div.innerHTML = text;
                    return div.textContent || div.innerText || "";
                },
                updateTranslationProgress = function () {
                    if (!$scope.ws_active) {
                        $http.post('/ajax/get-translation-progress/', {
                            text: textId,
                            target_lang: window['translationTargetLang']
                        }).success(function (data) {
                            $scope.translationProgress = data['translation_progress'];
                            $scope.translationCounts = data['translation_counts'];
                        }).error(function (a) {
                            //console.error(a);
                        });
                    }
                },
                applyTranslation = function (entry, translation) {
                    entry.translation = (clearTranslation(entry, translation));
                    updateTranslationProgress();
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
                },
                updateEntries = function () {
                    $scope.busy = true;
                    $http.get('/ajax/entry/', {
                        params: {
                            text: textId,
                            page: $scope.page,
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
                            entry.body = entry.body.replace(/\n/g, '<br>');
                            entry.translation = entry.translation.replace(/\n/g, '<br>');
                            entry.translations.forEach(function(trans) {
                                trans.body = trans.body.replace(/\n/g, "<br>");
                            });
                            updateTranslation(entry);
                            entriesById[entry['idInText']] = entry;
                        }
                        $scope.entries = entries;
                        $scope.textBody = data['text_body'].replace(/\n/g, "<br />");
                        $scope.pagesCount = data['total_pages'];
                        $scope.entriesById = entriesById;
                        $scope.busy = false;
                    }).error(function (a) {
                        console.log(a);
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
                updateEntries();
            };
            $scope.paginatorKeypress = function (event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (code === 13 || code === 10) {
                    $scope.paginatorBlur();
                }
            };
            $scope.userIsManager = false;

            updateEntries();

            var moveCursorToEnd = function (elem) {
                var caretPos = elem.innerHTML.length;
                var range = document.createRange();
                var sel = window.getSelection();
                range.setStart(elem.childNodes[0], caretPos);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
            };
            $scope.prevPage = function () {
                if ($scope.busy) {
                    return;
                }
                if ($scope.page > 1) {
                    $scope.page = $scope.page - 1;
                    updateEntries();
                }
            };
            $scope.nextPage = function () {
                if ($scope.busy) {
                    return;
                }
                if ($scope.page < $scope.pagesCount) {
                    $scope.page = $scope.page + 1;
                    updateEntries();
                }
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
                            // -100 is some space between header panel and the top position of the currently active entry
                            // it helps keep the context of the previous entry without additional scrolling
                            containerShift = $container.scrollTop() + $elem.offset()['top'] - $container.offset()['top'] - 100;
                        $container.stop().animate({
                            scrollTop: containerShift
                        }, 500);
                    }, 100);
                },
                scrollRightEntry = function (id) {
                    setTimeout(function () {
                        var $resContainer = $('#result-container'),
                            $resElem = $('#res-entry-' + id),
                            // -100 is some space between header panel and the top position of the currently active entry
                            // it helps keep the context of the previous entry without additional scrolling
                            resShift = $resContainer.scrollTop() + $resElem.offset()['top'] - $resContainer.offset()['top'] - 100;
                        $resContainer.stop().animate({
                            scrollTop: resShift
                        }, 500);
                    }, 100);
                },
                entrySetEditingStatus = function (entry, status) {
                    if ($scope.ws_active) {
                        if (status == "start") {
                            $scope.socket.send(JSON.stringify({"text": {
                                    "current_edit_start" : entry.id,
                                    "user": $scope.user
                                }}));
                        } else if (status == "stop") {
                            $scope.socket.send(JSON.stringify({"text": {
                                    "current_edit_stop" : entry.id,
                                    "user": $scope.user
                                }}));
                        }
                    }
                },
                expandEntry = function (entry) {
                    $scope.activeEntry = entry;
                    if (!entry.approved
                    && (!angular.isArray(entry['translations']) || !entry['translations'].length)
                    && $scope.translationAllowed) {
                        setTimeout(function () {
                            $('#entry-suggestion-' + entry.id).focus();
                        }, 10);
                    }
                    entrySetEditingStatus(entry, 'start');
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
                    entrySetEditingStatus(entry, 'stop');
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
                        entrySetEditingStatus(entry, 'start');
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
            $scope.entrySuggestSending = false;
            $scope.suggestTranslation = function (entry) {
                if (entry['meta'] && entry['meta']['msgid_plural']) {
                    entry.pluralVariants[entry.plural] = entry.suggestion;
                    entry.suggestion = entry.pluralVariants.join("‡");
                }
                var suggestionId = entry['suggestionId'],
                    data = {
                        id: entry.id,
                        text: entry.suggestion.replace(/<br\s*[\/]?>/gi, "\n"),
                        target_lang: window['translationTargetLang']
                    };
                if (suggestionId) {
                    data['translation_id'] = suggestionId;
                }
                entry.suggestionId = false;

                $scope.entrySuggestSending = true;
                $http.post('/ajax/entry-translate/', data).success(function (data) {
                    if (suggestionId) {
                        var i,
                            translation;
                        for (i = entry['translations'].length - 1; i >= 0; i--) {
                            translation = entry['translations'][i];
                            if (translation.id == suggestionId) {
                                translation.body = data.body.replace(/\n/g, "<br>");
                                translation.isApproved = data.isApproved;

                                break;
                            }
                        }
                    } else {
                        if (!(data in entry['translations'])){
                            entry['translations'].push(data);
                        }
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
                    $scope.entrySuggestSending = false;
                });
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
                entrySetEditingStatus(entry, 'stop');
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
                // $('#entry-' + entry.idInText).trigger("blur");
                $timeout(function () {
                    $scope.suggestTranslation(entry);
                }, 501);
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
                    if ((code === 13 || code === 10) && !event.metaKey && !event.ctrlKey && !event.shiftKey) {
                        console.log('just enter');
                        saveHotKey(entry);
                    } else if (event.shiftKey && (code === 13 || code === 10)) {
                        console.log('shift-enter to new line');
                    }
                } else {
                    if (code == 13 && event.metaKey) {
                        console.log('cmd enter');
                        saveHotKey(entry);
                    } else if (event.ctrlKey && (code === 13 || code === 10)) {
                        console.log('ctrl enter');
                        saveHotKey(entry);
                    } else if ((code === 13 || code === 10) && !event.metaKey && !event.ctrlKey && !event.shiftKey) {
                        event.stopPropagation(); // Disabling new-lines with Enter key to prevent a bug when cursor after first
                        event.preventDefault(); // char on new line moves to the beginning of the line
                    }
                }
            };

            $scope.showEntryCommentsModal = false;
            $scope.currentActiveCommentEntry = '';
            $scope.entryCommentsOpener = function ($event, commentEntryId, entryText) {
                var w = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
                var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
                var leftPanelWidth = document.getElementsByClassName('text-piece')[0].offsetWidth;

                if (!$scope.currentActiveCommentEntry) {
                    $scope.currentActiveCommentEntry = angular.element($event.target)[0];
                }
                var currentCommBtn = angular.element($event.target)[0];

                var bodyRect = document.body.getBoundingClientRect(),
                    elemRect = currentCommBtn.getBoundingClientRect(),
                    offset   = elemRect.top - bodyRect.top;

                if ($scope.showEntryCommentsModal) {
                    document.getElementById('commentedEntryId').value = 0;
                    $scope.currentActiveCommentEntry.classList.remove('text-piece__comment-button-absolute-active');
                    $scope.currentActiveCommentEntry = '';
                } else {
                    $scope.currentActiveCommentEntry.classList.add('text-piece__comment-button-absolute-active');
                    document.getElementById('commentedEntryId').value = commentEntryId;
                    document.getElementsByClassName('text-piece_comment-window__header')[0].innerHTML = entryText;
                    if (leftPanelWidth >= w) {
                        document.getElementById('entryCommentWindow').style.left = (leftPanelWidth/2-125) + 'px';
                        document.getElementById('entryCommentWindow').style.top = offset - 150 + 'px';
                    } else {
                        var rect = document.getElementById('entryCommentWindow').getBoundingClientRect();
                        console.log(rect);
                        var commentWindowHeight = rect.bottom - rect.top;
                        console.log('comment window height: '+commentWindowHeight);
                        console.log('comment window height: '+document.getElementById('entryCommentWindow').offsetHeight);
                        document.getElementById('entryCommentWindow').style.left = leftPanelWidth + 'px';
                        document.getElementById('entryCommentWindow').style.top = offset - 150 + 'px';
                        console.log(document.getElementById('entryCommentWindow').style.top);
                        console.log(h);
                    }

                }
                $scope.showEntryCommentsModal = !$scope.showEntryCommentsModal;
            };

            $scope.showDictModal = false;
            $scope.lastFocusedEntryInputId = '';
            $scope.lastFocusedEntryInputPosition = 0;
            $scope.dictOpener = function () {
                $scope.showDictModal = !$scope.showDictModal;
            };
            $scope.$on('GlobalKeydown', function (e, event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (event.ctrlKey && event.altKey) {
                    if (code === 84) { // Ctrl- Alt - t
                        translate();
                    }
                    if (code === 68) { // Ctrl - Alt - d
                        event.stopPropagation();
                        event.preventDefault();
                        e.preventDefault();
                        // hotkey for showing dictionary window
                        if (!$scope.showDictModal) {
                            // if dict window is not shown right now
                            // looking for current element focused
                            var curFocus = document.activeElement.id;
                            if (curFocus.startsWith("entry-suggestion-")) {
                                $scope.lastFocusedEntryInputId = curFocus;
                                var range = window.getSelection().getRangeAt(0);
                                $scope.lastFocusedEntryInputPosition = range.endOffset;
                            }
                        } else {
                            if ($scope.lastFocusedEntryInputId) {
                                document.getElementById($scope.lastFocusedEntryInputId).focus();

                                var textNode = document.getElementById($scope.lastFocusedEntryInputId).firstChild;
                                if (textNode !== null) {
                                    var caret = $scope.lastFocusedEntryInputPosition; // insert caret after the 10th character say
                                    var range = document.createRange();
                                    range.setStart(textNode, caret);
                                    range.setEnd(textNode, caret);
                                    var sel = window.getSelection();
                                    sel.removeAllRanges();
                                    sel.addRange(range);
                                }
                                $scope.lastFocusedEntryInputId = '';
                            }
                        }
                        $scope.showDictModal = !$scope.showDictModal;
                    }
                    return;
                }
                if (event.altKey) {
                    if (code === 68) { // Alt - d
                        event.stopPropagation();
                        event.preventDefault();
                        e.preventDefault();
                        // hotkey for showing dictionary window
                        if (!$scope.showDictModal) {
                            // if dict window is not shown right now
                            // looking for current element focused
                            var curFocus = document.activeElement.id;
                            if (curFocus.startsWith("entry-suggestion-")) {
                                $scope.lastFocusedEntryInputId = curFocus;
                                var range = window.getSelection().getRangeAt(0);
                                $scope.lastFocusedEntryInputPosition = range.endOffset;
                            }
                        } else {
                            if ($scope.lastFocusedEntryInputId) {
                                document.getElementById($scope.lastFocusedEntryInputId).focus();

                                var textNode = document.getElementById($scope.lastFocusedEntryInputId).firstChild;
                                if (textNode !== null) {
                                    var caret = $scope.lastFocusedEntryInputPosition; // insert caret after the 10th character say
                                    var range = document.createRange();
                                    range.setStart(textNode, caret);
                                    range.setEnd(textNode, caret);
                                    var sel = window.getSelection();
                                    sel.removeAllRanges();
                                    sel.addRange(range);
                                }
                                $scope.lastFocusedEntryInputId = '';
                            }
                        }
                        $scope.showDictModal = !$scope.showDictModal;
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