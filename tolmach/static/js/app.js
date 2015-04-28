'use strict';

/* App Module */

(function () {
    angular.module('tolmachApp', [
        'ui.bootstrap'
    ])
        .controller('transCtrl', function ($rootScope, $scope, $http) {
            $scope.activeEntry = null;
            $scope.textTab = 0;
            $scope.userIsManager = false;
            $http.post('.', {}).success(function (data) {
                var entries = data['entries'];
                $scope.userIsManager = !!data['user_is_manager'];
                $scope.user = data['user'];
                var entriesById = {},
                    i, entry;
                for(i = entries.length - 1; i >= 0; i--) {
                    entry = entries[i];
                    entry.mode = !!entry.translations.length ? 0 : 1;
                    entriesById[entry.idInText] = entry;
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
            $scope.toogleEntry = function (entry) {
                if (entry.approved) {
                    return;
                }
                if ($scope.activeEntry === entry) {
                    $scope.activeEntry = null;
                } else {
                    $scope.activeEntry = entry;
                    setTimeout(function () {
                        var $container = $('#translations-container'),
                            $elem = $('#entry-' + entry.id);
                        $container.scrollTop($container.scrollTop() + $elem.offset()['top'] - $container.offset()['top']);
                    }, 100);
                }
            };
            $scope.approveEntry = function (translation, entry) {
                $http.post('/api/entry-approve/', {id: translation.id}).success(function (data) {
                    translation.isApproved = true;
                    entry.approved = true;
                    entry.translation = translation.body;
                    $scope.activeEntry = null;
                    var t;
                    for (var i = entry.translations.length - 1; i >= 0; i--) {
                        t = entry.translations[i];
                        if (t.id !== translation.id) {
                            t.isApproved = false;
                        }
                    }
                })
            };
            $scope.disapproveEntry = function (entry, parent) {
                $http.post('/api/entry-disapprove/', {id: entry.id}).success(function (data) {
                    entry.isApproved = false;
                    parent.approved = false;
                    parent.translation = parent.body;
                    $scope.activeEntry = parent;
                })
            };
            $scope.suggestTranslation = function (entry) {
                var suggestionId = entry['suggestionId'],
                    data = {
                        id: entry.id,
                        text: entry.suggestion
                    };
                if (suggestionId) {
                    data['translation_id'] = suggestionId;
                }
                entry.suggestionId = false;
                $http.post('/api/entry-translate/', data).success(function (data) {
                    if (suggestionId) {
                        var i,
                            translation;
                        for (i = entry.translations.length - 1; i >= 0; i--) {
                            translation = entry.translations[i];
                            if (translation.id == suggestionId) {
                                translation.body = data.body;
                                if (translation.isApproved === true) {
                                    entry.approved = true;
                                    entry.translation = translation.body;
                                }
                                break;
                            }
                        }
                    } else {
                        entry.translations.push(data);
                    }
                    entry.mode = 0;
                })
            };
            $scope.focusEntry = function (id) {
                var entry = $scope.entriesById[id];
                if (entry.approved) {
                    return;
                }
                $scope.activeEntry = entry;
                setTimeout(function () {
                    var $container = $('#translations-container'),
                        $elem = $('#entry-' + id);
                    $container.scrollTop($container.scrollTop() + $elem.offset()['top'] - $container.offset()['top']);
                }, 100);
            };
            $scope.editTranslation = function (entry, translation) {
                entry.mode = 1;
                entry.suggestion = translation.body;
                entry.suggestionId = translation.id;
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
            }
        })

        .controller('projectsCtrl', function ($scope, $modal) {
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
        })
        .controller('NewProjectModalCtrl', function ($scope, $modalInstance, $http) {
            $scope.ok = function () {
                var data = {
                    'name': $scope.name,
                    'description': $scope.description,
                    'type': $scope.type
                };
                $scope.busy = true;
                $http.post('/api/project-create/', data)
                    .success(function(data, status, headers, config) {
                        location.reload();
                    })
                    .error(function(data, status, headers, config) {
                        $scope.busy = false;
                        //$modalInstance.close();
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        })

        .run(function ($http) {
            $http.defaults.headers.post['X-CSRFToken'] = window['csrfToken'];
        })
        .config(function ($interpolateProvider) {
            // replace {{ by {=
            $interpolateProvider.startSymbol('{=');
            // replace }} by =}
            $interpolateProvider.endSymbol('=}');
        })
        .directive('entry', function () {
            return {
                template: function(elem, attr) {
                    var id = attr['entry'];

                    return '<span ng-click="focusEntry(' + id + ')"' +
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
                template: function(elem, attr, scope) {
                    var word = attr['glossaryWord'];

                    return '<span ng-show="entry !== activeEntry || entry.mode !== 1">'
                                + elem.html() + '</span>' +
                           '<span ng-show="entry === activeEntry && entry.mode === 1"' +
                                 'class="glossary-word" ' +
                                 'ng-click="insertText($event, entry, \'' + word + '\')" ' +
                                 'tooltip-append-to-body="true" ' +
                                 'tooltip="' + word + '">'
                                + elem.html() + '</span>';
                },
                link: function (scope, element, attrs) {
                }
            };
        })
        .directive('content', function($compile, $parse) {
            return {
                link: function(scope, element, attr) {
                    var content = attr['content'];
                    element.html($parse(content)(scope));
                    $compile(element.contents())(scope);
                }
            }
        })
        .directive('insertText', function($rootScope, $parse) {
            return {
                link: function(scope, element, attrs) {
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
                            var sel = document.selection.createRange();
                            result = val;
                            scope.entry.suggestion = result;
                            scope.$apply();
                            domElement.focus();
                        } else if (domElement.selectionStart || domElement.selectionStart === 0) {
                            var startPos = domElement.selectionStart;
                            var endPos = domElement.selectionEnd;
                            var scrollTop = domElement.scrollTop;
                            result = domElement.value.substring(0, startPos) + val + domElement.value.substring(endPos, domElement.value.length);
                            scope.entry.suggestion = result;
                            scope.$apply();
                            domElement.focus();
                            domElement.selectionStart = startPos + val.length;
                            domElement.selectionEnd = startPos + val.length;
                            domElement.scrollTop = scrollTop;
                        } else {
                            result = domElement.value + val;
                            scope.entry.suggestion = result;
                            scope.$apply();
                            domElement.focus();
                        }
                    });
                }
            }
        })
        .filter('trusted', function($sce){
            return function(text) {
                return $sce.trustAsHtml(text);
            };
        });
})();
