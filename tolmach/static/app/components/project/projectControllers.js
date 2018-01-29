(function () {
    'use strict';

    var module = angular.module('projectControllers', []);

    module.controller('projectCtrl', ['$scope', '$modal', '$http',
        function ($scope, $modal, $http) {
            $scope.project = window['project'];
            $scope.projectId = window['projectId'];
            $scope.isUserManager = window['isUserManager'];
            $scope.managerId = window['managerId'];
            $scope.targetLang = window['targetLang'];
            $scope.languages = window['languages'];
            $scope.participants = [];
            $http.get('/ajax/participant', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.participants = response.data;
                });
            $scope.texts = [];
            $http.get('/ajax/text', {params: {project: $scope.projectId, project_target_lang: $scope.targetLang}})
                .then(function (response) {
                    $scope.texts = response.data;
                });
            $scope.glossaries = [];
            $http.get('/ajax/glossary', {params: {project: $scope.projectId, target_lang: $scope.targetLang}})
                .then(function (response) {
                    $scope.glossaries = response.data;
                });
            $http.get('/ajax/tmx', {params: {project: $scope.projectId, target_lang: $scope.targetLang}})
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
            $scope.changeParticipantStatus = function (participant) {
                console.log(participant);
                var ids = participant.split(",");
                var data = {
                    'project': window['projectId'],
                    'user': parseInt(ids[0]),
                    'status': parseInt(ids[1])
                };
                $scope.busy = true;
                $http.post('/ajax/participant/', data)
                    .success(function () {
                        for (var i in $scope.participants) {
                            if (i.id == parseInt(ids[0])) {
                                i.status = parseInt(ids[1]);
                            }
                        }
                        $scope.busy = false;
                        $http.get('/ajax/participant', {params: {project: $scope.projectId}})
                            .then(function (response) {
                                $scope.participants = response.data;
                            });
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.removeParticipant = function (participant) {
                var data = {
                    'project': window['projectId'],
                    'user': participant.id
                };
                $scope.busy = true;
                $http.delete('/ajax/participant/', {params: data})
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
            $scope.addProjectTranslation = function () {
                if (!$scope.isUserManager) {
                    return;
                }
                var modalInstance = $modal.open({
                    templateUrl: 'addProjectTranslationModal.html',
                    controller: 'AddProjectTranslationModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
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
                $http.delete('/ajax/text/', {params: data})
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
                $http.get('/ajax/glossary', {params: {project: $scope.projectId, glossary: glossary.id}})
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
                $http.delete('/ajax/glossary/', {params: data})
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
                $http.delete('/ajax/tmx/', {params: data})
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
                $http.post('/ajax/project/', {
                        'id': $scope.project.id,
                        'name': $scope.project.name.substring(0, 250)
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
                $http.post('/ajax/project/', {
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
                $http.delete('/ajax/project/', {params: {id: project.id}})
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
                return $http.get('/ajax/get-users', {params: {q: query}})
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
                $http.post('/ajax/participant/', data)
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
    module.controller('AddProjectTranslationModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
            $scope.error = '';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'project': window['projectId'],
                    'target_lang': $scope.target_lang
                };
                $scope.busy = true;
                $http.post('/ajax/project-add-translation/', data)
                    .success(function (data) {
                        location.href = '/project/' + data['project_id'] + '/' + data['target_lang'] + '/';
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
    module.controller('SelectTextRangesModalCtrl', ['$scope', '$modalInstance', '$http', 'Upload', 'data', '$timeout',
        function ($scope, $modalInstance, $http, Upload, data, $timeout) {
            var result = {},
                checkResult = function () {
                    for (var sheetName in result) {
                        if (!result.hasOwnProperty(sheetName)) {
                            continue;
                        }
                        var ranges = result[sheetName];
                        for (var j in ranges) {
                            if (!ranges.hasOwnProperty(j)) {
                                continue;
                            }
                            var range = ranges[j];
                            if (!range.source.coords) {
                                range.source.error = true;
                                $scope.currentSheetName = sheetName;
                                return false;
                            }
                            if (!range.target.coords) {
                                range.target.error = true;
                                $scope.currentSheetName = sheetName;
                                return false;
                            }
                        }
                    }
                    return true;
                };
            $scope.ranges = result;
            $scope.sheets = data;
            for (var i in data) {
                if (data.hasOwnProperty(i)) {
                    $scope.ranges[i] = [];
                }
            }
            $scope.currentSheetName = Object.keys(data)[0];
            $scope.updateResult = function (sheetName, value) {
                result[sheetName] = value;
            };
            $scope.ok = function () {
                if (!checkResult()) {
                    return;
                }
                $modalInstance.close(result);
            };
            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddTextModalCtrl', ['$scope', '$modalInstance', '$http', 'Upload', '$modal',
        function ($scope, $modalInstance, $http, Upload, $modal) {
            $scope.busy = false;
            $scope.progress = 0;
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
                $scope.error = '';
                var data = {
                    project: window['projectId'],
                    title: $scope.text.title.substring(0, 250),
                    project_target_lang: window['targetLang'],
                    subject: $scope.text.subject
                };
                if ($scope.tab === 0) {
                    if (!$scope.text.files || !$scope.text.files.length) {
                        $scope.error = 'Please, select a file';
                        return;
                    }
                    $scope.busy = true;
                    var fileName = $scope.text.files[0].name,
                        ext = fileName ? fileName.split('.').pop() : false;
                    if (ext === 'xlsx') {
                        data['xlsx_prepare_state'] = 1;
                    }
                    Upload.upload({
                            url: '/ajax/text/',
                            fields: data,
                            file: $scope.text.files[0]
                        })
                        .progress(function (evt) {
                            $scope.progress = 100.0 * evt.loaded / evt.total;
                        })
                        .success(function (text) {
                            $scope.busy = false;
                            if (ext === 'xlsx') {
                                var serverFileName = text['file_name'],
                                    serverFileType = text['file_type'],
                                    sheets = text['Text'],
                                    modalInstance = $modal.open({
                                    templateUrl: 'selectTextRangesModal.html',
                                    controller: 'SelectTextRangesModalCtrl',
                                    size: 'lg',
                                    backdrop: 'static',
                                    resolve: {
                                        data: function () {
                                            return sheets;
                                        }
                                    }
                                });

                                modalInstance.result.then(function (res) {
                                    var ranges = {};
                                    for (var i in res) {
                                        if (!res.hasOwnProperty(i)) {
                                            continue;
                                        }
                                        var sheet = res[i];
                                        ranges[i] = {
                                            'source_coords': [],
                                            'target_coords': []
                                        };
                                        for (var j in sheet) {
                                            if (!sheet.hasOwnProperty(j)) {
                                                continue;
                                            }
                                            var range = sheet[j];
                                            ranges[i]['source_coords'].push(range.source.text);
                                            ranges[i]['target_coords'].push(range.target.text);
                                        }
                                    }
                                    var data = {
                                        project: window['projectId'],
                                        title: $scope.text.title,
                                        project_target_lang: window['targetLang'],
                                        subject: $scope.text.subject,
                                        file_name: serverFileName,
                                        file_type: serverFileType,
                                        custom_parse: ranges
                                    };
                                    $scope.busy = true;
                                    $http.post('/ajax/text/', data)
                                        .success(function (text) {
                                            $scope.busy = false;
                                            $modalInstance.close(text);
                                        })
                                        .error(function (data) {
                                            $scope.busy = false;
                                        });
                                }, function () {
                                });

                            } else {
                                $modalInstance.close(text);
                            }
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
                    $http.post('/ajax/text/', data)
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
    module.controller('EditTextModalCtrl', ['$scope', '$modalInstance', '$http', 'text',
        function ($scope, $modalInstance, $http, text) {
            $scope.text = text;
            $scope.options = {};
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
                    title: $scope.text.title.substring(0, 250),
                    project_target_lang: window['targetLang'],
                    machine: $scope.text.machine,
                    subject: $scope.text.subject,
                    sourceLang: $scope.text.sourceLang,
                    targetLang: $scope.text.targetLang,
                    translations: $scope.text.translations,
                };
                $scope.busy = true;
                $http.post('/ajax/text/', data)
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
                $http.delete('/ajax/text/', {params: data})
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
                data['name'] = data['name'].substring(0, 250);
                data['target_lang'] = window['targetLang'];
                if ($scope.glossary.id || $scope.tab === 1) {
                    delete data.file;
                    $http.post('/ajax/glossary/', data)
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
                            url: '/ajax/glossary/',
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
                data['name'] = data['name'].substring(0, 250);
                data['project'] = window['projectId'];

                Upload.upload({
                        url: '/ajax/tmx/',
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
}());