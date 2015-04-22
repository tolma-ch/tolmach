'use strict';

/* App Module */

(function () {
    angular.module('tolmachApp', [
    ])
        .controller('transCtrl', function ($scope, $http) {
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
            $scope.approveEntry = function (entry, parent) {
                $http.post('/api/entry-approve/', {id: entry.id}).success(function (data) {
                    entry.isApproved = true;
                    parent.approved = true;
                    parent.translation = entry.body;
                    $scope.activeEntry = null;
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
                $scope.activeEntry = $scope.entriesById[id];
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
        });
})();
