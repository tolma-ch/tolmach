(function () {
    'use strict';

    /* App Module */

    var module = angular.module('tolmachApp', [
        'ui.select',
        'ui.toggle',
        'ngClickCopy',
        'mainModule',
        'profileModule',
        'projectModule',
        'projectsModule',
        'organizationsModule',
        'textModule',
        'chatModule',
        'dictModule'
    ]);

    module.run(function ($http) {
        $http.defaults.headers.post['X-CSRFToken'] = window.csrfToken;
    });
    module.config(function ($interpolateProvider, $httpProvider, $locationProvider) {
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
}());;(function () {
    'use strict';

    var module = angular.module('dictControllers', []);

    module.controller('DictCtrl', ['$scope', '$http', '$window', '$sce', 'Dict', '$rootScope',
        function ($scope, $http, $window, $sce, Dict, $rootScope) {
            var lastMeaningNum = 0;
            var showDictModal = 0;
            $rootScope.setDictWord = function (word) {
                $scope.word = word;
                $scope.searchWord();
            };
            $scope.dictSourceLang = window['translationSourceLang'];
            $scope.dictTargetLang = window['translationTargetLang'];
            $scope.style = {};
            $scope.$on('GlobalResize', function (e, w) {
                var height = w.h,
                    width = w.w;
            });
            $scope.textareaKeypress = function (event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (event.ctrlKey && (code === 13 || code === 10)) {
                    Dict.sendMessage(this.value);
                }
            };
            $scope.showMeanings = function (wordId) {
                console.log(wordId);
                $('.meanings').css('display', 'none');
                if (wordId != lastMeaningNum){
                    $('#meanings-' + wordId).css('display', 'block');
                }
                lastMeaningNum = wordId;
            };
            $scope.dictSwitchLangs = function () {
                var cur_source_lang = $scope.dictSourceLang;
                var cur_target_lang = $scope.dictTargetLang;
                $scope.dictSourceLang = cur_target_lang;
                $scope.dictTargetLang = cur_source_lang;
            };
            $scope.searchWord = function () {
                var notFoundBlock = document.getElementById('dict-nothing-found');
                notFoundBlock.style.display = "none";
                $scope.foundWords = [];
                $scope.wordToFind = "";

                var progressIcon = document.getElementById("dict-progress-anim");
                progressIcon.style.display = "inline-block";

                $http.post('/ajax/dict-search/', {
                        params: {
                            from: $scope.dictSourceLang,
                            dest: $scope.dictTargetLang,
                            phrase: $scope.word
                        }
                    }).success(function (res) {
                        var results = [];
                        angular.forEach(res, function (elem, key){
                            results.push({id: key,
                                        dict: elem['dict'],
                                        word: elem['word'],
                                        definition: elem['definition'].replace(/(\n)+/g, '<br />'),
                                        meanings: elem['meanings']
                            });
                        });
                        progressIcon.style.display = "none";
                        if (results && results.length == 0) {
                            var notFoundBlock = document.getElementById('dict-nothing-found');
                            notFoundBlock.style.display = "block";
                        } else {
                            $scope.wordToFind = $scope.word;
                            $scope.foundWords = results;
                        }
                    })
            }
        }
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('dictDirectives', []);

    module.directive('focusOn', ['$timeout', function($timeout) {
        return {
            restrict : 'A',
            link : function($scope,$element,$attr) {
                $scope.$watch($attr.focusOn,function(_focusVal) {
                    $timeout(function() {
                        //_focusVal ? $element[0].focus() : $element[0].blur();
                        if (_focusVal) {
                            $element[0].focus();
                            $element[0].setSelectionRange(0, $element[0].value.length);
                        } else {
                            $element[0].blur();
                        }
                    });
                });
            }
        }
    }]);
}());;(function () {
    'use strict';

    angular.module('dictModule', [
        'dictServices',
        'dictControllers',
        'dictDirectives'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('dictServices', []);

    module.factory('Dict', ['$http',
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

    var module = angular.module('organizationsControllers', []);

    module.controller('organizationsCtrl', ['$scope', '$uibModal', '$http',
        function ($scope, $uibModal, $http) {
            $scope.activeTab = window['activeTab'];
            $scope.orgId = window.userData['orgId'];
            $scope.members = [];

            $scope.reloadMembers = function () {
                $http.get('/ajax/orgs/members/', {params: {organization: $scope.orgId}})
                .then(function (response) {
                    $scope.members = response.data;
                });
            };
            if ($scope.activeTab === "members") {
                 $scope.reloadMembers();
            }

            $scope.createNewOrg = function () {
                var modalInstance = $uibModal.open({
                    templateUrl: 'newOrganizationModal.html',
                    controller: 'NewOrganizationModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function () {
                }, function () {
                });
            };

            $scope.addOrgParticipant = function () {
                var modalInstance = $uibModal.open({
                    templateUrl: 'addOrgParticipantModal.html',
                    controller: 'AddOrgParticipantModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function (member) {
                    $scope.members.push(member);
                }, function () {
                });
            };

            $scope.changeAdminStatus = function(member) {
                if(typeof(member.status) === "boolean") {
                    console.log(member.status);
                    var data = {
                        'organization': window.userData['orgId'],
                        'user': member.id,
                        'is_admin': member.status
                    };
                    $scope.busy = true;
                    $http.post('/ajax/orgs/members/', data)
                        .success(function (member) {
                            $scope.reloadMembers();
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            console.log(data);
                            $scope.busy = false;
                        });
                }
            };

            $scope.removeOrgParticipant = function (member) {
                var data = {
                    'organization': $scope.orgId,
                    'user': member.id
                };
                $scope.busy = true;
                $http.delete('/ajax/orgs/members/', {params: data})
                    .success(function () {
                        var i = $scope.members.indexOf(member);
                        if (i > -1) {
                            delete $scope.members.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

        }
    ]);

    module.controller('NewOrganizationModalCtrl', ['$scope', '$uibModalInstance', '$http',
        function ($scope, $uibModalInstance, $http) {
            $scope.name = generateRandomName();
            $scope.error = '';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'name': $scope.name.substring(0, 250)
                };
                $scope.busy = true;
                $http.post('/ajax/orgs/', data)
                    .success(function (data) {
                        location.href = '/orgs/' + data;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$uibModalInstance.close();
                    });
            };

            $scope.createOrgAdvancedOptions = false;
            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);

    module.controller('AddOrgParticipantModalCtrl', ['$scope', '$uibModalInstance', '$http', '$window',
        function ($scope, $uibModalInstance, $http, $window) {
            $scope.getUsers = function (query) {
                return $http.get('/ajax/get-users', {params: {q: query}})
                    .then(function (response) {
                        return response.data;
                    });
            };
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'organization': window.userData['orgId'],
                    'user': $scope.user.id
                };
                $scope.busy = true;
                $http.post('/ajax/orgs/members/', data)
                    .success(function (participant) {
                        $uibModalInstance.close(participant);
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
}());;(function () {
    'use strict';

    var module = angular.module('organizationsModule', [
        'ui.bootstrap',
        'organizationsControllers'
    ]);
}());;(function () {
    'use strict';

    var module = angular.module('profileControllers', []);

    module.controller('ProfileCtrl', ['$scope', '$uibModal',
        function ($scope, $uibModal) {
            $scope.userData = window['userData'];
            $scope.editProfile = function () {
                var modalInstance = $uibModal.open({
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

    var controller = module.controller('EditProfileModalCtrl', ['$scope', '$uibModalInstance', '$http', 'userData',
        function ($scope, $uibModalInstance, $http, userData) {
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
                                    $uibModalInstance.close(data);
                                });
                        } else {
                            $uibModalInstance.close(data);
                        }
                        location.reload();
                    })
                    .error(function(data) {
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

    module.controller('AddParticipantModalCtrl', ['$scope', '$uibModalInstance', '$http',
        function ($scope, $uibModalInstance, $http) {
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
                        $uibModalInstance.close(participant);
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
                    subject: $scope.text.subject,
                    split_mode: $scope.splitMode
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
                                    function getFirstKey( data ) {
                                        for (var elem in data ) {
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

    module.controller('projectsCtrl', ['$scope', '$uibModal', '$http', '$location',
        function ($scope, $uibModal, $http, $location) {
            $scope.page = parseInt($location.search().page ? $location.search().page : 1) || 1;
            $scope.projects = {};
            $scope.busy = false;

            var updateProjects = function () {
                $scope.busy = true;
                $http.get('/ajax/projects/' + window['active_tab'] + '/?page=' + $scope.page)
                    .then(function (response) {
                        $scope.projects = response.data;
                        $scope.busy = false;
                });
            };
            updateProjects();
            console.log($scope.projects);
            $scope.startNewProject = function () {
                var modalInstance = $uibModal.open({
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

            $scope.changePage = function (page_num) {
                if ($scope.busy) {
                    return;
                }
                if (1 <= page_num <= $scope.projects.paginator.num_pages) {
                    $scope.page = page_num;
                    updateProjects();
                    $location.search('page', $scope.page).replace();
                }
            };

        }
    ]);

    module.controller('NewProjectModalCtrl', ['$scope', '$uibModalInstance', '$http',
        function ($scope, $uibModalInstance, $http) {
            $scope.name = generateRandomName();
            $scope.error = '';
            $scope.type = 'private';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'name': $scope.name.substring(0, 250),
                    'description': $scope.description || " ",
                    'type': $scope.type,
                    'source_lang': $scope.source_lang,
                    'target_lang': $scope.target_lang,
                    'org_id': window.userData['orgId'] || 0
                };
                $scope.busy = true;
                $http.post('/ajax/project-create/', data)
                    .success(function (data) {
                        location.href = '/project/' + data;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$uibModalInstance.close();
                    });
            };

            $scope.addProjectAdvancedOptions = false;
            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
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

    module.controller('transCtrl', ['$rootScope', '$scope', '$sce', '$http', '$location', '$timeout', 'localStorageService',
        function ($rootScope, $scope, $sce, $http, $location, $timeout, localStorageService) {
            $rootScope.translationProgress = window['translation_progress'];
            $rootScope.translationCounts = window['translation_counts'];
            $scope.userMembershipStatus = window['userMembershipStatus'];
            $scope.currentTextId = window['textId'];
            $scope.currentTargetLang = window['translationTargetLang'];

            $scope.getHost = window['getHost'];
            $scope.isHttps = window['isHttps'];
            $scope.baseHost = ($scope.isHttps ? 'https' : 'http') + '://' + $scope.getHost;

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
                    console.log('updating progressbars');
                    $rootScope.translationProgress = ws_data['progress']['translation_progress'];
                    $rootScope.translationCounts = ws_data['progress']['translation_counts'];
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
                if ('entry_to_disable' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        var entry_to_disable = ws_data['entry_to_disable'];
                        $scope.entries.forEach(function (item, i, arr) {
                            if (item.id == entry_to_disable.id) {
                                var local_entry_to_disable = item;
                                //console.log("entry: " + item);
                                local_entry_to_disable.disabled = true;
                                local_entry_to_disable.approved = false;
                                var t;
                                for (var y = local_entry_to_disable['translations'].length - 1; y >= 0; y--) {
                                    t = local_entry_to_disable['translations'][y];
                                    t.isApproved = false;
                                }
                                if ($scope.activeEntry == local_entry_to_disable) {
                                    $scope.activeEntry = null;
                                }
                            }
                        });
                    }
                }
                if ('entry_to_enable' in ws_data) {
                    if (!($scope.user == ws_data['user'])) {
                        var entry_to_enable = ws_data['entry_to_enable'];
                        $scope.entries.forEach(function (item, i, arr) {
                            if (item.id == entry_to_enable.id) {
                                var local_entry_to_enable = item;
                                //console.log("entry: " + item);
                                local_entry_to_enable.disabled = false;
                                var t;
                                for (var y = local_entry_to_enable['translations'].length - 1; y >= 0; y--) {
                                    t = local_entry_to_enable['translations'][y];
                                    t.isApproved = false;
                                }
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
                                    "user": $scope.user,
                                    "page": $rootScope.page,
                                    "fragment": entry.idInText
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
                    var textAreaId = (entry.suggestionId) ? entry.suggestionId : entry.id;
                    entry.suggestion = localStorageService.get('sug-' + textAreaId, entry.suggestion) || "";
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
                            target_lang: window['translationTargetLang'],
                            short: true
                        }).success(function (data) {
                            $rootScope.translationProgress = data['translation_progress'];
                            $rootScope.translationCounts = data['translation_counts'];
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
                            page: $rootScope.page,
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
                        $rootScope.pagesCount = data['total_pages'];
                        $scope.entriesById = entriesById;
                        $scope.busy = false;

                        if ($scope.entryToFocus > 0) {
                            if ($scope.entryToFocus in $scope.entriesById){
                                if (!$scope.entriesById[$scope.entryToFocus].disabled) {
                                    $scope.toggleEntry($scope.entriesById[$scope.entryToFocus]);
                                } else {
                                    scrollToEntry($scope.entriesById[$scope.entryToFocus]);
                                }
                            }
                            $location.search('fragment', null).replace();
                            $scope.entryToFocus = 0;
                        }
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
            $scope.initialPage = parseInt($location.search().page ? $location.search().page : 1) || 1;
            $scope.entryToFocus = $location.search().fragment ? $location.search().fragment : 0;

            // Checking if it is initial text opening or direct link to the fragment
            if ($scope.initialPage == 1 && $scope.entryToFocus == 0) {
                // if this is simple text opening, getting the last position
                if (parseInt(window['savedPosition'].page) > 0) {
                    $scope.initialPage = parseInt(window['savedPosition'].page);
                    $scope.entryToFocus = parseInt(window['savedPosition'].fragment);

                    $location.search('page', $scope.initialPage).replace();
                }
            }

            $scope.countPerPage = 100;
            $rootScope.pagesCount = window['pagesCount'];
            $rootScope.page = ($scope.initialPage > $rootScope.pagesCount) ? ($rootScope.pagesCount) : ($scope.initialPage < 1 ? 1 : $scope.initialPage);
            $rootScope.paginatorBlur = function () {
                $rootScope.page = parseInt($rootScope.page) || 1;
                $rootScope.page = $rootScope.page > $rootScope.pagesCount ? $rootScope.pagesCount : ($rootScope.page < 1 ? 1 : $rootScope.page);
                updateEntries();
            };
            $rootScope.setPage = function (newPage) {
                $rootScope.editPage = false;
                $rootScope.page = newPage;
                updateEntries();
                $location.search('page', $rootScope.page).replace();
            };
            $scope.$on('GlobalClick', function (e, event) {
                if ($(event.target).parents('.text-overview__paginator').length === 0) {
                    $rootScope.editPage = false;
                }
            });
            $rootScope.paginatorKeypress = function (event) {
                var code = event.keyCode ? event.keyCode : event.which;
                if (code === 13 || code === 10) {
                    $rootScope.paginatorBlur();
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
            $rootScope.prevPage = function () {
                if ($scope.busy) {
                    return;
                }
                if ($rootScope.page > 1) {
                    $rootScope.page = $rootScope.page - 1;
                    updateEntries();
                    $location.search('page', $rootScope.page).replace();
                }
            };
            $rootScope.nextPage = function () {
                if ($scope.busy) {
                    return;
                }
                console.log($rootScope.page);
                if ($rootScope.page < $rootScope.pagesCount) {
                    $rootScope.page = $rootScope.page + 1;
                    updateEntries();
                    $location.search('page', $rootScope.page).replace();
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
            $scope.focusEntry = function (id) {
                var entry = $scope.entriesById[id];
                expandEntry(entry);
            };
            $scope.disableEntry = function (entry, skip_active_null) {
                skip_active_null = typeof skip_active_null !== 'undefined' ? skip_active_null : false;
                $http.post('/ajax/entry-disable/', {id: entry.id}).success(function () {
                    entry.disabled = true;
                    entry.approved = false;
                    entrySetEditingStatus(entry, 'stop');
                    var t;
                    for (var i = entry['translations'].length - 1; i >= 0; i--) {
                        t = entry['translations'][i];
                        t.isApproved = false;
                    }
                    if (!skip_active_null) {
                        $scope.activeEntry = null;
                    }
                })
            };
            $scope.enableEntry = function (entry) {
                $http.post('/ajax/entry-enable/', {id: entry.id}).success(function () {
                    entry.disabled = false;
                    var t;
                    for (var i = entry['translations'].length - 1; i >= 0; i--) {
                        t = entry['translations'][i];
                        t.isApproved = false;
                    }
                    $scope.activeEntry = entry;
                    entrySetEditingStatus(entry, 'start');
                })
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
            $scope.approveEntriesByUser = function (user) {
                $http.post('/ajax/entry-approve-by-user/', {translationTargetLang: $scope.currentTargetLang,
                                                            text: $scope.currentTextId,
                                                            userId: user.id}).success(function () {
                    $scope.activeEntry = null;
                })
            };
            $scope.disapproveEntriesByUser = function (user) {
                $http.post('/ajax/entry-disapprove-by-user/', {translationTargetLang: $scope.currentTargetLang,
                                                            text: $scope.currentTextId,
                                                            userId: user.id}).success(function () {
                    $scope.activeEntry = null;
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
                    var textAreaId = (entry.suggestionId) ? entry.suggestionId : entry.id;
                    localStorageService.remove("sug-" + textAreaId);
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
                    if (found === true && !someEntry.approved && !someEntry.disabled) {
                        $scope.toggleEntry(someEntry);
                        break;
                    }
                    if (someEntry === entry) {
                        found = true;
                    }
                }
            };
            var skipHotKey = function (entry) {
                // $('#entry-' + entry.idInText).trigger("blur");
                $timeout(function () {
                    $scope.disableEntry(entry, true);
                }, 501);
                var i,
                    found = false;
                for (i in $scope.entries) {
                    var someEntry = $scope.entries[i];
                    if (found === true && !someEntry.approved && !someEntry.disabled) {
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
                if (event.altKey) {
                    event.stopPropagation();
                    event.preventDefault();
                    if (code === 77) { // Alt - m
                        // hotkey for copying machine translation to textarea
                        if (typeof entry.yaMachines !== 'undefined') {
                            entry.suggestion = entry.yaMachines[0].text;
                            var input = $('#entry-suggestion-' + entry.id);
                            input.focus();
                            setTimeout(function () {
                                moveCursorToEnd(input[0]);
                            }, 10);
                        }
                    } else if (code === 79) { // Alt - o
                        // hotkey for copying original text to textarea
                        entry.suggestion = entry.rawBody;
                        var input = $('#entry-suggestion-' + entry.id);
                        input.focus();
                        setTimeout(function () {
                            moveCursorToEnd(input[0]);
                        }, 10);
                    } else if (code === 83) { // Alt - s
                        skipHotKey(entry);
                    }
                }
            };
            $scope.textareaAutoSave = function (event, entry) {
                var textAreaId = (entry.suggestionId) ? entry.suggestionId : entry.id;
                localStorageService.set('sug-' + textAreaId, entry.suggestion);
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

            $rootScope.showDictModal = false;
            $scope.lastFocusedEntryInputId = '';
            $scope.lastFocusedEntryInputPosition = 0;
            $rootScope.dictOpener = function () {
                $rootScope.showDictModal = !$rootScope.showDictModal;
            };
            $rootScope.dictClose = function () {
                $rootScope.showDictModal = false;
            };
            // $scope.dict
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
                        if (!$rootScope.showDictModal) {
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
                        $rootScope.showDictModal = !$rootScope.showDictModal;
                    }
                    return;
                }
                if (event.altKey) {
                    if (code === 68) { // Alt - d
                        event.stopPropagation();
                        event.preventDefault();
                        e.preventDefault();
                        // hotkey for showing dictionary window
                        if (!$rootScope.showDictModal) {
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
                        $rootScope.showDictModal = !$rootScope.showDictModal;
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
                                if (!someEntry.approved && !someEntry.disabled) {
                                    entry = someEntry;
                                    break;
                                }
                            }
                        }
                        if (code === 40) {
                            //down
                            for (index++; index < $scope.entries.length; index++) {
                                someEntry = $scope.entries[index];
                                if (!someEntry.approved && !someEntry.disabled) {
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
            var getSelectionText = function (target) {
                    var text = "",
                        x = 0,
                        y = 0,
                        width = 0;
                    if (window.getSelection) {
                        var sel = window.getSelection(),
                            range = sel.rangeCount ? sel.getRangeAt(0) : false,
                            rect = range ? range.getClientRects()[0] : false;
                        if (!target || target.contains(sel.baseNode)) {
                            if (rect) {
                                y = rect.bottom;
                                x = rect.left;
                                width = rect.right - rect.left;
                            }
                            text = sel.toString();
                        }
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
                translate = function (target) {
                    var selection = getSelectionText(target),
                        phrase = selection[0].trim().toLowerCase(),
                        coords = {'x': selection[1], 'y': selection[2]},
                        width = selection[3];
                    if (!phrase) {
                        return;
                    }
                    $rootScope.setDictWord(phrase);
                    $rootScope.showDictModal = true;
                    // var prevPhrase = $scope.translatedPhrase;
                    // $scope.translatedPhrase = phrase;
                    // if (phrase === prevPhrase) {
                    //     $scope.$parent.showTranslatePopup = false;
                    //     $scope.translatedPhrase = false;
                    //     return;
                    // }
                    // $http.jsonp('https://glosbe.com/gapi/translate', {
                    //     params: {
                    //         from: $scope.langPair3[0],
                    //         dest: $scope.langPair3[1],
                    //         phrase: phrase,
                    //         callback: 'JSON_CALLBACK',
                    //         format: 'json'
                    //     }
                    // }).success(function (res) {
                    //     var results = [];
                    //     if (angular.isArray(res['tuc'])) {
                    //         angular.forEach(res['tuc'], function (elem) {
                    //             if (elem['phrase'] && elem['phrase']['text']) {
                    //                 results.push(elem['phrase']['text']);
                    //             }
                    //         });
                    //     }
                    //     $scope.$parent.translationResults = results;
                    //     $scope.$parent.translatePopupStyle = {
                    //         display: 'block',
                    //         left: coords['x'] + 'px',
                    //         top: coords['y'] + 'px'
                    //     };
                    //     $scope.$parent.showTranslatePopup = true;
                    //     if ($scope.$parent.showTranslatePopup) {
                    //         $timeout(function () {
                    //             var elem = $('#translation-popup'),
                    //                 elemWidth = elem.width(),
                    //                 left = coords['x'] + (width - elemWidth) / 2;
                    //             $scope.$parent.translatePopupStyle.left = left + 'px';
                    //         },1);
                    //     }
                    // })
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
            $scope.mouseup = function ($event) {
                translate($event.target);
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
}());;(function () {
    'use strict';

    var module = angular.module('textFilters', []);

    module.filter('trusted', ['$sce', function ($sce) {
        return function (text) {
            return $sce.trustAsHtml(text);
        };
    }]);

    module.filter('range', function() {
        return function(input, total) {
            total = parseInt(total);

            for (var i=0; i<total; i++) {
                input.push(i);
            }

            return input;
        };
    });
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

    module.controller('mainCtrl', ['$scope', '$http', '$interval', '$uibModal', '$window', '$rootScope',
        function ($scope, $http, $interval, $uibModal, $window, $rootScope) {

            $rootScope.editPage = false;
            $rootScope.updateMessages = function () {
                $http.get('/ajax/message/').success(function (data) {
                    $scope.messages = data;
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
            $scope.showAllMessages = function () {
                var modalInstance = $uibModal.open({
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
            $interval($rootScope.updateMessages, 5000);

            $scope.showSearch = false;
            $scope.globalSearch = function (query) {
                $scope.searchTextId = window['textId'] !== undefined ? window['textId'] : 0;
                $scope.searchTargetLang = window['translationTargetLang'] !== undefined ? window['translationTargetLang'] : 'none';
                return $http.get('/ajax/search', {params: {q: query,
                                                           textId: $scope.searchTextId,
                                                           targetLang: $scope.searchTargetLang}})
                    .then(function (response) {
                        return response.data;
                    });
            };
            $scope.onSearchSelect = function($item, $model, $label){
                $scope.$item = $item;
                $scope.$model = $model;
                $scope.$label = $label;
                console.log($scope.item);
                window.location = $scope.$item.link;

                // only needed when updating angular-routed urls including "#"
                if ($scope.$item.link.includes("#")) {
                    window.location.reload(true);
                }
            };

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
            $scope.isFullscreenActive = false;
            $scope.toggleFullscreen = function () {
                if (screenfull.enabled) {
                    if (!screenfull.isFullscreen) {
                        screenfull.request();
                        $scope.isFullscreenActive = true;
                    } else {
                        screenfull.exit();
                        $scope.isFullscreenActive = false;
                    }
                }
            };
            function fullscreenchange() {
                if (screenfull.enabled) {
                    var elem = screenfull.element;

                    $('#status').text('Is fullscreen: ' + screenfull.isFullscreen);

                    if (elem) {
                        $('#element').text('Element: ' + elem.localName + (elem.id ? '#' + elem.id : ''));
                    }

                    if (!screenfull.isFullscreen) {
                        $('#external-iframe').remove();
                        document.body.style.overflow = 'auto';
                    }
                }
			}

            if (screenfull.enabled) {
                screenfull.on('change', fullscreenchange);
            }

			// Set the initial values
			fullscreenchange();
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

    module.controller('AllMessagesModalCtrl', ['$scope', '$uibModalInstance', '$http', '$rootScope',
        function ($scope, $uibModalInstance, $http, $rootScope) {
            $scope.error = '';
            $http.get('/ajax/message/all').success(function (data) {
                $scope.messages = data;
            }).error(function (data) {
            });
            $scope.readMessage = function (message) {
                if (message.was_read !== true) {
                    $http.post('/ajax/message/', {id: message.id}).success(function (data) {
                        for (var i in $scope.messages) {
                            if ($scope.messages[i].id == message.id) {
                                $scope.messages[i].was_read = true;
                            }
                        }
                        $rootScope.updateMessages();
                    }).error(function (data) {
                    })
                }
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
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