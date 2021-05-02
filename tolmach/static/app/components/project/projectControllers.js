(function () {
    'use strict';

    var module = angular.module('projectControllers', []);

    module.controller('projectCtrl', ['$scope', '$uibModal', '$http',
        function ($scope, $uibModal, $http) {
            $scope.project = window['project'];
            $scope.projectId = window['projectId'];
            $scope.isUserManager = window['isUserManager'];
            $scope.userMembershipStatus = window['userMembershipStatus'];
            $scope.managerId = window['managerId'];
            $scope.userId = window['userId'];
            $scope.targetLang = window['targetLang'];
            $scope.languages = window['languages'];
            $scope.participants = [];
            $scope.showDocumentStats = false;
            if (window['pageType'] !== "stats") {
                $http.get('/ajax/participant', {params: {project: $scope.projectId}})
                    .then(function (response) {
                        $scope.participants = response.data;
                    });
                $scope.texts = [];
                $http.get('/ajax/text', {params: {project: $scope.projectId, project_target_lang: $scope.targetLang}})
                    .then(function (response) {
                        var progressIcon = document.getElementById("documents-preloader");
                        progressIcon.style.display = "none";
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
            }
            $scope.addParticipant = function () {
                var modalInstance = $uibModal.open({
                    templateUrl: 'addParticipantModal.html',
                    controller: 'AddParticipantModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                        projectId: function () {
                            return $scope.projectId;
                        },
                        managerId: function () {
                            return $scope.managerId;
                        }
                    }
                });

                // modalInstance.result.then(function (participant) {
                //     $scope.participants.push(participant);
                // }, function () {
                // });
            };
            $scope.leaveProject = function () {
                var data = {
                    'project': window['projectId'],
                    'user': $scope.userId
                };
                $scope.busy = true;
                $http.delete('/ajax/participant/', {params: data})
                    .success(function () {
                        $scope.busy = false;
                        location.href = '/projects/my/';
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.addProjectTranslation = function () {
                if (!$scope.isUserManager && !($scope.userMembershipStatus == 0)) {
                    return;
                }
                var modalInstance = $uibModal.open({
                    templateUrl: 'addProjectTranslationModal.html',
                    controller: 'AddProjectTranslationModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });
            };
            $scope.addText = function () {
                var modalInstance = $uibModal.open({
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
                if (!$scope.isUserManager && !($scope.userMembershipStatus == 0)) {
                    return;
                }
                var modalInstance = $uibModal.open({
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
                modalInstance.rendered.then(function(){
                    $http.post('/ajax/get-translation-progress/', {
                            text: text.id,
                            target_lang: window['targetLang']
                        }).success(function (data) {
                            text.translation.translated_chars = data['translated_chars'];
                            text.translation.translated_chars_without_spaces = data['translated_chars_without_spaces'];
                            text.translation.users_translated = data['users_translated'];
                            text.translation.max_translated_fragments = data['max_translated_fragments'];
                        }).error(function (a) {
                            //console.error(a);
                        });
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
                var modalInstance = $uibModal.open({
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
                var modalInstance = $uibModal.open({
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
                var modalInstance = $uibModal.open({
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
                        location.href = '/projects/my/';
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            }
        }
    ]);

    module.controller('AddParticipantModalCtrl', ['$scope', '$uibModalInstance', '$http', 'projectId', 'managerId',
        function ($scope, $uibModalInstance, $http, projectId, managerId) {
            $scope.participants = [];
            $scope.projectInviteCode = "";
            $http.get('/ajax/project/invite-code/', {params: {project: projectId}})
                .then(function (response) {
                    $scope.projectInviteCode = response.data.project_invite_link_code;
                });
            $scope.updateInviteCode = function () {
                var data = {
                    'project': projectId
                };
                // $scope.busy = true;
                $http.post('/ajax/project/invite-code/', data)
                    .success(function (response) {
                        console.log(response.project_invite_link_code);
                        $scope.projectInviteCode = response.project_invite_link_code;
                        // $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        // $scope.busy = false;
                    });
            };
            $http.get('/ajax/participant', {params: {project: projectId}})
                .then(function (response) {
                    $scope.participants = response.data;
                });
            $scope.managerId = managerId;
            $scope.changeParticipantStatus = function (participant) {
                console.log(participant);
                var ids = participant.split(",");
                var data = {
                    'project': projectId,
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
                        $http.get('/ajax/participant', {params: {project: projectId}})
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
                    'project': projectId,
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
            $scope.getUsers = function (query) {
                return $http.get('/ajax/get-users', {params: {q: query}})
                    .then(function (response) {
                        return response.data;
                    });
            };
            $scope.addParticipant = function () {
                $scope.error = '';
                var data = {
                    'project': window['projectId'],
                    'user': $scope.user.id
                };
                $scope.busy = true;
                $http.post('/ajax/participant/', data)
                    .success(function (participant) {
                        $scope.busy = false;
                        $http.get('/ajax/participant', {params: {project: projectId}})
                            .then(function (response) {
                                $scope.participants = response.data;
                            });
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };
            $scope.ok = function () {
                $uibModalInstance.close();
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddProjectTranslationModalCtrl', ['$scope', '$uibModalInstance', '$http',
        function ($scope, $uibModalInstance, $http) {
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
                        //$uibModalInstance.close();
                    });
            };
            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('SelectTextRangesModalCtrl', ['$scope', '$uibModalInstance', '$http', 'Upload', 'data', '$timeout',
        function ($scope, $uibModalInstance, $http, Upload, data, $timeout) {
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
                $uibModalInstance.close(result);
            };
            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddTextModalCtrl', ['$scope', '$uibModalInstance', '$http', 'Upload', '$uibModal',
        function ($scope, $uibModalInstance, $http, Upload, $uibModal) {
            $scope.showOgCard = false;
            $scope.isValidUrl = false;
            $scope.encodedURI = '';
            $scope.ogCardData = {};
            $scope.busy = false;
            $scope.progress = 0;
            $scope.text = {
                subject: 1,
                readability: false,
            };
            $scope.tab = 0;
            $scope.$watch('text.files', function (value) {
                if (!$scope.text.title && angular.isArray(value) && value.length) {
                    $scope.text.title = value[0].name;
                }
            });

            $scope.checkIfURL = function () {
                var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
                '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
                '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
                '(\\:\\d+)?(\\/[-a-z\\d%_.@~+]*)*'+ // port and path
                '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
                '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
              console.log("< " + $scope.text.title + " >" + "is valid URL: " + !!pattern.test($scope.text.title));

              if (!!pattern.test($scope.text.title)) {
                  var data = {
                      url: $scope.text.title
                  };
                  $scope.busy = true;
                  $http.post('/ajax/get-url-og/', data)
                      .success(function (data) {
                          // $uibModalInstance.close(text);
                          console.log(data);
                          $scope.ogCardData = data;
                          $scope.showOgCard = true;
                          $scope.isValidUrl = true;
                          $scope.encodedURI = encodeURIComponent($scope.text.title);
                          $scope.error = '';
                          $scope.busy = false;
                      })
                      .error(function (data) {
                          $scope.error = data;
                          $scope.isValidUrl = false;
                          $scope.showOgCard = false;
                          $scope.busy = false;
                      });
              } else {
                  $scope.showOgCard = false;
                  $scope.isValidUrl = false;
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
                $scope.error = '';
                var data = {
                    project: window['projectId'],
                    title: $scope.text.title.substring(0, 250),
                    project_target_lang: window['targetLang'],
                    subject: $scope.text.subject,
                    split_mode: $scope.splitMode,
                    is_valid_url: $scope.isValidUrl,
                    readability: $scope.text.readability,
                };
                if ($scope.tab === 0) {
                    if ((!$scope.text.files || !$scope.text.files.length) && !$scope.isValidUrl) {
                        console.log('Please, select a file or provide URL to web page');
                        $scope.error = 'Please, select a file or provide URL to web page';
                        return;
                    }
                    $scope.busy = true;
                    if ($scope.isValidUrl) {
                        $http.post('/ajax/text/', data)
                        .success(function (text) {
                            $uibModalInstance.close(text);
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                    } else {
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
                                console.log(text);
                                if (ext === 'xlsx') {
                                    var serverFileName = text['file_name'],
                                        serverFileType = text['file_type'],
                                        sheets = text['Text'],
                                        modalInstance = $uibModal.open({
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

                                        function getFirstKey(data) {
                                            for (var elem in data) {
                                                return elem;
                                            }
                                        }

                                        var data = {
                                            project: window['projectId'],
                                            title: $scope.text.title,
                                            project_target_lang: window['targetLang'],
                                            subject: $scope.text.subject,
                                            file_name: serverFileName,
                                            file_type: serverFileType,
                                            custom_parse: ranges[getFirstKey(ranges)]['source_coords'].length > 0 ? ranges : []
                                        };
                                        $scope.busy = true;
                                        $http.post('/ajax/text/', data)
                                            .success(function (text) {
                                                $scope.busy = false;
                                                $uibModalInstance.close(text);
                                            })
                                            .error(function (data) {
                                                $scope.busy = false;
                                            });
                                    }, function () {
                                    });

                                } else {
                                    $uibModalInstance.close(text);
                                }
                            })
                            .error(function (data) {
                                $scope.error = data;
                                $scope.busy = false;
                            });
                    }
                } else {
                    if (!$scope.text.textBody) {
                        $scope.error = 'Empty text';
                        return;
                    }
                    data.textBody = $scope.text.textBody;
                    $scope.busy = true;
                    $http.post('/ajax/text/', data)
                        .success(function (text) {
                            $uibModalInstance.close(text);
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                }
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('EditTextModalCtrl', ['$scope', '$uibModalInstance', '$http', 'text',
        function ($scope, $uibModalInstance, $http, text) {
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
                        $uibModalInstance.close(text);
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
                        $uibModalInstance.close('removed');
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
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddGlossaryModalCtrl', ['$scope', '$uibModalInstance', '$http', 'glossary', 'Upload',
        function ($scope, $uibModalInstance, $http, glossary, Upload) {
            $scope.glossary = glossary || {
                    rows: [['', '']],
                    name: generateRandomName()
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
                if (!$scope.glossary.name) {
                    $scope.error = 'Where is the title?';
                    return;
                }
                $scope.busy = true;
                var data = $scope.glossary;
                data['project'] = window['projectId'];
                data['name'] = data['name'].substring(0, 250);
                data['target_lang'] = window['targetLang'];
                if ($scope.glossary.id || $scope.tab === 1) {
                    delete data.file;
                    $http.post('/ajax/glossary/', data)
                        .success(function (glossary) {
                            $uibModalInstance.close(glossary);
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
                            $uibModalInstance.close(glossary);
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            $scope.error = data;
                            $scope.busy = false;
                        });
                }
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
    module.controller('AddTmxModalCtrl', ['$scope', '$uibModalInstance', '$http', 'tmx', 'Upload',
        function ($scope, $uibModalInstance, $http, tmx, Upload) {
            $scope.tmx = tmx || {
                    rows: [['', '']],
                    name: generateRandomName()
                };
            $scope.ok = function () {
                $scope.busy = true;
                $scope.error = '';
                var data = $scope.tmx;
                data['name'] = data['name'].substring(0, 250);
                data['project'] = window['projectId'];
                data['target_lang'] = window['targetLang'];

                Upload.upload({
                        url: '/ajax/tmx/',
                        fields: data,
                        file: data.files[0]
                    })
                    .progress(function (evt) {
                    })
                    .success(function (tmxes) {
                        $uibModalInstance.close(tmxes);
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
}());