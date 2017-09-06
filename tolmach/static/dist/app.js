(function () {
    'use strict';

    /* App Module */

    var module = angular.module('tolmachApp', [
        'ui.select',
        'ui.toggle',
        'mainModule',
        'profileModule',
        'projectModule',
        'projectsModule',
        'textModule',
        'chatModule'
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

    var module = angular.module('chatControllers', []);

    module.controller('ChatCtrl', ['$scope', '$window', 'Chat',
        function ($scope, $window, Chat) {
            $scope.style = {};
            $scope.$on('GlobalResize', function (e, w) {
                var height = w.h,
                    width = w.w;
                //$scope.style.right = width + 'px';
                //$scope.style.right = width + 'px';
            });
            $scope.textareaKeypress = function (event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (event.ctrlKey && (code === 13 || code === 10)) {
                    Chat.sendMessage(this.value);
                }
            };
        }
    ]);
}());;(function () {
    'use strict';

    angular.module('chatModule', [
        'chatServices',
        'chatControllers'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('chatServices', []);

    module.factory('Chat', ['$http',
        function ($http) {
            var self = {};
            self.sendMessage = function () {

            };
            return self;
        }
    ]);
}());;angular
    .module('tolmachApp')
    .component('handsontable', {
        bindings: {
            onUpdate: '&',
            ranges: '<',
            sheet: '<'
        },
        templateUrl: 'handsontable.template.html',
        controller: ['$element', '$timeout', function ($element, $timeout) {
            var ctrl = this,
                hot,
                cellRenderer = function (instance, td, row, col, prop, value, cellProperties) {
                    Handsontable.renderers.TextRenderer.apply(this, arguments);
                    var color = matrix[row] && matrix[row][col];
                    if (color == 1) {
                        td.style.color = 'green';
                        td.style.background = '#CEC';
                    } else if (color == 2) {
                        td.style.color = 'blue';
                        td.style.background = '#CCE';
                    } else {
                        td.style.color = 'black';
                        td.style.background = '#FFF';
                    }
                },
                chr = function (codePt) {
                    if (codePt > 0xFFFF) {
                        codePt -= 0x10000;
                        return String.fromCharCode(0xD800 + (codePt >> 10), 0xDC00 + (codePt & 0x3FF));
                    }
                    return String.fromCharCode(codePt);
                },
                numToChar = function(number)    {
                    var numeric = number % 26;
                    var letter = chr(65 + numeric);
                    var number2 = parseInt(number / 26);
                    if (number2 > 0) {
                        return numToChar(number2) + letter;
                    } else {
                        return letter;
                    }
                },
                checkIntersection = function (coords1, coords2) {
                    if (Math.max(coords1[0], coords2[0]) <= Math.min(coords1[2], coords2[2])
                     && Math.max(coords1[1], coords2[1]) <= Math.min(coords1[3], coords2[3])) {
                        throw 'intersection';
                    }
                },
                matrix = [],
                fillRangeToMatrix = function (coords, color) {
                    for (var i = coords[0]; i <= coords[2]; i++) {
                        if (!matrix[i]) {
                            matrix[i] = [];
                        }
                        for (var j = coords[1]; j <= coords[3]; j++) {
                            matrix[i][j] = color;
                        }
                    }
                },
                fillMatrix = function () {
                    matrix = [];
                    for (var i in ctrl.ranges) {
                        if (!ctrl.ranges.hasOwnProperty(i)) {
                            continue;
                        }
                        var range = ctrl.ranges[i];
                        fillRangeToMatrix(range.source.coords, 1);
                        fillRangeToMatrix(range.target.coords, 2);
                    }
                },
                activateNextRange = function (activeRange) {
                    var activeRangeIndex = ctrl.ranges.indexOf(activeRange);
                    if (activeRangeIndex > -1 && ctrl.ranges.hasOwnProperty(activeRangeIndex + 1)) {
                        var nextRange = ctrl.ranges[activeRangeIndex + 1];
                        nextRange.active = true;
                        nextRange.source.active = true;
                    } else {
                        for (var i in ctrl.ranges) {
                            if (!ctrl.ranges.hasOwnProperty(i)) {
                                continue;
                            }
                            var range = ctrl.ranges[i];
                            if (!range.source.coords) {
                                range.active = true;
                                range.source.active = true;
                                range.target.active = false;
                                return;
                            }
                            if (!range.target.coords) {
                                range.active = true;
                                range.target.active = true;
                                range.source.active = false;
                                return;
                            }
                            range.active = false;
                            range.source.active = false;
                            range.target.active = false;
                        }
                    }
                };

            ctrl.update = function () {
                ctrl.onUpdate({value: ctrl.ranges});
            };
            ctrl.ranges = [];
            ctrl.$onChanges = function(bindings) {
                if (bindings.ranges
                    && angular.isUndefined(bindings.ranges.previousValue)
                    && angular.isDefined(bindings.ranges.currentValue)) {
                    ctrl.ranges = bindings.ranges.previousValue;;
                }
                if (bindings.sheet && !hot) {
                    var sheetContainer = $element.find('.sheet__container')[0];
                    $timeout (function () {
                        fillMatrix();
                        Handsontable.renderers.registerRenderer('cellRenderer', cellRenderer);
                        hot = new Handsontable(sheetContainer, {
                            data: ctrl.sheet,
                            minSpareCols: 0,
                            minSpareRows: 0,
                            rowHeaders: true,
                            colHeaders: true,
                            contextMenu: true,
                            height: 500,
                            afterSelectionEnd: function (rowStart, columnStart, rowEnd, columnEnd) {
                                var coords = [rowStart, columnStart, rowEnd, columnEnd],
                                    text = numToChar(columnStart) + (rowStart + 1) + ":" +
                                           numToChar(columnEnd) + (rowEnd + 1),
                                    activeRange;
                                try {
                                    for (var i in ctrl.ranges) {
                                        if (!ctrl.ranges.hasOwnProperty(i)) {
                                            continue;
                                        }
                                        var range = ctrl.ranges[i];
                                        range.source.error = false;
                                        range.target.error = false;
                                        if (range.active) {
                                            activeRange = range;
                                            if (range.source.active) {
                                                checkIntersection(coords, range.target.coords);
                                            } else {
                                                checkIntersection(coords, range.source.coords);
                                            }
                                        } else {
                                            checkIntersection(coords, range.source.coords);
                                            checkIntersection(coords, range.target.coords);
                                        }
                                    }
                                    if (!activeRange) {
                                        activeRange = {
                                            active: true,
                                            source: {
                                                coords: false,
                                                text: '',
                                                active: true
                                            },
                                            target: {
                                                coords: false,
                                                text: '',
                                                active: false
                                            }
                                        };
                                        ctrl.ranges.push(activeRange);
                                    }
                                    if (activeRange) {
                                        if (activeRange.source.active) {
                                            activeRange.source.coords = coords;
                                            activeRange.source.text = text;
                                            activeRange.source.active = false;
                                            activeRange.target.active = true;
                                        } else {
                                            activeRange.target.coords = coords;
                                            activeRange.target.text = text;
                                            activeRange.target.active = false;
                                            activeRange.active = false;
                                            activateNextRange(activeRange);
                                        }
                                    }
                                    fillMatrix();
                                    console.log(matrix);
                                } catch (e) {
                                    console.log('intersection');
                                }
                                hot.deselectCell();
                                ctrl.update();
                                hot.render();
                            },
                            cells: function (row, col, prop) {
                                var cellProperties = {};
                                cellProperties.renderer = cellRenderer;
                                return cellProperties;
                            }
                        });
                    });
                }
            };
            ctrl.selectRange = function (range, input) {
                for (var i in ctrl.ranges) {
                    if (!ctrl.ranges.hasOwnProperty(i)) {
                        continue;
                    }
                    var someRange = ctrl.ranges[i];
                    if (someRange === range) {
                        someRange.active = true;
                        someRange.source.active = !input;
                        someRange.target.active = input;
                    } else {
                        someRange.active = false;
                        someRange.source.active = false;
                        someRange.target.active = false;
                    }
                }
            };
            ctrl.removeRange = function (range) {
                var index = ctrl.ranges.indexOf(range);
                if (index > -1) {
                    ctrl.ranges.splice(index, 1);
                    ctrl.update();
                }
            }
        }]
    });;(function () {
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
            $scope.cropper = {};
            $scope.cropper.sourceImage = null;
            $scope.cropper.croppedImage   = null;
            $scope.bounds = {};
            $scope.bounds.left = 0;
            $scope.bounds.right = 0;
            $scope.bounds.top = 0;
            $scope.bounds.bottom = 0;

            $scope.error = '';
            $scope.userData = userData;
            $scope.ok = function () {
                $scope.busy = true;
                $scope.error = '';
                $http.post('/ajax/user/', $scope.userData)
                    .success(function(data) {
                        if ($scope.cropper.croppedImage) {
                            $http.post('/ajax/user/', JSON.stringify($scope.cropper.croppedImage))
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
        'angular-img-cropper',
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
            $http.get('/ajax/participant', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.participants = response.data;
                });
            $scope.texts = [];
            $http.get('/ajax/text', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.texts = response.data;
                });
            $scope.glossaries = [];
            $http.get('/ajax/glossary', {params: {project: $scope.projectId}})
                .then(function (response) {
                    $scope.glossaries = response.data;
                });
            $http.get('/ajax/tmx', {params: {project: $scope.projectId}})
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
                                        subject: $scope.text.subject,
                                        sourceLang: $scope.text.sourceLang,
                                        targetLang: $scope.text.targetLang,
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
                if (typeof id === 'undefined') {
                    $scope.options.currentTranslation.allGlossaries = !$scope.options.currentTranslation.allGlossaries;
                    if ($scope.options.currentTranslation.allGlossaries) {
                        $scope.options.currentTranslation.glossaries = $scope.glossaries.map(function (item) {return item.id;});
                    } else {
                        $scope.options.currentTranslation.glossaries = [];
                    }
                } else {
                    var index = $scope.options.currentTranslation.glossaries.indexOf(id);
                    if (index > -1) {
                        $scope.options.currentTranslation.glossaries.splice(index, 1);
                    } else {
                        $scope.options.currentTranslation.glossaries.push(id);
                    }
                    $scope.options.currentTranslation.allGlossaries = $scope.options.currentTranslation.glossaries.length === $scope.glossaries.length;
                }
            };
            $scope.toggleTmx = function (id) {
                if (typeof id === 'undefined') {
                    $scope.options.currentTranslation.allTmxes = !$scope.options.currentTranslation.allTmxes;
                    if ($scope.options.currentTranslation.allTmxes) {
                        $scope.options.currentTranslation.tmxes = $scope.tmxes.map(function (item) {return item.id;});
                    } else {
                        $scope.options.currentTranslation.tmxes = [];
                    }
                } else {
                    var index = $scope.options.currentTranslation.tmxes.indexOf(id);
                    if (index > -1) {
                        $scope.options.currentTranslation.tmxes.splice(index, 1);
                    } else {
                        $scope.options.currentTranslation.tmxes.push(id);
                    }
                    $scope.options.currentTranslation.allTmxes = $scope.options.currentTranslation.tmxes.length === $scope.tmxes.length;
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
                    machine: $scope.text.machine,
                    subject: $scope.text.subject,
                    sourceLang: $scope.text.sourceLang,
                    targetLang: $scope.text.targetLang,
                    glossaries: $scope.text.glossaries,
                    translations: $scope.text.translations,
                    tmxes: $scope.text.tmxes
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
            $scope.type = 'private';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'name': $scope.name,
                    'description': $scope.description,
                    'type': $scope.type
                };
                $scope.busy = true;
                $http.post('/ajax/project-create/', data)
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
                            entry.body = entry.body.replace("\n", '<br>');
                            updateTranslation(entry);
                            entriesById[entry['idInText']] = entry;
                        }
                        $scope.entries = entries;
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

                return '<span ng-show="entry !== activeEntry || !entry.editing">'
                    + elem.html() + '</span>' +
                    '<span ng-show="entry === activeEntry && entry.editing" ' +
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
                    allowBr = false,
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
        'textFilters',
        'LocalStorageModule'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('mainControllers', []);

    module.controller('mainCtrl', ['$scope', '$http', '$timeout', '$modal', '$window',
        function ($scope, $http, $timeout, $modal, $window) {

            var updateMessages = function () {
                $http.get('/ajax/message/').success(function (data) {
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
                $http.post('/ajax/message/', {id: message.id}).success(function (data) {
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
                switch ($scope.position) {
                    case 'top':
                        $scope.helpBlockStyle1['z-index'] = 10001;
                        break;
                    case 'left':
                        $scope.helpBlockStyle2['z-index'] = 10001;
                        break;
                    case 'right':
                        $scope.helpBlockStyle3['z-index'] = 10001;
                        break;
                }
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
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.position = 'top';
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
                $scope.position = 'top';
            };
            $scope.nextHelpStep = function () {
                $scope.currentBlock = false;
                $scope.helpText = false;
                $scope.hasNext = false;
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.position = 'top';
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

            $scope.showChatroom = false;
            $scope.toggleChat = function () {
                $scope.showChatroom = !$scope.showChatroom;
            };
            $scope.globalResize = function (window) {
                $scope.$broadcast('GlobalResize', window);
            };
            $scope.mouseup = function (event) {
                $scope.$broadcast('GlobalMouseup', event);
            };

            $scope.changeLanguage = function (language) {
                $http({
                    method: 'POST',
                    url: '/i18n/setlang/',
                    data: $.param({language: language}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function () {
                    $window.location.reload();
                })
            };
        }
    ]);

    module.controller('AllMessagesModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
            $scope.error = '';
            $http.get('/ajax/message/all').success(function (data) {
                $scope.messages = data;
                $timeout(updateMessages, 5000);
            }).error(function (data) {
            });

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('mainDirectives', []);

    //module.directive('resize', ['$window', function ($window) {
    //    return {
    //        scope: {
    //            resize: "="
    //        },
    //        link: function (scope, element, attr) {
    //            var w = angular.element($window);
    //            scope.$watch(function () {
    //                return {
    //                    'h': w.height(),
    //                    'w': w.width()
    //                };
    //            }, function (newValue) {
    //                scope.resize();
    //            }, true);
    //
    //            w.bind('resize', function () {
    //                scope.$apply();
    //            });
    //        }
    //    };
    //}]);
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
                    scope.resize(newValue);
                }, true);

                w.bind('resize', function () {
                    scope.$apply();
                });
            }
        };
    }]);
}());;(function () {
    'use strict';

    angular.module('mainModule', [
        'ui.bootstrap',
        'ngDragDrop',
        'mainControllers',
        'mainDirectives'
    ]);
}());