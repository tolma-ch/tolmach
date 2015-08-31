'use strict';

/* App Module */

(function () {
    angular.module('tolmachApp', [
        'ui.bootstrap',
        'ngFileUpload',
        'ui.select'
    ])
        .controller('mainCtrl', function ($scope, $http, $timeout) {
            var updateMessages = function () {
                $http.post('/api/message/').success(function (data) {
                    $scope.messages = data;
                    $timeout(updateMessages, 5000);
                }).error(function (data) {
                })
            };
            try {
                $scope.sidebarCollapsed = angular.fromJson(sessionStorage.sidebarCollapsed);
            } catch (e) {
                $scope.sidebarCollapsed = false;
            }
            $scope.toggleSidebar = function () {
                $scope.sidebarCollapsed = !$scope.sidebarCollapsed;
                sessionStorage.sidebarCollapsed = angular.toJson($scope.sidebarCollapsed);
            };
            updateMessages();
        })
        .controller('transCtrl', function ($rootScope, $scope, $http) {
            var textId = window['textId'],
                getYaMachines = function (entry) {
                    $http.post('/api/ya-translate/', {lang_pair: $scope.langPair, entry_body: entry['rawBody']}).success(function (data) {
                        entry.yaMachines = [{
                            text: data
                        }];
                    }).error(function (a) {
                        console.error(a);
                    });
                },
                getTmdbVariants = function (entry) {
                    $http.post('/api/tmdb-search/', {entry_id: entry['id']}).success(function (data) {
                        entry.tmdbVariants = data;
                    }).error(function (a) {
                        console.error(a);
                    });
                };
            $scope.activeEntry = null;
            $scope.textTab = 0;
            $scope.userIsManager = false;
            $http.get('/api/entry/', {params: {text: textId, target_lang: window['translationTargetLang']}}).success(function (data) {
                var entries = data['entries'];
                $scope.userIsManager = !!data['user_is_manager'];
                $scope.translationAllowed = !!data['translation_allowed'];
                $scope.langPair = data['lang_pair'];
                $scope.user = data['user'];
                var entriesById = {},
                    i, entry;
                for(i = entries.length - 1; i >= 0; i--) {
                    entry = entries[i];
                    entry.mode = (angular.isArray(entry['translations']) && !!entry['translations'].length)
                                || !$scope.translationAllowed ? 0 : 1;
                    entriesById[entry['idInText']] = entry;
                }
                $scope.entries = entries;
                $scope.entriesById = entriesById;
            }).error(function (a) {
                console.log(a);
            });
            $scope.machines = [
                {
                    'text': 'В студию графического дизайна Emil Stasovskiy Branding на постоянную работу приглашается графический дизайнер',
                    'percent': 70
                },
                {
                    'text': 'В японии полным ходом идет культовое мероприятие - rc custom body show',
                    'percent': 50
                },
                {
                    'text': 'На форуме выступят представители ведущих веб агентств  и дизайн студий: Nimax, Shishki, Astra Media Group, Журнал "Инфографика", Science, Webcom, No Comments и др.',
                    'percent': 40
                }
            ];
            $scope.addMachineSuggestion = function (entry, machine) {
                if (entry.suggestion) {
                    entry.suggestion += ' ' + machine.text;
                } else {
                    entry.suggestion = machine.text;
                }
            };
            var expandEntry = function (entry) {
                if (!entry.approved) {
                    if (typeof entry['machines'] === 'undefined') {
                        getYaMachines(entry);
                        getTmdbVariants(entry);
                    }
                    $scope.activeEntry = entry;
                    if (entry.mode === 1) {
                        setTimeout(function () {
                            $('#entry-' + entry.idInText).find('textarea').focus();
                        }, 10);
                    }
                }
                setTimeout(function () {
                    var $body = $('html, body'),
                        $container = $('#translations-container'),
                        $elem = $('#entry-' + entry.id),
                        $resElem = $('#res-entry-' + entry.id),
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
            var updateTranslation = function (entry) {
                if (!entry.isApproved && entry.translations.length) {
                    entry.translation = entry['rawBody'];
                    for (var i = entry.translations.length - 1; i >= 0; i -= 1) {
                        var translation = entry.translations[i];
                        if (translation.author.id === $scope.user) {
                            entry.translation = translation['body'];
                            break;
                        }
                    }
                }
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
                        target_lang: window['translationTargetLang'],
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
            }
        })

        .controller('projectsCtrl', function ($scope, $modal) {
            $scope.userData = window['userData'];
            $scope.startNewProject = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'newProjectModal.html',
                    controller: 'NewProjectModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                    }
                });

                modalInstance.result.then(function () {
                }, function () {
                });
            };
            $scope.editProfile = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'editProfileModal.html',
                    controller: 'EditProfileModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                        'userData': function () {
                            return $scope.userData;
                        }
                    }
                });

                modalInstance.result.then(function (userData) {
                    $scope.userData = userData;
                }, function () {

                });
            };
        })
        .controller('NewProjectModalCtrl', function ($scope, $modalInstance, $http) {
            $scope.error = '';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'name': $scope.name,
                    'description': $scope.description,
                    'type': $scope.type
                };
                $scope.busy = true;
                $http.post('/api/project-create/', data)
                    .success(function(data) {
                        location.href = '/project/' + data;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$modalInstance.close();
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .controller('EditProfileModalCtrl', function ($scope, $modalInstance, $http, userData) {
            $scope.error = '';
            $scope.userData = userData;
            $scope.ok = function () {
                $scope.error = '';
                $scope.busy = true;
                $http.post('/api/user/', $scope.userData)
                    .success(function(data) {
                        $modalInstance.close(data);
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$modalInstance.close();
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .controller('projectCtrl', function ($scope, $modal, $http) {
            $scope.project = window['project']
            $scope.projectId = window['projectId'];
            $scope.isUserManager = window['isUserManager'];
            $scope.languages = window['languages'];
            $scope.participants = [];
            $http.get('/api/participant', {params: {project: $scope.projectId}})
                 .then(function(response) {
                    $scope.participants = response.data;
                 });
            $scope.texts = [];
            $http.get('/api/text', {params: {project: $scope.projectId}})
                 .then(function(response) {
                    $scope.texts = response.data;
                 });
            $scope.glossaries = [];
            $http.get('/api/glossary', {params: {project: $scope.projectId}})
                 .then(function(response) {
                    $scope.glossaries = response.data;
                 });
            $http.get('/api/tmx', {params: {project: $scope.projectId}})
                 .then(function(response) {
                    $scope.tmxes = response.data;
                 });
            $scope.addParticipant = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'addParticipantModal.html',
                    controller: 'AddParticipantModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                    }
                });

                modalInstance.result.then(function (participant) {
                    $scope.participants.push(participant);
                }, function () {
                });
            };
            $scope.removeParticipant = function (participant) {
                var data = {
                    'project': window['projectId'],
                    'user': participant.id
                };
                $scope.busy = true;
                $http.delete('/api/participant/', {params: data})
                    .success(function() {
                        var i = $scope.participants.indexOf(participant);
                        if (i > -1) {
                            delete $scope.participants.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.addText = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'addTextModal.html',
                    controller: 'AddTextModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                    }
                });

                modalInstance.result.then(function (text) {
                    $scope.texts.push(text);
                }, function () {
                });
            };
            $scope.editText = function (text) {
                var modalInstance = $modal.open({
                    templateUrl: 'editTextModal.html',
                    controller: 'EditTextModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                        text: function () {
                            return text;
                        },
                        glossaries: function () {
                            return $scope.glossaries;
                        },
                        tmxes: function () {
                            return $scope.tmxes;
                        },
                        languages: function () {
                            return $scope.languages;
                        }
                    }
                });

                modalInstance.result.then(function (text) {
                    //$scope.texts.push(text);
                }, function () {
                });
            };
            $scope.removeText = function (text) {
                var data = {
                    'project': window['projectId'],
                    'text': text.id
                };
                $scope.busy = true;
                $http.delete('/api/text/', {params: data})
                    .success(function() {
                        var i = $scope.texts.indexOf(text);
                        if (i > -1) {
                            delete $scope.texts.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.addGlossary = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'addGlossaryModal.html',
                    controller: 'AddGlossaryModalCtrl',
                    size: 'md',
                    backdrop: 'true',
                    resolve: {
                        glossary: function () {
                            return false;
                        }
                    }
                });

                modalInstance.result.then(function (glossary) {
                    $scope.glossaries.push(glossary);
                }, function (data) {
                });
            };
            $scope.addTmx = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'addTmxModal.html',
                    controller: 'AddTmxModalCtrl',
                    size: 'md',
                    backdrop: 'true',
                    resolve: {
                        tmx: function () {
                            return false;
                        }
                    }
                });

                modalInstance.result.then(function (tmxes) {
                    if (angular.isArray($scope.tmxes)) {
                        $scope.tmxes = $scope.tmxes.concat(tmxes);
                    } else {
                        $scope.tmxes = tmxes;
                    }

                }, function (data) {
                });
            };
            $scope.editGlossary = function (glossary) {
                var modalInstance = $modal.open({
                    templateUrl: 'addGlossaryModal.html',
                    controller: 'AddGlossaryModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                        glossary: function () {
                            return glossary;
                        }
                    }
                });
                $http.get('/api/glossary', {params: {project: $scope.projectId, glossary: glossary.id}})
                     .then(function(response) {
                        glossary.rows = response.data.rows;
                        var lastRow = glossary.rows[glossary.rows.length - 1];
                        if (lastRow[0] && lastRow[1]) {
                            glossary.rows.push(['', ''])
                        }
                     });

                modalInstance.result.then(function (glossary) {
                }, function (data) {
                });
            };
            $scope.removeGlossary = function (glossary) {
                var data = {
                    'project': window['projectId'],
                    'glossary': glossary.id
                };
                $scope.busy = true;
                $http.delete('/api/glossary/', {params: data})
                    .success(function() {
                        var i = $scope.glossaries.indexOf(glossary);
                        if (i > -1) {
                            delete $scope.glossaries.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.removeTmx = function (tmx) {
                var data = {
                    'project': window['projectId'],
                    'tmx': tmx.id
                };
                $scope.busy = true;
                $http.delete('/api/tmx/', {params: data})
                    .success(function() {
                        var i = $scope.tmxes.indexOf(tmx);
                        if (i > -1) {
                            delete $scope.tmxes.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.closePopover = function () {
                $('.popover').remove();
            };

            $scope.editName = function () {
                $scope.projectName = $scope.project.name
                $scope.editingName = true;
            };
            $scope.saveName = function () {
                $scope.editingName = false;
                $scope.project.name = $scope.projectName;
                $http.post('/api/project/', {
                    'id': $scope.project.id,
                    'name': $scope.project.name
                })
                    .success(function(data) {
                    })
                    .error(function(data) {
                    });
            };
            $scope.cancelEditName = function () {
                $scope.editingName = false;
            };
            $scope.editDescription = function () {
                $scope.editingDescription = true;
                $scope.projectDescription = $scope.project.description
            };
            $scope.saveDescription = function () {
                $scope.project.description = $scope.projectDescription;
                $scope.editingDescription = false;
                $http.post('/api/project/', {
                    'id': $scope.project.id,
                    'description': $scope.project.description
                })
                    .success(function(data) {
                    })
                    .error(function(data) {
                    });
            };
            $scope.cancelEditDescription = function () {
                $scope.editingDescription = false;
            };

            $scope.removeProject = function (project) {
                $scope.busy = true;
                $http.delete('/api/project/', {params: {id: project.id}})
                    .success(function() {
                        $scope.busy = false;
                        location.href = '/projects/';
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            }
        })
        .controller('AddParticipantModalCtrl', function ($scope, $modalInstance, $http) {
            $scope.getUsers = function (query) {
                 return $http.get('/api/get-users', {params: {q: query}})
                     .then(function(response) {
                         return response.data;
                     });
            };
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'project': window['projectId'],
                    'user': $scope.user.id
                };
                $scope.busy = true;
                $http.post('/api/participant/', data)
                    .success(function(participant) {
                        $modalInstance.close(participant);
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .controller('AddTextModalCtrl', function ($scope, $modalInstance, $http, Upload) {
            $scope.text = {
                subject: 1
            };
            $scope.tab = 0;
            $scope.ok = function () {
                if (!$scope.text.title) {
                    $scope.error = 'Where is the title?';
                    return;
                }
                if (!$scope.text.subject) {
                    $scope.error = 'Subject is lost';
                    return;
                }
                if (!$scope.text.sourceLang || !$scope.text.targetLang) {
                    $scope.error = 'Langauges is not set?';
                    return;
                }
                $scope.error = '';
                var data = {
                    project: window['projectId'],
                    title: $scope.text.title,
                    subject: $scope.text.subject,
                    sourceLang: $scope.text.sourceLang,
                    targetLang: $scope.text.targetLang
                };
                if ($scope.tab === 0) {
                    if (!$scope.text.files || !$scope.text.files.length) {
                        $scope.error = 'Please, select a file';
                        return;
                    }
                    Upload.upload({
                        url: '/api/text/',
                        fields: data,
                        file: $scope.text.files[0]
                    })
                        .progress(function (evt) {
                        })
                        .success(function(text) {
                            $modalInstance.close(text);
                            $scope.busy = false;
                        })
                        .error(function(data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                } else {
                    if (!$scope.text.textBody) {
                        $scope.error = 'Empty text';
                        return;
                    }
                    data.textBody = $scope.text.textBody;
                    $scope.busy = true;
                    $http.post('/api/text/', data)
                        .success(function(text) {
                            $modalInstance.close(text);
                            $scope.busy = false;
                        })
                        .error(function(data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                }
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .controller('EditTextModalCtrl', function ($scope, $modalInstance, $http, text, glossaries, tmxes, languages) {
            $scope.text = text;
            $scope.options = {};
            if ($scope.text.translations.length) {
                $scope.options.currentTranslation = $scope.text.translations[0];
            } else {
                $scope.options.currentTranslation = null;
            }
            $scope.options.addNewTranslation = false;
            $scope.glossaries = glossaries;
            $scope.tmxes = tmxes;
            $scope.tab = 0;
            $scope.addTranslation = function (targetLang) {
                $scope.text.translations.push({
                    targetLangId: targetLang.id,
                    lang: targetLang.code,
                    langFull: targetLang.langFull,
                    langLocal: targetLang.langLocal
                });
                $scope.options.currentTranslation = $scope.text.translations[$scope.text.translations.length - 1];
                $scope.options.addNewTranslation = false;
            };
            $scope.getLanguages = function () {
                var result = [],
                    excludes = [],
                    i;
                for (i = 0; i < $scope.text.translations.length; i++) {
                    var translation = $scope.text.translations[i];
                    excludes.push(Number(translation.targetLangId));
                }
                for (i = 0; i < languages.length; i++) {
                    var language = languages[i];
                    if (excludes.indexOf(Number(language.id)) === -1) {
                        result.push(language);
                    }
                }
                return result;
            };
            $scope.toggleGlossary = function (id) {
                var index = $scope.text.glossaries.indexOf(id);
                if (index > -1) {
                    $scope.text.glossaries.splice(index, 1);
                } else {
                    $scope.text.glossaries.push(id);
                }
            };
            $scope.toggleTmx = function (id) {
                var index = $scope.text.tmxes.indexOf(id);
                if (index > -1) {
                    $scope.text.tmxes.splice(index, 1);
                } else {
                    $scope.text.tmxes.push(id);
                }
            };
            $scope.ok = function () {
                if (!$scope.text.title) {
                    $scope.error = 'Where is the title?';
                    return;
                }
                if (!$scope.text.subject) {
                    $scope.error = 'Subject is lost';
                    return;
                }
                if (!$scope.text.sourceLang || !$scope.text.targetLang) {
                    $scope.error = 'Langauges is not set?';
                    return;
                }
                $scope.error = '';
                var data = {
                    project: window['projectId'],
                    id: $scope.text.id,
                    title: $scope.text.title,
                    subject: $scope.text.subject,
                    sourceLang: $scope.text.sourceLang,
                    targetLang: $scope.text.targetLang,
                    glossaries: $scope.text.glossaries,
                    tmxes: $scope.text.tmxes
                };
                $scope.busy = true;
                $http.post('/api/text/', data)
                    .success(function(text) {
                        $modalInstance.close(text);
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .controller('AddGlossaryModalCtrl', function ($scope, $modalInstance, $http, glossary, Upload) {
            $scope.glossary = glossary || {
                rows: [['', '']]
            };
            $scope.changeRow = function (i) {
                if (i === $scope.glossary.rows.length - 1) {
                    if ($scope.glossary.rows[i][0] && $scope.glossary.rows[i][1]) {
                        $scope.glossary.rows.push(['', '']);
                    }
                } else if (i < $scope.glossary.rows.length - 1) {
                    if (!$scope.glossary.rows[i][0] && !$scope.glossary.rows[i][1]) {
                        delete $scope.glossary.rows.splice(i, 1);
                    }
                }
            };
            $scope.ok = function () {
                $scope.error = '';
                $scope.busy = true;
                var data = $scope.glossary;
                data['project'] = window['projectId'];
                if ($scope.glossary.id || $scope.tab === 1) {
                    delete data.file;
                    $http.post('/api/glossary/', data)
                        .success(function(glossary) {
                            $modalInstance.close(glossary);
                            $scope.busy = false;
                        })
                        .error(function(data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                } else {
                    Upload.upload({
                        url: '/api/glossary/',
                        fields: data,
                        file: data.files[0]
                    })
                        .progress(function (evt) {
                        })
                        .success(function(glossary) {
                            $modalInstance.close(glossary);
                            $scope.busy = false;
                        })
                        .error(function(data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                }
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .controller('AddTmxModalCtrl', function ($scope, $modalInstance, $http, tmx, Upload) {
            $scope.tmx = tmx || {
                rows: [['', '']]
            };
            $scope.ok = function () {
                $scope.busy = true;
                $scope.error = '';
                var data = $scope.tmx;
                data['project'] = window['projectId'];

                Upload.upload({
                        url: '/api/tmx/',
                        fields: data,
                        file: data.files[0]
                    })
                        .progress(function (evt) {
                        })
                        .success(function(tmxes) {
                            $modalInstance.close(tmxes);
                            $scope.busy = false;
                        })
                        .error(function(data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })
        .directive("fileread", [function () {
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
        }])

        .run(function ($http) {
            $http.defaults.headers.post['X-CSRFToken'] = window['csrfToken'];
        })
        .config(function ($interpolateProvider, $httpProvider) {
            // replace {{ by {=
            $interpolateProvider.startSymbol('{=');
            // replace }} by =}
            $interpolateProvider.endSymbol('=}');
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .directive('entry', function () {
            return {
                template: function(elem, attr) {
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
        })
        .directive('glossaryWord', function () {
            return {
                template: function(elem, attr) {
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
        })
        .directive('htmlContent', function($compile, $parse) {
            return {
                link: function(scope, element, attr) {
                    var content = attr['htmlContent'];
                    element.html($parse(content)(scope));
                    $compile(element.contents())(scope);
                }
            }
        })
        .directive('insertText', function($rootScope) {
            return {
                link: function(scope, element) {
                    if (typeof scope.entry !== 'undefined') {
                        scope.entry = scope.entry || undefined;
                        var id =  scope.entry.id;
                        $rootScope.$on('insertText', function(e, data) {
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
        })
        .filter('trusted', function($sce){
            return function(text) {
                return $sce.trustAsHtml(text);
            };
        });
})();
