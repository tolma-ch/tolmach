(function () {
    'use strict';

    /* App Module */

    var module = angular.module('tolmachApp', [
        'ui.select',
        'mainControllers',
        'profileModule',
        'projectModule',
        'projectsModule',
        'textModule'
    ]);

    module.run(function ($http) {
        $http.defaults.headers.post['X-CSRFToken'] = window.csrfToken;
    });
    module.config(function ($interpolateProvider, $httpProvider) {
        // replace {{ by {=
        $interpolateProvider.startSymbol('{=');
        // replace }} by =}
        $interpolateProvider.endSymbol('=}');
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });
}());;(function () {
    'use strict';

    var module = angular.module('profileControllers', []);

    module.controller('ProfileCtrl', ['$scope', '$modal',
        function ($scope, $modal) {
            $scope.userData = window['userData'];
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
        }
    ]);

    var controller = module.controller('EditProfileModalCtrl', ['$scope', '$modalInstance', '$http', 'userData',
        function ($scope, $modalInstance, $http, userData) {
            $scope.error = '';
            $scope.userData = userData;
            $scope.imageCropResult = null;
            $scope.showImageCropper = true;
            $scope.imageCropStep = 1;
            $scope.blah = 1;
            $scope.$watch('imageCropResult', function(newVal) {
                $scope.blah++;
                if (newVal) {
                    console.log('imageCropResult', newVal);
                }
                return newVal;
            });
            $scope.ok = function () {
                $scope.busy = true;
                $scope.error = '';
                $http.post('/api/user/', $scope.userData)
                    .success(function(data) {
                        if ($scope.imageCropResult) {
                            $http.post('/api/user/', JSON.stringify($scope.imageCropResult))
                                .success(function() {
                                    location.reload();
                                })
                                .error(function() {
                                    $scope.busy = false;
                                    $modalInstance.close(data);
                                });
                        } else {
                            $modalInstance.close(data);
                        }
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
        }
    ]);
}());;(function () {
    'use strict';

    angular.module('profileModule', [
        'ui.bootstrap',
        'ImageCropper',
        'profileControllers'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('projectControllers', []);

    module.controller('projectCtrl', ['$scope', '$modal', '$http',
        function ($scope, $modal, $http) {
            $scope.project = window['project'];
            $scope.projectId = window['projectId'];
            $scope.isUserManager = window['isUserManager'];
            $scope.languages = window['languages'];
            $scope.participants = [];
            $http.get('/api/participant', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.participants = response.data;
                });
            $scope.texts = [];
            $http.get('/api/text', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.texts = response.data;
                });
            $scope.glossaries = [];
            $http.get('/api/glossary', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.glossaries = response.data;
                });
            $http.get('/api/tmx', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.tmxes = response.data;
                });
            $scope.addParticipant = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'addParticipantModal.html',
                    controller: 'AddParticipantModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
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
                    .success(function () {
                        var i = $scope.participants.indexOf(participant);
                        if (i > -1) {
                            delete $scope.participants.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function (data) {
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
                    resolve: {}
                });

                modalInstance.result.then(function (text) {
                    $scope.texts.push(text);
                }, function () {
                });
            };
            $scope.editText = function (text) {
                if (!$scope.isUserManager) {
                    return;
                }
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

                modalInstance.result.then(function (res) {
                    if (res === 'removed') {
                        var i = $scope.texts.indexOf(text);
                        if (i > -1) {
                            delete $scope.texts.splice(i, 1);
                        }
                    }
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
                    .success(function () {
                        var i = $scope.texts.indexOf(text);
                        if (i > -1) {
                            delete $scope.texts.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function (data) {
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
                    .then(function (response) {
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
                    .success(function () {
                        var i = $scope.glossaries.indexOf(glossary);
                        if (i > -1) {
                            delete $scope.glossaries.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function (data) {
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
                    .success(function () {
                        var i = $scope.tmxes.indexOf(tmx);
                        if (i > -1) {
                            delete $scope.tmxes.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.closePopover = function () {
                $('.popover').remove();
            };

            $scope.editName = function () {
                $scope.projectName = $scope.project.name;
                $scope.editingName = true;
            };
            $scope.saveName = function () {
                $scope.editingName = false;
                $scope.project.name = $scope.projectName;
                $http.post('/api/project/', {
                        'id': $scope.project.id,
                        'name': $scope.project.name
                    })
                    .success(function (data) {
                    })
                    .error(function (data) {
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
                    .success(function (data) {
                    })
                    .error(function (data) {
                    });
            };
            $scope.cancelEditDescription = function () {
                $scope.editingDescription = false;
            };

            $scope.removeProject = function (project) {
                $scope.busy = true;
                $http.delete('/api/project/', {params: {id: project.id}})
                    .success(function () {
                        $scope.busy = false;
                        location.href = '/projects/';
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            }
        }
    ]);

    module.controller('AddParticipantModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
            $scope.getUsers = function (query) {
                return $http.get('/api/get-users', {params: {q: query}})
                    .then(function (response) {
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
                    .success(function (participant) {
                        $modalInstance.close(participant);
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddTextModalCtrl', ['$scope', '$modalInstance', '$http', 'Upload',
        function ($scope, $modalInstance, $http, Upload) {
            $scope.text = {
                subject: 1
            };
            $scope.tab = 0;
            $scope.$watch('text.files', function (value) {
                if (!$scope.text.title && angular.isArray(value) && value.length) {
                    $scope.text.title = value[0].name;
                }
            });
            $scope.ok = function () {
                if (!$scope.text.title) {
                    $scope.error = 'Where is the title?';
                    return;
                }
                if (!$scope.text.subject) {
                    $scope.error = 'Subject is lost';
                    return;
                }
                if (!$scope.text.sourceLang) {
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
                        .success(function (text) {
                            $modalInstance.close(text);
                            $scope.busy = false;
                        })
                        .error(function (data) {
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
                        .success(function (text) {
                            $modalInstance.close(text);
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                }
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('EditTextModalCtrl', ['$scope', '$modalInstance', '$http', 'text', 'glossaries', 'tmxes', 'languages',
        function ($scope, $modalInstance, $http, text, glossaries, tmxes, languages) {
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
                if (!targetLang) {
                    return;
                }
                $scope.text.translations.push({
                    targetLangId: targetLang.id,
                    lang: targetLang.code,
                    langFull: targetLang.langFull,
                    langLocal: targetLang.langLocal
                });
                $scope.options.NewTranslationTargetLang = null;
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
                var index = $scope.options.currentTranslation.glossaries.indexOf(id);
                if (index > -1) {
                    $scope.options.currentTranslation.glossaries.splice(index, 1);
                } else {
                    $scope.options.currentTranslation.glossaries.push(id);
                }
            };
            $scope.toggleTmx = function (id) {
                var index = $scope.options.currentTranslation.tmxes.indexOf(id);
                if (index > -1) {
                    $scope.options.currentTranslation.tmxes.splice(index, 1);
                } else {
                    $scope.options.currentTranslation.tmxes.push(id);
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
                if (!$scope.text.sourceLang) {
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
                    translations: $scope.text.translations,
                    tmxes: $scope.text.tmxes
                };
                $scope.busy = true;
                $http.post('/api/text/', data)
                    .success(function (text) {
                        $modalInstance.close(text);
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.remove = function () {
                var data = {
                    'project': window['projectId'],
                    'text': $scope.text.id
                };
                $scope.busy = true;
                $http.delete('/api/text/', {params: data})
                    .success(function () {
                        $scope.busy = false;
                        $modalInstance.close('removed');
                    })
                    .error(function (data) {
                        $scope.busy = false;
                        $scope.error = data;
                    });
            };
            $scope.removeTranslation = function (translation) {
                var i = $scope.text.translations.indexOf(translation);
                if (i === -1) {
                    return;
                }
                delete $scope.text.translations.splice(i, 1);
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddGlossaryModalCtrl', ['$scope', '$modalInstance', '$http', 'glossary', 'Upload',
        function ($scope, $modalInstance, $http, glossary, Upload) {
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
                        .success(function (glossary) {
                            $modalInstance.close(glossary);
                            $scope.busy = false;
                        })
                        .error(function (data) {
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
                        .success(function (glossary) {
                            $modalInstance.close(glossary);
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                }
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddTmxModalCtrl', ['$scope', '$modalInstance', '$http', 'tmx', 'Upload',
        function ($scope, $modalInstance, $http, tmx, Upload) {
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
                    .success(function (tmxes) {
                        $modalInstance.close(tmxes);
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());;(function () {
    'use strict';

    angular.module('projectModule', [
        'ui.bootstrap',
        'ngFileUpload',
        'projectControllers'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('projectsControllers', []);

    module.controller('projectsCtrl', ['$scope', '$modal',
        function ($scope, $modal) {
            $scope.startNewProject = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'newProjectModal.html',
                    controller: 'NewProjectModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function () {
                }, function () {
                });
            };

        }
    ]);

    module.controller('NewProjectModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
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
                    .success(function (data) {
                        location.href = '/project/' + data;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$modalInstance.close();
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('projectsModule', [
        'ui.bootstrap',
        'projectsControllers'
    ]);
}());;(function () {
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
                for (i = 0; i < nodes.length; i++) {
                    var node = nodes[i],
                        j,
                        index,
                        type;
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
                    nodes = [];
                angular.forEach(element.childNodes, function (node) {
                    nodes.push(node);
                });

                if (typeof win.getSelection != "undefined") {
                    sel = win.getSelection();
                    if (sel.rangeCount > 0) {
                        var range = win.getSelection().getRangeAt(0);
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
}());;(function () {
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
}());;(function () {
    'use strict';

    var module = angular.module('textFilters', []);

    module.filter('trusted', ['$sce', function ($sce) {
        return function (text) {
            return $sce.trustAsHtml(text);
        };
    }]);
}());;(function () {
    'use strict';

    angular.module('textModule', [
        'ui.bootstrap',
        'contenteditable',
        'textControllers',
        'textDirectives',
        'textFilters'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('mainControllers', [
        'ui.bootstrap'
    ]);

    module.controller('mainCtrl', ['$scope', '$http', '$timeout', '$modal',
        function ($scope, $http, $timeout, $modal) {

            var updateMessages = function () {
                $http.get('/api/message/').success(function (data) {
                    $scope.messages = data;
                    $timeout(updateMessages, 15 * 60 * 1000);
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
            $scope.readMessage = function (message) {
                $http.post('/api/message/', {id: message.id}).success(function (data) {
                    $scope.messages = data;
                    $timeout(updateMessages, 5000);
                }).error(function (data) {
                })
            };
            $scope.showAllMessages = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'allMessagesModal.html',
                    controller: 'AllMessagesModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function () {
                }, function () {
                });
            };
            updateMessages();

            $scope.redrawHelp = function () {
                if (!$scope.currentBlock) {
                    return;
                }
                var $block = $($scope.currentBlock),
                    params = $block.offset();
                params.width = $block.outerWidth();
                params.right = params.left + params.width;
                params.bottom = params.top + params.height;
                params.height = $block.outerHeight();
                $scope.helpBlockStyle1 = {
                    top: '0',
                    left: '0',
                    height: params.top + 'px',
                    right: '0'
                };
                $scope.helpBlockStyle2 = {
                    left: '0',
                    top: params.top + 'px',
                    width: params.left + 'px',
                    height: params.height + 'px'
                };
                $scope.helpBlockStyle3 = {
                    left: params.left + params.width + 'px',
                    top: params.top + 'px',
                    height: params.height + 'px',
                    right: 0
                };
                $scope.helpBlockStyle4 = {
                    left: '0',
                    top: params.top + params.height + 'px',
                    bottom: '0',
                    right: '0'
                };
                $scope.helpCenterBlockStyle1 = {
                    top: params.top + 'px',
                    left: params.left + 'px',
                    height: params.height + 'px',
                    width: params.width + 'px'
                };
                var $body = $('body'),
                    textWidth = Math.min(300, $body.width()),
                    textRight = params.left + params.width,
                    textLeft = $scope.leftAlign ? Math.max(0, params.left - textWidth + 40) : Math.max(0, textRight - textWidth);
                textRight = Math.max(0, textLeft + textWidth);
                textWidth = textRight - textLeft;
                $scope.helpTextStyle1 = {
                    'bottom': '0',
                    'left': textLeft + 'px',
                    'width': textWidth + 'px'
                };
            };
            $scope.beginHelpPresentation = function () {
                var event = $scope.$broadcast('helpPresentationStart');
                if (event.customized) {
                    return;
                }
                $scope.helpBlocks = $('.helped-block').toArray();
                $scope.currentBlock = $scope.helpBlocks.shift();
                $scope.clickBlock = function () {
                };
                $scope.leftAlign = false;
                $scope.hasNext = !!$scope.helpBlocks.length;
                if ($scope.currentBlock) {
                    $scope.helpText = $($scope.currentBlock).attr('help-text');
                    $scope.redrawHelp();
                    $scope.helpShow = true;
                } else {
                    $scope.closeHelpPresentation();
                }
            };
            $scope.closeHelpPresentation = function () {
                $scope.helpShow = false;
                $scope.helpBlocks = [];
                $scope.hasNext = false;
                $scope.currentBlock = null;
                $scope.clickBlock = false;
                $scope.leftAlign = false;
            };
            $scope.nextHelpStep = function () {
                var event = $scope.$broadcast('helpPresentationNext');
                if (event.customized) {
                    return;
                }
                $scope.currentBlock = $scope.helpBlocks.shift();
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.hasNext = !!$scope.helpBlocks.length;
                if ($scope.currentBlock) {
                    $scope.helpText = $($scope.currentBlock).attr('help-text');
                    $scope.redrawHelp();
                } else {
                    $scope.closeHelpPresentation();
                }
            };
            $scope.helpResize = function () {
                if ($scope.helpShow) {
                    $scope.redrawHelp();
                }
            };
            $scope.globalKeydown = function (event) {
                $scope.$broadcast('GlobalKeydown', event);
            };
            $scope.bodyClick = function (event) {
                $scope.$broadcast('GlobalClick', event);
            };
        }
    ]);

    module.controller('AllMessagesModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
            $scope.error = '';
            $http.get('/api/message/all').success(function (data) {
                $scope.messages = data;
                $timeout(updateMessages, 5000);
            }).error(function (data) {
            });

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());